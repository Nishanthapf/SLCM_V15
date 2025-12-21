# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class PlacementOffer(Document):
	pass

# I added this code-->> Nishanth


import frappe
from frappe.model.document import Document
from frappe.utils import nowdate


class PlacementOffer(Document):

    def validate(self):
        if self.offer_status in ("Accepted", "Declined") and not self.decision_date:
            self.decision_date = nowdate()