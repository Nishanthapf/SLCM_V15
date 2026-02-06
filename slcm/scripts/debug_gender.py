import frappe

def check_students():
    students = frappe.get_all("Student", fields=["name", "first_name", "gender"])
    print("Student Genders:")
    for s in students:
        print(f"{s.name} ({s.first_name}): '{s.gender}'")

    # Also check Attendance Session log
    sessions = frappe.get_all("Attendance Session", fields=["name", "total_boys", "total_girls", "present_count"])
    for s in sessions:
        print(f"Session {s.name}: Boys={s.total_boys}, Girls={s.total_girls}, Present={s.present_count}")

check_students()
