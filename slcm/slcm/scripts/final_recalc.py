import frappe
from slcm.slcm.utils.attendance_calculator import calculate_student_attendance

def execute():
    student_name = "Jenifar"
    course_title = "Law of Crime"
    
    # Get IDs
    s = frappe.get_all("Student Master", filters={"first_name": student_name}, limit=1)[0]
    co = frappe.get_all("Course Offering", filters={"course_title": course_title}, limit=1)[0]
    
    print(f"Recalculating for {s.name} / {co.name}...")
    res = calculate_student_attendance(s.name, co.name)
    print(f"Result - Eligible: {res['eligible_for_exam']}")
