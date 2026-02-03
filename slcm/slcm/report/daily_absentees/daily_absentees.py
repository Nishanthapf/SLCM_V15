import frappe
from frappe import _

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
			"fieldname": "course",
			"label": _("Course"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "attendance_date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 100
		}
	]
	
	if not filters:
		filters = {}
		
	conditions = ""
	if filters.get("date"):
		conditions += f" AND attendance_date = '{filters.get('date')}'"
	else:
		conditions += " AND attendance_date = CURDATE()"
		
	data = frappe.db.sql(f"""
		SELECT student, student_name, course, status, attendance_date
		FROM `tabStudent Attendance`
		WHERE status = 'Absent' {conditions}
		ORDER BY student
	""", as_dict=True)
	
	return columns, data
