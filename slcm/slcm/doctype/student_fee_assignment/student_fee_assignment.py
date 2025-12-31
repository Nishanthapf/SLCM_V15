# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class StudentFeeAssignment(Document):
	def validate(self):
		self.calculate_amounts()
		self.update_status()

	def on_submit(self):
		self.create_fee_invoice()

	def calculate_amounts(self):
		total = 0
		for component in self.fee_components:
			# Calculate tax if applicable
			if component.is_taxable and component.tax_rate:
				component.tax_amount = (component.amount * component.tax_rate) / 100
			else:
				component.tax_amount = 0

			component.total_amount = component.amount + (component.tax_amount or 0)
			total += component.total_amount

		self.total_amount = total
		self.outstanding_amount = self.total_amount - (self.paid_amount or 0)

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

	def create_fee_invoice(self):
		"""Create Fee Invoice when fee assignment is submitted"""
		if not frappe.db.exists("Fee Invoice", {"fee_assignment": self.name}):
			invoice = frappe.get_doc(
				{
					"doctype": "Fee Invoice",
					"student": self.student,
					"fee_assignment": self.name,
					"program": self.program,
					"academic_year": self.academic_year,
					"academic_term": self.academic_term,
					"due_date": self.due_date,
					"total_amount": self.total_amount,
					"outstanding_amount": self.total_amount,
				}
			)

			# Copy fee components
			for comp in self.fee_components:
				invoice.append(
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

			invoice.insert()
			frappe.msgprint(_("Fee Invoice {0} created").format(invoice.name))
