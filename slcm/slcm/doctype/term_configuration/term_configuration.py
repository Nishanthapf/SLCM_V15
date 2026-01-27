# Copyright (c) 2026, CU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class TermConfiguration(Document):
    def validate(self):
        self.validate_dates()
        self.validate_sequence()
    
    def validate_dates(self):
        """Validate that end date is after start date"""
        if self.starts and self.ends:
            start_date = getdate(self.starts)
            end_date = getdate(self.ends)
            
            if end_date <= start_date:
                frappe.throw("End date must be after start date")
    
    def validate_sequence(self):
        """Validate sequence number is positive"""
        if self.sequence and self.sequence < 1:
            frappe.throw("Sequence must be a positive number")
    
    def before_save(self):
        """Auto-generate term name if not provided"""
        if not self.term_name and self.academic_year and self.system and self.sequence:
            self.term_name = f"{self.academic_year} - {self.system} {self.sequence}"
