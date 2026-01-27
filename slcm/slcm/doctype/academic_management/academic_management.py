import frappe
from frappe.model.document import Document

class AcademicManagement(Document):
	pass

@frappe.whitelist()
def create_class(data):
	if isinstance(data, str):
		data = frappe.parse_json(data)

	# Check duplicate
	# Adapting to Class Configuration fields based on JS input
	# JS input: department, program, academic_year, academic_term, course, class_type, faculty, max_strength, section, student_group_name
	
	exists = frappe.db.exists(
		"Class Configuration",
		{
			"class_name": data.get("student_group_name"),
		},
	)

	if exists:
		frappe.throw("A class with this name already exists.")

	doc = frappe.new_doc("Class Configuration")
	doc.class_name = data.get("student_group_name")
	doc.department = data.get("department")
	doc.programme = data.get("program")
	doc.academic_year = data.get("academic_year")
	doc.term = data.get("academic_term")
	doc.course = data.get("course")
	doc.type = data.get("class_type")
	doc.faculty = data.get("faculty")
	doc.capacity = data.get("max_strength")
	# doc.section = data.get("section") # Assuming section is handled or linked
	
	doc.insert()
	return doc.name

@frappe.whitelist()
def create_classes_by_section(
	department, program, academic_year, batch, academic_term, course, class_type, faculty
):
	# Enqueue this to run in background
	frappe.enqueue(
		"slcm.slcm.doctype.academic_management.academic_management.process_bulk_class_creation",
		queue="long",
		timeout=1500,
		department=department,
		program=program,
		academic_year=academic_year,
		batch=batch,
		academic_term=academic_term,
		course=course,
		class_type=class_type,
		faculty=faculty,
		user=frappe.session.user,
	)
	return "Bulk creation started. You will be notified upon completion."

def process_bulk_class_creation(
	department, program, academic_year, batch, academic_term, course, class_type, faculty, user
):
	sections = frappe.get_all(
		"Program Batch Section",
		filters={
			"department": department,
			"program": program,
			"academic_year": academic_year,
			"batch": batch,
		},
		fields=["name", "section_name", "capacity"],
	)

	created_count = 0
	skipped_count = 0

	for section in sections:
		class_name = f"{course}-{section.section_name}-{class_type}"
		
		if frappe.db.exists("Class Configuration", {"class_name": class_name}):
			skipped_count += 1
			continue

		doc = frappe.new_doc("Class Configuration")
		doc.class_name = class_name
		doc.department = department
		doc.programme = program
		doc.academic_year = academic_year
		doc.term = academic_term
		doc.course = course
		doc.type = class_type
		doc.faculty = faculty
		doc.capacity = section.capacity
		# Store section info if field exists, otherwise rely on name
		
		doc.insert()
		created_count += 1

	frappe.publish_realtime(
		"bulk_class_creation_done", {"created": created_count, "skipped": skipped_count}, user=user
	)
