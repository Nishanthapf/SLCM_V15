# import frappe
# from frappe.model.document import Document


# class IDCardTemplate(Document):
# 	def validate(self):
# 		self.validate_fields()

# 	def validate_fields(self):
# 		# Get Student Master Meta
# 		student_meta = frappe.get_meta("Student Master")
# 		valid_fields = [f.fieldname for f in student_meta.fields]
# 		valid_fields.extend(["name", "owner", "creation", "modified", "docstatus"])

# 		# Special fields
# 		special_fields = ["photo", "qrcode", "static_text"]

# 		for row in self.fields:
# 			if row.student_fieldname not in special_fields:
# 				if row.student_fieldname not in valid_fields:
# 					frappe.throw(
# 						f"Row {row.idx}: Field '{row.student_fieldname}' does not exist in Student Master."
# 					)

# 	@frappe.whitelist()
# 	def get_preview(self):
# 		# Fetch a sample student
# 		student = frappe.db.get_value("Student Master", {"student_status": "Active"}, "name")
# 		if not student:
# 			# Fallback to any student
# 			student = frappe.db.get_value("Student Master", {}, "name")

# 		if not student:
# 			return "<div class='alert alert-warning'>No students found in the system to generate a preview.</div>"

# 		# Use the same logic as IDCardGenerationTool.get_preview_html
# 		from slcm.slcm.doctype.id_card_generation_tool.id_card_generation_tool import IDCardGenerationTool
# 		tool = frappe.new_doc("ID Card Generation Tool")
# 		return tool.get_preview_html(self.name, student)


import frappe
from frappe.model.document import Document


class IDCardTemplate(Document):
	def validate(self):
		self.validate_fields()

	def validate_fields(self):
		student_meta = frappe.get_meta("Student Master")
		valid_fields = [f.fieldname for f in student_meta.fields]
		valid_fields.extend(["name", "owner", "creation", "modified", "docstatus"])

		special_fields = ["photo", "qrcode", "static_text"]

		for row in self.fields:
			if row.student_fieldname not in special_fields:
				if row.student_fieldname not in valid_fields:
					frappe.throw(
						f"Row {row.idx}: Field '{row.student_fieldname}' does not exist in Student Master."
					)

	@frappe.whitelist()
	def get_preview(self):
		# Pick a sample student
		student_name = frappe.db.get_value(
			"Student Master", {"student_status": "Active"}, "name"
		) or frappe.db.get_value("Student Master", {}, "name")

		if not student_name:
			return "<div class='alert alert-warning'>" "No students found to generate preview." "</div>"

		student = frappe.get_doc("Student Master", student_name)

		# Safe preview context
		context = {
			"school_name": self.institute_name or "Institute Name",
			"school_logo": self.institute_logo or "",
			"student_name": student.first_name or "Student Name",
			"email": student.email or "email@example.com",
			"phone": student.phone or "9999999999",
			"address": getattr(student, "address", ""),
			"student_photo": "",
			"qr_code": "",
			"student": student,
			"template": self,
		}

		html = "<div class='row'>"

		if self.front_html:
			html += "<div class='col-md-6'><h5>Front</h5>"
			html += frappe.render_template(self.front_html, context)
			html += "</div>"

		if self.back_html:
			html += "<div class='col-md-6'><h5>Back</h5>"
			html += frappe.render_template(self.back_html, context)
			html += "</div>"

		html += "</div>"

		return html
