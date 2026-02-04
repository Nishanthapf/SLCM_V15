import frappe

def execute():
    student_name = "Jenifar"
    course_title = "Law of Crime"
    
    print(f"\n--- DEBUGGING FOR {student_name} / {course_title} ---")
    
    # 1. FIND CORRECT IDs
    s = frappe.get_all("Student Master", filters={"first_name": student_name}, limit=1)
    if not s:
        print("Student not found")
        return
    student_id = s[0].name
    print(f"Student ID: {student_id}")
    
    co = frappe.get_all("Course Offering", filters={"course_title": course_title}, limit=1)
    if not co:
        print("Course Offering not found")
        return
    course_offering_id = co[0].name
    print(f"Course Offering ID: {course_offering_id}")
    
    # 2. CHECK ATTENDANCE SESSIONS (Denominator)
    print("\n[Denominator Check] Attendance Sessions (Lecture/Tutorial):")
    sessions = frappe.get_all("Attendance Session", 
        filters={"course_offering": course_offering_id},
        fields=["name", "session_type", "session_status", "duration_hours", "session_date"]
    )
    if not sessions:
        print("❌ NO ATTENDANCE SESSIONS FOUND. Total Classes will be 0.")
    else:
        for sess in sessions:
            print(f"- {sess.name}: {sess.session_date} | {sess.session_type} | {sess.session_status} | {sess.duration_hours} hrs")
    
    # 3. CHECK FA/MFA APPLICATIONS (Override)
    print("\n[Override Check] FA/MFA Applications:")
    apps = frappe.get_all("FA MFA Application",
        filters={"student": student_id, "course": course_title}, # FA MFA links to Course Name, not Offering usually? Check logic
        fields=["name", "status"]
    )
    # Logic uses: course_id = frappe.db.get_value("Course Offering", course_offering, "course_title")
    # Then queries FA MFA with "course": course_id
    
    if apps:
        for app in apps:
            print(f"- {app.name}: Status = {app.status}")
    else:
        print("No FA/MFA Applications found.")

    # 4. CHECK SUMMARY DOC
    summary = frappe.get_all("Attendance Summary", 
        filters={"student": student_id, "course_offering": course_offering_id},
        fields=["name", "total_classes", "attended_classes", "attendance_percentage", "eligible_for_exam"]
    )
    if summary:
        print(f"\n[Current DB State] {summary[0]}")
    else:
        print("\nSummary document not found.")
