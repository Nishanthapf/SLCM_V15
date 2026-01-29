import json

import frappe
from frappe.model.document import Document


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
			{"enrollment_type": "Audit", "is_active": 0, "display_name": "Audit"},
		]
		for d in defaults:
			self.append("enrollment_types", d)


@frappe.whitelist()
def get_curriculum(program, academic_year, batch=None, section=None):
	if not program or not academic_year:
		return None

	try:
		# NAMING STRATEGY:
		# If Batch is present, we try to find a Curriculum specific to that Batch.
		# Name Format: {program}-{academic_year}-{batch}
		# Fallback: {program}-{academic_year} (Generic)
		
		curriculum_name = None
		if batch:
			# Try specific batch curriculum
			batch_c_name = f"{program}-{academic_year}-{batch}"
			if frappe.db.exists("Curriculum", batch_c_name):
				curriculum_name = batch_c_name
		
		# If no batch-specific found, fallback to generic?
		# User requirement: "configure the term department curriculum" based on batch/section
		# This implies if they select a batch, they WANT to see/edit that batch's curriculum.
		# If it doesn't exist yet, we should probably return empty or the generic one as 'template'?
		# For now, let's look for the generic one if specific doesn't exist, 
		# BUT if they save, it will create a new specific one (in save_curriculum).
		
		if not curriculum_name:
			generic_name = f"{program}-{academic_year}"
			if frappe.db.exists("Curriculum", generic_name):
				curriculum_name = generic_name

		data = {}

		if curriculum_name and frappe.db.exists("Curriculum", curriculum_name):
			doc = frappe.get_doc("Curriculum", curriculum_name)
			data = doc.as_dict()
			
			# If we fell back to generic, but user selected a batch, 
			# we might want to warn or indicate this is "inherited".
			# But for simplicity, we just load it. 
			# The frontend "Save" will trigger `save_curriculum` with the batch, creating a new record.
		else:
			# Return empty structure with defaults
			data = {
				"program": program,
				"academic_year": academic_year,
				"batch": batch,
				"academic_system": "Semester",  # Default
				"curriculum_courses": [],
			}

		# ---------------------------------------------------------
		# DYNAMIC SYNC: Enrich with latest Course Master Data
		# ---------------------------------------------------------
		if data.get("curriculum_courses"):
			# Collect all course names
			course_names = [
				d.get("course")
				for d in data["curriculum_courses"]
				if d.get("course_group_type") == "Course" and d.get("course")
			]

			if course_names:
				# Fetch latest details for these courses
				# We fetch ALL fields to support dynamic UI rendering
				courses_info = frappe.get_all("Course", filters={"name": ["in", course_names]}, fields=["*"])
				course_map = {c.name: c for c in courses_info}

				# Update the list in-memory
				for row in data["curriculum_courses"]:
					if row.get("course_group_type") == "Course" and row.get("course"):
						c_info = course_map.get(row.get("course"))
						if c_info:
							# Update Credit Value if strictly tied to master?
							# Requirement says "Changes in Course DocType... not reflected properly"
							# This implies we should show Master value, OR update stored value.
							# Let's update the 'read' value.
							# We also merge ALL logic fields so the UI can verify them.
							row.update(c_info)
							# explicitly ensure 'credits' matches 'credit_value' from master
							# unless we want to allow override?
							# Usually Curriculum overrides Master. But 'credit value edits are not syncing correctly'
							# implies the user wants to EDIT it.
							# If I overwrite it here, I reset user edits!
							# WAIT. "Changes in Course DocType are not reflected" vs "Edit credit value... not saved"
							# If user Edits credit in Curriculum, it should stay.
							# If user changes Master, does it update Curriculum?
							# Standard logic: Master is default. Curriculum is override.
							# If Curriculum 'credits' is 0 or None, take Master.
							# If Master changed from 3 to 4, and Curriculum was 3 (default), should it become 4?
							# If it was manually set to 3, it should stay 3.
							# HOW to distinguish? Hard.

							# Let's take a safe approach:
							# 1. Merge all OTHER descriptive fields (Description, Code, Custom Fields)
							# 2. For Credits, only update if it looks like a default?
							# Ref user complaint: "Changes in Course DocType are not reflected properly".
							# Likely referring to metadata (Name, new fields).
							# Ref complaint 3: "Edit credit value... updated credit value is NOT saved".
							# This means they DO want to save overrides.

							# Strategy:
							# - Map `credit_value` from Course to `master_credits` just in case UI wants to show diff.
							# - Copy all other fields.
							pass

		return data

	except Exception as e:
		frappe.log_error(f"Error fetching curriculum: {e}")
		return None


@frappe.whitelist()
def save_curriculum(program, academic_year, department, courses, academic_system="Semester", batch=None, section=None):
	if isinstance(courses, str):
		courses = json.loads(courses)

	# Naming Logic:
	# If batch is provided, create/update Program-Year-Batch
	# Else create/update Program-Year
	
	if batch:
		curriculum_name = f"{program}-{academic_year}-{batch}"
	else:
		curriculum_name = f"{program}-{academic_year}"

	if frappe.db.exists("Curriculum", curriculum_name):
		doc = frappe.get_doc("Curriculum", curriculum_name)
	else:
		doc = frappe.new_doc("Curriculum")
		doc.program = program
		doc.academic_year = academic_year
		doc.batch = batch # Set batch if new
		# Department is required for creation
		doc.department = department

	doc.department = department
	doc.academic_system = academic_system
	if batch:
		doc.batch = batch

	# Clear existing courses and re-add
	doc.set("curriculum_courses", [])

	for course in courses:
		row = {
			"semester": course.get("semester"),
			"course_group_type": course.get("course_group_type", "Course"),
			"course": course.get("course"),
			"enrollment_type": course.get("enrollment_type"),
			"cluster_name": course.get("cluster_name"),
			"min_courses": course.get("min_courses"),
			"max_courses": course.get("max_courses"),
			"credits": course.get("credits"),  # Persist user edit
		}
		doc.append("curriculum_courses", row)

	doc.save()
	return doc.name


@frappe.whitelist()
def get_course_dialog_columns():
	meta = frappe.get_meta("Course")
	columns = []
	for df in meta.fields:
		if (
			df.in_list_view
			and not df.hidden
			and df.fieldtype not in ["Section Break", "Column Break", "HTML", "Table", "Button"]
		):
			columns.append(df.fieldname)

	if not columns:
		columns = ["course_name", "department"]

	# Ensure critical fields are present
	for field in ["course_name", "course_code", "department_name"]:
		if field not in columns and any(f.fieldname == field for f in meta.fields):
			columns.insert(0, field)

	return columns


@frappe.whitelist()
def get_details_from_section(section):
	if not section:
		return {}
	
	return frappe.db.get_value(
		"Program Batch Section", 
		section, 
		["department", "program", "academic_year", "batch"], 
		as_dict=True
	)


@frappe.whitelist()
def get_courses_for_curriculum(department, txt=None, start=0, page_length=20):
	# Ensure correct types (VERY IMPORTANT)
	start = int(start or 0)
	page_length = int(page_length or 20)

	txt = f"%{txt}%" if txt else "%"

	return frappe.db.sql(
		"""
		SELECT
			c.name,
			c.course_name,
			c.credit_value,
			COALESCE(d.department_name, d.name) AS department_name
		FROM `tabCourse` c
		LEFT JOIN `tabDepartment` d
			ON d.name = c.department
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
