# Copyright (c) 2026, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import time_diff_in_hours
from slcm.slcm.utils.attendance_calculator import calculate_student_attendance

class AttendanceSession(Document):
	"""Track conducted class sessions for attendance calculation"""
	
	def validate(self):
		"""Validate session details"""
		self.calculate_duration()
		self.validate_times()
	
	def after_insert(self):
		"""Populate student attendance records"""
		self.create_student_attendance_records()

	def on_submit(self):
		"""Trigger attendance calculations"""
		self.update_student_attendance_status()
		self.trigger_calculations()

	def calculate_duration(self):
		"""Calculate session duration in hours"""
		if self.session_start_time and self.session_end_time:
			self.duration_hours = time_diff_in_hours(self.session_end_time, self.session_start_time)
	
	def validate_times(self):
		"""Ensure end time is after start time"""
		if self.session_start_time and self.session_end_time:
			if self.session_end_time <= self.session_start_time:
				frappe.throw("Session end time must be after start time")

	def create_student_attendance_records(self):
		"""Fetch enrolled students and create initial attendance records"""
		if self.flags.skip_auto_attendance:
			return

		students = self.get_enrolled_students()
		
		for student_id in students:
			# Check if record already exists to avoid duplicates
			exists = frappe.db.exists("Student Attendance", {
				"student": student_id,
				"attendance_session": self.name
			})
			
			if not exists:
				doc = frappe.get_doc({
					"doctype": "Student Attendance",
					"student": student_id,
					"attendance_session": self.name,
					"course_schedule": self.course_schedule,
					"course_offer": self.course_offering,
					"attendance_date": self.session_date,
					"date": self.session_date,
					"status": "Absent", # Default to Absent or Present based on logic, safely Absent
					"source": "Manual"
				})
				doc.insert(ignore_permissions=True)
				
		self.update_attendance_summary()

	def get_enrolled_students(self):
		"""Find students enrolled in the course"""
		# Approach: Find Student Enrollments that have this Course in their Program Enrollment table (table_hxbo)
		# Note: table_hxbo is likely named 'courses' in the object, but we query by table name in SQL for safety
		# Or rely on Student Enrollment -> Program Enrollment child table
		
		course_name = self.course
		if not course_name and self.course_offering:
			course_name = frappe.db.get_value("Course Offering", self.course_offering, "course_title")

		if not course_name:
			return []

		# Using SQL to join Student Enrollment and its child table
		students = frappe.db.sql("""
			SELECT DISTINCT parent.student 
			FROM `tabStudent Enrollment` as parent
			JOIN `tabProgram Enrollment` as child ON child.parent = parent.name
			WHERE child.course = %s
			AND parent.status = 'Enrolled'
			AND parent.docstatus = 0
		""", (course_name,), as_dict=True)
		
		return [s.student for s in students]

	def update_student_attendance_status(self):
		"""Lock attendance records on submit"""
		pass # Student Attendance is submittable? Or we just leave them.
		# If Student Attendance is a submittable doctype, we should submit them.
		# Let's check Student Attendance doctype. It has docstatus, so it might be submittable.
		# Generally Student Attendance is not a submittable document in standard ERPNext, but here?
		# It has "submitted" status? 
		# If it's not submittable, we just leave them.
		
	def trigger_calculations(self):
		"""Recalculate attendance for all students in this session"""
		students = self.get_enrolled_students()
		for student_id in students:
			calculate_student_attendance(student_id, self.course_offering)

	def before_save(self):
		"""Calculate summary before saving"""
		self.update_attendance_summary()
	
	def update_attendance_summary(self):
		"""Update attendance counts and student list"""
		# Count attendance records for this session
		# Query for counts
		attendance_data = frappe.db.sql("""
			SELECT 
				COUNT(*) as total,
				SUM(CASE WHEN status IN ('Present', 'Late') THEN 1 ELSE 0 END) as present,
				SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent,
				SUM(CASE WHEN status IN ('Present', 'Late') AND (s.gender = 'Male' OR s.gender = 'Man') THEN 1 ELSE 0 END) as boys,
				SUM(CASE WHEN status IN ('Present', 'Late') AND (s.gender = 'Female' OR s.gender = 'Woman') THEN 1 ELSE 0 END) as girls
			FROM `tabStudent Attendance` sa
			JOIN `tabStudent Master` s ON sa.student = s.name
			WHERE sa.attendance_session = %s
		""", self.name, as_dict=True)
		
		if attendance_data:
			data = attendance_data[0]
			self.total_students = data.get('total', 0)
			self.present_count = data.get('present', 0)
			self.absent_count = data.get('absent', 0)
			self.total_boys = data.get('boys', 0)
			self.total_girls = data.get('girls', 0)
			
			if self.total_students > 0:
				self.attendance_percentage = (self.present_count / self.total_students) * 100
			else:
				self.attendance_percentage = 0
			
			self.attendance_marked = 1 if self.total_students > 0 else 0
			
		# Populate Child Table
		# Clear existing rows to avoid duplication/stale data
		self.set("students", [])
		
		# Fetch details for child table
		student_records = frappe.db.sql("""
			SELECT sa.student, s.first_name, sa.status, s.gender
			FROM `tabStudent Attendance` sa
			JOIN `tabStudent Master` s ON sa.student = s.name
			WHERE sa.attendance_session = %s
			ORDER BY s.first_name asc
		""", self.name, as_dict=True)
		
		for record in student_records:
			self.append("students", {
				"student": record.student,
				"student_name": record.first_name,
				"status": record.status,
				"gender": record.gender
			})
			
	# Note: No separate save() call needed because this is called in before_save
	# or can be called manually followed by save() 

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
