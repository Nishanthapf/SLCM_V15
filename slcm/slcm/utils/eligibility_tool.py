import frappe
from frappe.utils import flt, nowdate

def generate_eligibility_list(course_offering, cutoff_date=None):
	"""
	Generate a list of students with their eligibility status
	"""
	if not cutoff_date:
		cutoff_date = nowdate()
		
	# Ensure summaries are up to date
	update_summaries(course_offering)
	
	settings = frappe.get_single("Attendance Settings")
	min_req = flt(settings.minimum_attendance_percentage)
	condonable_range = [min_req - 10, min_req] # E.g., 65-75%
	
	data = []
	
	summaries = frappe.get_all("Attendance Summary", 
		filters={"course_offering": course_offering},
		fields=["student", "student_name", "attendance_percentage", "attended_classes", "total_classes"]
	)
	
	for s in summaries:
		status = "Eligible"
		action = "Release Hall Ticket"
		
		# Recalculate if needed or trust summary
		pct = s.attendance_percentage
		
		if pct < min_req:
			if pct >= condonable_range[0]:
				status = "Condonable Shortage"
				action = "Fine Applicable"
			else:
				status = "Detained"
				action = "Block Hall Ticket"
		
		data.append({
			"student": s.student,
			"student_name": s.student_name,
			"attendance_percentage": pct,
			"status": status,
			"recommended_action": action
		})
		
	return data

def update_summaries(course_offering):
	"""Force update of all summaries for this course"""
	from slcm.slcm.utils.attendance_calculator import calculate_student_attendance
	
	students = frappe.db.sql_list("""
		SELECT student FROM `tabAttendance Summary` WHERE course_offering=%s
	""", course_offering)
	
	for student in students:
		calculate_student_attendance(student, course_offering)
