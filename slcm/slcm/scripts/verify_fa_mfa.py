import frappe
from frappe.utils import add_days, now_datetime, getdate

def execute():
    frappe.db.rollback()
    print("--- STARTING FA/MFA VERIFICATION ---")
    
    # SETUP
    setup_settings()
    student = "STU-FA-TEST"
    setup_student(student)
    course = "CS-FA-TEST"
    setup_course(course)
    
    # 1. TEST: Invalid Dates (Event too far future)
    print("\n[TEST 1] Invalid Dates (Event > 3 days after Exam)")
    try:
        exam_date = getdate("2026-05-01")
        event_from = getdate("2026-05-10") # 9 days later
        create_app(student, course, "University Representation", exam_date, event_from, event_from)
        print("❌ Failed: Should have thrown error for exceeding 3 days gap")
    except frappe.exceptions.ValidationError as e:
        print(f"✅ Caught expected validation error: {e}")
    except Exception as e:
        print(f"✅ Caught expected error: {e}")

    # 2. TEST: Valid Dates
    print("\n[TEST 2] Valid Dates (Event 2 days after Exam)")
    try:
        exam_date = getdate("2026-05-01")
        event_from = getdate("2026-05-03")
        doc = create_app(student, course, "University Representation", exam_date, event_from, event_from)
        print(f"✅ Success: Application created {doc.name}")
    except Exception as e:
        print(f"❌ Failed Valid Date Test: {e}")

    # 3. TEST: Rejection without Reason
    print("\n[TEST 3] Rejection without Reason")
    try:
        doc.status = "Rejected"
        doc.rejection_reason = None
        doc.save(ignore_permissions=True)
        print("❌ Failed: Should have thrown error for missing rejection reason")
    except Exception as e:
        print(f"✅ Caught expected error: {e}")

    # 4. TEST: Approval sets Approver
    print("\n[TEST 4] Approval sets Approver")
    try:
        doc.reload()
        doc.status = "Approved"
        doc.save(ignore_permissions=True)
        if doc.approver == frappe.session.user:
            print(f"✅ Approver successfully set to {doc.approver}")
        else:
            print(f"❌ Approver not set correctly: {doc.approver}")
    except Exception as e:
        print(f"❌ Failed Approval Test: {e}")

    frappe.db.rollback()

def setup_settings():
    s = frappe.get_single("Attendance Settings")
    s.allow_fa_mfa = 1
    s.save()

def setup_student(sid):
    if not frappe.db.exists("Student Master", sid):
        doc = frappe.new_doc("Student Master")
        doc.first_name = "FA Test Student"
        doc.name = sid
        doc.application_number = "APP-FA-001"
        doc.dob = "2000-01-01"
        doc.marital_status = "Unmarried"
        doc.email = "fatest@example.com"
        doc.personal_email = "test.personal@example.com"
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

def setup_course(cid):
    if not frappe.db.exists("Course Master", "FA Test Course"):
        cm = frappe.new_doc("Course Master")
        cm.course_name = "FA Test Course"
        cm.name = "FA Test Course"
        cm.course_code = "FA-101" # Assuming code is needed
        # Check if credits field exists in Master? Usually just name.
        cm.insert(ignore_permissions=True)

    if not frappe.db.exists("Course", cid):
        c = frappe.new_doc("Course")
        c.course_name = "FA Test Course"
        c.course_code = cid 
        c.insert(ignore_permissions=True)

def create_app(student, course, reason, exam_date, from_date=None, to_date=None):
    doc = frappe.new_doc("FA MFA Application")
    doc.student = student
    doc.course = course
    doc.application_type = "First Attempt (FA)"
    doc.reason = reason
    doc.examination_date = exam_date
    doc.event_from_date = from_date
    doc.event_to_date = to_date
    doc.proof_document = "/files/test.jpg"
    doc.insert(ignore_permissions=True)
    return doc
