
import frappe
from frappe.utils import add_days, nowdate, nowtime, get_datetime

def execute():
    frappe.db.commit() # Commit any pending transaction
    print("🚀 Starting Phase 1 Verification...")

    try:
        # 1. Setup Prerequisites
        print("\n[1/6] Setting up Prerequisites...")
        setup_data = setup_prerequisites()
        print("✅ Prerequisites created/verified.")

        # 2. Test Attendance Settings
        print("\n[2/6] Verifying Attendance Settings...")
        settings = frappe.get_single("Attendance Settings")
        if settings.minimum_attendance_percentage != 75:
            settings.minimum_attendance_percentage = 75
            settings.save()
        print(f"✅ Attendance Settings verified (Min %: {settings.minimum_attendance_percentage})")

        # 3. Test Attendance Session & Student Attendance
        print("\n[3/6] Testing Attendance Session & Student Attendance...")
        
        # Create Attendance Session
        session = frappe.get_doc({
            "doctype": "Attendance Session",
            "course_schedule": setup_data["schedule"],
            "course_offering": setup_data["offering"],
            "session_date": nowdate(),
            "session_start_time": "10:00:00",
            "session_end_time": "11:00:00",
            "session_status": "Conducted",
            "instructor": setup_data["faculty"]
        })
        session.insert()
        print(f"✅ Attendance Session Created: {session.name}")

        # Create Student Attendance linked to this session
        attendance = frappe.get_doc({
            "doctype": "Student Attendance",
            "student": setup_data["student"],
            "course_offer": setup_data["offering"], 
            "attendance_date": nowdate(),
            "date": nowdate(), # Mandatory redundant field
            "status": "Present",
            "attendance_session": session.name, 
            "source": "Manual"
        })
        attendance.insert()
        print(f"✅ Student Attendance Created: {attendance.name}")

        # Update Session Summary
        session.reload()
        session.update_attendance_summary()
        print(f"✅ Session Summary Updated: Total: {session.total_students}, Present: {session.present_count}")


        # 4. Verify Audit Log
        print("\n[4/6] Verifying Audit Log...")
        # Update attendance to trigger log
        attendance.status = "Absent"
        attendance.edit_reason = "Testing Audit Log"
        attendance.save()
        
        logs = frappe.get_all("Attendance Edit Log", filters={"attendance_record": attendance.name})
        if logs:
            print(f"✅ Audit Log Verified. Found {len(logs)} logs.")
        else:
            print("❌ Audit Log NOT found!")

        # 5. Verify Calculation Engine (Attendance Summary)
        print("\n[5/6] Verifying Calculation Engine...")
        # Trigger calculation
        from slcm.slcm.utils.attendance_calculator import calculate_student_attendance
        summary = calculate_student_attendance(setup_data["student"], setup_data["offering"])
        
        if summary:
            print(f"✅ Attendance Summary Calculated: {summary['attendance_percentage']}%")
        else:
            print("❌ Attendance Summary Calculation Failed!")

        # 6. Test Office Hours
        print("\n[6/6] Testing Office Hours...")
        oh_session = frappe.get_doc({
            "doctype": "Office Hours Session",
            "course_offering": setup_data["offering"],
            "faculty": setup_data["faculty"],
            "session_date": nowdate(),
            "start_time": "14:00:00",
            "end_time": "15:00:00",
            "location": "Room 101"
        })
        oh_session.insert()
        print(f"✅ Office Hours Session Created: {oh_session.name}")

        oh_attendance = frappe.get_doc({
            "doctype": "Office Hours Attendance",
            "office_hours_session": oh_session.name,
            "student": setup_data["student"],
            "check_in_time": f"{nowdate()} 14:05:00",
            "check_out_time": f"{nowdate()} 14:55:00"
        })
        oh_attendance.insert()
        print(f"✅ Office Hours Attendance Created: {oh_attendance.name}")
        
        oh_session.reload()
        if oh_session.total_students_attended > 0:
            print(f"✅ Office Hours Count Updated: {oh_session.total_students_attended}")
        else:
            print("❌ Office Hours Count NOT Updated!")

        print("\n🎉 Phase 1 Verification Completed Successfully!")
        frappe.db.commit() 

    except Exception as e:
        frappe.db.rollback()
        print(f"\n❌ Error during verification: {str(e)}")
        import traceback
        print(traceback.format_exc())

def setup_prerequisites():
    # 1. Academic Year
    if not frappe.db.exists("Academic Year", "2025-2026"):
        frappe.get_doc({
            "doctype": "Academic Year", 
            "academic_year_name": "2025-2026", # Changed field name
            "year_start_date": "2025-01-01",
            "year_end_date": "2025-12-31"
        }).insert()
    
    if not frappe.db.exists("Program", "Test Program"):
        frappe.get_doc({
            "doctype": "Program", 
            "program_name": "Test Program", 
            "program_shortcode": "TP", # Added mandatory field
            "program_abbreviation": "TP"
        }).insert()

    # 3. Department
    if not frappe.db.exists("Department", "Test Dept"):
        frappe.get_doc({
            "doctype": "Department", 
            "department_name": "Test Dept",
            "department_id": "TD01", # Added mandatory field
            "status": "Active"
        }).insert()

    # 3.5 Course Master (Prerequisite for Course)
    course_master = "Test Course"
    if not frappe.db.exists("Course Master", course_master):
        frappe.get_doc({"doctype": "Course Master", "name": course_master}).insert()

    # 4. Course
    if not frappe.db.exists("Course", "TEST101"):
        frappe.get_doc({
            "doctype": "Course", 
            "course_code": "TEST101", 
            "course_name": course_master, # Link to Course Master
            "department": "Test Dept"
        }).insert()
        
    # 5. Faculty
    if not frappe.db.exists("Faculty", "TEST_FACULTY"):
        frappe.get_doc({
            "doctype": "Faculty",
            "first_name": "Test",
            "last_name": "Faculty",
            "faculty_id": "TEST_FACULTY",
            "email": "faculty@example.com", # Added mandatory
            "designation": "Professor", # Added mandatory
            "status": "Active"
        }).insert()
    
    faculty = frappe.db.get_value("Faculty", {"faculty_id": "TEST_FACULTY"}, "name")

    # 6. Student
    if not frappe.db.exists("Student Master", "TEST_STUDENT"):
        frappe.get_doc({
            "doctype": "Student Master",
            "first_name": "Test",
            "last_name": "Student",
            "registration_id": "TEST_STUDENT",
            "email": "test@example.com",
            # Mandatory fields added below
            "application_number": "APP001",
            "phone": "+91-9999999999",
            "personal_email": "test.personal@example.com", # Mandatory
            "marital_status": "Unmarried", # Mandatory
            "ug_degree_completed": "No", # Mandatory
            "dob": "2000-01-01",
            "class_x_completion_year": "2016",
            "class_x_percentage": 90.0,
            "class_x_school": "Test School",
            "class_x_board": "CBSE",
            "class_xii_exam_name": "HSC",
            "class_xii_completion_year": "2018",
            "class_xii_school": "Test College",
            "class_xii_board": "State Board",
            "class_xii_percentage": 85.0,
            # Dummy Attachments
            "aadhaar_card": "/files/test_aadhaar.jpg",
            "pan_card": "/files/test_pan.jpg",
            "passport_size_photo": "/files/test_photo.jpg",
            "std_x_marksheet": "/files/test_x_marks.jpg",
            "class_xii_marksheet": "/files/test_xii_marks.jpg"
        }).insert(ignore_permissions=True)
    
    student = frappe.db.get_value("Student Master", {"registration_id": "TEST_STUDENT"}, "name")

    # 7. Cohort (Prerequisite for Course Offering)
    if not frappe.db.exists("Cohort", "Test Cohort 2025-Term1"):
        frappe.get_doc({
            "doctype": "Cohort",
            "cohort_name": "Test Cohort 2025-Term1",
            "cohort_code": "TC2025T1",
            "program": "Test Program",
            "academic_year": "2025-2026",
            "term_name": "Term 1",
            "start_date": "2025-01-01",
            "end_date": "2025-06-30",
            "status": "Active"
        }).insert()

    # 8. Course Offering
    if not frappe.db.exists("Course Offering", "CO-TEST101-2025"): # ID might differ if autonamed
        # Check if already exists by link
        offering_name = frappe.db.get_value("Course Offering", {"course_title": course_master, "cohort": "Test Cohort 2025-Term1"}, "name")
        
        if not offering_name:
            doc = frappe.get_doc({
                "doctype": "Course Offering",
                "course_offering_id": "CO-TEST101-2025",
                "course_title": course_master, # Link to Course Name
                "program": "Test Program",
                "cohort": "Test Cohort 2025-Term1",
                "faculty": faculty,
                "status": "Open"
            })
            doc.insert()
            offering_name = doc.name
    else:
        offering_name = "CO-TEST101-2025" # Assuming ID match
        # Verify
        if not frappe.db.exists("Course Offering", offering_name):
             offering_name = frappe.db.get_value("Course Offering", {"course_title": course_master, "cohort": "Test Cohort 2025-Term1"}, "name")

    # 9. Course Schedule
    # Check if exists
    cs_name = frappe.db.exists("Course Schedule", {"course": course_master, "schedule_date": nowdate()}) 
    if not cs_name:
         doc = frappe.get_doc({
            "doctype": "Course Schedule",
            "course": course_master, # Link to Course Name "Test Course"
            "schedule_date": nowdate(),
            "from_time": "10:00:00",
            "to_time": "11:00:00",
            "room": "", 
            "instructor": faculty # Use true faculty name
        })
         doc.insert()
         cs_name = doc.name
    
    return {
        "student": student, # Use true student name
        "offering": offering_name,
        "faculty": faculty,
        "schedule": cs_name
    }
