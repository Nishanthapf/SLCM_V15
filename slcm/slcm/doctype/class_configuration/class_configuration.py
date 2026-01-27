# Copyright (c) 2026, CU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ClassConfiguration(Document):
    def validate(self):
        self.validate_seat_limit()
        self.auto_generate_class_name()
    
    def validate_seat_limit(self):
        """Validate that number of students doesn't exceed seat limit"""
        if self.seat_limit and self.students:
            student_count = len(self.students)
            if student_count > self.seat_limit:
                frappe.throw(f"Number of students ({student_count}) exceeds seat limit ({self.seat_limit})")
    
    def auto_generate_class_name(self):
        """Auto-generate class name if not provided"""
        if not self.class_name:
            parts = []
            if self.course:
                parts.append(self.course)
            if self.type:
                parts.append(self.type)
            if self.batch:
                parts.append(self.batch)
            if self.section:
                parts.append(self.section)
            
            if parts:
                self.class_name = " - ".join(parts)


@frappe.whitelist()
def get_students_by_filter(programme=None, batch=None, section=None):
    """Get students based on programme, batch, and section filters"""
    filters = {}
    
    if programme:
        filters['programme'] = programme
    if batch:
        filters['batch_year'] = batch
    
    students = frappe.get_all(
        'Student Master',
        filters=filters,
        fields=['name', 'first_name', 'middle_name', 'last_name', 'registration_id', 'email']
    )
    
    return students
