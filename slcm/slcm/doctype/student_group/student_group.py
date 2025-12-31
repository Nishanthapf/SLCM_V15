# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint


class StudentGroup(Document):
	def validate(self):
		self.validate_mandatory_fields()
		self.validate_strength()
		self.validate_students()
		self.validate_and_set_child_table_fields()
		self.validate_duplicate_students()

	def validate_mandatory_fields(self):
		if self.group_based_on == "Course" and not self.course:
			frappe.throw(_("Please select Course"))
		if self.group_based_on == "Course" and (not self.program and self.batch):
			frappe.throw(_("Please select Program"))
		if self.group_based_on == "Batch" and not self.program:
			frappe.throw(_("Please select Program"))

	def validate_strength(self):
		if cint(self.max_strength) < 0:
			frappe.throw(_("Max strength cannot be less than zero."))
		if self.max_strength and len(self.students) > self.max_strength:
			frappe.throw(
				_("Cannot enroll more than {0} students for this student group.").format(self.max_strength)
			)

	def validate_students(self):
		"""Validate students are enrolled and active"""
		enrolled_students = get_enrolled_students(
			self.academic_year,
			self.academic_term,
			self.program,
			self.batch,
			self.student_category,
			self.course,
		)
		enrolled_student_list = [d.student for d in enrolled_students] if enrolled_students else []

		for d in self.students:
			# Check if student is active
			student_status = frappe.db.get_value("Student Master", d.student, "student_status")
			if student_status != "Active" and d.active and not self.disabled:
				frappe.throw(
					_("{0} - {1} is not an active student").format(d.group_roll_number, d.student_name)
				)

			# Validate enrollment for Batch-based groups
			if (self.group_based_on == "Batch") and d.student not in enrolled_student_list:
				frappe.throw(
					_("{0} - {1} is not enrolled in the Batch {2}").format(
						d.group_roll_number, d.student_name, self.batch
					)
				)

			# Validate enrollment for Course-based groups
			if (self.group_based_on == "Course") and d.student not in enrolled_student_list:
				frappe.throw(
					_("{0} - {1} is not enrolled in the Course {2}").format(
						d.group_roll_number, d.student_name, self.course
					)
				)

	def validate_and_set_child_table_fields(self):
		"""Auto-set roll numbers and student names"""
		roll_numbers = [d.group_roll_number for d in self.students if d.group_roll_number]
		max_roll_no = max(roll_numbers) if roll_numbers else 0
		roll_no_list = []

		for d in self.students:
			if not d.student_name and d.student:
				student_doc = frappe.get_doc("Student Master", d.student)
				d.student_name = student_doc.first_name or student_doc.name

			if not d.group_roll_number:
				max_roll_no += 1
				d.group_roll_number = max_roll_no

			if d.group_roll_number in roll_no_list:
				frappe.throw(_("Duplicate roll number for student {0}").format(d.student_name))
			else:
				roll_no_list.append(d.group_roll_number)

	def validate_duplicate_students(self):
		"""Prevent duplicate students in the same group"""
		student_list = [d.student for d in self.students]
		duplicates = [s for s in student_list if student_list.count(s) > 1]
		if duplicates:
			frappe.throw(_("Duplicate students found: {0}").format(", ".join(set(duplicates))))


@frappe.whitelist()
def get_students(
	academic_year,
	group_based_on,
	academic_term=None,
	program=None,
	batch=None,
	student_category=None,
	course=None,
):
	"""
	Get enrolled students based on criteria
	Works with Student Enrollment structure
	"""
	enrolled_students = get_enrolled_students(
		academic_year, academic_term, program, batch, student_category, course
	)

	if enrolled_students:
		student_list = []
		for s in enrolled_students:
			# Check student status
			student_status = frappe.db.get_value("Student Master", s.student, "student_status")
			if student_status == "Active":
				s.update({"active": 1})
			else:
				s.update({"active": 0})
			student_list.append(s)
		return student_list
	else:
		frappe.msgprint(_("No students found"))
		return []


def get_enrolled_students(
	academic_year,
	academic_term=None,
	program=None,
	batch=None,
	student_category=None,
	course=None,
):
	"""
	Get enrolled students from Student Enrollment
	Adapted to work with Student Enrollment and Cohort structure
	"""
	filters = {"academic_year": academic_year, "status": "Enrolled", "docstatus": 1}

	# Build query
	query = """
		SELECT DISTINCT
			se.student,
			se.student_name
		FROM
			`tabStudent Enrollment` se
		WHERE
			se.academic_year = %(academic_year)s
			AND se.status = 'Enrolled'
			AND se.docstatus = 1
	"""

	if academic_term:
		query += " AND se.term_name = %(academic_term)s"
		filters["academic_term"] = academic_term

	if program:
		query += " AND se.program = %(program)s"
		filters["program"] = program

	# For batch-based, check Cohort batch field or Student Enrollment data_xgxm
	if batch:
		query += """
			AND (
				EXISTS (
					SELECT 1 FROM `tabCohort` c
					WHERE c.name = se.cohort
					AND c.batch = %(batch)s
				)
				OR se.data_xgxm = %(batch)s
			)
		"""
		filters["batch"] = batch

	# For course-based, check Program Enrollment child table
	if course:
		query += """
			AND EXISTS (
				SELECT 1 FROM `tabProgram Enrollment` pe
				WHERE pe.parent = se.name
				AND pe.course = %(course)s
			)
		"""
		filters["course"] = course

	query += " ORDER BY se.student_name ASC"

	students = frappe.db.sql(query, filters, as_dict=True)

	return students


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def fetch_students(doctype, txt, searchfield, start, page_len, filters):
	"""
	Fetch students for Student Group Student table
	Works with Student Enrollment structure
	"""
	if filters.get("group_based_on") != "Activity":
		enrolled_students = get_enrolled_students(
			filters.get("academic_year"),
			filters.get("academic_term"),
			filters.get("program"),
			filters.get("batch"),
			filters.get("student_category"),
			filters.get("course"),
		)

		# Students already in this group
		student_group_students = frappe.db.sql_list(
			"SELECT student FROM `tabStudent Group Student` WHERE parent=%s",
			(filters.get("student_group"),),
		)

		students = (
			[s.student for s in enrolled_students if s.student not in student_group_students]
			if enrolled_students
			else []
		)

		# Avoid empty IN () SQL
		if not students:
			return []

		placeholders = ", ".join(["%s"] * len(students))

		query = f"""
			SELECT name, first_name
			FROM `tabStudent Master`
			WHERE name IN ({placeholders})
			  AND (`{searchfield}` LIKE %s OR first_name LIKE %s)
			ORDER BY first_name
			LIMIT %s, %s
		"""

		return frappe.db.sql(
			query,
			(*students, f"%{txt}%", f"%{txt}%", start, page_len),
		)

	# Activity-based groups → show all students
	query = f"""
		SELECT name, first_name
		FROM `tabStudent Master`
		WHERE `{searchfield}` LIKE %s OR first_name LIKE %s
		ORDER BY first_name
		LIMIT %s, %s
	"""

	return frappe.db.sql(
		query,
		(f"%{txt}%", f"%{txt}%", start, page_len),
	)
