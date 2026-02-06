import frappe
from frappe.utils import nowdate, add_to_date
import json

def run_verification():
    print("Starting verification (Bulk Attendance Fix)...")
    frappe.db.commit()

    # Find offering
    offering = frappe.get_all("Course Offering", filters={"status": "Open"}, fields=["name", "course_title", "program", "term_name"], limit=1)
    if not offering:
        print("No open Course Offering found. Cannot verify.")
        return
    offering = offering[0]
    
    # Fixing potential typo
    term_name = offering.term_name
    if term_name == "Semster I":
        term_name = "Semester I"

    # Find a valid Student Group (with students)
    student_group = None
    groups = frappe.get_all("Student Group", fields=["name", "program"])
    for g in groups:
        # Check if it has students
        if frappe.db.count("Student Group Student", {"parent": g.name, "active": 1}) > 0:
            student_group = g.name
            print(f"Found valid Student Group: {student_group}")
            break
            
    if not student_group:
        print("No Student Group with students found. Cannot verify.")
        return

    # 1. Create Class Schedule
    check_date = add_to_date(nowdate(), days=7)
    
    cs_doc = frappe.get_doc({
        "doctype": "Class Schedule",
        "schedule_date": check_date,
        "from_time": "09:00:00",
        "to_time": "10:00:00",
        "course_offering": offering.name,
        "course": offering.course_title,
        "programme": offering.program,
        "student_group": student_group, # Added
        "term": term_name,
        "repeat_frequency": "Never"
    })
    
    cs_doc.insert(ignore_permissions=True)
    print(f"Created Class Schedule: {cs_doc.name}")
    frappe.db.commit()

    # 2. Verify Attendance Session Created (Scheduled)
    session_name = frappe.db.exists("Attendance Session", {
        "class_schedule": cs_doc.name,
        "session_date": check_date
    })
    
    if not session_name:
        print("FAILURE: Session not created automatically.")
        return

    session = frappe.get_doc("Attendance Session", session_name)
    if session.session_status != "Scheduled":
        print(f"WARNING: Initial status is {session.session_status}, expected Scheduled")
    
    print(f"Session created: {session.name} (Status: {session.session_status}, Marked: {session.attendance_marked})")

    # 3. Mark Attendance using API
    # Find a student in this offering/program
    # Logic in API fetches students from Student Group
    # We need to know which Student Group was assigned.
    student_group = session.student_group
    print(f"Using Student Group: {student_group}")
    
    group_students = frappe.get_all("Student Group Student", filters={"parent": student_group, "active": 1}, fields=["student"])
    if not group_students:
        print("No students in group. Cannot test attendance marking.")
        return
        
    student_id = group_students[0].student
    print(f"Marking attendance for student: {student_id}")

    # Call API
    from slcm.api.bulk_attendance import mark_attendance
    
    # Simulate UI call
    try:
        mark_attendance(
            students_present=[{"student": student_id}],
            students_absent=[],
            student_group=student_group,
            class_schedule=cs_doc.name,
            date=check_date,
            based_on="Class Schedule"
        )
        print("Attendance API called successfully.")
    except Exception as e:
        print(f"API Call Failed: {e}")
        return

    frappe.db.commit() # Commit API changes

    # 4. Verify Session Status Update
    session.reload()
    print(f"Session Update: Name={session.name}, Status={session.session_status}, Marked={session.attendance_marked}")
    
    if session.session_status == "Conducted" and session.attendance_marked == 1:
        print("SUCCESS: Session status updated to Conducted and Attendance Marked = 1.")
    else:
        print("FAILURE: Session status not updated.")

    # 5. Verify Attendance Summary Update (Triggered by calc)
    # The calc runs async in enqueue usually? 
    # The API calls session.update_attendance_summary() which calculates present/absent counts.
    # But calculate_student_attendance is called by Student Attendance hooks (on update).
    # Since we use enqueue 'short' queue in hook, it might not run immediately in test script without worker.
    # Use frappe.flags.in_test = True maybe or manually call it.
    
    # Let's check session summary counts first
    if session.present_count >= 1:
         print(f"SUCCESS: Session Present Count updated to {session.present_count}")
    else:
         print(f"FAILURE: Session Present Count is {session.present_count}")

    # Cleanup
    frappe.delete_doc("Class Schedule", cs_doc.name, force=1)
    frappe.delete_doc("Attendance Session", session.name, force=1)
    # Delete created student attendance
    sa = frappe.db.exists("Student Attendance", {"attendance_session": session.name})
    if sa:
        frappe.delete_doc("Student Attendance", sa, force=1)

    frappe.db.commit()
    print("Cleanup done.")
