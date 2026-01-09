import frappe


def generate_id_card_images(docname):
	try:
		doc = frappe.get_doc("Student ID Card", docname)
		doc.generate_card()
	except Exception as e:
		frappe.log_error(f"ID Card Generation Failed for {docname}: {e!s}", "ID Card Generation Error")
		# Update status to error if possible, but generate_card might fail before.
		# We can re-fetch or use SQL to update status if doc save failed.
		frappe.db.set_value("Student ID Card", docname, "card_status", "Error")
		frappe.db.commit()
