import frappe
from frappe.model.document import Document
import json

class CurriculumManagement(Document):
	def onload(self):
		if not self.enrollment_types:
			self.set_default_enrollment_types()

	def set_default_enrollment_types(self):
		defaults = [
			{"enrollment_type": "Core", "is_active": 1, "display_name": "Core"},
			{"enrollment_type": "Programme Elective", "is_active": 1, "display_name": "Programme Elective"},
			{"enrollment_type": "Open Elective", "is_active": 1, "display_name": "Open Elective"},
			{"enrollment_type": "Zero Credit", "is_active": 0, "display_name": "Zero Credit"},
			{"enrollment_type": "Audit", "is_active": 0, "display_name": "Audit"}
		]
		for d in defaults:
			self.append("enrollment_types", d)

@frappe.whitelist()
def get_curriculum(program, academic_year):
	if not program or not academic_year:
		return None
	
	try:
		curriculum_name = f"{program}-{academic_year}"
		if frappe.db.exists("Curriculum", curriculum_name):
			doc = frappe.get_doc("Curriculum", curriculum_name)
			return doc.as_dict()
		else:
			# Return empty structure or existing data if partial
			return {
				"program": program,
				"academic_year": academic_year,
				"curriculum_courses": []
			}
	except Exception as e:
		frappe.log_error(f"Error fetching curriculum: {str(e)}")
		return None

@frappe.whitelist()
def save_curriculum(program, academic_year, department, courses):
	if isinstance(courses, str):
		courses = json.loads(courses)
		
	curriculum_name = f"{program}-{academic_year}"
	
	if frappe.db.exists("Curriculum", curriculum_name):
		doc = frappe.get_doc("Curriculum", curriculum_name)
	else:
		doc = frappe.new_doc("Curriculum")
		doc.program = program
		doc.academic_year = academic_year
		# Department is required for creation
		doc.department = department 

	doc.department = department
	
	# Clear existing courses and re-add
	doc.set("curriculum_courses", [])
	
	for course in courses:
		doc.append("curriculum_courses", {
			"semester": course.get("semester"),
			"course_group_type": course.get("course_group_type", "Course"),
			"course": course.get("course"),
			"enrollment_type": course.get("enrollment_type"),
			"cluster_name": course.get("cluster_name"),
			"min_courses": course.get("min_courses"),
			"max_courses": course.get("max_courses"),
			"credits": course.get("credits")
		})
		
	doc.save()
	return doc.name
