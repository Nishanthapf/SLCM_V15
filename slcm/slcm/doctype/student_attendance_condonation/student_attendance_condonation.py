# Copyright (c) 2026, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class StudentAttendanceCondonation(Document):
	def validate(self):
		self.validate_shortage()
	
	def validate_shortage(self):
		"""Ensure student actually has a shortage before allowing application"""
		# Only validate on new application, not during approval process
		if self.is_new():
			# Fetch current summary
			summary = frappe.db.get_value("Attendance Summary", 
				{"student": self.student, "course_offering": self.course_offering}, 
				["attendance_percentage"], as_dict=True)
			
			if not summary:
				# Force calculation if summary doesn't exist
				from slcm.slcm.utils.attendance_calculator import calculate_student_attendance
				summary_data = calculate_student_attendance(self.student, self.course_offering)
				summary = frappe._dict(summary_data)
			
			settings = frappe.get_single("Attendance Settings")
			min_req = flt(settings.minimum_attendance_percentage)
			
			if summary.attendance_percentage >= min_req:
				frappe.msgprint("Warning: Student already has sufficient attendance.", alert=True)

	def on_submit(self):
		if self.final_status != "Approved":
			frappe.throw("Only Approved applications can be submitted")
			
		self.trigger_recalculation()
	
	def on_cancel(self):
		self.trigger_recalculation()
		
	def trigger_recalculation(self):
		from slcm.slcm.utils.attendance_calculator import calculate_student_attendance
		calculate_student_attendance(self.student, self.course_offering)
