import frappe
from frappe.model.document import Document


class IDCardTemplate(Document):
	def validate(self):
		self.validate_fields()

	def validate_fields(self):
		# Get Student Master Meta
		student_meta = frappe.get_meta("Student Master")
		valid_fields = [f.fieldname for f in student_meta.fields]
		valid_fields.extend(["name", "owner", "creation", "modified", "docstatus"])

		# Special fields
		special_fields = ["photo", "qrcode", "static_text"]

		for row in self.fields:
			if row.student_fieldname not in special_fields:
				if row.student_fieldname not in valid_fields:
					frappe.throw(
						f"Row {row.idx}: Field '{row.student_fieldname}' does not exist in Student Master."
					)
