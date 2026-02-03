# Copyright (c) 2026, Nishanth and contributors
# For license information, please see license.txt

"""
Background Processor: RFID Attendance Logs → Student Attendance
This module processes raw RFID swipe logs and converts them into attendance records.

Business Rules:
- First swipe of the day → IN time
- Second swipe → OUT time  
- Single swipe → Mark as PRESENT
- Multiple swipes → Calculate total hours
"""

import frappe
from frappe import _
from frappe.utils import (
	getdate, 
	now_datetime, 
	get_datetime, 
	time_diff_in_hours,
	add_to_date
)
from collections import defaultdict


def process_pending_logs():
	"""
	Main entry point for scheduled job.
	Processes all unprocessed attendance logs.
	"""
	try:
		frappe.logger().info("🔄 Starting attendance log processing...")
		
		# Fetch unprocessed logs
		logs = get_unprocessed_logs()
		
		if not logs:
			frappe.logger().info("✅ No pending logs to process")
			return
		
		# Group logs by student and date
		grouped_logs = group_logs_by_student_and_date(logs)
		
		# Process each group
		processed_count = 0
		for key, student_logs in grouped_logs.items():
			try:
				process_student_logs(student_logs)
				processed_count += len(student_logs)
			except Exception as e:
				frappe.log_error(
					title=f"Error processing logs for {key}",
					message=str(e)
				)
		
		frappe.db.commit()
		frappe.logger().info(f"✅ Processed {processed_count} attendance logs")
		
	except Exception as e:
		frappe.log_error(
			title="Attendance Log Processing Failed",
			message=str(e)
		)


def get_unprocessed_logs():
	"""
	Fetch all unprocessed attendance logs that have a valid student link.
	"""
	return frappe.get_all(
		"Attendance Log",
		filters={
			"processed": 0,
			"student": ["!=", ""]
		},
		fields=[
			"name", 
			"student", 
			"swipe_time", 
			"device_id", 
			"location",
			"rfid_uid"
		],
		order_by="swipe_time asc"
	)


def group_logs_by_student_and_date(logs):
	"""
	Group logs by student and date.
	Returns: {(student, date): [log1, log2, ...]}
	"""
	grouped = defaultdict(list)
	
	for log in logs:
		student = log.get("student")
		date = getdate(log.get("swipe_time"))
		key = (student, date)
		grouped[key].append(log)
	
	return grouped


def process_student_logs(logs):
	"""
	Process logs for a single student on a single date.
	Creates or updates Student Attendance record.
	
	Args:
		logs: List of attendance logs for same student and date
	"""
	if not logs:
		return
	
	first_log = logs[0]
	student = first_log.get("student")
	date = getdate(first_log.get("swipe_time"))
	
	# Sort logs by time
	logs = sorted(logs, key=lambda x: x.get("swipe_time"))
	
	# Extract swipe times
	swipe_times = [get_datetime(log.get("swipe_time")) for log in logs]
	
	# Determine IN and OUT times
	in_time = swipe_times[0]
	out_time = swipe_times[-1] if len(swipe_times) > 1 else None
	
	# Calculate total hours
	total_hours = 0
	if out_time:
		total_hours = time_diff_in_hours(out_time, in_time)
	
	# Determine attendance status
	status = "Present"
	if total_hours > 0 and total_hours < 4:
		status = "Half Day"
	elif total_hours == 0:
		status = "Present"  # Single swipe
	
	# Check if attendance record already exists
	existing_attendance = frappe.db.exists(
		"Student Attendance",
		{
			"student": student,
			"attendance_date": date,
			"date": date
		}
	)
	
	if existing_attendance:
		# Update existing record
		attendance_doc = frappe.get_doc("Student Attendance", existing_attendance)
		attendance_doc.in_time = in_time
		attendance_doc.out_time = out_time
		attendance_doc.total_hours = total_hours
		attendance_doc.status = status
		attendance_doc.attendance_log = logs[-1].get("name") if logs else None
		attendance_doc.save(ignore_permissions=True)
		
		frappe.logger().info(f"📝 Updated attendance for {student} on {date}")
	else:
		# Create new attendance record
		attendance_doc = frappe.get_doc({
			"doctype": "Student Attendance",
			"student": student,
			"attendance_date": date,
			"date": date,
			"based_on": "Student Group",
			"status": status,
			"in_time": in_time,
			"out_time": out_time,
			"total_hours": total_hours,
			"source": "RFID",
			"attendance_log": logs[-1].get("name") if logs else None
		})
		attendance_doc.insert(ignore_permissions=True)
		
		frappe.logger().info(f"✅ Created attendance for {student} on {date}")
	
	# Mark all logs as processed and link to attendance record
	for log in logs:
		frappe.db.set_value(
			"Attendance Log",
			log.get("name"),
			{
				"processed": 1,
				"student_attendance": attendance_doc.name
			}
		)


@frappe.whitelist()
def process_logs_manually():
	"""
	Manual trigger for processing logs (for testing/admin use).
	Can be called from UI or console.
	"""
	process_pending_logs()
	return {
		"status": "success",
		"message": "Attendance logs processed successfully"
	}
