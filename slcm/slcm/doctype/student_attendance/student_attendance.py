# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class StudentAttendance(Document):
	def validate(self):
		self.validate_duplicate_attendance()
		self.fetch_course_details()

	def validate_duplicate_attendance(self):
		"""Prevent duplicate attendance for same student, date, and course schedule/group"""
		filters = {"student": self.student, "attendance_date": self.attendance_date, "docstatus": ["<", 2]}

		if self.course_schedule:
			filters["course_schedule"] = self.course_schedule
		elif self.student_group:
			filters["student_group"] = self.student_group
		elif self.course_offer:
			filters["course_offer"] = self.course_offer

		if self.period:
			filters["period"] = self.period

		existing = frappe.db.exists("Student Attendance", filters)

		if existing and existing != self.name:
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
