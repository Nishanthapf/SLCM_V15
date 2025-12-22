# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

# import frappe
# from frappe.model.document import Document


# class PlacementOpportunity(Document):
# 	pass


# I added this code-->> Nishanth

# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PlacementOpportunity(Document):

    def validate(self):
        """
        Validate application date range
        """
        if self.application_start and self.application_end:
            if self.application_end <= self.application_start:
                frappe.throw("Application End must be after Application Start")

# def on_update(self):
#     if self.application_end < frappe.utils.now_datetime():
#         self.status = "Closed"
