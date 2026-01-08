import frappe


def verify_meta():
	try:
		meta = frappe.get_meta("Student Master")
		field = meta.get_field("registration_status")

		print(f"Label: {field.label}")
		print(f"In List View: {field.in_list_view}")
		print(f"In Standard Filter: {field.in_standard_filter}")
		print(f"Read Only: {field.read_only}")

		if field.label == "Current Status" and field.in_list_view == 1:
			print("SUCCESS: Metadata updated correctly.")
		else:
			print("FAIL: Metadata mismatch.")

	except Exception as e:
		print(f"Error: {e}")


if __name__ == "__main__":
	verify_meta()
