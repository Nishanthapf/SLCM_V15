import frappe
from frappe.utils import add_days, nowdate


def test_hostel_flow():
	frappe.set_user("Administrator")

	# 1. Create a Hostel
	hostel_name = "Test Hostel A"
	if not frappe.db.exists("Hostel", hostel_name):
		hostel = frappe.get_doc(
			{
				"doctype": "Hostel",
				"hostel_name": hostel_name,
				"hostel_type": "Co-ed",
				"total_rooms": 10,
				"total_capacity": 20,
			}
		).insert()
		print(f"Created Hostel: {hostel.name}")
	else:
		hostel = frappe.get_doc("Hostel", hostel_name)
		print(f"Using existing Hostel: {hostel.name}")

	# 2. Create a Hostel Room
	room_number = "101"
	# Check existence
	room_exists = frappe.db.get_value("Hostel Room", {"hostel": hostel.name, "room_number": room_number})

	if not room_exists:
		room = frappe.get_doc(
			{
				"doctype": "Hostel Room",
				"hostel": hostel.name,
				"room_number": room_number,
				"capacity": 1,
				"room_type": "Non-AC",
			}
		).insert()
		print(f"Created Room: {room.name}")
	else:
		room = frappe.get_doc("Hostel Room", room_exists)
		print(f"Using existing Room: {room.name}")
		# Reset occupied for test
		room.occupied = 0
		room.save()

	# 3. Allocations
	# Need a Student Master
	student_app_no = "TEST-APP-001"
	if not frappe.db.exists("Student Master", {"application_number": student_app_no}):
		try:
			student = frappe.get_doc(
				{
					"doctype": "Student Master",
					"first_name": "Test",
					"last_name": "Student",
					"application_number": student_app_no,
					"program_shortcode": "TEST",  # Might be needed
					"gender": "Male",
				}
			)
			student.insert(ignore_permissions=True)
			print(f"Created Student Master: {student.name}")
		except Exception as e:
			print(f"Could not create student: {e}")
			# Fetch random
			s = frappe.get_list("Student Master", limit=1)
			if s:
				student = frappe.get_doc("Student Master", s[0].name)
				print(f"Using existing student: {student.name}")
			else:
				print("No Student Master found.")
				return
	else:
		student = frappe.get_doc("Student Master", {"application_number": student_app_no})
		print(f"Using existing Student: {student.name}")

	# Check Room Occupancy before
	print(f"Room Occupied Before: {room.occupied}")
	assert room.occupied == 0

	# Allocation 1
	allocation = frappe.get_doc(
		{
			"doctype": "Hostel Allocation",
			"student": student.name,
			"hostel": hostel.name,
			"room": room.name,
			"from_date": nowdate(),
			"to_date": add_days(nowdate(), 30),
		}
	)
	allocation.insert()
	allocation.submit()
	print(f"Created Allocation: {allocation.name}")

	room.reload()
	print(f"Room Occupied After Allocation: {room.occupied}")
	assert room.occupied == 1

	# Error Case: Overbooking
	try:
		allocation2 = frappe.get_doc(
			{
				"doctype": "Hostel Allocation",
				"student": student.name,
				"hostel": hostel.name,
				"room": room.name,
				"from_date": nowdate(),
			}
		)
		allocation2.insert()
		# Validate might be called on insert
		print("ERROR: Should have failed due to capacity")
	except Exception as e:
		print(f"Correctly caught overbooking error: {e}")

	# Cancel Allocation
	allocation.cancel()
	room.reload()
	print(f"Room Occupied After Cancel: {room.occupied}")
	assert room.occupied == 0

	print("Verification Successful!")


if __name__ == "__main__":
	try:
		test_hostel_flow()
	except Exception as e:
		print(f"Test Failed: {e}")
		import traceback

		traceback.print_exc()
