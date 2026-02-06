
import frappe
from slcm.slcm.utils.attendance_calculator import calculate_student_attendance


def execute():
    try:
        # Force reload metas to ensure fields are recognized if migrate is stuck
        frappe.reload_doc("slcm", "doctype", "Attendance Condonation Reference")
        frappe.reload_doc("slcm", "doctype", "Attendance FA MFA Reference")
        frappe.reload_doc("slcm", "doctype", "Attendance Summary")
        
        student = "BALLB26001"
        course_offering = "Law of Crime"
        
        print(f"Verifying for {student} - {course_offering}")
        
        # 1. Create Dummy Condonation (if not exists)
        if not frappe.db.count("Student Attendance Condonation", {"student": student, "course_offering": course_offering}):
            print("Creating dummy Condonation application...")
            doc = frappe.get_doc({
                "doctype": "Student Attendance Condonation",
                "student": student,
                "course_offering": course_offering,
                "number_of_sessions": 2,
                "number_of_hours": 2,
                "condonation_reason": "Medical reasons",
                "final_status": "Pending", # Should still show up
                "docstatus": 0
            })
            doc.insert()
            created_condonation = doc.name
        else:
            created_condonation = None
            print("Using existing Condonation application(s).")

        # 2. Calculate
        print("Calculating attendance...")
        result = calculate_student_attendance(student, course_offering)
        
        # 3. Verify
        summary_name = frappe.db.get_value("Attendance Summary", {"student": student, "course_offering": course_offering})
        doc = frappe.get_doc("Attendance Summary", summary_name)
        
        print("\n--- Condonation Applications ---")
        if hasattr(doc, 'condonation_list') and doc.condonation_list:
            for row in doc.condonation_list:
                print(f"- {row.condonation_application}: {row.condonation_reason} ({row.final_status})")
        else:
            print("No Condonation Applications found.")
            
        print("\n--- FA/MFA Applications ---")
        if hasattr(doc, 'fa_mfa_list') and doc.fa_mfa_list:
            for row in doc.fa_mfa_list:
                print(f"- {row.fa_mfa_application}: {row.application_type} - {row.reason} ({row.status})")
        else:
            print("No FA/MFA Applications found.")

        # 4. Cleanup
        if created_condonation:
            print(f"\nCleaning up {created_condonation}...")
            frappe.delete_doc("Student Attendance Condonation", created_condonation)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
