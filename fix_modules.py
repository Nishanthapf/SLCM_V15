import os

base_path = "/home/appi/Education_V15/apps/slcm/slcm/slcm/doctype"

doctypes = [
	"hostel_block",
	"hostel_floor",
	"hostel_bed",
	"hostel_rules",
	"hostel_fee_structure",
	"student_hostel_profile",
	"hostel_attendance",
	"hostel_leave_request",
	"visitor_entry_log",
	"hostel_complaint",
	"room_change_request",
	"mess",
	"mess_menu",
	"mess_subscription",
	"mess_attendance",
	"mess_payment",
	"mess_feedback",
	"hostel_fine",
	"hostel_refund_request",
	"hostel_asset",
	"hostel_maintenance_log",
	"hostel_inventory",
	"hostel_settings",
	"hostel_approval_dashboard",
]

for dt in doctypes:
	folder_path = os.path.join(base_path, dt)

	# 1. Ensure __init__.py exists
	init_path = os.path.join(folder_path, "__init__.py")
	if not os.path.exists(init_path):
		with open(init_path, "w") as f:
			f.write("")
		print(f"Created {init_path}")

	# 2. Ensure [doctype].py exists
	py_path = os.path.join(folder_path, f"{dt}.py")
	class_name = "".join([part.title() for part in dt.split("_")])

	if not os.path.exists(py_path):
		content = f"""# Copyright (c) 2026, Administrator and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document

class {class_name}(Document):
	pass
"""
		with open(py_path, "w") as f:
			f.write(content)
		print(f"Created {py_path}")
