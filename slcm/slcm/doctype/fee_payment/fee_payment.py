# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class FeePayment(Document):
	def validate(self):
		if self.fee_invoice:
			self.validate_payment_amount()

	def on_submit(self):
		self.update_fee_invoice()

	def on_cancel(self):
		self.update_fee_invoice(cancel=True)

	def validate_payment_amount(self):
		"""Validate that payment amount doesn't exceed outstanding amount"""
		invoice = frappe.get_doc("Fee Invoice", self.fee_invoice)

		# Get existing payments for this invoice
		existing_payments = frappe.db.sql(
			"""
			SELECT SUM(amount) as total
			FROM `tabFee Payment`
			WHERE fee_invoice = %s
			AND docstatus = 1
			AND name != %s
		""",
			(self.fee_invoice, self.name),
			as_dict=True,
		)

		paid_amount = (existing_payments[0].total or 0) if existing_payments else 0
		outstanding = invoice.total_amount - paid_amount

		if self.amount > outstanding:
			frappe.throw(
				_("Payment amount ({0}) cannot exceed outstanding amount ({1})").format(
					self.amount, outstanding
				)
			)

	def update_fee_invoice(self, cancel=False):
		"""Update fee invoice with payment"""
		invoice = frappe.get_doc("Fee Invoice", self.fee_invoice)

		# Add or remove payment entry
		if cancel:
			# Remove payment entry
			invoice.payments = [p for p in invoice.payments if p.payment != self.name]
		else:
			# Add payment entry if not exists
			payment_exists = False
			for payment in invoice.payments:
				if payment.payment == self.name:
					payment.amount = self.amount
					payment.payment_date = self.payment_date
					payment.payment_mode = self.payment_mode
					payment_exists = True
					break

			if not payment_exists:
				invoice.append(
					"payments",
					{
						"payment": self.name,
						"amount": self.amount,
						"payment_date": self.payment_date,
						"payment_mode": self.payment_mode,
					},
				)

		invoice.save()
		invoice.reload()
