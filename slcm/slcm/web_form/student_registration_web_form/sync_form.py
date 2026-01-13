import json
import os

import frappe


def execute():
	try:
		# Define the path to the JSON file
		file_path = "/home/appi/Education_V15/apps/slcm/slcm/slcm/web_form/student_registration_web_form/student_registration_web_form.json"

		# Read the JSON file
		with open(file_path) as f:
			data = json.load(f)

		# Get the Web Form Name
		web_form_name = data.get("name")

		print(f"Syncing Web Form: {web_form_name}")

		# Get the Document
		doc = frappe.get_doc("Web Form", web_form_name)

		# Update scalar fields
		doc.route = data.get("route")
		doc.title = data.get("title")
		doc.login_required = data.get("login_required")
		doc.published = data.get("published")
		doc.introduction_text = data.get("introduction_text")
		doc.success_url = data.get("success_url")

		# Clear existing fields and re-add from JSON
		doc.set("web_form_fields", [])

		for field in data.get("fields", []):
			field_row = doc.append("web_form_fields", {})
			field_row.fieldname = field.get("fieldname")
			field_row.fieldtype = field.get("fieldtype")
			field_row.label = field.get("label")
			field_row.reqd = field.get("reqd", 0)
			field_row.options = field.get("options", "")
			field_row.hidden = field.get("hidden", 0)
			field_row.default = field.get("default", "")

		# Save the document
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		print(f"Success! Synced {len(doc.web_form_fields)} fields.")

	except Exception as e:
		print(f"Error Syncing Web Form: {e}")
		frappe.db.rollback()
