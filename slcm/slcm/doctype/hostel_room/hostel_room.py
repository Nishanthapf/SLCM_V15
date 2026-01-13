# Copyright (c) 2024, Logic 360 and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class HostelRoom(Document):
	def validate(self):
		self.update_availability()

	def update_availability(self):
		if self.occupied >= self.capacity:
			self.is_available = 0
		else:
			self.is_available = 1
