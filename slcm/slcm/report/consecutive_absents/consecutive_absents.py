import frappe
from frappe import _
from datetime import timedelta

def execute(filters=None):
	columns = [
		{
			"fieldname": "student",
			"label": _("Student"),
			"fieldtype": "Link",
			"options": "Student Master",
			"width": 150
		},
		{
			"fieldname": "student_name",
			"label": _("Student Name"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "program",
			"label": _("Program"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "consecutive_days",
			"label": _("Consecutive Days"),
			"fieldtype": "Int",
			"width": 120
		},
		{
			"fieldname": "last_absent_date",
			"label": _("Last Absent Date"),
			"fieldtype": "Date",
			"width": 120
		}
	]
	
	data = get_consecutive_absents(filters)
	
	return columns, data

def get_consecutive_absents(filters):
	# Fetch all absences ordered by student and date
	# We limit to last 30 days by default to optmize, or use filter
	
	threshold = frappe.utils.cint(filters.get("threshold")) or 3
	
	conditions = "status = 'Absent'"
	if filters.get("program"):
		conditions += f" AND student IN (SELECT name FROM `tabStudent Master` WHERE programme = '{filters.get('program')}')"
		
	# Get absences
	logs = frappe.db.sql(f"""
		SELECT student, student_name, attendance_date, course, course_offer
		FROM `tabStudent Attendance`
		WHERE {conditions}
		ORDER BY student, attendance_date DESC
	""", as_dict=True)
	
	result = []
	student_map = {}
	
	# Group by student
	for log in logs:
		if log.student not in student_map:
			student_map[log.student] = []
		student_map[log.student].append(log.attendance_date)
		
	# Check consecutive
	for student, dates in student_map.items():
		if len(dates) < threshold:
			continue
			
		dates.sort(reverse=True) # Newest first
		
		consecutive = 1
		for i in range(len(dates) - 1):
			diff = (dates[i] - dates[i+1]).days
			if diff == 1:
				consecutive += 1
			else:
				# Break if gap found. 
				# logic: we act on *current* consecutive streak? 
				# Or any streak? Usually current alert.
				break
				
		if consecutive >= threshold:
			# Get student details
			student_details = frappe.db.get_value("Student Master", student, ["first_name", "programme"], as_dict=True)
			
			result.append({
				"student": student,
				"student_name": student_details.first_name if student_details else "",
				"program": student_details.programme if student_details else "",
				"consecutive_days": consecutive,
				"last_absent_date": dates[0]
			})
			
	return result
