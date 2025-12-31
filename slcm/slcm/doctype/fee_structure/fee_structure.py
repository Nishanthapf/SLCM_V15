# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class FeeStructure(Document):
	def validate(self):
		self.validate_dates()
		self.calculate_total()

	def validate_dates(self):
		if self.valid_from and self.valid_until:
			if self.valid_from > self.valid_until:
				frappe.throw(_("Valid From date cannot be after Valid Until date"))

	def calculate_total(self):
		total = 0
		for component in self.components:
			total += component.amount or 0
		self.total_amount = total
