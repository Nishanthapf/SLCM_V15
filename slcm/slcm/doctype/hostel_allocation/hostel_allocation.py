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

	def on_submit(self):
		self.update_room_occupancy(1)

	def on_cancel(self):
		self.update_room_occupancy(-1)

	def update_room_occupancy(self, change):
		if not self.room:
			return
		
		room_doc = frappe.get_doc("Hostel Room", self.room)
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
