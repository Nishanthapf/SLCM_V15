# Copyright (c) 2026, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AttendanceSettings(Document):
	"""
	Single DocType to manage attendance configuration.
	This includes minimum percentage, course hours, office hours, and FA/MFA settings.
	"""
	
	def validate(self):
		"""Validate attendance settings"""
		self.validate_percentage()
		self.validate_hours()
	
	def validate_percentage(self):
		"""Ensure minimum attendance percentage is valid"""
		if self.minimum_attendance_percentage < 0 or self.minimum_attendance_percentage > 100:
			frappe.throw("Minimum attendance percentage must be between 0 and 100")
	
	def validate_hours(self):
		"""Ensure course hours are positive"""
		if self.core_course_hours <= 0:
			frappe.throw("Core course hours must be greater than 0")
		
		if self.elective_course_hours <= 0:
			frappe.throw("Elective course hours must be greater than 0")
		
		if self.core_office_hours < 0:
			frappe.throw("Core office hours cannot be negative")
		
		if self.elective_office_hours < 0:
			frappe.throw("Elective office hours cannot be negative")


@frappe.whitelist()
def get_attendance_settings():
	"""Get attendance settings as a dict"""
	if not frappe.db.exists("Attendance Settings", "Attendance Settings"):
		# Create default settings if not exists
		doc = frappe.get_doc({
			"doctype": "Attendance Settings",
			"minimum_attendance_percentage": 75,
			"attendance_unit": "Session",
			"core_course_hours": 60,
			"elective_course_hours": 40,
			"core_office_hours": 1,
			"elective_office_hours": 2,
			"include_office_hours_in_attendance": 1,
			"allow_condonation": 1,
			"condonation_approval_role": "Programme Chair",
			"allow_fa_mfa": 1,
			"fa_application_days_before_exam": 10,
			"fa_application_days_after_exam": 10,
			"auto_calculate_summary": 1,
			"calculation_frequency": "Daily"
		})
		doc.insert(ignore_permissions=True)
	
	return frappe.get_single("Attendance Settings").as_dict()


@frappe.whitelist()
def get_minimum_attendance_percentage():
	"""Get minimum attendance percentage"""
	settings = get_attendance_settings()
	return settings.get("minimum_attendance_percentage", 75)


@frappe.whitelist()
def get_course_hours(course_type):
	"""Get course hours based on course type (Core/Elective)"""
	settings = get_attendance_settings()
	
	if course_type == "Core":
		return {
			"course_hours": settings.get("core_course_hours", 60),
			"office_hours": settings.get("core_office_hours", 1)
		}
	elif course_type == "Elective":
		return {
			"course_hours": settings.get("elective_course_hours", 40),
			"office_hours": settings.get("elective_office_hours", 2)
		}
	else:
		frappe.throw(f"Invalid course type: {course_type}")
