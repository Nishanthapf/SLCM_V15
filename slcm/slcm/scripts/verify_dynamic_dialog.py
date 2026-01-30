import frappe

from slcm.slcm.doctype.course_management.course_management import get_course_dialog_columns


def run_test():
	frappe.set_user("Administrator")
	print("Testing dynamic column fetching (Version 2 - Objects)...")

	try:
		columns = get_course_dialog_columns()
		print(f"Columns returned (First 1): {columns[0] if columns else 'None'}")

		# Verify structure
		if columns and isinstance(columns[0], dict) and "fieldname" in columns[0]:
			print("PASS: Columns are dictionaries with fieldname.")

			fieldnames = [c["fieldname"] for c in columns]
			expected = ["department", "status"]
			missing = [f for f in expected if f not in fieldnames]

			if not missing:
				print(f"PASS: All expected columns found: {fieldnames}")
			else:
				print(f"FAIL: Missing columns: {missing}")
		else:
			print("FAIL: Columns are not list of dicts.")

	except Exception as e:
		print(f"FAIL: Error executing method: {e}")


run_test()
