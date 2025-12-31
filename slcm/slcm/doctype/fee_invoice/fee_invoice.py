# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class FeeInvoice(Document):
	def validate(self):
		self.calculate_amounts()
		self.update_status()

	def calculate_amounts(self):
		# Calculate total from components
		if not self.fee_components:
			# If no components, get from fee assignment
			if self.fee_assignment:
				assignment = frappe.get_doc("Student Fee Assignment", self.fee_assignment)
				self.total_amount = assignment.total_amount
				if not self.fee_components:
					for comp in assignment.fee_components:
						self.append(
							"fee_components",
							{
								"fee_component": comp.fee_component,
								"component_name": comp.component_name,
								"amount": comp.amount,
								"is_taxable": comp.is_taxable,
								"tax_rate": comp.tax_rate,
								"tax_amount": comp.tax_amount,
								"total_amount": comp.total_amount,
							},
						)
		else:
			total = 0
			for component in self.fee_components:
				total += component.total_amount or 0
			self.total_amount = total

		# Calculate paid amount from payments
		paid = 0
		for payment in self.payments:
			paid += payment.amount or 0
		self.paid_amount = paid

		self.outstanding_amount = self.total_amount - self.paid_amount

	def update_status(self):
		if self.outstanding_amount <= 0:
			self.status = "Paid"
		elif self.paid_amount > 0:
			self.status = "Partially Paid"
		else:
			self.status = "Unpaid"

		# Check if overdue
		if self.due_date and frappe.utils.today() > self.due_date and self.status != "Paid":
			self.status = "Overdue"

	def on_update_after_submit(self):
		# Update fee assignment when payment is made
		if self.fee_assignment:
			assignment = frappe.get_doc("Student Fee Assignment", self.fee_assignment)
			assignment.paid_amount = self.paid_amount
			assignment.outstanding_amount = self.outstanding_amount
			assignment.update_status()
			assignment.save()
