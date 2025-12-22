# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PlacementEvent(Document):
	def validate(self):
		# Event must be within application window
		opportunity = frappe.get_doc("Placement Opportunity", self.opportunity)

		if not (opportunity.application_start <= self.event_date <= opportunity.application_end):
			frappe.throw("Event date must be within the application period.")
