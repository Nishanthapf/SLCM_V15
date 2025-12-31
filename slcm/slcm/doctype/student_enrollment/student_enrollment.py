# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class StudentEnrollment(Document):
	def validate(self):
		self.validate_duplicate_enrollment()

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
