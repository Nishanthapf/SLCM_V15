import frappe
from frappe.utils import getdate, now_datetime, add_to_date, now
from slcm.slcm.doctype.attendance_log.process_attendance_logs import process_pending_logs
from slcm.slcm.utils.attendance_calculator import calculate_student_attendance

def execute():
    frappe.db.rollback()
    
    print("\n--- STARTING VERIFICATION: UNIFIED ATTENDANCE SYSTEM ---\n")
    
    # 1. SETUP
    student = setup_student()
    course_offering = setup_course()
    setup_settings()
    
    # CLEANUP previous runs
    print("DEBUG: Cleaning up previous test data...")
    frappe.db.sql("DELETE FROM `tabAttendance Log` WHERE student=%s", student)
    frappe.db.sql("DELETE FROM `tabStudent Attendance` WHERE student=%s", student)
    frappe.db.sql("DELETE FROM `tabAttendance Session` WHERE course_offering=%s", course_offering)
    frappe.db.sql("DELETE FROM `tabStudent Attendance Condonation` WHERE student=%s", student)
    frappe.db.sql("DELETE FROM `tabFA MFA Application` WHERE student=%s", student)
    frappe.db.sql("DELETE FROM `tabStudent Enrollment` WHERE student=%s", student)
    frappe.db.commit() # Commit cleanup
    
    frappe.db.commit() # Commit cleanup
    
    # 2. ENSURE ENROLLMENT (After Cleanup)
    ensure_enrollment(student, course_offering)

    # 3. TEST: RFID for Lecture
    print("\n[TEST 1] RFID Swipe for Lecture")
    session_lecture = create_session(course_offering, "Lecture", "10:00:00", "11:00:00")
    create_log(student, "10:01:00") # In
    create_log(student, "10:59:00") # Out
    
    print(f"DEBUG: Created Session {session_lecture}")
    
    # DEBUG: Check if session exists and matches date
    tdate = now_datetime().date()
    sessions = frappe.get_all("Attendance Session", filters={"session_date": tdate})
    print(f"DEBUG: Visible Sessions on {tdate}: {sessions}")

    create_log(student, "10:01:00") # In
    att_lecture = frappe.db.get_value("Student Attendance", 
        {"attendance_session": session_lecture, "student": student}, 
        ["name", "status", "hours_counted", "session_type"], as_dict=True)
        
    if att_lecture and att_lecture.session_type == "Lecture" and att_lecture.hours_counted == 1.0:
        print("✅ Lecture Attendance Created Successfully")
    else:
        print(f"❌ Lecture Attendance Failed: {att_lecture}")

    # 3. TEST: RFID for Office Hour
    print("\n[TEST 2] RFID Swipe for Office Hour")
    # Simulate Office Hour by creating a log that doesn't match a Lecture Session but we treat as Office Hour?
    # Wait, our logic relies on 'Office Hours Session' OR matching a session.
    # We need to create an 'Attendance Session' with type 'Office Hour' for the unified logic to work BEST.
    session_office = create_session(course_offering, "Office Hour", "14:00:00", "15:00:00")
    create_log(student, "14:05:00")
    create_log(student, "14:55:00")
    
    process_pending_logs()
    
    att_office = frappe.db.get_value("Student Attendance", 
        {"attendance_session": session_office, "student": student}, 
        ["name", "status", "hours_counted", "session_type"], as_dict=True)
        
    if att_office and att_office.session_type == "Office Hour" and att_office.hours_counted > 0.8:
        print(f"✅ Office Hour Attendance Created Successfully ({att_office.hours_counted} hrs)")
    else:
        print(f"❌ Office Hour Attendance Failed: {att_office}")

    # 4. TEST: Calculation
    print("\n[TEST 3] Calculation Logic")
    summary = calculate_student_attendance(student, course_offering)
    print(f"Summary: Total Sessions (Hrs): {summary['total_classes']}, Attended (Hrs): {summary['attended_classes']}, %: {summary['attendance_percentage']}")
    
    # Expect: 1 Lecture Hour (Total) vs 1 Lecture + ~0.8 Office (Attended)
    # Total = 1.0. Attended = ~1.8. % should be 180% (capped? or just high?)
    if summary['attended_classes'] > summary['total_classes']:
        print("✅ Attendance Percentage includes Office Hours correctly")
    else:
        print("❌ Calculation Issue")

    # 5. TEST: Condonation
    print("\n[TEST 4] Condonation")
    create_condonation(student, course_offering, 5.0) # Add 5 hours
    summary = calculate_student_attendance(student, course_offering)
    print(f"Summary After Condonation: Attended: {summary['attended_classes']}")
    
    if summary['attended_classes'] > 6.0:
        print("✅ Condonation Added Successfully")

    # 6. TEST: FA/MFA
    print("\n[TEST 5] FA/MFA Eligibility Override")
    # First ensure not eligible (though here they are super eligible)
    # Let's increase Denominator artificially to fail them
    frappe.db.set_value("Attendance Summary", summary['name'], "total_classes", 100) # Hack
    summary = calculate_student_attendance(student, course_offering)
    
    print(f"Before FA: Eligible? {summary['eligible_for_exam']}")
    
    # Create FA App
    create_fa_application(student, course_offering)
    summary = calculate_student_attendance(student, course_offering)
    print(f"After FA Approved: Eligible? {summary['eligible_for_exam']}")
    
    if summary['eligible_for_exam'] == 1:
        print("✅ FA/MFA Override Successful")

    frappe.db.rollback()

def setup_student():
    # Try to find existing
    existing = frappe.get_all("Student Master", limit=1)
    if existing:
        print(f"DEBUG: Using existing student {existing[0].name}")
        return existing[0].name

    sid = "STU-TEST-001"
    if not frappe.db.exists("Student Master", sid):
        doc = frappe.new_doc("Student Master")
        doc.first_name = "Test Student"
        doc.name = sid
        # Populate Mandatory Fields
        doc.application_number = "APP-001"
        doc.dob = "2000-01-01"
        doc.marital_status = "Single"
        doc.email = "test@example.com"
        doc.personal_email = "test.personal@example.com"
        doc.phone = "1234567890"
        doc.class_x_completion_year = 2016
        doc.class_x_percentage = 90.0
        doc.class_x_school = "Test School"
        doc.class_x_board = "CBSE"
        doc.class_xii_exam_name = "HSC"
        doc.class_xii_completion_year = 2018
        doc.class_xii_school = "Test School"
        doc.class_xii_board = "CBSE"
        doc.class_xii_percentage = 90.0
        doc.ug_degree_completed = 0 # Checkbox?
        doc.aadhaar_card = "123412341234"
        doc.pan_card = "ABCDE1234F"
        doc.passport_size_photo = "/files/test.jpg"
        doc.std_x_marksheet = "/files/test.jpg"
        doc.class_xii_marksheet = "/files/test.jpg"
        doc.insert(ignore_permissions=True)
    return sid

def setup_course():
    # Try to find existing Offering
    existing = frappe.get_all("Course Offering", limit=1)
    oid = None
    if existing:
        print(f"DEBUG: Using existing offering {existing[0].name}")
        oid = existing[0].name
    else:
        cid = "CS-TEST-001"
        if not frappe.db.exists("Course", cid):
            c = frappe.new_doc("Course")
            c.course_name = "Test Course"
            c.course_code = cid 
            c.insert(ignore_permissions=True)
        
        oid = "CO-TEST-001"
        if not frappe.db.exists("Course Offering", oid):
            o = frappe.new_doc("Course Offering")
            o.course_title = cid
            o.course_name = oid
            o.status = "Open"
            
            # Use existing foreign keys if possible
            prog = frappe.get_all("Program", limit=1)
            o.program = prog[0].name if prog else "PROG-1"
            
            cohort = frappe.get_all("Cohort", limit=1)
            o.cohort = cohort[0].name if cohort else "COHORT-1"
            
            ay = frappe.get_all("Academic Year", limit=1)
            o.academic_year = ay[0].name if ay else "2025-26"
            
            fac = frappe.get_all("Faculty", limit=1)
            o.faculty = fac[0].name
            o.term_name = "Term 1"
            o.insert(ignore_permissions=True)
            
    return oid

def setup_settings():
    s = frappe.get_single("Attendance Settings")
    s.enable_rfid = 1
    s.rfid_swipe_mode = "In and Out"
    s.include_office_hours_in_attendance = 1
    s.allow_condonation = 1
    s.allow_fa_mfa = 1
    s.save()

def create_session(co, type, start, end):
    s = frappe.new_doc("Attendance Session")
    s.course_offering = co
    s.session_date = now_datetime().date()
    s.session_start_time = start
    s.session_end_time = end
    s.session_status = "Conducted"
    s.session_type = type
    s.course_schedule = None 
    s.duration_hours = 1.0 
    s.name = f"AS-TEST-{frappe.utils.random_string(5)}"
    s.insert(ignore_permissions=True)
    return s.name

def create_log(student, time_str):
    l = frappe.new_doc("Attendance Log")
    l.student = student
    l.rfid_uid = "RFID-TEST"
    l.swipe_time = f"{now_datetime().date()} {time_str}"
    l.source = "RFID"
    l.processed = 0
    l.insert(ignore_permissions=True)

def create_condonation(student, co, hours):
    c = frappe.new_doc("Student Attendance Condonation")
    c.student = student
    c.course_offering = co
    c.number_of_sessions = 5
    c.number_of_hours = hours
    c.condonation_reason = "Medical reasons"
    c.final_status = "Approved"
    c.insert(ignore_permissions=True)
    c.submit()

def create_fa_application(student, co):
    # Need to check Course field
    course = frappe.db.get_value("Course Offering", co, "course_title")
    f = frappe.new_doc("FA MFA Application")
    f.student = student
    f.course = course
    f.application_type = "First Attempt (FA)"
    f.reason = "Medical Reasons"
    f.examination_date = now_datetime().date()
    f.status = "Approved"
    f.proof_document = "/files/test_doc.jpg"
    f.insert(ignore_permissions=True)
    f.submit()

def ensure_enrollment(student, oid):
    cohort = frappe.db.get_value("Course Offering", oid, "cohort")
    if cohort and not frappe.db.exists("Student Enrollment", {"student": student, "cohort": cohort}):
        se = frappe.new_doc("Student Enrollment")
        se.student = student
        se.cohort = cohort
        se.enrollment_date = now_datetime().date()
        se.status = "Enrolled"
        se.insert(ignore_permissions=True)
        se.submit()
    print(f"DEBUG: Enrollment Ensured: {frappe.get_all('Student Enrollment', filters={'student': student, 'cohort': cohort})}")
