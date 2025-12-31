# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AttendancePeriod(Document):
	def validate(self):
		if self.start_time and self.end_time:
			if self.start_time >= self.end_time:
				frappe.throw("Start Time must be before End Time")
