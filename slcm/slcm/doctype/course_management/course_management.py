import json
import frappe
from frappe.model.document import Document


class CourseManagement(Document):
	def onload(self):
		self.set_default_course_types()
		self.set_default_enrollment_types()

	def set_default_course_types(self):
		defaults = [
			{"course_type": "Core", "is_active": 1, "display_name": "Core"},
			{"course_type": "Open Elective", "is_active": 1, "display_name": "Open Elective"},
			{"course_type": "Program Elective", "is_active": 1, "display_name": "Program Elective"},
			{"course_type": "Seminar", "is_active": 1, "display_name": "Seminar"},
		]
		
		# Get course_types safely (might not exist for Single DocType on first load)
		course_types = getattr(self, "course_types", None) or []
		
		# If empty, populate all
		if not course_types:
			for d in defaults:
				self.append("course_types", d)
		else:
			# Ensure missing ones are added
			existing = [d.course_type for d in course_types]
			for d in defaults:
				if d["course_type"] not in existing:
					self.append("course_types", d)

	def set_default_enrollment_types(self):
		defaults = [
			{"enrollment_type": "Full", "is_active": 1, "display_name": "Full"},
			{"enrollment_type": "Zero Credit", "is_active": 0, "display_name": "Zero Credit"}, # Default inactive per screenshot logic if needed, but user said "Load these". Check screenshot users defaults.
			# Screenshot shows: Core, Prog Elective... in Enrollment Types (OLD BAD STATE). 
			# User REQUIREMENT: Enrollment Type: Full, Zero Credit, Audit.
			# Screenshot 1 shows Enrollment Types with: Core, Prog El, Open El, Zero Credit, Audit.
			# This implies 'Zero Credit' and 'Audit' were ALREADY there but mixed with Course Types.
			# And 'Full' is missing.
			
			{"enrollment_type": "Audit", "is_active": 0, "display_name": "Audit"},
		]
		
		# User wanted: Enrollment_type: Full, Zero Credit, Audit.
		# I will ensure these exist.
		
		# Clean up WRONG types from Enrollment Types if they exist?
		# The user screenshot shows "Core", "Programme Elective", "Open Elective" INSIDE Enrollment Types.
		# These are WRONG. They belong in Course Types.
		# I should probably remove them from Enrollment Types to be clean, OR just leave them if user didn't ask to remove.
		# "so based on that the screenshot details should load" implies I should match the requirement.
		# Requirement: "Enrollment_type: Data field for the type name (Full, Zero credit, Audit) this need to show in default"
		
		# I'll simply ensure Full, Zero Credit, Audit are present.
		
		desired_types = ["Full", "Zero Credit", "Audit"]
	
		# Get enrollment_types safely (might not exist for Single DocType on first load)
		enrollment_types = getattr(self, "enrollment_types", None) or []
		
		if not enrollment_types:
			# Completley empty, easy.
			self.append("enrollment_types", {"enrollment_type": "Full", "is_active": 1, "display_name": "Full"})
			self.append("enrollment_types", {"enrollment_type": "Zero Credit", "is_active": 1, "display_name": "Zero Credit"})
			self.append("enrollment_types", {"enrollment_type": "Audit", "is_active": 1, "display_name": "Audit"})
		else:
			# Check existing
			existing_map = {d.enrollment_type: d for d in enrollment_types}
			
			if "Full" not in existing_map:
				self.append("enrollment_types", {"enrollment_type": "Full", "is_active": 1, "display_name": "Full"})
			
			if "Zero Credit" not in existing_map:
				self.append("enrollment_types", {"enrollment_type": "Zero Credit", "is_active": 1, "display_name": "Zero Credit"})
			
			if "Audit" not in existing_map:
				self.append("enrollment_types", {"enrollment_type": "Audit", "is_active": 1, "display_name": "Audit"})



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

	name = frappe.db.get_value("Course List", filters, "name")

	# Fallback to generic curriculum
	if not name and batch:
		name = frappe.db.get_value(
			"Course List",
			{"program": program, "academic_year": academic_year, "batch": ["is", "not set"]},
			"name",
		)

	if name:
		doc = frappe.get_doc("Course List", name)
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

	name = frappe.db.get_value("Course List", filters, "name")
	
	# If not found with batch, try without batch (fallback for existing records without batch)
	if not name and batch:
		name = frappe.db.get_value("Course List", {
			"program": program,
			"academic_year": academic_year,
		}, "name")

	# ----------------------------------
	# CASE 1: UPDATE EXISTING
	# ----------------------------------
	if name:
		doc = frappe.get_doc("Course List", name)

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
				"course_type": course.get("course_type"),
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
	doc = frappe.new_doc("Course List")
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
			"course_type": course.get("course_type"),
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
