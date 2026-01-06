# Copyright (c) 2025, Nishanth and contributors
# Complete setup script for Student Master Registration Workflow

import frappe
from frappe import _


def setup_student_master_workflow():
	"""Complete setup: Create Workflow States, Roles, Permissions, and Workflow"""

	frappe.msgprint("Starting Student Master Registration Workflow setup...")

	try:
		# Step 1: Create Workflow States
		create_workflow_states()

		# Step 2: Create Required Roles
		create_required_roles()

		# Step 3: Setup Role Permissions
		setup_role_permissions()

		# Step 4: Create/Update Workflow
		create_workflow()

		frappe.db.commit()
		frappe.msgprint("Student Master Registration Workflow setup completed successfully.")

	except Exception as e:
		frappe.db.rollback()
		frappe.log_error(f"Error in workflow setup: {e!s}")
		frappe.throw(f"Error setting up workflow: {e!s}")


def create_workflow_states():
	"""Create all required Workflow States"""

	states = [
		"Draft",
		"Pending REGO",
		"Pending FINO",
		"Pending Registration",
		"Pending Print & Scan",
		"Pending Residences",
		"Pending IT",
		"Completed",
	]

	created_states = []

	for state_name in states:
		if not frappe.db.exists("Workflow State", state_name):
			try:
				state_doc = frappe.get_doc(
					{
						"doctype": "Workflow State",
						"workflow_state_name": state_name,
					}
				)
				state_doc.insert(ignore_permissions=True)
				created_states.append(state_name)
			except Exception as e:
				frappe.log_error(f"Error creating state {state_name}: {e!s}")

	if created_states:
		frappe.msgprint(f"Created workflow states: {', '.join(created_states)}")
	else:
		frappe.msgprint("All workflow states already exist.")


def create_required_roles():
	"""Create required roles if they don't exist"""

	required_roles = [
		{"role_name": "Registration User"},
		{"role_name": "REGO Officer"},
		{"role_name": "FINO Officer"},
		{"role_name": "Registration Officer"},
		{"role_name": "Documentation Officer"},
		{"role_name": "Residence / Hostel Admin"},
		{"role_name": "IT Admin"},
	]

	created_roles = []
	updated_roles = []

	for role_info in required_roles:
		role_name = role_info["role_name"]

		if not frappe.db.exists("Role", role_name):
			try:
				role = frappe.get_doc(
					{
						"doctype": "Role",
						"role_name": role_name,
						"desk_access": 1,
					}
				)
				role.insert(ignore_permissions=True)
				created_roles.append(role_name)
			except Exception as e:
				frappe.log_error(f"Error creating role {role_name}: {e!s}")
		else:
			try:
				role = frappe.get_doc("Role", role_name)
				if not role.desk_access:
					role.desk_access = 1
					role.save(ignore_permissions=True)
					updated_roles.append(role_name)
			except Exception as e:
				frappe.log_error(f"Error updating role {role_name}: {e!s}")

	if created_roles:
		frappe.msgprint(f"Created roles: {', '.join(created_roles)}")
	if updated_roles:
		frappe.msgprint(f"Updated roles: {', '.join(updated_roles)}")
	if not created_roles and not updated_roles:
		frappe.msgprint("All required roles already exist.")


def setup_role_permissions():
	"""Setup permissions for all roles on Student Master"""

	role_permissions = {
		"Registration User": {"read": 1, "write": 1, "create": 1, "delete": 0},
		"REGO Officer": {"read": 1, "write": 1},
		"FINO Officer": {"read": 1, "write": 1},
		"Registration Officer": {"read": 1, "write": 1, "create": 1},
		"Documentation Officer": {"read": 1, "write": 1},
		"Residence / Hostel Admin": {"read": 1, "write": 1},
		"IT Admin": {"read": 1, "write": 1},
	}

	doctype = "Student Master"
	doc_type = frappe.get_doc("DocType", doctype)
	updated_permissions = []

	for role_name, perms in role_permissions.items():
		existing_perm = next(
			(perm for perm in doc_type.permissions if perm.role == role_name),
			None,
		)

		if existing_perm:
			existing_perm.update(perms)
		else:
			doc_type.append("permissions", {"role": role_name, **perms})

		updated_permissions.append(role_name)

	doc_type.save(ignore_permissions=True)
	frappe.clear_cache(doctype=doctype)

	if updated_permissions:
		frappe.msgprint(f"Updated permissions for {len(updated_permissions)} roles.")


def create_workflow():
	"""Create or update the Workflow"""

	workflow_name = "Student Registration Workflow"
	doctype = "Student Master"

	states_data = [
		{"state": "Draft", "doc_status": 0, "allow_edit": "System Manager"},
		{"state": "Pending REGO", "doc_status": 0, "allow_edit": "REGO Officer"},
		{"state": "Pending FINO", "doc_status": 0, "allow_edit": "FINO Officer"},
		{"state": "Pending Registration", "doc_status": 0, "allow_edit": "Registration Officer"},
		{"state": "Pending Print & Scan", "doc_status": 0, "allow_edit": "Documentation Officer"},
		{"state": "Pending Residences", "doc_status": 0, "allow_edit": "Residence / Hostel Admin"},
		{"state": "Pending IT", "doc_status": 0, "allow_edit": "IT Admin"},
		{"state": "Completed", "doc_status": 1, "allow_edit": "System Manager"},
	]

	transitions_data = [
		{
			"state": "Draft",
			"action": "Submit for REGO",
			"next_state": "Pending REGO",
			"allowed": "Registration User",
		},
		{
			"state": "Pending REGO",
			"action": "Approve Documents",
			"next_state": "Pending FINO",
			"allowed": "REGO Officer",
		},
		{
			"state": "Pending FINO",
			"action": "Approve Finances",
			"next_state": "Pending Registration",
			"allowed": "FINO Officer",
		},
		{
			"state": "Pending Registration",
			"action": "Complete Registration",
			"next_state": "Pending Print & Scan",
			"allowed": "Registration Officer",
		},
		{
			"state": "Pending Print & Scan",
			"action": "Upload Documents",
			"next_state": "Pending Residences",
			"allowed": "Documentation Officer",
		},
		{
			"state": "Pending Residences",
			"action": "Allocate Room",
			"next_state": "Pending IT",
			"allowed": "Residence / Hostel Admin",
		},
		{
			"state": "Pending IT",
			"action": "Allocate Assets",
			"next_state": "Completed",
			"allowed": "IT Admin",
		},
	]

	if frappe.db.exists("Workflow", workflow_name):
		frappe.msgprint(f"Workflow '{workflow_name}' exists. Updating.")
		workflow = frappe.get_doc("Workflow", workflow_name)
		workflow.states = []
		workflow.transitions = []
	else:
		workflow = frappe.get_doc(
			{
				"doctype": "Workflow",
				"workflow_name": workflow_name,
				"document_type": doctype,
				"is_active": 1,
				"override_status": 1,
				"workflow_state_field": "registration_status",
			}
		)

	for state_data in states_data:
		workflow.append("states", state_data)

	for trans_data in transitions_data:
		workflow.append("transitions", trans_data)

	workflow.is_active = 1
	workflow.save(ignore_permissions=True)

	frappe.msgprint(f"Workflow '{workflow_name}' is active and ready.")


def run():
	"""Run via bench execute"""
	setup_student_master_workflow()


if __name__ == "__main__":
	run()
