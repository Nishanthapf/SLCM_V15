import frappe
from slcm.slcm.utils.attendance_calculator import calculate_student_attendance

def execute():
    # Fetch the summary shown in the user screenshot "AS-2026-00002" to get student and offering
    try:
        summary_name = "AS-2026-00002"
        if frappe.db.exists("Attendance Summary", summary_name):
            doc = frappe.get_doc("Attendance Summary", summary_name)
            print(f"Recalculating for {doc.student} - {doc.course_offering}")
            
            result = calculate_student_attendance(doc.student, doc.course_offering)
            print("Recalculation Result:")
            print(f"Total Classes: {result['total_classes']}")
            print(f"Attended Classes: {result['attended_classes']}")
            print(f"Percentage: {result['attendance_percentage']}")
        else:
            print(f"Summary {summary_name} not found. Trying to find by Student Name 'Jenifar'")
            s = frappe.get_all("Student Master", filters={"first_name": "Jenifar"}, limit=1)
            if s:
                student = s[0].name
                # Find course offering "Law of Crime"
                # The screenshot says Course Offering "Law of Crime" which implies Title is Law of Crime OR ID is Law of Crime
                # Let's try to search
                co = frappe.get_all("Course Offering", filters={"course_title": "Law of Crime"}, limit=1)
                if co:
                    calculate_student_attendance(student, co[0].name)
                    print("Recalculated based on lookup.")
                else:
                    print("Could not find Course Offering 'Law of Crime'")
            else:
                 print("Could not find Student 'Jenifar'")

    except Exception as e:
        print(f"Error: {e}")
