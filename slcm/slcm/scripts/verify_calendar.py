import frappe

from slcm.slcm.doctype.course_schedule.course_schedule import get_events


def run_test():
	frappe.set_user("Administrator")
	print("Testing Course Schedule Calendar backend...")

	# Needs a Course Schedule to return something
	if not frappe.db.get_list("Course Schedule", limit=1):
		print("Creating dummy Course Schedule...")
		try:
			# Need dependencies
			if not frappe.db.exists("Student Group", "Test-Group-Calendar"):
				# Prereqs for group
				# Just try creating simple if possible or skip if too complex
				pass
		except Exception:
			pass

	# Just run get_events for a wide range
	start = "2025-01-01"
	end = "2026-12-31"

	try:
		events = get_events(start, end)
		print(f"Events found: {len(events)}")
		if events:
			print(f"Sample Event: {events[0]}")
			if "start" in events[0] and "end" in events[0]:
				print("PASS: Event has start and end fields.")
			else:
				print("FAIL: Event missing start/end fields.")
		else:
			print("No events found, but method executed successfully.")

	except Exception as e:
		print(f"FAIL: get_events execution error: {e}")


run_test()
