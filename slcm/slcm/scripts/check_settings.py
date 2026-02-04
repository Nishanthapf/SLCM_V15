import frappe

def execute():
    settings = frappe.get_single("Attendance Settings")
    print(f"Minimum Percentage: {settings.minimum_attendance_percentage}")
