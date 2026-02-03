# Test Script for Session-Based RFID Logic
import frappe
from frappe.utils import now_datetime, add_to_date, getdate
from slcm.slcm.doctype.attendance_log.process_attendance_logs import process_pending_logs

def test_session_logic():
    print("🧪 Testing Session-Based RFID Logic...")
    
    # Reload DocType to ensure new fields (rfid_swipe_mode) are recognized
    frappe.reload_doc("slcm", "doctype", "attendance_settings")

    # 0. Setup: Enable RFID
    frappe.db.set_value("Attendance Settings", "Attendance Settings", "enable_rfid", 1)
    
    student = frappe.get_all("Student Master", limit=1)[0].name
    # Use a future date to ensure no conflict with previous test runs
    today = add_to_date(getdate(), days=1)
    print(f"   [i] Testing for Date: {today}")
    
    # Fetch valid Course Offering or create Enrollment
    course_off = frappe.get_all("Course Offering", limit=1)
    if not course_off:
        print("   [!] No Course Offering found. Setup required.")
        return
    co_name = course_off[0].name
    
    # Clean up OLD data
    print("   [i] Cleaning up old logs and attendance...")
    frappe.db.sql("DELETE FROM `tabAttendance Log` WHERE student=%s", student)
    frappe.db.sql("DELETE FROM `tabStudent Attendance` WHERE student=%s", student)
    frappe.db.commit()

    # 1. Create Student Group and Enroll Student
    sg_name = "SG-RFID-TEST"
    try:
        if not frappe.db.exists("Student Group", sg_name):
             sg = frappe.new_doc("Student Group")
             sg.student_group_name = sg_name
             sg.group_based_on = "Activity"
             sg.insert(ignore_permissions=True, ignore_mandatory=True)
             print(f"   [x] Created Student Group: {sg_name}")
    except Exception as e:
         print(f"   [!] SG Create Error: {e}")
    
    # Add student to group
    if not frappe.db.exists("Student Group Student", {"parent": sg_name, "student": student}):
        try:
            sgs = frappe.get_doc({
                "doctype": "Student Group Student",
                "parent": sg_name,
                "parenttype": "Student Group",
                "student": student,
                "student_name": student
            })
            sgs.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"   [x] Added student to group {sg_name}")
        except Exception as e:
            print(f"   [!] SG Add Error: {e}")

    # Fetch valid Room or Create One
    room_name = "Room 101"
    rooms = frappe.get_all("Room", limit=1)
    if rooms:
        room_name = rooms[0].name
    else:
        try:
            r = frappe.get_doc({"doctype": "Room", "room_name": room_name, "room_number": "101", "capacity": 50})
            r.insert(ignore_permissions=True)
            print("   [x] Created Room 101")
        except Exception as e:
            print(f"   [!] Room Create Error: {e}")

    # 2. Create Course Schedule linked to Group
    cs_name = "CS-RFID-TEST"
    try:
        cs = frappe.get_doc({
             "doctype": "Course Schedule",
             "name": cs_name, 
             "student_group": sg_name,
             "course_offering": co_name,
             "schedule_date": today,
             "from_time": "10:00:00",
             "to_time": "11:00:00",
             "room": room_name
        })
        cs.insert(ignore_permissions=True, ignore_mandatory=True)
        cs_name = cs.name
        print(f"   [x] Created Schedule: {cs_name}")
    except Exception as e:
        # Check if exists
        exists = frappe.get_all("Course Schedule", filters={"student_group": sg_name, "schedule_date": today}, limit=1)
        if exists:
            cs_name = exists[0].name
            print(f"   [i] Using existing schedule: {cs_name}")
        else:
            print(f"   [!] Schedule Create Error: {e}")

    # 3. Create Session with real Schedule
    session = frappe.get_doc({
        "doctype": "Attendance Session",
        "session_date": today,
        "session_start_time": "10:00:00",
        "session_end_time": "11:00:00",
        "course_offering": co_name,
        "course_schedule": cs_name,
        "status": "Scheduled"
    })
    try:
        session.insert(ignore_permissions=True, ignore_mandatory=True)
    except:
        pass 
    print(f"   [x] Session Ready: {session.name}")

    # ----------------------------------------------------
    # TEST CASE A: IN ONLY MODE
    # ----------------------------------------------------
    print("\n--- Test A: In Only Mode ---")
    frappe.db.set_value("Attendance Settings", "Attendance Settings", "rfid_swipe_mode", "In Only")
    
    # Create Swipe at 10:05
    log_in = create_log(student, today, "10:05:00")
    
    # Process
    process_pending_logs()
    
    # Verify
    log_in.reload()
    if log_in.processed == 1:
        print("   ✅ SUCCESS: 'In Only' processed single swipe.")
    else:
        print("   ❌ FAILURE: 'In Only' did NOT process single swipe.")

    # ----------------------------------------------------
    # TEST CASE B: IN AND OUT MODE
    # ----------------------------------------------------
    print("\n--- Test B: In and Out Mode ---")
    frappe.db.set_value("Attendance Settings", "Attendance Settings", "rfid_swipe_mode", "In and Out")
    
    # Swipe at 10:05 (In) -- should be ignored by itself? 
    # Actually code marks processed if attendance created.
    # Let's clean up first.
    frappe.db.sql("DELETE FROM `tabStudent Attendance` WHERE student=%s AND attendance_date=%s", (student, today))
    frappe.db.sql("UPDATE `tabAttendance Log` SET processed=0 WHERE name=%s", log_in.name)
    frappe.db.commit()

    # Process (Just IN)
    process_pending_logs()
    log_in.reload()
    if log_in.processed == 0:
        print("   ✅ SUCCESS: 'In and Out' ignored single swipe.")
    else:
        print("   ❌ FAILURE: 'In and Out' processed single swipe incorrectly.")
        
    # Create Swipe at 10:55 (Out)
    log_out = create_log(student, today, "10:55:00")
    print(f"   [i] Created Out Log: {log_out.name}")

    # Debug DB Dump
    print("   [i] DUMPING ALL LOGS:")
    all_logs = frappe.get_all("Attendance Log", fields=["name", "student", "swipe_time", "processed"])
    for l in all_logs:
        print(f"       - {l.name}: {l.student} @ {l.swipe_time} (Processed: {l.processed})")
    
    # Process (IN + OUT)
    process_pending_logs()
    
    log_in.reload()
    if log_in.processed == 1:
        print("   ✅ SUCCESS: 'In and Out' processed valid swipe pair.")
    else:
        print("   ❌ FAILURE: 'In and Out' failed to process pair.")


def create_log(student, date_obj, time_str):
    log = frappe.get_doc({
        "doctype": "Attendance Log",
        "student": student,
        "rfid_uid": "TEST-SESSION-UID",
        "swipe_time": f"{date_obj} {time_str}",
        "device_id": "TEST-DEVICE",
        "source": "RFID",
        "processed": 0
    })
    log.insert(ignore_permissions=True)
    frappe.db.commit()
    return log

if __name__ == "__main__":
    try:
        test_session_logic()
    finally:
        frappe.db.rollback()
