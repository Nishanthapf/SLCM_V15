# Copyright (c) 2025, Nishanth and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_fullname, now_datetime


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

	def before_save(self):
		"""Track status changes"""
		if self.is_new():
			return

		# Get previous status from database
		previous_status = frappe.db.get_value("Student Master", self.name, "registration_status")

		if previous_status != self.registration_status:
			# Status changed, update tracking fields
			self.status_updated_by = frappe.session.user
			self.status_updated_on = now_datetime()

			# Update Status History Child Table
			self.append(
				"workflow_history",
				{
					"workflow_state": self.registration_status,
					"previous_state": previous_status,
					"updated_by": frappe.session.user,
					"updated_on": now_datetime(),
					"remarks": self.status_remarks,
				},
			)

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
						get_fullname(frappe.session.user),
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
	is_system_manager = "System Manager" in user_roles or frappe.session.user == "Administrator"
	is_admin = is_system_manager

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

	# System Manager and Administrator can do anything
	if not is_admin:
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

	# Admin and System Manager can change to any status
	if not is_admin:
		if current_status in valid_transitions:
			if new_status not in valid_transitions[current_status]:
				frappe.throw(
					_(
						"Invalid status transition from {0} to {1}. Please follow the workflow sequence."
					).format(current_status, new_status)
				)

	# Validate specific requirements for transition
	validate_transition_requirements(student, new_status)

	# Update status
	student.registration_status = new_status
	student.status_updated_by = frappe.session.user
	student.status_updated_on = now_datetime()

	# Remarks is mandatory
	if not remarks:
		frappe.throw(_("Remarks is mandatory for status update"))

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
	is_admin = "System Manager" in user_roles or frappe.session.user == "Administrator"

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
			"action": "Submit for Print & Scan",
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

	# Admin and System Manager can see all possible statuses
	if is_admin:
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


def validate_transition_requirements(student, new_status):
	"""
	Validate strict requirements for moving to the next status
	"""
	if new_status == "Pending FINO":
		# Pending REGO -> Pending FINO
		# Required Docs: Aadhaar, PAN, 10th Marksheet, Photo
		required_docs = [
			"aadhaar_card",
			"pan_card",
			"std_x_marksheet",
			"passport_size_photo",
		]
		missing_docs = [doc for doc in required_docs if not student.get(doc)]
		if missing_docs:
			frappe.throw(
				_("Cannot move to Pending FINO. Missing documents: {0}").format(
					", ".join([frappe.get_meta("Student Master").get_label(d) for d in missing_docs])
				)
			)

	elif new_status == "Pending Registration":
		# Pending FINO -> Pending Registration
		# Fee Status must be Paid or Partially Paid
		if student.fee_payment_status not in ["Paid", "Partially Paid"]:
			frappe.throw(
				_("Cannot move to Pending Registration. Fee Payment Status must be 'Paid' or 'Partially Paid'. Current: {0}").format(
					student.fee_payment_status
				)
			)

	elif new_status == "Pending Print & Scan":
		# Pending Registration -> Pending Print & Scan
		# Mandatory fields check
		required_fields = [
			"first_name",
			"last_name",
			"dob",
			"gender",
			"email",
			"phone",
			"programme",
			"department",
		]
		missing_fields = [field for field in required_fields if not student.get(field)]
		if missing_fields:
			frappe.throw(
				_("Cannot move to Pending Print & Scan. Missing mandatory details: {0}").format(
					", ".join([frappe.get_meta("Student Master").get_label(f) for f in missing_fields])
				)
			)

	elif new_status == "Pending Residences":
		# Pending Print & Scan -> Pending Residences
		# Check ID Card Issued and Aadhaar Verified
		if not student.id_card_issued:
			frappe.throw(_("Cannot move to Pending Residences. ID Card must be issued."))
		
		if not student.aadhaar_verified:
			frappe.throw(_("Cannot move to Pending Residences. Aadhaar must be verified."))

	elif new_status == "Pending IT":
		# Pending Residences -> Pending IT
		# Hostel check: Room must be allocated OR if not hosteller, skip
		if student.is_hosteller:
			if not student.hostel_room:
				frappe.throw(_("Cannot move to Pending IT. Hostel Room must be allocated for hostellers."))
			if not student.keys_handed_over:
				frappe.throw(_("Cannot move to Pending IT. Keys must be handed over."))

	elif new_status == "Completed":
		# Pending IT -> Completed
		# IT Check: Official Email
		if not student.official_email_id:
			frappe.throw(_("Cannot complete. Official Email ID must be set."))

