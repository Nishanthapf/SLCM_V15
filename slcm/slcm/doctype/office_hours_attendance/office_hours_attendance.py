# Copyright (c) 2026, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import time_diff_in_hours


class OfficeHoursAttendance(Document):
	"""Track student attendance in office hours"""
	
	def validate(self):
		"""Validate office hours attendance"""
		self.calculate_duration()
	
	def calculate_duration(self):
		"""Calculate duration if check-in and check-out times are provided"""
		if self.check_in_time and self.check_out_time:
			self.duration_hours = time_diff_in_hours(self.check_out_time, self.check_in_time)
	
	def after_insert(self):
		"""Update office hours session count after insert"""
		self.update_session_count()
		self.trigger_recalculation()
	
	def on_update(self):
		"""Trigger recalc on update"""
		self.trigger_recalculation()

	def on_trash(self):
		"""Update office hours session count after delete"""
		self.update_session_count()
		self.trigger_recalculation()
	
	def update_session_count(self):
		"""Update the total students attended count in the session"""
		if self.office_hours_session:
			session = frappe.get_doc("Office Hours Session", self.office_hours_session)
			session.update_attendance_count()

	def trigger_recalculation(self):
		"""Trigger attendance summary recalculation"""
		if self.student and self.course_offering:
			try:
				from slcm.slcm.utils.attendance_calculator import calculate_student_attendance
				frappe.enqueue(
					calculate_student_attendance,
					student=self.student,
					course_offering=self.course_offering,
					queue="short"
				)
			except Exception as e:
				frappe.log_error(f"Error triggering recalculation from office hours: {str(e)}")


@frappe.whitelist()
def get_student_office_hours_attendance(student, course_offering=None):
	"""Get office hours attendance for a student"""
	filters = {"student": student}
	
	if course_offering:
		filters["course_offering"] = course_offering
	
	return frappe.get_all(
		"Office Hours Attendance",
		filters=filters,
		fields=["*"],
		order_by="attendance_date desc"
	)
