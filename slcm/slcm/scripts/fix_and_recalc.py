import frappe
from slcm.slcm.utils.attendance_calculator import calculate_student_attendance

def execute():
    # 1. Update Settings
    print("Updating Attendance Settings...")
    settings = frappe.get_single("Attendance Settings")
    settings.minimum_attendance_percentage = 75.0
    settings.save()
    print("Settings updated: Minimum % set to 75.0")

    # 2. Update Session Status
    print("Updating Session Status...")
    sessions = frappe.get_all("Attendance Session", filters={"session_status": "Scheduled"}, limit=1)
    if sessions:
        # Just update the one relevant to our debug, or generic
        # Ideally calculate_student_attendance recalculates based on DB state
        # We found AS-2026-00047 in previous debug
        frappe.db.set_value("Attendance Session", "AS-2026-00047", "session_status", "Conducted")
        print("Updated AS-2026-00047 to Conducted")
    else:
        print("No Scheduled session found (or already updated)")

    # 3. Recalculate
    print("Recalculating Summary...")
    student = "BALLB26002" # Jenifar
    # Find course offering "Law of Crime"
    co = frappe.get_all("Course Offering", filters={"course_title": "Law of Crime"}, limit=1)
    if co:
        res = calculate_student_attendance(student, co[0].name)
        print("Recalculation Result:")
        print(f"Total Classes: {res['total_classes']}")
        print(f"Attended Classes: {res['attended_classes']}")
        print(f"Percentage: {res['attendance_percentage']}")
        print(f"Eligible: {res['eligible_for_exam']}")
