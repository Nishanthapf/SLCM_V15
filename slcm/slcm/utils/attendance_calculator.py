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
	# Note: total_classes now stores HOURS
	summary.total_classes = sessions_data['conducted_hours']
	
	# Basic Attendance (Sessions)
	raw_attended = attendance_data['attended_hours']
	
	# Total Attended (including exceptions)
	total_attended = raw_attended
	
	# Add Office Hours if enabled
	if settings.include_office_hours_in_attendance:
		total_attended += office_hours_data['total_hours']
	
	# Add Condonation (assuming condonation records hours too)
	total_attended += condonation_data['hours']
	
	summary.attended_classes = total_attended
	
	# Calculate Percentage
	if summary.total_classes > 0:
		summary.attendance_percentage = (summary.attended_classes / summary.total_classes) * 100
	else:
		summary.attendance_percentage = 0
	
	# Determine eligibility
	minimum_required = flt(settings.minimum_attendance_percentage)
	
	is_eligible = 0
	if summary.attendance_percentage >= minimum_required:
		is_eligible = 1
	
	# Check FA/MFA status (Override)
	if not is_eligible and settings.allow_fa_mfa:
		if check_fa_mfa_eligibility(student, course_offering):
			is_eligible = 1
			# Optionally log or mark separate field that it is via FA/MFA
	
	summary.eligible_for_exam = is_eligible
	# summary.eligibility_status = "Eligible" if is_eligible else "Shortage"
	
	# Populate Application Lists (Condonation & FA/MFA)
	populate_application_lists(summary, student, course_offering)
	
	# Populate Student Group (Section)
	student_group = get_student_group(student, course_offering)
	summary.student_group = student_group
	if student_group:
		summary.section = frappe.db.get_value("Student Group", student_group, "section")

	# Save
	summary.last_updated = frappe.utils.now()
	summary.save(ignore_permissions=True)
	
	return summary.as_dict()


def calculate_sessions(course_offering):
	"""
	Calculate session statistics for a course offering.
	Returns total hours of CONDUCTED sessions (for Denominator).
	"""
	# We assume only 'Lecture' and 'Tutorial' count towards the mandatory denominator.
	# Office Hours are usually supplementary.
	sessions = frappe.db.sql("""
		SELECT 
			COALESCE(SUM(duration_hours), 0) as total_hours,
			COALESCE(SUM(CASE WHEN session_status = 'Conducted' THEN duration_hours ELSE 0 END), 0) as conducted_hours
		FROM `tabAttendance Session`
		WHERE course_offering = %s
		AND session_type IN ('Lecture', 'Tutorial')
		AND session_status != 'Cancelled'
	""", course_offering, as_dict=True)
	
	if sessions:
		return sessions[0]
	
	return {'total_hours': 0, 'conducted_hours': 0}


def calculate_attendance_records(student, course_offering):
	"""
	Calculate attendance for Regular Class (Lecture/Tutorial).
	Returns hours attended.
	"""
	attendance = frappe.db.sql("""
		SELECT 
			COALESCE(SUM(CASE 
				WHEN status IN ('Present', 'Late', 'Excused') THEN hours_counted 
				ELSE 0 
			END), 0) as attended_hours
		FROM `tabStudent Attendance`
		WHERE student = %s
		AND course_offer = %s
		AND session_type IN ('Lecture', 'Tutorial')
		AND docstatus < 2
	""", (student, course_offering), as_dict=True)
	
	if attendance:
		return attendance[0]
	
	return {'attended_hours': 0}


def calculate_office_hours(student, course_offering):
	"""
	Calculate office hours attendance for a student (from Student Attendance now).
	"""
	office_hours = frappe.db.sql("""
		SELECT 
			COALESCE(SUM(hours_counted), 0) as total_hours
		FROM `tabStudent Attendance`
		WHERE student = %s
		AND course_offer = %s
		AND session_type = 'Office Hour'
		AND status IN ('Present', 'Late', 'Excused')
		AND docstatus < 2
	""", (student, course_offering), as_dict=True)
	
	if office_hours:
		return office_hours[0]
	
	return {'total_hours': 0}


def get_approved_condonation(student, course_offering):
	"""Get approved condonation sessions for a student"""
	try:
		condonation = frappe.db.sql("""
			SELECT 
				COALESCE(SUM(number_of_sessions), 0) as sessions,
				COALESCE(SUM(number_of_hours), 0) as hours
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
	summary.insert(ignore_permissions=True)
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
			frappe.log_error(message=f"Error calculating attendance for {summary.student}: {str(e)}", title="Attendance Calculation Error")
	
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
			attendance_percentage,
			eligible_for_exam
		FROM `tabAttendance Summary`
		WHERE course_offering = %s
		AND attendance_percentage < %s
		ORDER BY attendance_percentage ASC
	""", (course_offering, threshold), as_dict=True)
	
	return shortage_students


@frappe.whitelist()
def get_eligibility_list(course_offering):
	"""Get list of eligible students for exams"""
	eligible_students = frappe.db.sql("""
		SELECT 
			student,
			student_name,
			attendance_percentage,
			eligible_for_exam
		FROM `tabAttendance Summary`
		WHERE course_offering = %s
		AND eligible_for_exam = 1
		ORDER BY student_name ASC
	""", course_offering, as_dict=True)
	
	return eligible_students


@frappe.whitelist()
def check_fa_mfa_eligibility(student, course_offering):
	"""Check if student has an approved FA/MFA application for this course"""
	# Get Course ID from Offering
	course_id = frappe.db.get_value("Course Offering", course_offering, "course_title")
	
	if not course_id:
		return False

	exists = frappe.db.exists("FA MFA Application", {
		"student": student,
		"course": course_id,
		"status": "Approved",
		"docstatus": 1
	})
	
	return True if exists else False


def populate_application_lists(summary, student, course_offering):
	"""
	Populate Condonation and FA/MFA application tables in Attendance Summary.
	"""
	# 1. Condonation Applications
	summary.set("condonation_list", [])
	
	try:
		condonation_apps = frappe.get_all("Student Attendance Condonation",
			filters={
				"student": student,
				"course_offering": course_offering,
				"docstatus": ["<", 2]  # Exclude Cancelled
			},
			fields=["name", "condonation_reason", "number_of_sessions", "number_of_hours", "final_status"],
			order_by="creation desc"
		)
		
		for app in condonation_apps:
			row = summary.append("condonation_list", {})
			row.condonation_application = app.name
			row.condonation_reason = app.condonation_reason
			row.number_of_sessions = app.number_of_sessions
			row.number_of_hours = app.number_of_hours
			row.final_status = app.final_status
			
	except Exception as e:
		frappe.log_error(message=f"Error fetching condonation list: {str(e)}", title="Condonation List Fetch Error")

	# 2. FA/MFA Applications
	summary.set("fa_mfa_list", [])
	
	try:
		# Need Course ID for FA/MFA
		course_id = frappe.db.get_value("Course Offering", course_offering, "course_title")
		if course_id:
			fa_mfa_apps = frappe.get_all("FA MFA Application",
				filters={
					"student": student,
					"course": course_id,
					"docstatus": ["<", 2]
				},
				fields=["name", "application_type", "reason", "status"],
				order_by="creation desc"
			)
			
			for app in fa_mfa_apps:
				row = summary.append("fa_mfa_list", {})
				row.fa_mfa_application = app.name
				row.application_type = app.application_type
				row.reason = app.reason
				row.status = app.status
				
	except Exception as e:
		frappe.log_error(message=f"Error fetching FA/MFA list: {str(e)}", title="FA/MFA List Fetch Error")


def get_student_group(student, course_offering):
	"""
	Get the primary Student Group (Section) for a student in this course offering.
	Fetches from the most recent Student Attendance record.
	"""
	# Try fetching from latest attendance record for this course offering
	# Using SQL to ensure latest record is fetched correctly
	groups = frappe.db.sql("""
		SELECT student_group FROM `tabStudent Attendance`
		WHERE student = %s AND course_offer = %s AND docstatus < 2
		AND student_group IS NOT NULL AND student_group != ''
		ORDER BY attendance_date DESC LIMIT 1
	""", (student, course_offering))
	
	if groups and groups[0][0]:
		return groups[0][0]
		
	# Fallback: Try connection via Course Offering if no attendance yet
	try:
		offering_details = frappe.db.get_value("Course Offering", course_offering, ["course_title", "term_name", "academic_year"], as_dict=True)
		if offering_details:
			groups = frappe.db.sql("""
				SELECT parent
				FROM `tabStudent Group Student`
				WHERE student = %s
				AND parent IN (
					SELECT name FROM `tabStudent Group`
					WHERE course = %s
					AND academic_term = %s
					AND academic_year = %s
					AND docstatus < 2
				)
				LIMIT 1
			""", (
				student, 
				offering_details.course_title, 
				offering_details.term_name, 
				offering_details.academic_year
			))
			
			if groups:
				return groups[0][0]
	except Exception:
		pass

	return None

