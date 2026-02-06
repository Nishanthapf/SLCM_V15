# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class StudentAttendance(Document):
	def validate(self):
		self.validate_attendance_lock()
		self.validate_duplicate_attendance()
		self.fetch_course_details()
		self.track_changes()
	
	def validate_attendance_lock(self):
		"""Prevent modification of attendance records older than lock period"""
		if frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles():
			return
			
		lock_days = frappe.db.get_single_value("Attendance Settings", "attendance_lock_days")
		if not lock_days:
			return

		if self.attendance_date:
			from frappe.utils import date_diff, nowdate
			days_diff = date_diff(nowdate(), self.attendance_date)
			
			if days_diff > lock_days:
				frappe.throw(_("Attendance for this date is locked and cannot be modified."))

	
	def validate_duplicate_attendance(self):
		"""Prevent duplicate attendance for same student, date, and Session/Schedule"""
		filters = {"student": self.student, "docstatus": ["<", 2]}
		
		# If linked to a Session, uniqueness is strictly on Session
		if self.attendance_session:
			filters["attendance_session"] = self.attendance_session
		else:
			# Legacy/Manual checks
			filters["attendance_date"] = self.attendance_date
			if self.course_schedule:
				filters["course_schedule"] = self.course_schedule
			elif self.student_group:
				filters["student_group"] = self.student_group
			elif self.course_offer:
				filters["course_offer"] = self.course_offer
			
			if self.period:
				filters["period"] = self.period
			
			# Allow same day attendance if Session Type is different (e.g. Lecture vs Office Hour)
			if self.session_type:
				filters["session_type"] = self.session_type

		existing = frappe.db.exists("Student Attendance", filters)

		if existing and existing != self.name:
			if self.attendance_session:
				frappe.throw(_("Attendance already marked for this session."))
			else:
				frappe.throw(_("Attendance already exists for this student on {0}").format(self.attendance_date))

	def fetch_course_details(self):
		"""Fetch course details based on based_on field"""
		if self.based_on == "Course Schedule" and self.course_schedule:
			schedule = frappe.get_doc("Course Schedule", self.course_schedule)
			if not self.course:
				self.course = schedule.course
			if not self.program:
				self.program = schedule.program
			if not self.instructor:
				self.instructor = schedule.instructor
			if not self.room:
				self.room = schedule.room
			if schedule.student_group and not self.student_group:
				self.student_group = schedule.student_group

		elif self.based_on == "Student Group" and self.student_group:
			group = frappe.get_doc("Student Group", self.student_group)
			if not self.academic_year:
				self.academic_year = group.academic_year
			if not self.academic_term:
				self.academic_term = group.academic_term
			if not self.program:
				self.program = group.program

		# Fetch course from course offering
		if self.course_offer and not self.course:
			offering = frappe.get_doc("Course Offering", self.course_offer)
			self.course = offering.course_title
	
	def track_changes(self):
		"""Track changes for audit log"""
		if self.is_new():
			return
		
		# Get old doc
		old_doc = self.get_doc_before_save()
		if not old_doc:
			return
		
		# Track status changes
		if old_doc.status != self.status:
			self._log_change("status", old_doc.status, self.status)
	
	def _log_change(self, field, old_value, new_value):
		"""Store change information for logging after save"""
		if not hasattr(self, "_changes_to_log"):
			self._changes_to_log = []
		
		self._changes_to_log.append({
			"field": field,
			"old_value": old_value,
			"new_value": new_value
		})
	
	def on_update(self):
		"""Create audit log entries for changes"""
		if hasattr(self, "_changes_to_log"):
			for change in self._changes_to_log:
				self.create_edit_log(
					change["field"],
					change["old_value"],
					change["new_value"]
				)
		self.trigger_recalculation()
		self.trigger_session_update()
	
	def create_edit_log(self, field_changed, old_value, new_value):
		"""Create an attendance edit log entry"""
		try:
			from slcm.slcm.doctype.attendance_edit_log.attendance_edit_log import log_attendance_edit
			
			edit_reason = self.get("edit_reason") or "Attendance updated"
			
			log_attendance_edit(
				attendance_record=self.name,
				field_changed=field_changed,
				old_value=old_value,
				new_value=new_value,
				edit_reason=edit_reason
			)
		except Exception as e:
			frappe.log_error(f"Error creating edit log: {str(e)}")
	
	def on_trash(self):
		"""Trigger updates on deletion"""
		self.trigger_recalculation()
		self.trigger_session_update()
	
	def after_insert(self):
		"""Trigger attendance recalculation after insert"""
		self.trigger_recalculation()
		self.trigger_session_update()
	
	def on_update_after_submit(self):
		"""Trigger attendance recalculation after update"""
		self.trigger_recalculation()
		self.trigger_session_update()
	
	def on_cancel(self):
		"""Trigger attendance recalculation after cancel"""
		self.trigger_recalculation()
		self.trigger_session_update()
	
	def trigger_recalculation(self):
		"""Trigger attendance summary recalculation"""
		if self.student and self.course_offer:
			try:
				from slcm.slcm.utils.attendance_calculator import calculate_student_attendance
				frappe.enqueue(
					calculate_student_attendance,
					student=self.student,
					course_offering=self.course_offer,
					queue="short"
				)
			except Exception as e:
				frappe.log_error(f"Error triggering recalculation: {str(e)}")

	def trigger_session_update(self):
		"""Update the parent Attendance Session counts"""
		if self.attendance_session:
			try:
				doc = frappe.get_doc("Attendance Session", self.attendance_session)
				doc.update_attendance_summary()
			except Exception as e:
				frappe.log_error(f"Error updating session summary: {str(e)}")


@frappe.whitelist()
def get_enrolled_cohorts(student):
	"""
	Fetch all cohorts that a student is currently enrolled in.
	Used to filter Course Offerings in the UI.
	"""
	if not student:
		return []

	return frappe.get_all(
		"Student Enrollment",
		filters={"student": student, "status": "Enrolled"},
		pluck="cohort"
	)
