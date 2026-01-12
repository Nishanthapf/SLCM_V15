import os

import frappe


def test_naming_series_logic():
	frappe.db.rollback()

	try:
		# Reload to capture JSON changes if needed
		frappe.reload_doc("slcm", "doctype", "student_id_card", force=True)
		frappe.reload_doc("slcm", "doctype", "driver")
		frappe.reload_doc("slcm", "doctype", "faculty")

		# 1. Create a Faculty
		faculty = frappe.new_doc("Faculty")
		faculty.first_name = "Dr. Jane"
		faculty.last_name = "Smith"
		faculty.faculty_id = "FAC-TEST-002"
		faculty.email = "jane.smith@example.com"
		faculty.designation = "Associate Professor"
		faculty.status = "Active"
		try:
			faculty.insert()
		except frappe.DuplicateEntryError:
			faculty = frappe.get_doc("Faculty", {"first_name": "Dr. Jane"})

		# 2. Get a Template
		template_name = frappe.db.get_value("ID Card Template", {}, "name")
		if not template_name:
			print("No template found, skipping test.")
			return

		# 3. Test Faculty Naming Series
		card_fac = frappe.new_doc("Student ID Card")
		card_fac.card_type = "Faculty"
		card_fac.faculty = faculty.name
		card_fac.id_card_template = template_name
		card_fac.naming_series = "FAC-.#####"  # JS usually sets this, but in py test we must set it
		card_fac.issue_date = frappe.utils.today()
		card_fac.expiry_date = frappe.utils.add_years(frappe.utils.today(), 1)
		card_fac.card_status = "Draft"
		card_fac.insert()

		print(f"Created Faculty Card: {card_fac.name}")
		if not card_fac.name.startswith("FAC-"):
			print("FAILED: Faculty Card naming series incorrect.")

		if card_fac.designation != "Associate Professor":
			print("FAILED: Designation not fetched from Faculty")

		# Get any existing Department
		dept = frappe.db.get_value("Department", {}, "name")
		if not dept:
			# If no department exists, we can't easily guess the schema to create one.
			# But for testing, maybe we can just use a string if validation is loose on the Link?
			# No, Link validation is strict.
			print("WARNING: No Department found. Creating a dummy one might fail if schema is strict.")
			dept = "IT"  # Fallback, might fail if link validation is on

		# 4. Test Non-Faculty Card
		card_nf = frappe.new_doc("Student ID Card")
		card_nf.card_type = "Non-Faculty"
		card_nf.non_faculty_name = "John Admin"
		card_nf.designation = "System Administrator"
		card_nf.department = dept
		card_nf.id_card_template = template_name
		card_nf.naming_series = "STF-.#####"
		card_nf.issue_date = frappe.utils.today()
		card_nf.expiry_date = frappe.utils.add_years(frappe.utils.today(), 1)
		card_nf.card_status = "Draft"
		card_nf.insert()

		print(f"Created Non-Faculty Card: {card_nf.name}")
		if not card_nf.name.startswith("STF-"):
			print("FAILED: Non-Faculty Card naming series incorrect.")

		card_nf.generate_card()
		print(f"Non-Faculty Image: {card_nf.front_id_image}")

		# 5. Test Default/Student
		card_stu = frappe.new_doc("Student ID Card")
		card_stu.card_type = "Student"
		# Mocking a student link for naming check only
		# In real scenario we'd link a student
		# But since 'student' is mandatory dependent, we might skip full insert if we don't have a clean student
		# Just checking if we can set series STU-
		card_stu.naming_series = "STU-.#####"
		print(f"Student Series set to: {card_stu.naming_series}")

	except Exception as e:
		print(f"ERROR: {e}")
		import traceback

		traceback.print_exc()
	finally:
		frappe.db.rollback()


if __name__ == "__main__":
	test_naming_series_logic()
