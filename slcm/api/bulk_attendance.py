# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _


@frappe.whitelist()
def create_bulk_attendance_from_schedule(course_schedule, attendance_date, attendance_data):
	"""
	Create bulk attendance records from Course Schedule
	"""
	if not course_schedule:
		frappe.throw(_("Course Schedule is required"))

	if not attendance_date:
		frappe.throw(_("Attendance Date is required"))

	schedule = frappe.get_doc("Course Schedule", course_schedule)

	if not schedule.student_group:
		frappe.throw(_("Student Group is required in Course Schedule"))

	student_group = frappe.get_doc("Student Group", schedule.student_group)
	students = [row.student for row in student_group.students if row.active]

	if not students:
		frappe.throw(_("No active students found in Student Group"))

	if isinstance(attendance_data, str):
		attendance_data = json.loads(attendance_data)

	created_count = 0
	updated_count = 0
	errors = []

	for student in students:
		status = attendance_data.get(student, "Absent")

		existing = frappe.db.exists(
			"Student Attendance",
			{
				"student": student,
				"course_schedule": course_schedule,
				"attendance_date": attendance_date,
				"docstatus": ["<", 2],
			},
		)

		try:
			if existing:
				attendance = frappe.get_doc("Student Attendance", existing)
				attendance.status = status
				attendance.save()
				updated_count += 1
			else:
				attendance = frappe.get_doc(
					{
						"doctype": "Student Attendance",
						"student": student,
						"based_on": "Course Schedule",
						"course_schedule": course_schedule,
						"attendance_date": attendance_date,
						"status": status,
						"source": "Manual",
						"program": schedule.program,
						"course": schedule.course,
						"instructor": schedule.instructor,
						"room": schedule.room,
					}
				)
				attendance.insert()
				created_count += 1
		except Exception as e:
			errors.append(f"Error for student {student}: {e!s}")

	frappe.db.commit()

	total_processed = created_count + updated_count
	present_count = sum(1 for s in students if attendance_data.get(s) == "Present")
	absent_count = total_processed - present_count

	message = _("Successfully marked attendance for {0} students").format(total_processed)
	message += _(" ({0} Present, {1} Absent)").format(present_count, absent_count)

	return {
		"status": "success",
		"total_students": len(students),
		"created": created_count,
		"updated": updated_count,
		"total_processed": total_processed,
		"present_count": present_count,
		"absent_count": absent_count,
		"errors": errors,
		"message": message,
	}


@frappe.whitelist()
def create_bulk_attendance_from_group(student_group, attendance_date, attendance_data):
	"""
	Create bulk attendance records from Student Group
	"""
	if not student_group:
		frappe.throw(_("Student Group is required"))

	if not attendance_date:
		frappe.throw(_("Attendance Date is required"))

	group = frappe.get_doc("Student Group", student_group)
	students = [row.student for row in group.students if row.active]

	if not students:
		frappe.throw(_("No active students found in Student Group"))

	if isinstance(attendance_data, str):
		attendance_data = json.loads(attendance_data)

	created_count = 0
	updated_count = 0
	errors = []

	for student in students:
		status = attendance_data.get(student, "Absent")

		existing = frappe.db.exists(
			"Student Attendance",
			{
				"student": student,
				"student_group": student_group,
				"attendance_date": attendance_date,
				"docstatus": ["<", 2],
			},
		)

		try:
			if existing:
				attendance = frappe.get_doc("Student Attendance", existing)
				attendance.status = status
				attendance.save()
				updated_count += 1
			else:
				attendance = frappe.get_doc(
					{
						"doctype": "Student Attendance",
						"student": student,
						"based_on": "Student Group",
						"student_group": student_group,
						"group_based_on": group.group_based_on,
						"attendance_date": attendance_date,
						"status": status,
						"source": "Manual",
						"program": group.program,
						"academic_year": group.academic_year,
						"academic_term": group.academic_term,
					}
				)
				attendance.insert()
				created_count += 1
		except Exception as e:
			errors.append(f"Error for student {student}: {e!s}")

	frappe.db.commit()

	return {
		"status": "success",
		"created": created_count,
		"updated": updated_count,
		"errors": errors,
	}


@frappe.whitelist()
def mark_attendance(
	students_present=None,
	students_absent=None,
	student_group=None,
	course_schedule=None,
	date=None,
	based_on=None,
	group_based_on=None,
):
	"""
	Main API used by Student Attendance Tool
	"""
	if not date:
		frappe.throw(_("Date is required"))

	if isinstance(students_present, str):
		students_present = json.loads(students_present)
	if isinstance(students_absent, str):
		students_absent = json.loads(students_absent)

	students_present = students_present or []
	students_absent = students_absent or []

	created_count = 0
	updated_count = 0
	errors = []

	group_doc = frappe.get_doc("Student Group", student_group) if student_group else None
	schedule_doc = frappe.get_doc("Course Schedule", course_schedule) if course_schedule else None

	for student in students_present:
		try:
			attendance = frappe.get_doc(
				{
					"doctype": "Student Attendance",
					"student": student.get("student"),
					"attendance_date": date,
					"status": "Present",
					"source": "Manual",
					"based_on": based_on,
					"student_group": student_group,
					"course_schedule": course_schedule,
					"program": schedule_doc.program if schedule_doc else group_doc.program,
				}
			)
			attendance.insert()
			created_count += 1
		except Exception as e:
			errors.append(f"Error for student {student.get('student')}: {e!s}")

	for student in students_absent:
		try:
			attendance = frappe.get_doc(
				{
					"doctype": "Student Attendance",
					"student": student.get("student"),
					"attendance_date": date,
					"status": "Absent",
					"source": "Manual",
					"based_on": based_on,
					"student_group": student_group,
					"course_schedule": course_schedule,
					"program": schedule_doc.program if schedule_doc else group_doc.program,
				}
			)
			attendance.insert()
			created_count += 1
		except Exception as e:
			errors.append(f"Error for student {student.get('student')}: {e!s}")

	frappe.db.commit()

	return {
		"status": "success",
		"created": created_count,
		"updated": updated_count,
		"errors": errors,
	}
