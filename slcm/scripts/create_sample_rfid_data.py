import frappe
from frappe.utils import add_to_date, getdate, nowtime

def execute():
    frappe.db.auto_commit_on_many_writes = 1

    print("🚀 Starting Sample Data Creation for RFID Attendance...")

    # 1. Get or Create a Test Student with RFID
    student = frappe.get_all("Student Master", limit=1)
    if not student:
        print("❌ No Student Master found. Please create a student first.")
        return
    
    student_id = student[0].name
    rfid_uid = "SAMPLE-RFID-001"
    
    frappe.db.set_value("Student Master", student_id, "rfid_uid", rfid_uid)
    print(f"✅ Student Configured: {student_id} (RFID: {rfid_uid})")

    # 2. Get or Create a Course Offering
    course_offerings = frappe.get_all("Course Offering", limit=1)
    if not course_offerings:
        print("❌ No Course Offering found. Please create one first.")
        return
    course_offering = course_offerings[0].name
    print(f"✅ Using Course Offering: {course_offering}")

    # 3. Create a Room
    room_name = "Sample Room 101"
    if not frappe.db.exists("Room", room_name):
        frappe.get_doc({
            "doctype": "Room",
            "room_name": room_name,
            "room_number": "101",
            "capacity": 30
        }).insert(ignore_permissions=True)
    print(f"✅ Room Ready: {room_name}")

    # 4. Create an RFID Device linked to that Room
    device_id = "DEV-SAMPLE-001"
    if not frappe.db.exists("RFID Device", {"device_id": device_id}):
        frappe.get_doc({
            "doctype": "RFID Device",
            "device_id": device_id,
            "device_name": "Sample Reader 01",
            "location": room_name,
            "is_active": 1
        }).insert(ignore_permissions=True)
    print(f"✅ Device Ready: {device_id} (Location: {room_name})")

    # 5. Create a Student Group and Add Student
    group_name = "SG-SAMPLE-RFID"
    academic_year = frappe.get_all("Academic Year", limit=1)
    if not academic_year:
         term = frappe.get_doc({"doctype": "Academic Year", "academic_year_name": "2025-2026", "year_start_date": "2025-01-01", "year_end_date": "2025-12-31"})
         term.insert(ignore_permissions=True)
         academic_year_name = term.name
    else:
         academic_year_name = academic_year[0].name

    if not frappe.db.exists("Student Group", group_name):
        frappe.get_doc({
            "doctype": "Student Group",
            "student_group_name": group_name,
            "group_based_on": "Activity",
            "academic_year": academic_year_name
        }).insert(ignore_permissions=True)
    
    if not frappe.db.exists("Student Group Student", {"parent": group_name, "student": student_id}):
        frappe.get_doc({
            "doctype": "Student Group Student",
            "parent": group_name,
            "parenttype": "Student Group",
            "student": student_id
        }).insert(ignore_permissions=True)
    print(f"✅ Student Group Ready: {group_name}")

    # 6. Create a Course Schedule for TODAY
    #    Schedule it for a wide window today so testing is easy (e.g., 8 AM to 8 PM)
    #    Or better: Current time +/- 1 hour
    today = getdate()
    
    # Check if a schedule already exists for this group today to avoid overlaps
    existing_schedule = frappe.db.exists("Course Schedule", {
        "student_group": group_name,
        "schedule_date": today
    })

    schedule_name = existing_schedule
    if not schedule_name:
        cs = frappe.get_doc({
            "doctype": "Course Schedule",
            "student_group": group_name,
            "course_offering": course_offering,
            "schedule_date": today,
            "from_time": "08:00:00",
            "to_time": "20:00:00",
            "room": room_name
        })
        cs.insert(ignore_permissions=True)
        schedule_name = cs.name
    print(f"✅ Course Schedule Ready: {schedule_name} (Today)")

    # 7. Create an Attendance Session from that Schedule
    #    The system might auto-create it, but let's force create one for the sample
    session_name = frappe.db.exists("Attendance Session", {
        "course_schedule": schedule_name,
        "session_date": today
    })

    if not session_name:
        session = frappe.get_doc({
            "doctype": "Attendance Session",
            "session_date": today,
            "session_start_time": "08:00:00",
            "session_end_time": "20:00:00",
            "course_offering": course_offering,
            "course_schedule": schedule_name,
            "room": room_name,
            "status": "Scheduled"
        })
        session.insert(ignore_permissions=True)
        session_name = session.name
    print(f"✅ Attendance Session Ready: {session_name}")

    frappe.db.commit()
    print("\n🎉 Sample Data Created Successfully!")
    print("------------------------------------------------")
    print(f"Student ID:     {student_id}")
    print(f"RFID UID:       {rfid_uid}")
    print(f"Device ID:      {device_id}")
    print(f"Session ID:     {session_name}")
    print("------------------------------------------------")
    print("You can now test by simulating a swipe for this Student and Device.")
