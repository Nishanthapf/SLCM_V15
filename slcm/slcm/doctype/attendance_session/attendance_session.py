# Copyright (c) 2026, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import time_diff_in_hours


class AttendanceSession(Document):
	"""Track conducted class sessions for attendance calculation"""
	
	def validate(self):
		"""Validate session details"""
		self.calculate_duration()
		self.validate_times()
	
	def calculate_duration(self):
		"""Calculate session duration in hours"""
		if self.session_start_time and self.session_end_time:
			self.duration_hours = time_diff_in_hours(self.session_end_time, self.session_start_time)
	
	def validate_times(self):
		"""Ensure end time is after start time"""
		if self.session_start_time and self.session_end_time:
			if self.session_end_time <= self.session_start_time:
				frappe.throw("Session end time must be after start time")
	
	def update_attendance_summary(self):
		"""Update attendance counts for this session"""
		if self.session_status != "Conducted":
			return
		
		# Count attendance records for this session
		attendance_data = frappe.db.sql("""
			SELECT 
				COUNT(*) as total,
				SUM(CASE WHEN status IN ('Present', 'Late') THEN 1 ELSE 0 END) as present,
				SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent
			FROM `tabStudent Attendance`
			WHERE attendance_session = %s
			AND docstatus < 2
		""", self.name, as_dict=True)
		
		if attendance_data:
			data = attendance_data[0]
			self.total_students = data.get('total', 0)
			self.present_count = data.get('present', 0)
			self.absent_count = data.get('absent', 0)
			
			if self.total_students > 0:
				self.attendance_percentage = (self.present_count / self.total_students) * 100
			else:
				self.attendance_percentage = 0
			
			self.attendance_marked = 1 if self.total_students > 0 else 0
			
			self.save()


@frappe.whitelist()
def mark_session_conducted(session_name):
	"""Mark a session as conducted"""
	session = frappe.get_doc("Attendance Session", session_name)
	session.session_status = "Conducted"
	session.save()
	return session


@frappe.whitelist()
def get_pending_sessions(instructor=None, course_offering=None):
	"""Get sessions where attendance is not yet marked"""
	filters = {
		"session_status": "Conducted",
		"attendance_marked": 0
	}
	
	if instructor:
		filters["instructor"] = instructor
	
	if course_offering:
		filters["course_offering"] = course_offering
	
	return frappe.get_all(
		"Attendance Session",
		filters=filters,
		fields=["name", "session_date", "course", "instructor", "duration_hours"],
		order_by="session_date desc"
	)
