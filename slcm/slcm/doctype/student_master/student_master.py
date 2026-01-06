# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


class StudentMaster(Document):
	def validate(self):
		self.validate_status_transition()

	def validate_status_transition(self):
		"""Validate status transitions follow the workflow sequence"""
		if self.is_new():
			# New documents start as Draft
			if not self.registration_status:
				self.registration_status = "Draft"
			return

		# Get previous status from database
		previous_status = frappe.db.get_value("Student Master", self.name, "registration_status")

		if previous_status == self.registration_status:
			# No change, skip validation
			return

		# Define valid transitions
		valid_transitions = {
			"Draft": ["Pending REGO"],
			"Pending REGO": ["Pending FINO"],
			"Pending FINO": ["Pending Registration"],
			"Pending Registration": ["Pending Print & Scan"],
			"Pending Print & Scan": ["Pending Residences"],
			"Pending Residences": ["Pending IT"],
			"Pending IT": ["Completed"],
			"Completed": ["Draft"],  # Only System Manager can re-open
		}

		# Check if transition is valid
		if previous_status and previous_status in valid_transitions:
			if self.registration_status not in valid_transitions[previous_status]:
				# Check if user is System Manager (can do backward transitions)
				if "System Manager" not in frappe.get_roles():
					frappe.throw(
						_(
							"Invalid status transition from {0} to {1}. Please follow the workflow sequence."
						).format(previous_status, self.registration_status)
					)

	def on_update(self):
		"""Track status changes"""
		if self.is_new():
			return

		# Get previous status from database
		previous_status = frappe.db.get_value("Student Master", self.name, "registration_status")

		if previous_status != self.registration_status:
			# Status changed, update tracking fields
			self.status_updated_by = frappe.session.user
			self.status_updated_on = now_datetime()

			# Add comment for audit trail
			frappe.get_doc(
				{
					"doctype": "Comment",
					"comment_type": "Workflow",
					"reference_doctype": self.doctype,
					"reference_name": self.name,
					"content": _("Status changed from {0} to {1} by {2}").format(
						previous_status or "Draft",
						self.registration_status,
						frappe.get_fullname(frappe.session.user),
					),
				}
			).insert(ignore_permissions=True)


@frappe.whitelist()
def update_registration_status(student_id, new_status, remarks=None):
	"""
	Update registration status with role-based validation
	This function works independently of workflow system
	Auto-creates workflow state if missing
	"""
	user_roles = frappe.get_roles()
	is_system_manager = "System Manager" in user_roles

	# Auto-create workflow state if it doesn't exist
	if not frappe.db.exists("Workflow State", new_status):
		try:
			state_doc = frappe.get_doc({"doctype": "Workflow State", "workflow_state_name": new_status})
			state_doc.insert(ignore_permissions=True)
			frappe.db.commit()
		except Exception as e:
			frappe.throw(_("Failed to create Workflow State '{0}'. Error: {1}").format(new_status, str(e)))

	# Get student document
	student = frappe.get_doc("Student Master", student_id)
	current_status = student.registration_status or "Draft"

	# Define role mappings for transitioning TO each status
	# This defines who can set the status to this value
	transition_roles = {
		"Pending REGO": ["Student", "Registration User", "System Manager"],
		"Pending FINO": ["REGO Officer", "System Manager"],
		"Pending Registration": ["FINO Officer", "System Manager"],
		"Pending Print & Scan": ["Registration Officer", "System Manager"],
		"Pending Residences": ["Documentation Officer", "System Manager"],
		"Pending IT": ["Residence / Hostel Admin", "System Manager"],
		"Completed": ["IT Admin", "System Manager"],
		"Draft": ["System Manager"],  # Only System Manager can re-open
	}

	# Check if user has permission for this status transition
	required_roles = transition_roles.get(new_status, [])

	# System Manager can do anything
	if not is_system_manager:
		# Check if user has required role
		if not any(role in user_roles for role in required_roles):
			frappe.throw(
				_("You do not have permission to set status to {0}. Required roles: {1}").format(
					new_status, ", ".join(required_roles)
				)
			)

	# Validate transition sequence
	valid_transitions = {
		"Draft": ["Pending REGO"],
		"Pending REGO": ["Pending FINO"],
		"Pending FINO": ["Pending Registration"],
		"Pending Registration": ["Pending Print & Scan"],
		"Pending Print & Scan": ["Pending Residences"],
		"Pending Residences": ["Pending IT"],
		"Pending IT": ["Completed"],
		"Completed": ["Draft"],
	}

	if not is_system_manager:
		if current_status in valid_transitions:
			if new_status not in valid_transitions[current_status]:
				frappe.throw(
					_(
						"Invalid status transition from {0} to {1}. Please follow the workflow sequence."
					).format(current_status, new_status)
				)

	# Update status
	student.registration_status = new_status
	student.status_updated_by = frappe.session.user
	student.status_updated_on = now_datetime()

	if remarks:
		student.status_remarks = remarks

	try:
		student.save(ignore_permissions=True)
		frappe.db.commit()
	except Exception as e:
		frappe.db.rollback()
		frappe.throw(_("Error updating status: {0}").format(str(e)))

	return {"status": "success", "message": _("Status updated to {0}").format(new_status)}


@frappe.whitelist()
def get_available_status_actions(student_id):
	"""
	Get available status actions based on current status and user roles
	"""
	student = frappe.get_doc("Student Master", student_id)
	current_status = student.registration_status or "Draft"
	user_roles = frappe.get_roles()

	# Define workflow transitions
	workflow_transitions = {
		"Draft": {
			"action": "Submit for REGO",
			"next_state": "Pending REGO",
			"roles": ["Student", "Registration User", "System Manager"],
		},
		"Pending REGO": {
			"action": "Approve Documents",
			"next_state": "Pending FINO",
			"roles": ["REGO Officer", "System Manager"],
		},
		"Pending FINO": {
			"action": "Approve Finances",
			"next_state": "Pending Registration",
			"roles": ["FINO Officer", "System Manager"],
		},
		"Pending Registration": {
			"action": "Complete Registration",
			"next_state": "Pending Print & Scan",
			"roles": ["Registration Officer", "System Manager"],
		},
		"Pending Print & Scan": {
			"action": "Upload Documents",
			"next_state": "Pending Residences",
			"roles": ["Documentation Officer", "System Manager"],
		},
		"Pending Residences": {
			"action": "Allocate Room",
			"next_state": "Pending IT",
			"roles": ["Residence / Hostel Admin", "System Manager"],
		},
		"Pending IT": {
			"action": "Allocate Assets",
			"next_state": "Completed",
			"roles": ["IT Admin", "System Manager"],
		},
		"Completed": {"action": "Re-Open", "next_state": "Draft", "roles": ["System Manager"]},
	}

	available_actions = []
	is_system_manager = "System Manager" in user_roles

	# System Manager can see all possible statuses
	if is_system_manager:
		all_states = [
			"Draft",
			"Pending REGO",
			"Pending FINO",
			"Pending Registration",
			"Pending Print & Scan",
			"Pending Residences",
			"Pending IT",
			"Completed",
		]
		for state in all_states:
			if state != current_status:
				available_actions.append(
					{"action": f"Set to {state}", "next_state": state, "label": f"Set to {state}"}
				)
	else:
		# Regular users see only valid transitions
		if current_status in workflow_transitions:
			transition = workflow_transitions[current_status]
			# Check if user has required role
			if any(role in user_roles for role in transition["roles"]):
				available_actions.append(
					{
						"action": transition["action"],
						"next_state": transition["next_state"],
						"label": transition["action"],
					}
				)

	return {"current_status": current_status, "available_actions": available_actions}
