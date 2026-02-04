import frappe
from frappe.utils import now_datetime
from slcm.api.bulk_attendance import mark_attendance

def execute():
    frappe.db.rollback()
    
    # SETUP
    group = setup_data()
    
    student = "STU-TOOL-TEST"
    
    print("\n--- TEST: MARK ATTENDANCE ---")
    try:
        # Simulate the call from JS
        # JS passes: students_present=[{student: ...}], date="YYYY-MM-DD", based_on="Student Group", ...
        
        present_list = [{"student": student, "student_name": "Test Student"}]
        
        result = mark_attendance(
            students_present=present_list,
            student_group=group,
            date="2026-02-04",
            based_on="Student Group", 
            # group_based_on="Course" # Not used by python function but passed by JS
        )
        print(f"Result: {result}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    frappe.db.rollback()

def setup_data():
    student = "STU-TOOL-TEST"
    if not frappe.db.exists("Student Master", student):
        doc = frappe.new_doc("Student Master")
        doc.first_name = "Tool Test Student"
        doc.name = student
        doc.application_number = "APP-TOOL-001"
        doc.dob = "2000-01-01"
        doc.marital_status = "Unmarried"
        doc.email = "tooltest@example.com"
        doc.personal_email = "tooltest.personal@example.com"
        doc.phone = "+91-9999999999"
        doc.class_x_completion_year = 2016
        doc.class_x_percentage = 90.0
        doc.class_x_school = "Test School"
        doc.class_x_board = "CBSE"
        doc.class_xii_exam_name = "HSC"
        doc.class_xii_completion_year = 2018
        doc.class_xii_school = "Test School"
        doc.class_xii_board = "CBSE"
        doc.class_xii_percentage = 90.0
        doc.ug_degree_completed = 0
        doc.aadhaar_card = "123412341234"
        doc.pan_card = "ABCDE1234F"
        doc.passport_size_photo = "/files/test.jpg"
        doc.std_x_marksheet = "/files/test.jpg"
        doc.class_xii_marksheet = "/files/test.jpg"
        doc.insert(ignore_permissions=True)

    ay = "2025-26"
    if not frappe.db.exists("Academic Year", ay):
        a = frappe.new_doc("Academic Year")
        a.academic_year_name = ay
        a.year_start_date = "2025-06-01"
        a.year_end_date = "2026-05-31"
        a.insert(ignore_permissions=True)

    program = "PROG-TOOL-TEST"
    program_doc_name = program
    if not frappe.db.exists("Program", program):
        p = frappe.new_doc("Program")
        p.program_name = "Tool Test Program"
        p.program_code = program
        p.program_shortcode = "TTP"
        p.insert(ignore_permissions=True)
        program_doc_name = p.name
    elif frappe.db.exists("Program", program):
         # IfExists by name "PROG..."? or filter?
         # Assume name is PROG... if exists check passed?
         # frappe.db.exists returns name if true for single string arg?
         program_doc_name = frappe.db.exists("Program", program)

    group = "SG-TOOL-TEST"
    if not frappe.db.exists("Student Group", group):
        g = frappe.new_doc("Student Group")
        g.student_group_name = "Tool Test Group"
        g.group_based_on = "Activity" 
        g.program = program_doc_name
        g.academic_year = "2025-26" 
        g.insert(ignore_permissions=True)
        group_doc_name = g.name
        
        # Add student to group
        sgs = frappe.new_doc("Student Group Student")
        sgs.parent = group_doc_name
        sgs.parenttype = "Student Group"
        sgs.parentfield = "students"
        sgs.student = student
        sgs.active = 1
        sgs.insert(ignore_permissions=True)
    elif frappe.db.exists("Student Group", group):
        group_doc_name = frappe.db.exists("Student Group", group)
    else:
        # Fallback if exists by name logic is complex, just try to find by student_group_name
        found = frappe.get_all("Student Group", filters={"student_group_name": "Tool Test Group"}, limit=1)
        if found:
            group_doc_name = found[0].name

    # We need to return this name or ensure execute uses it
    # Since execute calls setup_data, setup_data should return it or set a global? 
    # Better to return it.
    return group_doc_name
