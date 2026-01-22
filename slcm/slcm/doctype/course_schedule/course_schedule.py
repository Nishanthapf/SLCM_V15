# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CourseSchedule(Document):
	pass


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
