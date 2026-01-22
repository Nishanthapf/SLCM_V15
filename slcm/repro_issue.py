import json

import frappe

from slcm.slcm.doctype.student_id_card.student_id_card import StudentIDCard


def test_mapping():
	# 1. Get existing Student
	student_name = frappe.db.get_value("Student Master", {}, "name")
	if not student_name:
		print("No student found. Cannot proceed.")
		return

	student = frappe.get_doc("Student Master", student_name)
	print(f"Using student: {student.name}")

	# 2. Create/Get dummy Template
	canvas_data = {
		"orientation": "horizontal",
		"front": [
			{"type": "image", "mapping": "authority_signature", "x": 10, "y": 10, "width": 100, "height": 50},
			{"type": "image", "mapping": "qr_code_image", "x": 10, "y": 70, "width": 100, "height": 100},
		],
		"back": [],
		"bg_color": {"front": "#ffffff", "back": "#ffffff"},
	}

	template_name = "Test Mapping Template"
	if frappe.db.exists("ID Card Template", template_name):
		template = frappe.get_doc("ID Card Template", template_name)
	else:
		template = frappe.new_doc("ID Card Template")
		template.template_name = template_name

	template.template_creation_mode = "Drag and Drop"
	template.canvas_data = json.dumps(canvas_data)
	template.authority_signature = "/assets/frappe/images/test_sig.png"
	template.save(ignore_permissions=True)
	print(f"Using template: {template.name}")

	# 3. Get or Create Student ID Card
	# Find ANY active card for this student
	existing = frappe.db.get_value(
		"Student ID Card", {"student": student.name, "card_status": ["!=", "Cancelled"]}, "name"
	)

	if existing:
		print(f"Found existing card: {existing}")
		card = frappe.get_doc("Student ID Card", existing)
		card.id_card_template = template.name
	else:
		print("Creating new card")
		card = frappe.new_doc("Student ID Card")
		card.student = student.name
		card.id_card_template = template.name
		card.issue_date = "2024-01-01"
		card.expiry_date = "2025-01-01"
		card.insert(ignore_permissions=True)

	# Mock QR Code Image path for test
	card.qr_code_image = "/assets/frappe/images/test_qr.png"

	print("Testing generate_card_from_canvas logic (simulation)...")

	# We call the ACTUAL method which now has prints
	try:
		card.generate_card_from_canvas(template, student)
	except Exception as e:
		print(f"Caught exception (expected, as it tries to run wkhtmltoimage): {e}")

	print("Done.")
