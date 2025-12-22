# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class PlacementApplication(Document):
	def before_insert(self):
		# Prevent multiple applications for the same opportunity
		exists = frappe.db.exists(
			"Placement Application",
			{
				"student": self.student,
				"opportunity": self.opportunity,
			},
		)
		if exists:
			frappe.throw("You have already applied for this opportunity.")

		# Check application window
		opportunity = frappe.get_doc("Placement Opportunity", self.opportunity)
		now = now_datetime()

		if not (opportunity.application_start <= now <= opportunity.application_end):
			frappe.throw("Applications are closed for this opportunity.")
