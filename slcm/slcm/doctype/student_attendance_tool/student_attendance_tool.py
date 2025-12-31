# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class StudentAttendanceTool(Document):
	pass


@frappe.whitelist()
def get_student_attendance_records(
	based_on,
	date=None,
	student_group=None,
	course_schedule=None,
):
	"""
	Get student list with existing attendance status
	"""
	student_list = []
	student_attendance_list = []

	# Fetch student group from course schedule if needed
	if based_on == "Course Schedule" and course_schedule:
		student_group = frappe.db.get_value("Course Schedule", course_schedule, "student_group")

	# Get students from Student Group
	if student_group:
		student_list = frappe.get_all(
			"Student Group Student",
			fields=["student", "student_name", "group_roll_number"],
			filters={"parent": student_group, "active": 1},
			order_by="group_roll_number",
		)

	# Query Builder DocType
	StudentAttendance = frappe.qb.DocType("Student Attendance")

	# Fetch existing attendance
	if course_schedule:
		query = (
			frappe.qb.from_(StudentAttendance)
			.select(StudentAttendance.student, StudentAttendance.status)
			.where(StudentAttendance.course_schedule == course_schedule)
			.where(
				StudentAttendance.attendance_date == date
				if date
				else StudentAttendance.attendance_date.isnotnull()
			)
			.where(StudentAttendance.docstatus < 2)
		)
	else:
		query = (
			frappe.qb.from_(StudentAttendance)
			.select(StudentAttendance.student, StudentAttendance.status)
			.where(StudentAttendance.student_group == student_group)
			.where(StudentAttendance.attendance_date == date)
			.where((StudentAttendance.course_schedule == "") | StudentAttendance.course_schedule.isnull())
			.where(StudentAttendance.docstatus < 2)
		)

	student_attendance_list = query.run(as_dict=True)

	# Merge attendance status with student list
	attendance_map = {a.student: a.status for a in student_attendance_list}

	for student in student_list:
		if student.student in attendance_map:
			student.status = attendance_map[student.student]

	return student_list
