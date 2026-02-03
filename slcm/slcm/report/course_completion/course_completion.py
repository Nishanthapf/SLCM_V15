import frappe
from frappe import _
from frappe.utils import flt

def execute(filters=None):
	columns = [
		{
			"fieldname": "course_offering",
			"label": _("Course Offering"),
			"fieldtype": "Link",
			"options": "Course Offering",
			"width": 150
		},
		{
			"fieldname": "course_name",
			"label": _("Course Name"),
			"fieldtype": "Data",
			"width": 200
		},
		{
			"fieldname": "instructor",
			"label": _("Instructor"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"fieldname": "course_type",
			"label": _("Type"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"fieldname": "planned_hours",
			"label": _("Planned Hours"),
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "conducted_hours",
			"label": _("Conducted Hours"),
			"fieldtype": "Float",
			"width": 120
		},
		{
			"fieldname": "completion_percentage",
			"label": _("% Completion"),
			"fieldtype": "Percent",
			"width": 120
		},
		{
			"fieldname": "status",
			"label": _("Status"),
			"fieldtype": "Data",
			"width": 120
		}
	]
	
	data = get_course_completion_data(filters)
	
	return columns, data

def get_course_completion_data(filters):
	# 1. Get Settings for Planned Hours
	settings = frappe.get_single("Attendance Settings")
	core_hours = flt(settings.core_course_hours)
	elective_hours = flt(settings.elective_course_hours)
	
	conditions = "1=1"
	if filters.get("term"):
		conditions += f" AND co.term_name = '{filters.get('term')}'"
	if filters.get("academic_year"):
		conditions += f" AND co.academic_year = '{filters.get('academic_year')}'"
		
	# 2. Fetch Course Offerings with Course details
	offerings = frappe.db.sql(f"""
		SELECT 
			co.name as course_offering,
			co.course_title as course_name,
			co.instructor_name as instructor,
			c.course_type
		FROM `tabCourse Offering` co
		LEFT JOIN `tabCourse` c ON c.name = co.course
		WHERE {conditions}
	""", as_dict=True)
	
	result = []
	
	for off in offerings:
		# Determine Planned Hours
		planned = core_hours # Default
		if off.course_type == "Elective":
			planned = elective_hours
			
		# 3. Calculate Conducted Hours
		# specific method to calculate hours from sessions
		# Using SQL for aggregation
		stats = frappe.db.sql("""
			SELECT SUM(duration_in_hours) as conducted
			FROM `tabAttendance Session`
			WHERE course_offering = %s
			AND session_status = 'Completed'
		""", (off.course_offering), as_dict=True)
		
		conducted = flt(stats[0].conducted) if stats and stats[0].conducted else 0.0
		
		# 4. Calculate Percentage
		pct = 0.0
		if planned > 0:
			pct = (conducted / planned) * 100
			
		status = "On Track"
		if pct >= 100:
			status = "Completed"
		elif pct < 50: # Arbitrary warning threshold, maybe improve later
			status = "Lagging"
			
		result.append({
			"course_offering": off.course_offering,
			"course_name": off.course_name,
			"instructor": off.instructor,
			"course_type": off.course_type,
			"planned_hours": planned,
			"conducted_hours": conducted,
			"completion_percentage": pct,
			"status": status
		})
		
	return result
