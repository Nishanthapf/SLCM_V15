# Copyright (c) 2026, Nishanth and contributors
# For license information, please see license.txt

"""
Centralized Attendance Calculation Engine
This module contains all attendance calculation logic to ensure consistency
across the system. All attendance calculations should use these functions.
"""

import frappe
from frappe import _
from frappe.utils import flt


def calculate_student_attendance(student, course_offering):
	"""
	Calculate attendance for a single student in a specific course offering.
	
	Args:
		student: Student ID
		course_offering: Course Offering ID
	
	Returns:
		dict: Attendance summary with all calculated fields
	"""
	# Get or create attendance summary
	summary = get_or_create_summary(student, course_offering)
	
	# Get Settings
	settings = frappe.get_single("Attendance Settings")
	
	# Calculate sessions
	sessions_data = calculate_sessions(course_offering)
	
	# Calculate attendance
	attendance_data = calculate_attendance_records(student, course_offering)
	
	# Calculate office hours
	office_hours_data = calculate_office_hours(student, course_offering)
	
	# Get condonation
	condonation_data = get_approved_condonation(student, course_offering)
	
	# -- Update summary fields --
	# Map to existing fields in Attendance Summary JSON
	summary.total_classes = sessions_data['conducted']
	
	# Basic Attendance (Sessions)
	raw_attended = attendance_data['present'] + attendance_data['late']
	
	# Total Attended (including exceptions)
	total_attended = raw_attended
	
	# Add Office Hours if enabled
	if settings.include_office_hours_in_attendance:
		total_attended += office_hours_data['total']
	
	# Add Condonation
	total_attended += condonation_data['sessions']
	
	summary.attended_classes = total_attended
	
	# Calculate Percentage
	if summary.total_classes > 0:
		summary.attendance_percentage = (summary.attended_classes / summary.total_classes) * 100
	else:
		summary.attendance_percentage = 0
	
	# Determine eligibility
	minimum_required = flt(settings.minimum_attendance_percentage)
	
	if summary.attendance_percentage >= minimum_required:
		summary.eligible_for_exam = 1
		# summary.eligibility_status = "Eligible" # Field not in JSON
	else:
		summary.eligible_for_exam = 0
		# summary.eligibility_status = "Shortage" # Field not in JSON
	
	# Save
	summary.last_updated = frappe.utils.now()
	summary.save()
	
	return summary.as_dict()


def calculate_sessions(course_offering):
	"""Calculate session statistics for a course offering"""
	sessions = frappe.db.sql("""
		SELECT 
			COUNT(*) as total,
			SUM(CASE WHEN session_status = 'Scheduled' THEN 1 ELSE 0 END) as scheduled,
			SUM(CASE WHEN session_status = 'Conducted' THEN 1 ELSE 0 END) as conducted,
			SUM(CASE WHEN session_status = 'Cancelled' THEN 1 ELSE 0 END) as cancelled
		FROM `tabAttendance Session`
		WHERE course_offering = %s
	""", course_offering, as_dict=True)
	
	if sessions:
		return sessions[0]
	
	return {'total': 0, 'scheduled': 0, 'conducted': 0, 'cancelled': 0}


def calculate_attendance_records(student, course_offering):
	"""Calculate attendance record statistics for a student"""
	attendance = frappe.db.sql("""
		SELECT 
			COUNT(*) as total,
			SUM(CASE WHEN status = 'Present' THEN 1 ELSE 0 END) as present,
			SUM(CASE WHEN status = 'Absent' THEN 1 ELSE 0 END) as absent,
			SUM(CASE WHEN status = 'Late' THEN 1 ELSE 0 END) as late,
			SUM(CASE WHEN status = 'Excused' THEN 1 ELSE 0 END) as excused
		FROM `tabStudent Attendance`
		WHERE student = %s
		AND course_offer = %s
		AND docstatus < 2
	""", (student, course_offering), as_dict=True)
	
	if attendance:
		return attendance[0]
	
	return {'total': 0, 'present': 0, 'absent': 0, 'late': 0, 'excused': 0}


def calculate_office_hours(student, course_offering):
	"""Calculate office hours attendance for a student"""
	office_hours = frappe.db.sql("""
		SELECT 
			COUNT(*) as total,
			SUM(duration_hours) as total_hours
		FROM `tabOffice Hours Attendance`
		WHERE student = %s
		AND course_offering = %s
	""", (student, course_offering), as_dict=True)
	
	if office_hours:
		return office_hours[0]
	
	return {'total': 0, 'total_hours': 0}


def get_approved_condonation(student, course_offering):
	"""Get approved condonation sessions for a student"""
	try:
		condonation = frappe.db.sql("""
			SELECT 
				SUM(number_of_sessions) as sessions,
				SUM(number_of_hours) as hours
			FROM `tabStudent Attendance Condonation`
			WHERE student = %s
			AND course_offering = %s
			AND final_status = 'Approved'
			AND docstatus = 1
		""", (student, course_offering), as_dict=True)
		
		if condonation and condonation[0]['sessions']:
			return condonation[0]
	except Exception:
		# Table might not exist yet in Phase 1
		pass
	
	return {'sessions': 0, 'hours': 0}


def get_or_create_summary(student, course_offering):
	"""Get existing summary or create new one"""
	summary_name = frappe.db.exists("Attendance Summary", {
		"student": student,
		"course_offering": course_offering
	})
	
	if summary_name:
		return frappe.get_doc("Attendance Summary", summary_name)
	
	# Create new summary
	summary = frappe.get_doc({
		"doctype": "Attendance Summary",
		"student": student,
		"course_offering": course_offering
	})
	summary.insert()
	return summary


@frappe.whitelist()
def calculate_course_attendance(course_offering):
	"""Calculate attendance for all students in a course offering"""
	students = frappe.db.sql("""
		SELECT DISTINCT student
		FROM `tabStudent Attendance`
		WHERE course_offer = %s
	""", course_offering, as_dict=True)
	
	results = []
	for student_row in students:
		result = calculate_student_attendance(student_row.student, course_offering)
		results.append(result)
	
	return results


@frappe.whitelist()
def calculate_term_attendance(student, academic_term):
	"""Calculate attendance for all courses in a term for a student"""
	course_offerings = frappe.db.sql("""
		SELECT DISTINCT course_offer
		FROM `tabStudent Attendance`
		WHERE student = %s
		AND academic_term = %s
	""", (student, academic_term), as_dict=True)
	
	results = []
	for course_row in course_offerings:
		result = calculate_student_attendance(student, course_row.course_offer)
		results.append(result)
	
	return results


@frappe.whitelist()
def recalculate_all_summaries():
	"""Recalculate all attendance summaries (scheduled job)"""
	summaries = frappe.get_all("Attendance Summary", fields=["student", "course_offering"])
	
	count = 0
	for summary in summaries:
		try:
			calculate_student_attendance(summary.student, summary.course_offering)
			count += 1
		except Exception as e:
			frappe.log_error(f"Error calculating attendance for {summary.student}: {str(e)}")
	
	return {"success": True, "recalculated": count}


@frappe.whitelist()
def get_shortage_students(course_offering, threshold=None):
	"""Get students below attendance threshold"""
	if not threshold:
		settings = frappe.get_single("Attendance Settings")
		threshold = flt(settings.minimum_attendance_percentage)
	
	shortage_students = frappe.db.sql("""
		SELECT 
			student,
			student_name,
			final_attendance_percentage,
			shortage_hours,
			eligibility_status
		FROM `tabAttendance Summary`
		WHERE course_offering = %s
		AND final_attendance_percentage < %s
		ORDER BY final_attendance_percentage ASC
	""", (course_offering, threshold), as_dict=True)
	
	return shortage_students


@frappe.whitelist()
def get_eligibility_list(course_offering):
	"""Get list of eligible students for exams"""
	eligible_students = frappe.db.sql("""
		SELECT 
			student,
			student_name,
			final_attendance_percentage,
			eligibility_status
		FROM `tabAttendance Summary`
		WHERE course_offering = %s
		AND eligible_for_exam = 1
		ORDER BY student_name ASC
	""", course_offering, as_dict=True)
	
	return eligible_students
