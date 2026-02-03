# Copyright (c) 2026, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class AttendanceEditLog(Document):
	"""Track all changes to attendance records for audit purposes"""
	
	def before_insert(self):
		"""Set default values before insert"""
		if not self.edited_by:
			self.edited_by = frappe.session.user
		
		if not self.edit_timestamp:
			self.edit_timestamp = frappe.utils.now()


@frappe.whitelist()
def log_attendance_edit(attendance_record, field_changed, old_value, new_value, edit_reason):
	"""Create an audit log entry for attendance edit"""
	log = frappe.get_doc({
		"doctype": "Attendance Edit Log",
		"attendance_record": attendance_record,
		"field_changed": field_changed,
		"old_value": str(old_value) if old_value else "",
		"new_value": str(new_value) if new_value else "",
		"edit_reason": edit_reason,
		"edited_by": frappe.session.user,
		"edit_timestamp": frappe.utils.now(),
		"approval_status": "Pending"
	})
	log.insert(ignore_permissions=True)
	return log.name


@frappe.whitelist()
def get_attendance_edit_history(attendance_record):
	"""Get all edit logs for an attendance record"""
	return frappe.get_all(
		"Attendance Edit Log",
		filters={"attendance_record": attendance_record},
		fields=["*"],
		order_by="edit_timestamp desc"
	)
