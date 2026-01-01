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
		self.set_child_table_fields()
		self.validate_duplicate_students()

	# --------------------------------------------------
	# Mandatory field validation
	# --------------------------------------------------
	def validate_mandatory_fields(self):
		if self.group_based_on == "Batch":
			if not self.program:
				frappe.throw(_("Program is mandatory for Batch based Student Group"))
			if not self.batch:
				frappe.throw(_("Batch is mandatory for Batch based Student Group"))

		if self.group_based_on == "Course":
			if not self.program:
				frappe.throw(_("Program is mandatory for Course based Student Group"))
			if not self.course:
				frappe.throw(_("Course is mandatory for Course based Student Group"))

	# --------------------------------------------------
	# Strength validation
	# --------------------------------------------------
	def validate_strength(self):
		if cint(self.max_strength) < 0:
			frappe.throw(_("Max Strength cannot be less than zero"))

		if self.max_strength and len(self.students) > self.max_strength:
			frappe.throw(_("Cannot enroll more than {0} students").format(self.max_strength))

	# --------------------------------------------------
	# Student validation (PROGRAM-BASED ONLY)
	# --------------------------------------------------
	def validate_students(self):
		"""
		Validation MUST match get_students() logic
		"""

		if not self.program:
			return

		enrolled_students = frappe.db.sql(
			"""
			SELECT DISTINCT student
			FROM `tabStudent Enrollment`
			WHERE
				program = %(program)s
				AND IFNULL(status, '') IN ('Enrolled', 'Active')
				AND docstatus < 2
			""",
			{"program": self.program},
			as_dict=True,
		)

		enrolled_ids = {s.student for s in enrolled_students}

		for d in self.students:
			# Active student check
			student_status = frappe.db.get_value("Student Master", d.student, "student_status")

			if student_status != "Active" and d.active:
				frappe.throw(_("{0} is not an Active student").format(d.student))

			# Enrollment check
			if d.student not in enrolled_ids:
				frappe.throw(_("{0} is not enrolled in Program {1}").format(d.student, self.program))

	# --------------------------------------------------
	# Auto-set child table values
	# --------------------------------------------------
	def set_child_table_fields(self):
		roll_nos = [d.group_roll_number for d in self.students if d.group_roll_number]
		max_roll = max(roll_nos) if roll_nos else 0
		used_rolls = set()

		for d in self.students:
			if not d.student_name:
				d.student_name = frappe.db.get_value("Student Master", d.student, "first_name")

			if not d.group_roll_number:
				max_roll += 1
				d.group_roll_number = max_roll

			if d.group_roll_number in used_rolls:
				frappe.throw(_("Duplicate Roll Number: {0}").format(d.group_roll_number))

			used_rolls.add(d.group_roll_number)

	# --------------------------------------------------
	# Prevent duplicate students
	# --------------------------------------------------
	def validate_duplicate_students(self):
		students = [d.student for d in self.students]
		duplicates = {s for s in students if students.count(s) > 1}

		if duplicates:
			frappe.throw(_("Duplicate students found: {0}").format(", ".join(duplicates)))


# ======================================================
# BUTTON API — PROGRAM BASED FETCH
# ======================================================
@frappe.whitelist()
def get_students(program):
	"""
	Fetch students enrolled in a Program
	"""

	if not program:
		frappe.throw(_("Program is required"))

	students = frappe.db.sql(
		"""
		SELECT
			se.student,
			se.student_name
		FROM `tabStudent Enrollment` se
		WHERE
			se.program = %(program)s
			AND IFNULL(se.status, '') IN ('Enrolled', 'Active')
			AND se.docstatus < 2
		ORDER BY se.student_name
		""",
		{"program": program},
		as_dict=True,
	)

	for s in students:
		s.active = frappe.db.get_value("Student Master", s.student, "student_status") == "Active"

	return students
