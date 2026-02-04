import frappe

def execute():
    student_name = "Jenifar"
    course_title = "Law of Crime"
    
    s = frappe.get_all("Student Master", filters={"first_name": student_name}, limit=1)[0]
    co = frappe.get_all("Course Offering", filters={"course_title": course_title}, limit=1)[0]
    course_id = frappe.db.get_value("Course Offering", co.name, "course_title")
    
    # Create new app since old is cancelled
    doc = frappe.new_doc("FA MFA Application")
    doc.student = s.name
    doc.course = course_id
    doc.application_type = "First Attempt (FA)"
    doc.reason = "Medical Reasons"
    doc.status = "Approved"
    doc.examination_date = "2026-05-10" 
    doc.event_from = "2026-05-08" # event_date might be event_from/event_to
    doc.event_to = "2026-05-08"
    doc.proof_document = "/files/proof.pdf"
    doc.approver = "Administrator"
    doc.insert(ignore_permissions=True)
    doc.submit()
    print(f"Re-created FA/MFA App: {doc.name}")
    
    from slcm.slcm.utils.attendance_calculator import calculate_student_attendance
    calculate_student_attendance(s.name, co.name)
    print("Recalculated.")
