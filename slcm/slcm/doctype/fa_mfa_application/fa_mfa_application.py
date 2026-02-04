
# Copyright (c) 2026, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import getdate, date_diff

class FAMFAApplication(Document):
	def validate(self):
		self.validate_dates()

	def validate_dates(self):
		if not self.examination_date:
			return

		settings = frappe.get_single("Attendance Settings")
		if not settings.allow_fa_mfa:
			frappe.throw("FA/MFA Applications are currently disabled in Attendance Settings.")

		exam_date = getdate(self.examination_date)
		today = getdate()
		
		# If applying strictly for University Representation (Competitions), check dates
		if self.reason == "University Representation":
			if not self.event_from_date or not self.event_to_date:
				frappe.throw("Event dates are required for University Representation.")
			
			event_from = getdate(self.event_from_date)
			event_to = getdate(self.event_to_date)
			
			# Rule: participation dates fall within three days of the exam
			# Logic: Check if exam_date is within [event_from - 3 days, event_to + 3 days]
			# Or if the event overlaps with Exam Date +/- 3 days window.
			# Simplified Interpretation: The event happened within 3 days (before/after/during) of the exam.
			
			days_diff_from = date_diff(exam_date, event_from) # exam - event_start
			days_diff_to = date_diff(event_to, exam_date)     # event_end - exam
			
			# Check if event is too far in past or future relative to exam
			# Distance between interval [event_from, event_to] and point exam_date should be <= 3
			
			# If exam is BEFORE event:
			if exam_date < event_from:
				gap = date_diff(event_from, exam_date)
			# If exam is AFTER event:
			elif exam_date > event_to:
				gap = date_diff(exam_date, event_to)
			else:
				# During event
				gap = 0
				
			if gap > 3:
				frappe.throw("For University Representation, participation dates must be within 3 days of the examination date.")

			# Application Submit Window Rule
			days_before = settings.fa_application_days_before_exam or 10
			if date_diff(exam_date, today) < days_before:
				# Check if it is a "late" application which is allowed but requires justification
				pass 

		# General Check: Application shouldn't be too old if applying AFTER exam?
		if date_diff(today, exam_date) > (settings.fa_application_days_after_exam or 10):
			if self.reason != "University Representation": 
				frappe.msgprint("Warning: Application is submitted more than 10 days after the examination.")

	def on_submit(self):
		if self.status != "Approved":
			frappe.throw("Only Approved applications can be submitted.")
