# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from slcm.slcm.utils.rfid_processor import process_log_entry

class AttendanceLog(Document):
	def after_insert(self):
		pass
		# self.process_log()
		
	def process_log(self):
		"""Process log entry to mark attendance"""
		try:
			process_log_entry(self)
		except Exception as e:
			frappe.log_error(f"Error processing attendance log {self.name}: {str(e)}")
