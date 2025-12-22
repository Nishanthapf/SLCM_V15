# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CompanyContact(Document):
	def before_save(self):
		"""
		Ensure only one primary contact exists per company
		"""

		if self.primary_contact:
			frappe.db.sql(
				"""
                UPDATE `tabCompany Contact`
                SET primary_contact = 0
                WHERE company = %s
                  AND name != %s
                """,
				(self.company, self.name),
			)
