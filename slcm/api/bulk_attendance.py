# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _


# ------------------------------------------------------------
# BULK ATTENDANCE FROM COURSE SCHEDULE
# ------------------------------------------------------------
@frappe.whitelist()
def create_bulk_attendance_from_schedule(course_schedule, attendance_date, attendance_data):
	if not course_schedule:
		frappe.throw(_("Course Schedule is required"))

	if not attendance_date:
		frappe.throw(_("Attendance Date is required"))

	schedule = frappe.get_doc("Course Schedule", course_schedule)

	if not schedule.student_group:
		frappe.throw(_("Student Group is required in Course Schedule"))

	group = frappe.get_doc("Student Group", schedule.student_group)
	students = [row.student for row in group.students if row.active]

	if not students:
		frappe.throw(_("No active students found"))

	if isinstance(attendance_data, str):
		attendance_data = json.loads(attendance_data)

	created, updated, errors = 0, 0, []

	for student in students:
		status = attendance_data.get(student, "Absent")

		existing = frappe.db.exists(
			"Student Attendance",
			{
				"student": student,
				"attendance_date": attendance_date,
				"course_schedule": course_schedule,
				"based_on": "Course Schedule",
				"docstatus": ("<", 2),
			},
		)

		try:
			if existing:
				doc = frappe.get_doc("Student Attendance", existing)
				doc.status = status
				doc.save()
				updated += 1
			else:
				frappe.get_doc(
					{
						"doctype": "Student Attendance",
						"student": student,
						"attendance_date": attendance_date,
						"date": attendance_date,
						"status": status,
						"based_on": "Course Schedule",
						"course_schedule": course_schedule,
						"student_group": schedule.student_group,
						"program": schedule.program,
						"course": schedule.course,
						"instructor": schedule.instructor,
						"room": schedule.room,
						"source": "Manual",
					}
				).insert()
				created += 1
		except Exception as e:
			errors.append(f"{student}: {e!s}")

	return {
		"status": "success",
		"created": created,
		"updated": updated,
		"errors": errors,
	}


# ------------------------------------------------------------
# BULK ATTENDANCE FROM STUDENT GROUP
# ------------------------------------------------------------
@frappe.whitelist()
def create_bulk_attendance_from_group(student_group, attendance_date, attendance_data):
	if not student_group:
		frappe.throw(_("Student Group is required"))

	if not attendance_date:
		frappe.throw(_("Attendance Date is required"))

	group = frappe.get_doc("Student Group", student_group)
	students = [row.student for row in group.students if row.active]

	if not students:
		frappe.throw(_("No active students found"))

	if isinstance(attendance_data, str):
		attendance_data = json.loads(attendance_data)

	created, updated, errors = 0, 0, []

	for student in students:
		status = attendance_data.get(student, "Absent")

		existing = frappe.db.exists(
			"Student Attendance",
			{
				"student": student,
				"attendance_date": attendance_date,
				"student_group": student_group,
				"based_on": "Student Group",
				"docstatus": ("<", 2),
			},
		)

		try:
			if existing:
				doc = frappe.get_doc("Student Attendance", existing)
				doc.status = status
				doc.save()
				updated += 1
			else:
				frappe.get_doc(
					{
						"doctype": "Student Attendance",
						"student": student,
						"attendance_date": attendance_date,
						"date": attendance_date,
						"status": status,
						"based_on": "Student Group",
						"student_group": student_group,
						"group_based_on": group.group_based_on,
						"program": group.program,
						"academic_year": group.academic_year,
						"academic_term": group.academic_term,
						"source": "Manual",
					}
				).insert()
				created += 1
		except Exception as e:
			errors.append(f"{student}: {e!s}")

	return {
		"status": "success",
		"created": created,
		"updated": updated,
		"errors": errors,
	}


# ------------------------------------------------------------
# MAIN STUDENT ATTENDANCE TOOL API
# ------------------------------------------------------------
@frappe.whitelist()
def mark_attendance(
	students_present=None,
	students_absent=None,
	student_group=None,
	course_schedule=None,
	date=None,
	based_on=None,
):
	if not date:
		frappe.throw(_("Date is required"))

	if not based_on:
		frappe.throw(_("Based On is required"))

	if isinstance(students_present, str):
		students_present = json.loads(students_present)
	if isinstance(students_absent, str):
		students_absent = json.loads(students_absent)

	students_present = students_present or []
	students_absent = students_absent or []

	group = frappe.get_doc("Student Group", student_group) if student_group else None
	schedule = frappe.get_doc("Course Schedule", course_schedule) if course_schedule else None

	program = schedule.program if schedule else group.program if group else None

	if not program:
		frappe.throw(_("Program could not be determined"))

	def upsert(student_id, status):
		existing = frappe.db.exists(
			"Student Attendance",
			{
				"student": student_id,
				"attendance_date": date,
				"based_on": based_on,
				"student_group": student_group,
				"course_schedule": course_schedule,
				"docstatus": ("<", 2),
			},
		)

		if existing:
			doc = frappe.get_doc("Student Attendance", existing)
			doc.status = status
			doc.save()
			return "updated"

		frappe.get_doc(
			{
				"doctype": "Student Attendance",
				"student": student_id,
				"attendance_date": date,
				"date": date,
				"status": status,
				"based_on": based_on,
				"student_group": student_group,
				"course_schedule": course_schedule,
				"program": program,
				"source": "Manual",
			}
		).insert()
		return "created"

	created, updated, errors = 0, 0, []

	for row in students_present:
		try:
			result = upsert(row.get("student"), "Present")
			created += result == "created"
			updated += result == "updated"
		except Exception as e:
			errors.append(f"{row.get('student')}: {e!s}")

	for row in students_absent:
		try:
			result = upsert(row.get("student"), "Absent")
			created += result == "created"
			updated += result == "updated"
		except Exception as e:
			errors.append(f"{row.get('student')}: {e!s}")

	return {
		"status": "success",
		"created": created,
		"updated": updated,
		"errors": errors,
	}
