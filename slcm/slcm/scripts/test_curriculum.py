import json

import frappe

from slcm.slcm.doctype.curriculum_management.curriculum_management import get_curriculum, save_curriculum


def test():
	print("Testing Save Curriculum...")

	# Mock Data
	program = "B.Sc"
	academic_year = "2025 - 2026"
	department = "Department of History"  # using one from DB check or irrelevant if inferred

	# Check if dependencies exist
	if not frappe.db.exists("Program", program):
		print(f"Skipping: Program {program} not found.")
		return
	if not frappe.db.exists("Academic Year", academic_year):
		print(f"Skipping: Year {academic_year} not found.")
		return

	print(f"Using: {program} | {academic_year}")

	# fetch department from program
	department = frappe.db.get_value("Program", program, "department")
	if not department:
		# Fallback
		department = "Department of History"

	# Get two courses
	c_list = frappe.get_all("Course", limit=2)
	if len(c_list) < 2:
		print("Need at least 2 courses to test multiple save.")
		return

	courses = [
		{
			"semester": "Semester 1",
			"course_group_type": "Course",
			"course": c_list[0].name,
			"enrollment_type": "Core",
			"credits": 4,
		},
		{
			"semester": "Semester 1",
			"course_group_type": "Course",
			"course": c_list[1].name,
			"enrollment_type": "Core",
			"credits": 3,
		},
	]

	# Use Semester system to match the hardcoded "Semester 1" strings
	print(f"Saving {len(courses)} courses for {program} - {academic_year} with Semester System...")
	try:
		# Pass academic_system="Semester"
		doc_name = save_curriculum(
			program, academic_year, department, json.dumps(courses), academic_system="Semester"
		)
		# ...

		# Verify
		doc = frappe.get_doc("Curriculum", doc_name)
		print(f"Rows in DB: {len(doc.curriculum_courses)}")
		print(f"Academic System: {doc.academic_system}")

		if len(doc.curriculum_courses) == 2:
			print("PASS: Both courses persisted.")
		else:
			print(f"FAIL: Expected 2 rows, got {len(doc.curriculum_courses)}")

	except Exception as e:
		print(f"Error: {e}")
		import traceback

		traceback.print_exc()


if __name__ == "__main__":
	test()
