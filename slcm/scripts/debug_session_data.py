import frappe

def debug_session(session_name):
    print(f"Checking Session: {session_name}")
    
    # 1. Check if Session exists
    if not frappe.db.exists("Attendance Session", session_name):
        print("Session not found!")
        return

    # 2. Check Student Attendance records linked to this session
    attendance_records = frappe.db.sql("""
        SELECT name, student, status, attendance_session 
        FROM `tabStudent Attendance` 
        WHERE attendance_session = %s
    """, session_name, as_dict=True)
    
    print(f"Found {len(attendance_records)} Student Attendance records for this session.")
    for att in attendance_records:
        print(f" - {att.name}: Student={att.student}, Status={att.status}")
        
        # 3. Check if Student Master exists for this student
        student_exists = frappe.db.exists("Student Master", att.student)
        print(f"   -> Linked Student Master '{att.student}' exists? {student_exists}")

    # 4. Run the query used in the code to see what it returns
    code_query_results = frappe.db.sql("""
        SELECT sa.student, s.first_name, sa.status, s.gender
        FROM `tabStudent Attendance` sa
        JOIN `tabStudent Master` s ON sa.student = s.name
        WHERE sa.attendance_session = %s
    """, session_name, as_dict=True)
    print(f"Code Query returned {len(code_query_results)} rows.")

debug_session("AS-2026-00008")
