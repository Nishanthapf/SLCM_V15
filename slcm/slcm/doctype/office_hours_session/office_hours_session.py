# Copyright (c) 2026, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import time_diff_in_hours


class OfficeHoursSession(Document):
	"""Track office hours sessions separately from regular class sessions"""
	
	def validate(self):
		"""Validate office hours session"""
		self.calculate_duration()
		self.validate_times()
	
	def calculate_duration(self):
		"""Calculate session duration in hours"""
		if self.start_time and self.end_time:
			self.duration_hours = time_diff_in_hours(self.end_time, self.start_time)
	
	def validate_times(self):
		"""Ensure end time is after start time"""
		if self.start_time and self.end_time:
			if self.end_time <= self.start_time:
				frappe.throw("End time must be after start time")
	
	def update_attendance_count(self):
		"""Update count of students who attended"""
		count = frappe.db.count(
			"Office Hours Attendance",
			filters={"office_hours_session": self.name}
		)
		self.total_students_attended = count
		self.save()


@frappe.whitelist()
def get_office_hours_for_course(course_offering, faculty=None):
	"""Get all office hours sessions for a course"""
	filters = {"course_offering": course_offering}
	
	if faculty:
		filters["faculty"] = faculty
	
	return frappe.get_all(
		"Office Hours Session",
		filters=filters,
		fields=["*"],
		order_by="session_date desc"
	)
