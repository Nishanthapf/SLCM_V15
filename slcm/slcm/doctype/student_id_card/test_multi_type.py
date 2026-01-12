import os

import frappe


def test_multi_type_generation():
	frappe.db.rollback()

	try:
		frappe.clear_cache()
		# Reload to capture JSON changes if needed
		frappe.reload_doc("slcm", "doctype", "student_id_card", force=True)

		# Debug Metadata
		meta = frappe.get_meta("Student ID Card")
		student_field = meta.get_field("student")
		print(
			f"DEBUG: Student Field reqd={student_field.reqd}, mandatory_depends_on={student_field.mandatory_depends_on}"
		)

		frappe.reload_doc("slcm", "doctype", "driver")
		frappe.reload_doc("slcm", "doctype", "faculty")

		# 1. Create a Faculty
		faculty = frappe.new_doc("Faculty")
		faculty.first_name = "Dr. John"
		faculty.last_name = "Doe"
		faculty.faculty_id = "FAC-TEST-001"
		faculty.email = "john.doe@example.com"
		faculty.designation = "Professor"
		faculty.status = "Active"
		faculty.insert()

		# 2. Get a Template
		template_name = frappe.db.get_value("ID Card Template", {}, "name")
		if not template_name:
			print("No template found, skipping test.")
			return

		# 3. Create ID Card for Faculty
		card = frappe.new_doc("Student ID Card")
		card.card_type = "Faculty"
		card.faculty = faculty.name
		card.id_card_template = template_name
		card.issue_date = frappe.utils.today()
		card.expiry_date = frappe.utils.add_years(frappe.utils.today(), 1)
		card.card_status = "Draft"
		card.insert()

		print(f"Created ID Card: {card.name}")
		print(f"Name on Card: {card.student_name}")
		print(f"Email: {card.email}")  # Should be john.doe@example.com

		if card.email != "john.doe@example.com":
			print("FAILED: Email not fetched from Faculty")

		# 4. Generate Image
		card.generate_card()

		if not card.front_id_image:
			print("FAILED: Front ID Image not generated")
		else:
			print(f"SUCCESS: Generated Front Image: {card.front_id_image}")

		# 5. Backward Compatibility - Student
		student = frappe.get_doc("Student Master", {"email": ["!=", None]})
		if student:
			card_s = frappe.new_doc("Student ID Card")
			card_s.card_type = "Student"
			card_s.student = student.name
			card_s.id_card_template = template_name
			card_s.insert()

			print(f"Created Student Card: {card_s.name}")
			if card_s.student_name != f"{student.first_name} {student.last_name or ''}".strip():
				print(f"FAILED: Student Name mismatch. Got {card_s.student_name}")

			card_s.generate_card()
			if card_s.front_id_image:
				print(f"SUCCESS: Generated Student Card Image: {card_s.front_id_image}")
			else:
				print("FAILED: Student Card Image not generated")

	except Exception as e:
		print(f"ERROR: {e}")
		import traceback

		traceback.print_exc()
	finally:
		frappe.db.rollback()


if __name__ == "__main__":
	test_multi_type_generation()
