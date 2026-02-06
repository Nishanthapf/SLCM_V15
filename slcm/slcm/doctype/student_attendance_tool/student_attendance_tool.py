# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class StudentAttendanceTool(Document):
	pass


@frappe.whitelist()
def get_student_attendance_records(
	based_on=None,
	date=None,
	student_group=None,
	course_schedule=None,
	class_schedule=None,
):
	"""
	Get student list with existing attendance status
	"""

	# -------------------- VALIDATION --------------------

	if not based_on:
		frappe.throw(_("Based On is required"))

	if based_on == "Student Group":
		if not student_group or not date:
			frappe.throw(_("Student Group and Date are required"))

	if based_on == "Course Schedule":
		if not course_schedule:
			frappe.throw(_("Course Schedule is required"))

	if based_on == "Class Schedule":
		if not class_schedule:
			frappe.throw(_("Class Schedule is required"))

	# -------------------- RESOLVE STUDENT GROUP --------------------

	if based_on == "Course Schedule" and course_schedule:
		student_group = frappe.db.get_value(
			"Course Schedule",
			course_schedule,
			"student_group",
		)

	if based_on == "Class Schedule" and class_schedule:
		student_group = frappe.db.get_value(
			"Class Schedule",
			class_schedule,
			"student_group",
		)

	if not student_group:
		return []

	# -------------------- FETCH STUDENTS --------------------

	student_list = frappe.get_all(
		"Student Group Student",
		fields=[
			"student",
			"student_name",
			"group_roll_number",
		],
		filters={
			"parent": student_group,
			"active": 1,
		},
		order_by="group_roll_number",
	)

	if not student_list:
		return []

	# -------------------- FETCH EXISTING ATTENDANCE --------------------

	StudentAttendance = frappe.qb.DocType("Student Attendance")

	query = (
		frappe.qb.from_(StudentAttendance)
		.select(
			StudentAttendance.student,
			StudentAttendance.status,
		)
		.where(StudentAttendance.docstatus < 2)
	)

	if based_on == "Course Schedule":
		query = query.where(StudentAttendance.course_schedule == course_schedule)

	if based_on == "Class Schedule":
		query = query.where(StudentAttendance.class_schedule == class_schedule)

	if date:
		query = query.where(StudentAttendance.attendance_date == date)

	if based_on == "Student Group":
		query = query.where(StudentAttendance.student_group == student_group)
		query = query.where(
			(StudentAttendance.course_schedule == "") | StudentAttendance.course_schedule.isnull()
		)

	attendance_rows = query.run(as_dict=True)

	# -------------------- MERGE STATUS --------------------

	attendance_map = {row["student"]: row["status"] for row in attendance_rows}

	for student in student_list:
		student["status"] = attendance_map.get(student["student"], "Absent")

	return student_list
