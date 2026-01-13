# Copyright (c) 2024, Logic 360 and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HostelAllocation(Document):
	def validate(self):
		self.validate_room_availability()

	def validate_room_availability(self):
		if not self.room:
			return

		# Check if room belongs to the selected hostel
		room_doc = frappe.get_doc("Hostel Room", self.room)
		if room_doc.hostel != self.hostel:
			frappe.throw(_("Selected room {0} does not belong to Hostel {1}").format(self.room, self.hostel))

		# Validate Bed
		if self.bed:
			bed_doc = frappe.get_doc("Hostel Bed", self.bed)
			if bed_doc.room != self.room:
				frappe.throw(_("Selected bed {0} does not belong to Room {1}").format(self.bed, self.room))

			# Check vacancy (only for new or if bed changed)
			if (self.is_new() or self.has_value_changed("bed")) and bed_doc.is_occupied:
				frappe.throw(_("Bed {0} is already occupied.").format(self.bed))

		# Check capacity (fallback if no bed is selected, though bed should be reqd)
		# keeping logic just in case
		if self.is_new() or self.has_value_changed("room"):
			if room_doc.occupied >= room_doc.capacity:
				frappe.throw(_("Room {0} is fully occupied.").format(self.room))

	def on_update(self):
		# Always sync to Student Master on save, regardless of status
		# Status is now just a data field for information
		self.update_occupancy_on_save()
		self.update_student_master()

	def on_trash(self):
		self.update_occupancy_on_trash()
		self.clear_student_master()

	def update_occupancy_on_save(self):
		if not self.room:
			return

		# New Document
		if self.is_new():
			if self.status == "Allocated":
				self.update_occupancy(self.room, self.bed, 1)
			return

		# Existing Document
		before_save = self.get_doc_before_save()
		if not before_save:
			return

		# Status changed: Allocated -> Vacated (Decrease)
		if before_save.status == "Allocated" and self.status != "Allocated":
			self.update_occupancy(self.room, self.bed, -1)

		# Status changed: Vacated -> Allocated (Increase)
		elif before_save.status != "Allocated" and self.status == "Allocated":
			self.update_occupancy(self.room, self.bed, 1)

		# Bed/Room changed (only if currently allocated)
		elif self.status == "Allocated":
			# If room or bed changed, we need to handle it
			if self.has_value_changed("room") or self.has_value_changed("bed"):
				old_room = before_save.room
				old_bed = before_save.bed

				# Revert old
				self.update_occupancy(old_room, old_bed, -1)
				# Apply new
				self.update_occupancy(self.room, self.bed, 1)

	def update_occupancy_on_trash(self):
		if self.status == "Allocated":
			self.update_occupancy(self.room, self.bed, -1)

	def update_occupancy(self, room_id, bed_id, change):
		# Update Room Count
		if room_id:
			room_doc = frappe.get_doc("Hostel Room", room_id)
			room_doc.occupied += change
			if room_doc.occupied < 0:
				room_doc.occupied = 0
			room_doc.save()

		# Update Bed Status
		if bed_id:
			bed_doc = frappe.get_doc("Hostel Bed", bed_id)
			if change > 0:
				bed_doc.is_occupied = 1
			else:
				bed_doc.is_occupied = 0
			bed_doc.save()

	def update_student_master(self):
		if not self.student:
			return

		# Defensive coding as requested
		student = frappe.get_doc("Student Master", self.student)
		remarks = self.get("remarks")

		# Set is_hosteller flag based on status
		if self.status == "Allocated":
			student.is_hosteller = 1
			# Clear vacated date if re-allocated
			student.vacated_date = None

			# Map Fields for Active Allocation
			student.hostel = self.hostel
			student.hostel_room = self.room
			student.hostel_bed = self.bed
			student.hostel_block = self.hostel  # Derived from Hostel Name

			student.allocation_date = self.from_date
			student.allocation_end_date = self.to_date

			student.hostel_status = self.status
			student.hostel_remarks = remarks

			student.residence_agreement_signed = self.agreement_signed
			student.keys_handed_over = self.keys_handed_over

		else:
			# Vacated / Cleared / Other Status
			student.is_hosteller = 0

			# Set Vacated Date from to_date if available
			if self.to_date:
				student.vacated_date = self.to_date

			# Clear Location Fields (Residence Tab)
			student.hostel = None
			student.hostel_room = None
			student.hostel_bed = None
			student.hostel_block = None

			student.allocation_date = None
			student.allocation_end_date = None

			student.residence_agreement_signed = 0
			student.keys_handed_over = 0

			# Maintain Status and Remarks for history/info
			student.hostel_status = self.status
			student.hostel_remarks = remarks

		student.flags.ignore_validate = True
		student.save(ignore_permissions=True)

	def clear_student_master(self):
		if not self.student:
			return

		student = frappe.get_doc("Student Master", self.student)

		# Only clear if the student is still allocated to THIS hostel/room
		if student.hostel == self.hostel and student.hostel_room == self.room:
			student.is_hosteller = 0
			student.hostel = None
			student.hostel_block = None
			student.hostel_room = None
			student.hostel_bed = None
			student.allocation_date = None
			student.vacated_date = None  # Clear this too? Or set it?
			# User said: "WHEN Hostel Allocation is REMOVED / CLEARED: Clear Residence tab fields"

			student.hostel_status = None
			student.hostel_remarks = None

			student.save(ignore_permissions=True)


@frappe.whitelist()
def get_room_query(doctype, txt, searchfield, start, page_len, filters):
	hostel = filters.get("hostel")
	if not hostel:
		return []

	return frappe.db.sql(
		"""
		SELECT name, room_number, capacity, occupied
		FROM `tabHostel Room`
		WHERE hostel = %(hostel)s
		AND is_available = 1
		AND name LIKE %(txt)s
	""",
		{"hostel": hostel, "txt": "%" + txt + "%"},
	)


@frappe.whitelist()
def get_bed_query(doctype, txt, searchfield, start, page_len, filters):
	room = filters.get("room")
	if not room:
		return []

	return frappe.db.sql(
		"""
		SELECT name, bed_no
		FROM `tabHostel Bed`
		WHERE room = %(room)s
		AND is_occupied = 0
		AND name LIKE %(txt)s
	""",
		{"room": room, "txt": "%" + txt + "%"},
	)
