# Copyright (c) 2026, Nishanth and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import today, add_days

class TestHostelAllocation(FrappeTestCase):
	def setUp(self):
		# Create Dependencies
		self.student = create_student("Test Student Sync")
		self.hostel = create_hostel("Test Hostel A")
		self.room = create_room(self.hostel.name, "101")
		self.bed = create_bed(self.room.name, "1")

	def tearDown(self):
		frappe.db.rollback()

	def test_student_master_sync(self):
		# 1. Allocate
		allocation = frappe.get_doc({
			"doctype": "Hostel Allocation",
			"student": self.student.name,
			"hostel": self.hostel.name,
			"room": self.room.name,
			"bed": self.bed.name,
			"from_date": today(),
			"to_date": add_days(today(), 30),
			"status": "Allocated"
		}).insert()

		# Check Student Master
		student = frappe.get_doc("Student Master", self.student.name)
		self.assertEqual(student.is_hosteller, 1)
		self.assertEqual(student.hostel, self.hostel.name)
		self.assertEqual(student.hostel_room, self.room.name)
		self.assertEqual(student.hostel_bed, self.bed.name)
		self.assertEqual(str(student.allocation_date), today())
		self.assertEqual(student.vacated_date, None)

		# 2. Change Status to Vacated
		allocation.status = "Vacated"
		allocation.save()

		student.reload()
		self.assertEqual(student.is_hosteller, 0)
		# Details should still be there for history
		self.assertEqual(student.hostel, self.hostel.name)
		# Vacated Date should be set
		self.assertEqual(str(student.vacated_date), str(allocation.to_date))


def create_student(first_name):
	# Simplified student creation
	if frappe.db.exists("Student Master", {"first_name": first_name}):
		return frappe.get_doc("Student Master", {"first_name": first_name})
	
	doc = frappe.get_doc({
		"doctype": "Student Master",
		"naming_series": "STUD-.YYYY.-",
		"first_name": first_name,
		"last_name": "Test",
		"application_number": "APP-TEST-001",
		"email": "test@example.com"
	})
	doc.insert(ignore_permissions=True)
	return doc

def create_hostel(name):
	if frappe.db.exists("Hostel", name):
		return frappe.get_doc("Hostel", name)
	doc = frappe.get_doc({
		"doctype": "Hostel",
		"hostel_name": name,
		"hostel_type": "Co-ed"
	})
	doc.insert(ignore_permissions=True)
	return doc

def create_room(hostel, number):
	name = f"{hostel}-{number}"
	if frappe.db.exists("Hostel Room", name):
		return frappe.get_doc("Hostel Room", name)
	doc = frappe.get_doc({
		"doctype": "Hostel Room",
		"hostel": hostel,
		"room_number": number,
		"capacity": 2
	})
	doc.insert(ignore_permissions=True)
	return doc

def create_bed(room, number):
	name = f"{room}-{number}"
	if frappe.db.exists("Hostel Bed", name):
		return frappe.get_doc("Hostel Bed", name)
	doc = frappe.get_doc({
		"doctype": "Hostel Bed",
		"room": room,
		"bed_no": number
	})
	doc.insert(ignore_permissions=True)
	return doc
