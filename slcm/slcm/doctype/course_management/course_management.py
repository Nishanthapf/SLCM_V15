import json
import frappe
from frappe.model.document import Document


class CourseManagement(Document):
	def onload(self):
		if not self.enrollment_types:
			self.set_default_enrollment_types()

	def set_default_enrollment_types(self):
		defaults = [
			{"enrollment_type": "Core", "is_active": 1, "display_name": "Core"},
			{"enrollment_type": "Programme Elective", "is_active": 1, "display_name": "Programme Elective"},
			{"enrollment_type": "Open Elective", "is_active": 1, "display_name": "Open Elective"},
			{"enrollment_type": "Zero Credit", "is_active": 0, "display_name": "Zero Credit"},
			{"enrollment_type": "Audit", "is_active": 0, "display_name": "Audit"},
		]
		for d in defaults:
			self.append("enrollment_types", d)


# ---------------------------------------------------------------------
# GET CURRICULUM
# ---------------------------------------------------------------------
@frappe.whitelist()
def get_curriculum(program, academic_year, batch=None, section=None):
	if not program or not academic_year:
		return None

	# Prefer batch-specific curriculum
	filters = {
		"program": program,
		"academic_year": academic_year,
	}

	if batch:
		filters["batch"] = batch

	name = frappe.db.get_value("Curriculum", filters, "name")

	# Fallback to generic curriculum
	if not name and batch:
		name = frappe.db.get_value(
			"Curriculum",
			{"program": program, "academic_year": academic_year, "batch": ["is", "not set"]},
			"name",
		)

	if name:
		doc = frappe.get_doc("Curriculum", name)
		return doc.as_dict()

	# Return empty structure
	return {
		"program": program,
		"academic_year": academic_year,
		"batch": batch,
		"academic_system": "Semester",
		"curriculum_courses": [],
	}


# ---------------------------------------------------------------------
# SAVE CURRICULUM (MASTER FIX)
# ---------------------------------------------------------------------
@frappe.whitelist()
def save_curriculum(
	program,
	academic_year,
	department,
	courses,
	academic_system="Semester",
	batch=None,
	section=None,
):


	if isinstance(courses, str):
		courses = json.loads(courses)

	# ----------------------------------
	# Determine EXISTING document NAME
	# ----------------------------------
	filters = {
		"program": program,
		"academic_year": academic_year,
	}

	if batch:
		filters["batch"] = batch

	name = frappe.db.get_value("Curriculum", filters, "name")
	
	# If not found with batch, try without batch (fallback for existing records without batch)
	if not name and batch:
		name = frappe.db.get_value("Curriculum", {
			"program": program,
			"academic_year": academic_year,
		}, "name")

	# ----------------------------------
	# CASE 1: UPDATE EXISTING
	# ----------------------------------
	if name:
		doc = frappe.get_doc("Curriculum", name)

		# Update fields
		doc.department = department
		doc.academic_system = academic_system
		doc.batch = batch
		doc.section = section

		# Replace child table
		doc.set("curriculum_courses", [])

		for course in courses:
			doc.append("curriculum_courses", {
				"semester": course.get("semester"),
				"enrollment_type": course.get("enrollment_type"),
				"course_group_type": course.get("course_group_type", "Course"),
				"course": course.get("course"),
				"cluster_name": course.get("cluster_name"),
				"min_courses": course.get("min_courses"),
				"max_courses": course.get("max_courses"),
				"credits": course.get("credits"),
			})

		# Save the document properly
		doc.save(ignore_permissions=True)
		frappe.db.commit()

		return {"status": "updated", "name": doc.name}

	# ----------------------------------
	# CASE 2: CREATE NEW (ONCE)
	# ----------------------------------
	doc = frappe.new_doc("Curriculum")
	doc.program = program
	doc.academic_year = academic_year
	doc.department = department
	doc.academic_system = academic_system
	doc.batch = batch
	doc.section = section

	for course in courses:
		doc.append("curriculum_courses", {
			"semester": course.get("semester"),
			"enrollment_type": course.get("enrollment_type"),
			"course_group_type": course.get("course_group_type", "Course"),
			"course": course.get("course"),
			"cluster_name": course.get("cluster_name"),
			"min_courses": course.get("min_courses"),
			"max_courses": course.get("max_courses"),
			"credits": course.get("credits"),
		})

	# 🔥 INSERT ONLY ONCE
	doc.insert(ignore_permissions=True)
	frappe.db.commit()

	return {"status": "created", "name": doc.name}



# ---------------------------------------------------------------------
# COURSE DIALOG COLUMNS
# ---------------------------------------------------------------------
@frappe.whitelist()
def get_course_dialog_columns():
	meta = frappe.get_meta("Course")
	columns = [
		df.fieldname
		for df in meta.fields
		if df.in_list_view
		and not df.hidden
		and df.fieldtype not in ["Section Break", "Column Break", "HTML", "Table", "Button"]
	]

	for field in ["course_name", "course_code", "department_name"]:
		if field not in columns and any(f.fieldname == field for f in meta.fields):
			columns.insert(0, field)

	return columns or ["course_name", "department_name"]


# ---------------------------------------------------------------------
# SECTION DETAILS
# ---------------------------------------------------------------------
@frappe.whitelist()
def get_details_from_section(section):
	if not section:
		return {}

	return frappe.db.get_value(
		"Program Batch Section",
		section,
		["department", "program", "academic_year", "batch"],
		as_dict=True,
	)


# ---------------------------------------------------------------------
# COURSE SEARCH (CUSTOM DIALOG)
# ---------------------------------------------------------------------
@frappe.whitelist()
def get_courses_for_curriculum(department, txt=None, start=0, page_length=20):
	start = int(start or 0)
	page_length = int(page_length or 20)
	txt = f"%{txt}%" if txt else "%"

	return frappe.db.sql(
		"""
		SELECT
			c.name,
			c.course_name,
			c.course_code,
			c.credit_value,
			COALESCE(d.department_name, d.name) AS department_name
		FROM `tabCourse` c
		LEFT JOIN `tabDepartment` d ON d.name = c.department
		WHERE
			c.department = %s
			AND c.status = 'Active'
			AND c.course_name LIKE %s
		ORDER BY c.course_name
		LIMIT %s, %s
		""",
		(department, txt, start, page_length),
		as_dict=True,
	)
