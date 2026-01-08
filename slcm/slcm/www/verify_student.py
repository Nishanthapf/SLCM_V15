import frappe
from frappe.utils import getdate, today


def get_context(context):
	student_id = frappe.form_dict.get("student_id")
	context.no_cache = 1

	if not student_id:
		context.error_message = "No Student ID provided."
		return

	if not frappe.db.exists("Student Master", student_id):
		context.error_message = f"Student {student_id} not found."
		return

	student = frappe.get_doc("Student Master", student_id)
	context.student = student

	# Check for latest generated card
	card_name = frappe.db.get_value(
		"Student ID Card",
		{"student": student_id, "card_status": ["in", ["Generated", "Printed"]]},
		"name",
		order_by="creation desc",
	)

	if card_name:
		card = frappe.get_doc("Student ID Card", card_name)
		context.card = card

		is_expired = getdate(card.expiry_date) < getdate(today())
		is_active = student.student_status == "Active"

		if not is_expired and is_active:
			context.valid = True
			context.status_label = "VALID"
			context.status_color = "success"
		else:
			context.valid = False
			context.status_label = "INVALID / EXPIRED"
			context.status_color = "danger"

			if is_expired:
				context.reason = "Card Expired"
			elif not is_active:
				context.reason = "Student Inactive"
	else:
		context.valid = False
		context.status_label = "NO ACTIVE CARD"
		context.status_color = "warning"
