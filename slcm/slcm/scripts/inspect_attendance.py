import frappe

def execute():
    student_name = "Jenifar"
    course_title = "Law of Crime"
    
    print(f"\n--- INSPECTING ATTENDANCE FOR {student_name} ---")
    
    # 1. Get IDs
    s = frappe.get_all("Student Master", filters={"first_name": student_name}, limit=1)
    if not s: print("Student not found"); return
    student_id = s[0].name
    
    co = frappe.get_all("Course Offering", filters={"course_title": course_title}, limit=1)
    if not co: print("Course Offering not found"); return
    course_offering_id = co[0].name
    
    print(f"Student: {student_id}")
    print(f"Course Offering: {course_offering_id}")
    
    # 2. Check Summary Docs
    summaries = frappe.get_all("Attendance Summary", 
        filters={"student": student_id, "course_offering": course_offering_id},
        fields=["name", "creation", "modified", "total_classes", "attended_classes"]
    )
    print(f"\nFound {len(summaries)} Summaries:")
    for sum_doc in summaries:
        print(f"- {sum_doc.name} (Created: {sum_doc.creation}): Total={sum_doc.total_classes}, Attended={sum_doc.attended_classes}")

    # 3. Check Student Attendance Records
    print(f"\nScanning 'Student Attendance' records for Student={student_id} AND CourseOffer={course_offering_id}")
    recs = frappe.get_all("Student Attendance",
        filters={"student": student_id, "course_offer": course_offering_id},
        fields=["name", "attendance_date", "status", "session_type", "hours_counted", "docstatus", "based_on"]
    )
    
    if not recs:
        print("❌ NO Student Attendance records found linked to this Course Offering.")
        # Check if maybe they are linked to the Course but NOT the Offering?
        # Logic uses course_offer.
        
        print("\nChecking records linked to Student only (Last 5):")
        all_recs = frappe.get_all("Student Attendance", 
            filters={"student": student_id}, 
            fields=["name", "course_offer", "course", "attendance_date"],
            limit=5, order_by="creation desc"
        )
        for r in all_recs:
             print(f"- {r.name}: CourseOffer={r.course_offer}, Course={r.course}")
    else:
        for r in recs:
             print(f"- {r.name}: {r.attendance_date} | {r.status} | Type={r.session_type} | Hours={r.hours_counted} | DocStatus={r.docstatus} | BasedOn={r.based_on}")

