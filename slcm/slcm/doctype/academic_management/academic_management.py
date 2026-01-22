# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

# import frappe
import frappe
from frappe.model.document import Document


class AcademicManagement(Document):
	pass


@frappe.whitelist()
def get_classes(filters=None):
	if isinstance(filters, str):
		filters = frappe.parse_json(filters)

	# Base query for Student Groups which are "Classes"
	query_filters = {}
	if filters.get("department"):
		query_filters["department"] = filters.get("department")
	if filters.get("academic_term"):
		query_filters["academic_term"] = filters.get("academic_term")
	if filters.get("course"):
		query_filters["course"] = filters.get("course")
	if filters.get("class_type"):
		query_filters["class_type"] = filters.get("class_type")
	if filters.get("faculty"):
		query_filters["faculty"] = filters.get("faculty")

	# Additional filter for text search
	or_filters = {}
	if filters.get("search_text"):
		or_filters["student_group_name"] = ["like", f"%{filters.get('search_text')}%"]

	classes = frappe.get_list(
		"Student Group",
		fields=[
			"name",
			"student_group_name",
			"course",
			"academic_term",
			"faculty",
			"class_type",
			"max_strength",
			"section",
			"status",
		],
		filters=query_filters,
		or_filters=or_filters,
		order_by="creation desc",
		limit_page_length=50,
	)
	return classes


@frappe.whitelist()
def create_class(data):
	if isinstance(data, str):
		data = frappe.parse_json(data)

	# Check duplicate
	exists = frappe.db.exists(
		"Student Group",
		{
			"program": data.get("program"),
			"academic_year": data.get("academic_year"),
			"academic_term": data.get("academic_term"),
			"course": data.get("course"),
			"class_type": data.get("class_type"),
			"section": data.get("section"),
			# Allow multiple theory classes for same section? assuming prompt implies unique configuration
		},
	)

	if exists:
		frappe.throw("A class with this configuration already exists.")

	doc = frappe.new_doc("Student Group")
	doc.update(data)
	doc.group_based_on = "Course"  # Default for academic classes
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
		# Construct Name or Check Duplicate
		filters = {
			"program": program,
			"academic_year": academic_year,
			"academic_term": academic_term,
			"course": course,
			"class_type": class_type,
			"section": section.name,
		}

		if frappe.db.exists("Student Group", filters):
			skipped_count += 1
			continue

		# Create Class
		doc = frappe.new_doc("Student Group")
		doc.student_group_name = f"{course}-{section.section_name}-{class_type}"  # Auto-naming strategy
		doc.group_based_on = "Course"
		doc.program = program
		doc.academic_year = academic_year
		doc.academic_term = academic_term
		doc.batch = batch  # Link batch if applicable
		doc.course = course
		doc.department = department
		doc.class_type = class_type
		doc.faculty = faculty
		doc.section = section.name
		doc.max_strength = section.capacity
		doc.status = "Active"

		# Uniquify name if needed manually, but autoname field is set.
		# If autoname is field:student_group_name, we must ensure it's unique.
		if frappe.db.exists("Student Group", doc.student_group_name):
			doc.student_group_name = f"{doc.student_group_name}-{frappe.generate_hash(length=4)}"

		doc.insert()
		created_count += 1

	frappe.publish_realtime(
		"bulk_class_creation_done", {"created": created_count, "skipped": skipped_count}, user=user
	)
