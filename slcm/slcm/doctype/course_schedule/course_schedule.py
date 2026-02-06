# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CourseSchedule(Document):
	def after_insert(self):
		self.create_attendance_session()

	def create_attendance_session(self):
		if not self.schedule_date or not self.from_time or not self.to_time:
			return

		# Check if session already exists
		exists = frappe.db.exists("Attendance Session", {
			"course_schedule": self.name,
			"session_date": self.schedule_date,
			"session_start_time": self.from_time
		})

		if exists:
			return
		
		# Find Course Offering
		course_offering = self.get_course_offering()
		if not course_offering:
			frappe.log_error(f"Could not find Course Offering for Course Schedule {self.name}")
			return

		doc = frappe.get_doc({
			"doctype": "Attendance Session",
			"based_on": "Course Schedule",
			"course_schedule": self.name,
			"student_group": self.student_group,
			"course_offering": course_offering,
			"course": self.course,
			"instructor": self.instructor, # Note: Course Schedule has instructor link
			"room": self.room,
			"session_date": self.schedule_date,
			"session_start_time": self.from_time,
			"session_end_time": self.to_time,
			"session_type": "Lecture",
			"session_status": "Scheduled"
		})
		doc.insert(ignore_permissions=True)

	def get_course_offering(self):
		# Try to find an open course offering for this course and program
		filters = {
			"course_title": self.course,
			"status": "Open"
		}
		if self.program:
			filters["program"] = self.program
			
		offerings = frappe.get_all("Course Offering", filters=filters, limit=1)
		if offerings:
			return offerings[0].name
			
		# Fallback: try without program
		if self.program:
			del filters["program"]
			offerings = frappe.get_all("Course Offering", filters=filters, limit=1)
			if offerings:
				return offerings[0].name
				
		return None


@frappe.whitelist()
def get_events(start, end, filters=None):
	"""Returns events for Calendar view"""
	if not frappe.has_permission("Course Schedule", "read"):
		raise frappe.PermissionError

	if filters:
		filters = frappe.parse_json(filters)

	if not isinstance(filters, dict):
		filters = {}

	# Filter by date range
	filters["schedule_date"] = ["between", [start, end]]

	events = frappe.get_list(
		"Course Schedule",
		fields=[
			"name",
			"student_group",
			"course",
			"instructor_name",
			"room",
			"schedule_date",
			"from_time",
			"to_time",
			"color",
			"class_schedule_color",
		],
		filters=filters,
	)

	result = []
	for e in events:
		# Construct title
		title = e.course
		if e.student_group:
			title += f" - {e.student_group}"
		if e.room:
			title += f" ({e.room})"

		# Handle color
		color = e.color or e.class_schedule_color

		# Construct datetimes
		start_dt = f"{e.schedule_date} {e.from_time}"
		end_dt = f"{e.schedule_date} {e.to_time}"

		result.append(
			{
				"name": e.name,
				"doctype": "Course Schedule",
				"start": start_dt,
				"end": end_dt,
				"title": title,
				"allDay": 0,
				"color": color,
			}
		)

	return result
