import json
import os

import frappe


def run_fix():
	file_path = (
		"/home/apfd/Education_V15/apps/slcm/slcm/slcm/doctype/student_master/student_master_workflow.json"
	)

	if not os.path.exists(file_path):
		print(f"File not found: {file_path}")
		return

	with open(file_path) as f:
		data = json.load(f)

	docname = data.get("workflow_name")
	if not docname:
		print("No workflow_name found in JSON")
		return

	print(f"Force Updating Workflow: {docname}...")

	# Ensure Workflow Action Masters exist
	# Add ALL actions used in JSON
	all_actions = set()
	for t in data.get("transitions", []):
		if t.get("action"):
			all_actions.add(t.get("action"))

	print(f"Required Actions: {all_actions}")

	for action_name in all_actions:
		if not frappe.db.exists("Workflow Action Master", action_name):
			try:
				# Autoname is field:workflow_action_name, so name will be action_name
				action = frappe.get_doc(
					{"doctype": "Workflow Action Master", "workflow_action_name": action_name}
				)
				action.insert()
				print(f"Created Workflow Action Master: {action.name}")
			except Exception as e:
				print(f"Error creating action {action_name}: {e}")

	frappe.db.commit()

	try:
		if frappe.db.exists("Workflow", docname):
			doc = frappe.get_doc("Workflow", docname)

			# Clear existing child tables
			doc.set("states", [])
			doc.set("transitions", [])

			# Save to clear
			doc.save()

			# Add new rows
			for state in data.get("states", []):
				doc.append("states", state)

			for transition in data.get("transitions", []):
				doc.append("transitions", transition)

			# Update other fields
			doc.is_active = data.get("is_active", 1)
			doc.override_status = data.get("override_status", 1)
			doc.workflow_state_field = data.get("workflow_state_field")

			doc.save()
			print(f"Successfully force updated Workflow: {docname}")
		else:
			print("Workflow not found to update.")

		frappe.db.commit()
	except Exception as e:
		print(f"Error updating workflow: {e}")
		frappe.db.rollback()
