import frappe
from frappe import _
from frappe.utils import now_datetime, getdate, get_datetime, time_diff_in_hours


@frappe.whitelist(methods=["POST"])
def create_attendance_log():
	"""
	Secure API to receive RFID attendance data and store it in Attendance Log
	Authentication: API Key (Device-based)
	REAL-TIME PROCESSING: Attendance is created immediately after log creation
	"""

	# --------------------------------------------------
	# 1. Read incoming POST data
	# --------------------------------------------------
	data = frappe.local.form_dict or {}

	# --------------------------------------------------
	# 2. Validate required fields
	# --------------------------------------------------
	required_fields = ["rfid_uid"]
	for field in required_fields:
		if not data.get(field):
			frappe.throw(
				_(f"Missing required field: {field}"),
				frappe.ValidationError
			)

	rfid_uid = data.get("rfid_uid").strip()

	# --------------------------------------------------
	# 3. Map RFID UID to Student
	# --------------------------------------------------
	student = frappe.db.get_value(
		"Student Master",
		{"rfid_uid": rfid_uid},
		["name", "first_name", "last_name", "department", "programme"],
		as_dict=True
	)

	if not student:
		# Log the attempt even if student is not found
		frappe.log_error(
			title=f"Unregistered RFID UID: {rfid_uid}",
			message=f"RFID UID {rfid_uid} attempted to swipe but is not registered to any student."
		)
		frappe.throw(
			_(f"RFID UID {rfid_uid} is not registered. Please contact administration."),
			frappe.ValidationError
		)

	# --------------------------------------------------
	# 4. Device Validation (if device_id provided)
	# --------------------------------------------------
	device_id = data.get("device_id")
	
	if device_id:
		device = frappe.db.get_value(
			"RFID Device",
			device_id,
			["name", "is_active", "location"],
			as_dict=True
		)
		
		if not device:
			frappe.log_error(
				title=f"Unauthorized Device: {device_id}",
				message=f"Device {device_id} attempted to submit attendance but is not registered."
			)
			frappe.throw(
				_(f"Device {device_id} is not authorized. Please contact administration."),
				frappe.PermissionError
			)
		
		if not device.get("is_active"):
			frappe.throw(
				_(f"Device {device_id} is inactive. Please contact administration."),
				frappe.PermissionError
			)
		
		# Update last_seen timestamp for the device
		frappe.db.set_value("RFID Device", device_id, "last_seen", now_datetime())
		
		# Use device location if not provided in request
		if not data.get("location") and device.get("location"):
			location = device.get("location")
		else:
			location = data.get("location")
	else:
		location = data.get("location")

	# --------------------------------------------------
	# 5. Optional fields with defaults
	# --------------------------------------------------
	swipe_time = data.get("swipe_time") or now_datetime()
	source = data.get("source") or "RFID"

	# --------------------------------------------------
	# 6. Duplicate protection (Anti-Flood)
	#    Prevent same UID flooding within 10 seconds
	# --------------------------------------------------
	recent_log = frappe.db.exists(
		"Attendance Log",
		{
			"rfid_uid": rfid_uid,
			"swipe_time": [">", frappe.utils.add_to_date(now_datetime(), seconds=-10)]
		}
	)

	if recent_log:
		return {
			"status": "ignored",
			"message": "Duplicate swipe ignored (within 10 seconds)",
			"student": student.get("name"),
			"student_name": f"{student.get('first_name')} {student.get('last_name') or ''}".strip()
		}

	# --------------------------------------------------
	# 7. Create Attendance Log with Student Link
	# --------------------------------------------------
	# --------------------------------------------------
	# 7. Create Attendance Log with Student Link
	# --------------------------------------------------
	attendance_log = frappe.get_doc({
		"doctype": "Attendance Log",
		"rfid_uid": rfid_uid,
		"student": student.get("name"),
		"swipe_time": swipe_time,
		"device_id": device_id,
		"location": location,
		"source": source,
		"processed": 0
	})

	attendance_log.insert(ignore_permissions=True)
	frappe.db.commit()

	# Reload to get updates from after_insert hook (rfid_processor)
	attendance_log.reload()

	# --------------------------------------------------
	# 8. Construct Response
	# --------------------------------------------------
	attendance_info = {
		"attendance_created": False,
		"attendance_id": None,
		"status": None
	}

	if attendance_log.student_attendance:
		att = frappe.get_doc("Student Attendance", attendance_log.student_attendance)
		attendance_info.update({
			"attendance_created": True,
			"attendance_id": att.name,
			"status": att.status,
			"in_time": str(att.in_time) if att.in_time else None
		})
	elif attendance_log.processed and not attendance_log.student_attendance:
		attendance_info["message"] = "Log processed but no matching session found or ignored."

	# --------------------------------------------------
	# 9. Success response with student and attendance information
	# --------------------------------------------------
	return {
		"status": "success",
		"message": "Attendance log received",
		"attendance_log": attendance_log.name,
		"student": student.get("name"),
		"student_name": f"{student.get('first_name')} {student.get('last_name') or ''}".strip(),
		"department": student.get("department"),
		"programme": student.get("programme"),
		"swipe_time": str(swipe_time),
		"attendance": attendance_info
	}
