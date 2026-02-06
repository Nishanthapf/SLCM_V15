# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.utils import time_diff_in_hours, get_datetime


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
	class_schedule=None,
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
	class_sched = frappe.get_doc("Class Schedule", class_schedule) if class_schedule else None

	program = None
	if schedule:
		program = schedule.program
	elif class_sched:
		program = class_sched.programme
	elif group:
		program = group.program

	if not program:
		frappe.throw(_("Program could not be determined"))

	# Determine Course
	course = None
	if schedule:
		course = schedule.course
	elif class_sched:
		course = class_sched.course
	elif group:
		course = group.course

	# Determine Course Offering
	course_offering = None
	
	# Priority 0: Explicit link in Class Schedule
	if class_sched and class_sched.course_offering:
		course_offering = class_sched.course_offering
	
	# Priority 1: Strict match with Academic Year and Term (if available)
	if not course_offering and course and program:
		filters = {"course_title": course, "program": program, "docstatus": 1}
		
		# Add Academic Year if available in Student Group
		if group and group.academic_year:
			filters["academic_year"] = group.academic_year
			
		# Add Academic Term if available in Student Group (check against term_name or similar)
		# Note: Course Offering has 'term_name' data field, might be risky to filter strictly if naming differs.
		# We'll stick to Year for strictness first.
		
		# Try fetching with Year
		course_offering = frappe.db.get_value("Course Offering", filters, "name")
		
		# Strategy 2: If fail, try removing Academic Year (maybe data mismatch)
		if not course_offering:
			filters.pop("academic_year", None)
			course_offering = frappe.db.get_value("Course Offering", filters, "name")
			
		# Strategy 3: If still fail, try finding *any* Open/Active offering for this Course+Program
		# Sort by creation desc to get the most recent one
		if not course_offering:
			offerings = frappe.get_all(
				"Course Offering",
				filters={"course_title": course, "program": program, "docstatus": 1},
				fields=["name"],
				order_by="creation desc",
				limit=1
			)
			if offerings:
				course_offering = offerings[0].name

	# ---------------------------------------------------------
	# Ensure Attendance Session Exists (Unified Model)
	# ---------------------------------------------------------
	attendance_session = None
	if class_sched:
		# Check if session exists for this schedule and date
		session_name = frappe.db.exists(
			"Attendance Session",
			{
				"course_schedule": class_schedule if based_on == "Course Schedule" else None, # Class Schedule logic used strictly below
				# Wait, fields are mismatched.
				# Attendance Session has 'course_schedule' (Link: Course Schedule).
				# It doesn't seem to have 'class_schedule' yet?
				# If we are moving to Class Schedule, Attendance Session might need updating too.
				# For now, let's look for session by DATE and COURSE OFFERING + START TIME
				"session_date": date,
				"course_offering": course_offering,
				"docstatus": ("<", 2)
			}
		)
		
		if session_name:
			attendance_session = session_name
		else:
			# Create new Attendance Session
			# We need start/end time from Class Schedule
			if class_sched.from_time and class_sched.to_time:
				# Calculate duration
				start_dt = frappe.utils.get_datetime(f"{date} {class_sched.from_time}")
				end_dt = frappe.utils.get_datetime(f"{date} {class_sched.to_time}")
				duration = frappe.utils.time_diff_in_hours(end_dt, start_dt)
				
				sess_doc = frappe.get_doc({
					"doctype": "Attendance Session",
					"session_date": date,
					"based_on": based_on,
					"student_group": student_group,
					"class_schedule": class_schedule,
					"course_schedule": course_schedule if based_on == "Course Schedule" else None,
					"course_offering": course_offering,
					"session_start_time": class_sched.from_time,
					"session_end_time": class_sched.to_time,
					"duration_hours": duration,
					"session_type": "Lecture", # Default, maybe fetch from Class Schedule later
					"instructor": class_sched.instructor,
					"room": class_sched.room,
					"session_status": "Conducted", # Since we are marking attendance
					"attendance_marked": 1
				})
				sess_doc.flags.skip_auto_attendance = True
				sess_doc.insert(ignore_permissions=True)
				attendance_session = sess_doc.name

	# ---------------------------------------------------------

	def upsert(student_id, status):
		existing = frappe.db.exists(
			"Student Attendance",
			{
				"student": student_id,
				"attendance_date": date,
				"based_on": based_on,
				"student_group": student_group,
				"course_schedule": course_schedule,
				"class_schedule": class_schedule,
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
				"attendance_based_on": based_on,
				"student_group": student_group,
				"course_schedule": course_schedule,
				"class_schedule": class_schedule,
				"program": program,
				"course": course,
				"course_offer": course_offering,
				"attendance_session": attendance_session,
				"instructor": schedule.instructor if schedule else class_sched.instructor if class_sched else None,
				"room": schedule.room if schedule else class_sched.room if class_sched else None,
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

	# ---------------------------------------------------------
	# Trigger Session Summary Update
	# ---------------------------------------------------------
	if attendance_session:
		try:
			session_doc = frappe.get_doc("Attendance Session", attendance_session)
			session_doc.update_attendance_summary()
		except Exception as e:
			# Don't fail the whole request if summary update fails, just log it
			frappe.log_error(f"Failed to update summary for session {attendance_session}: {e!s}")
	# ---------------------------------------------------------

	return {
		"status": "success",
		"created": created,
		"updated": updated,
		"errors": errors,
	}
