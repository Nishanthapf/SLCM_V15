import frappe


def execute():
	try:
		options = frappe.get_meta("Student Master").get_field("naming_series").options
		print(f"DEBUG_OPTIONS: {options}")
	except Exception as e:
		print(f"DEBUG_ERROR: {e}")
