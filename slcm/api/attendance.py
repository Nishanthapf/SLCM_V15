# import frappe
# from frappe import _

# @frappe.whitelist(allow_guest=True)
# def create_attendance_log():
#     """
#     API to receive RFID attendance data and store it in Attendance Log
#     """

#     data = frappe.local.form_dict

#     # 🔹 Required fields validation
#     required_fields = ["rfid_uid", "swipe_time"]

#     for field in required_fields:
#         if not data.get(field):
#             frappe.throw(_(f"Missing required field: {field}"))

#     # 🔹 Create Attendance Log
#     attendance_log = frappe.get_doc({
#         "doctype": "Attendance Log",
#         "rfid_uid": data.get("rfid_uid"),
#         "swipe_time": data.get("swipe_time"),
#         "device_id": data.get("device_id"),
#         "location": data.get("location"),
#         "source": data.get("source") or "RFID",
#         "processed": 0
#     })

#     attendance_log.insert(ignore_permissions=True)
#     frappe.db.commit()

#     return {
#         "status": "success",
#         "message": "Attendance Log created successfully",
#         "attendance_log": attendance_log.name
#     }


import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def create_attendance_log():
	"""
	API to receive RFID attendance data and store it in Attendance Log
	"""

	# 🔹 Get request data
	data = frappe.local.form_dict

	# 🔹 Required fields validation
	required_fields = ["rfid_uid", "swipe_time"]
	for field in required_fields:
		if not data.get(field):
			frappe.throw(_(f"Missing required field: {field}"))

	# 🔹 Create Attendance Log data as array (dict)
	attendance_data = {
		"doctype": "Attendance Log",
		"rfid_uid": data.get("rfid_uid"),
		"swipe_time": data.get("swipe_time"),
		"device_id": data.get("device_id"),
		"location": data.get("location"),
		"source": data.get("source") or "RFID",
		"processed": 0,
	}

	# 🔹 Pass array as parameter
	attendance_log = frappe.get_doc(attendance_data)

	attendance_log.insert(ignore_permissions=True)
	frappe.db.commit()

	return {
		"status": "success",
		"message": "Attendance Log created successfully",
		"attendance_log": attendance_log.name,
	}
