import frappe
from slcm.slcm.utils.attendance_calculator import get_student_group

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

debug_session("AS-2026-00025")

# Test get_student_group
try:
    from slcm.slcm.utils.attendance_calculator import get_student_group
    # Fetch a student from the session to test
    students = frappe.db.sql("SELECT student FROM `tabStudent Attendance` WHERE attendance_session = 'AS-2026-00025' LIMIT 1", as_dict=True)
    if students:
        student = students[0].student
        offering = frappe.db.get_value("Attendance Session", "AS-2026-00025", "course_offering")
        print(f"\nTesting get_student_group for {student} in {offering}:")
        group = get_student_group(student, offering)
        print(f"Result: {group}")
    else:
        print("\nNo students found in session to test get_student_group")
except Exception as e:
    print(f"\nError testing get_student_group: {e}")
