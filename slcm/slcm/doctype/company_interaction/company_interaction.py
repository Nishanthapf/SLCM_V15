# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class CompanyInteraction(Document):
	pass

# I added this code-->> Nishanth

from frappe.model.document import Document
import frappe


class CompanyInteraction(Document):
    def before_insert(self):
        if not self.logged_by:
            self.logged_by = frappe.session.user
