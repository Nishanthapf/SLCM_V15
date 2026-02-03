import frappe
from frappe.utils import get_datetime, add_to_date

def process_log_entry(log_doc):
	"""Process a raw attendance log entry"""
	if log_doc.processed:
		return
		
	swipe_time = get_datetime(log_doc.swipe_time)
	
	# 1. Anti-Flood / Debounce Check
	# Ignore if same student swiped within last 10 minutes
	recent_logs = frappe.db.count("Attendance Log", {
		"rfid_uid": log_doc.rfid_uid,
		"name": ["!=", log_doc.name],
		"swipe_time": [">", add_to_date(swipe_time, minutes=-10)],
		"swipe_time": ["<", swipe_time]
	})
	
	if recent_logs > 0:
		log_doc.processed = 1
		log_doc.db_update()
		return

	# 2. Identify Student
	student = frappe.db.get_value("Student Master", {"rfid_uid": log_doc.rfid_uid})
	if not student:
		frappe.msgprint(f"Unknown RFID Tag: {log_doc.rfid_uid}")
		# We can leave it unprocessed or mark as 'Unknown'
		return

	log_doc.student = student
	log_doc.db_update()
	
	# 3. Identify Session context
	if not log_doc.device_id:
		return
		
	# Get Device Location (Room)
	device_location = frappe.db.get_value("RFID Device", {"device_id": log_doc.device_id}, "location")
	if not device_location:
		return
		
	# Find matching session
	# Matches: Same Room, Same Date, Time overlapping
	log_date = swipe_time.date()
	log_time_str = swipe_time.strftime('%H:%M:%S')
	
	sessions = frappe.db.sql("""
		SELECT name, course_schedule, course_offering
		FROM `tabAttendance Session`
		WHERE room = %s
		AND session_date = %s
		AND session_start_time <= %s
		AND session_end_time >= %s
		AND session_status != 'Cancelled'
		LIMIT 1
	""", (device_location, log_date, log_time_str, log_time_str), as_dict=True)
	
	if not sessions:
		# No active session found for this room/time
		return
		
	session = sessions[0]
	
	# 4. Mark Attendance
	# Find existing student attendance record for this session
	attendance_name = frappe.db.exists("Student Attendance", {
		"student": student,
		"attendance_session": session.name
	})
	
	if attendance_name:
		doc = frappe.get_doc("Student Attendance", attendance_name)
		if doc.status != "Present":
			doc.status = "Present"
			doc.source = "RFID"
			doc.in_time = swipe_time
			doc.attendance_log = log_doc.name
			doc.save(ignore_permissions=True)
			
			log_doc.student_attendance = doc.name
	else:
		# If record doesn't exist (student not enrolled or session not initialized properly)
		# We could optionally create it if 'Ad-hoc' attendance is allowed
		# For now, we only update existing records to be safe
		pass

	log_doc.processed = 1
	log_doc.db_update()
