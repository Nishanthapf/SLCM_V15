import frappe
from frappe.model.workflow import apply_workflow


def setup_student_enrollment_workflow():
	workflow_name = "Student Enrollment Workflow"
	doctype = "Student Enrollment"

	if frappe.db.exists("Workflow", workflow_name):
		frappe.msgprint(f"Workflow {workflow_name} already exists.")
		return

	# 0. Ensure Custom Field exists
	if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": "workflow_state"}):
		cf = frappe.new_doc("Custom Field")
		cf.dt = doctype
		cf.fieldname = "workflow_state"
		cf.label = "Workflow State"
		cf.fieldtype = "Link"
		cf.options = "Workflow State"
		cf.hidden = 1
		cf.insert(ignore_permissions=True)

	# 1. Create Workflow States
	states = [
		{"state": "Draft", "doc_status": 0, "allow_edit": "System Manager", "update_field": "workflow_state"},
		{
			"state": "Pending Approval",
			"doc_status": 0,
			"allow_edit": "System Manager",
			"update_field": "workflow_state",
		},
		{
			"state": "Approved",
			"doc_status": 1,
			"allow_edit": "System Manager",
			"update_field": "workflow_state",
		},
		{
			"state": "Rejected",
			"doc_status": 2,
			"allow_edit": "System Manager",
			"update_field": "workflow_state",
		},
	]

	for s in states:
		if not frappe.db.exists("Workflow State", s["state"]):
			doc = frappe.new_doc("Workflow State")
			doc.workflow_state_name = s["state"]
			doc.insert(ignore_permissions=True)

	# 2. Create Workflow
	wf = frappe.new_doc("Workflow")
	wf.workflow_name = workflow_name
	wf.document_type = doctype
	wf.workflow_state_field = "workflow_state"
	wf.is_active = 1

	# Add States
	for s in states:
		wf.append("states", s)

	# Add Transitions
	transitions = [
		{"state": "Draft", "action": "Submit", "next_state": "Pending Approval", "allowed": "System Manager"},
		{
			"state": "Pending Approval",
			"action": "Approve",
			"next_state": "Approved",
			"allowed": "System Manager",
		},
		{
			"state": "Pending Approval",
			"action": "Reject",
			"next_state": "Rejected",
			"allowed": "System Manager",
		},
		{"state": "Rejected", "action": "Review", "next_state": "Draft", "allowed": "System Manager"},
	]

	for t in transitions:
		wf.append("transitions", t)

	wf.insert(ignore_permissions=True)
	frappe.msgprint(f"Workflow {workflow_name} created successfully.")


def run():
	setup_student_enrollment_workflow()
