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
		
		# Check capacity (only for new allocations or if room changed)
		if self.is_new() or self.has_value_changed("room"):
			if room_doc.occupied >= room_doc.capacity:
				frappe.throw(_("Room {0} is fully occupied.").format(self.room))

	def on_update(self):
		self.validate_room_availability()
		self.update_occupancy_on_save()

	def on_trash(self):
		# When deleting, if room was allocated, free it up
		if self.status == "Allocated":
			self.update_room_occupancy(-1)

	def update_occupancy_on_save(self):
		if not self.room:
			return

		# New Document
		if self.is_new():
			if self.status == "Allocated":
				self.update_room_occupancy(1)
			return

		# Existing Document - check for status change
		before_save = self.get_doc_before_save()
		if not before_save:
			return

		# Status changed: Allocated -> Vacated/etc (Decrease)
		if before_save.status == "Allocated" and self.status != "Allocated":
			self.update_room_occupancy(-1)
		
		# Status changed: Vacated/etc -> Allocated (Increase)
		elif before_save.status != "Allocated" and self.status == "Allocated":
			self.update_room_occupancy(1)
		
		# Edge Case: Room changed (Not typically allowed, but good to handle)
		if before_save.room != self.room:
			# Revert old room
			if before_save.status == "Allocated":
				self.update_occupancy_for_room(before_save.room, -1)
			# Apply new room
			if self.status == "Allocated":
				self.update_occupancy_for_room(self.room, 1)

	def update_room_occupancy(self, change):
		self.update_occupancy_for_room(self.room, change)

	def update_occupancy_for_room(self, room_id, change):
		room_doc = frappe.get_doc("Hostel Room", room_id)
		room_doc.occupied += change
		room_doc.save()

@frappe.whitelist()
def get_room_query(doctype, txt, searchfield, start, page_len, filters):
	hostel = filters.get("hostel")
	if not hostel:
		return []
	
	return frappe.db.sql("""
		SELECT name, room_number, capacity, occupied
		FROM `tabHostel Room`
		WHERE hostel = %(hostel)s
		AND is_available = 1
		AND name LIKE %(txt)s
	""", {
		'hostel': hostel,
		'txt': "%" + txt + "%"
	})

@frappe.whitelist()
def bulk_update_status(names, status):
	import json
	if isinstance(names, str):
		names = json.loads(names)
	
	for name in names:
		doc = frappe.get_doc("Hostel Allocation", name)
		doc.status = status
		doc.save()
