# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class StudentEnrollment(Document):
	def validate(self):
		self.validate_duplicate_enrollment()

	def before_save(self):
		self.fetch_program_and_courses()

	def fetch_program_and_courses(self):
		# 1. Ensure Program is set if Cohort is present
		if not self.program and self.cohort:
			self.program = frappe.db.get_value("Cohort", self.cohort, "program")

		# 2. Fetch courses if program is set and table is empty
		if self.program and not self.table_hxbo:
			program_doc = frappe.get_doc("Program", self.program)

			if program_doc.table_fela:
				for pc in program_doc.table_fela:
					self.append(
						"table_hxbo",
						{
							"course": pc.course,
							"course_name": pc.course_name,
							"course_type": pc.course_type,
							"course_status": pc.course_status,
							"credit_value": pc.credit_value,
						},
					)

	def validate_duplicate_enrollment(self):
		"""Prevent duplicate enrollment for same student, cohort, and academic year"""
		filters = {
			"student": self.student,
			"cohort": self.cohort,
			"academic_year": self.academic_year,
			"docstatus": ["<", 2],
		}

		existing = frappe.db.exists("Student Enrollment", filters)

		if existing and existing != self.name:
			frappe.throw(_("Enrollment already exists for this student in the selected cohort"))

	def on_update(self):
		# Update related records when enrollment is updated
		pass

	def get_attendance_summary(self):
		"""Get attendance summary for this enrollment"""
		attendance_records = frappe.get_all(
			"Student Attendance",
			filters={"student": self.student, "academic_year": self.academic_year, "docstatus": 1},
			fields=["status", "count(*) as count"],
			group_by="status",
		)
		return attendance_records

	def get_fee_summary(self):
		"""Get fee summary for this enrollment"""
		fee_assignments = frappe.get_all(
			"Student Fee Assignment",
			filters={"student": self.student, "enrollment": self.name, "docstatus": 1},
			fields=[
				"sum(total_amount) as total",
				"sum(paid_amount) as paid",
				"sum(outstanding_amount) as outstanding",
			],
		)
		return fee_assignments[0] if fee_assignments else None
