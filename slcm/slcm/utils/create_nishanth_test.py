import frappe

from slcm.slcm.utils.student_email import handle_registration_completion


def create_nishanth_record():
	"""
	Creates a test record for Nishanth and triggers the completion email.
	"""
	print("---------------------------------------------------")
	print("Starting Test Data Creation for Nishanth...")
	print("---------------------------------------------------")

	# 1. Configuration
	target_email = "nishanth.a@azimpremjifoundation.org"
	student_name = "STU-NISHANTH-TEST"

	# 2. Cleanup Existing Data
	if frappe.db.exists("Student Master", {"email": target_email}):
		existing_students = frappe.get_all("Student Master", filters={"email": target_email})
		for s in existing_students:
			frappe.delete_doc("Student Master", s.name, force=True)
			print(f"Deleted existing record: {s.name}")

	if frappe.db.exists("Student Master", student_name):
		frappe.delete_doc("Student Master", student_name, force=True)

	# 3. Get Masters
	dept = frappe.db.get_value("Department", {}, "name") or "Test Dept"
	prog = frappe.db.get_value("Programme", {}, "name") or "Test Programme"
	series = "STU-.YYYY.-"

	# 4. Create Student Document
	# We create it directly as a new document
	student = frappe.get_doc(
		{
			"doctype": "Student Master",
			"naming_series": series,
			"first_name": "Nishanth",
			"last_name": "A",
			"email": target_email,
			"registration_status": "Draft",
			"application_number": "APP-NISH-FINAL",
			"programme": prog,
			"department": dept,
			"phone": "+91-9999999999",
			"dob": "1995-01-01",
			"gender": "Male",
			"aadhaar_number": 999999999999,
			"pan_card": "/files/test_pan.jpg",
			"std_x_marksheet": "/files/test_10th.jpg",
			"passport_size_photo": "/files/test_photo.jpg",
			"aadhaar_card": "/files/test_aadhaar.jpg",
		}
	)

	try:
		student.insert(ignore_permissions=True)
		print(f"✅ Created Student: {student.name}")
	except Exception as e:
		print(f"❌ Failed to create student: {e}")
		return

	# 5. Simulate Completion
	# We update the DB directly to 'Completed' to bypass strict workflow transition validations
	# that might block a direct jump from Draft -> Completed in a test script.
	print("Setting Status to 'Completed'...")
	frappe.db.set_value("Student Master", student.name, "registration_status", "Completed")
	frappe.db.commit()

	# 6. Trigger Email Logic
	# We explicitly verify the trigger mechanism by calling on_update()
	# This simulates exactly what the system does when a Doc is saved.
	print("Triggering Email Notification...")
	try:
		student.reload()
		# triggering the hook which calls 'handle_registration_email' which calls 'handle_registration_completion'
		student.on_update()
		print("✅ Email Logic Executed Successfully.")
	except Exception as e:
		print(f"❌ Error during email trigger: {e}")
		import traceback

		traceback.print_exc()

	# 7. Verification
	print("\n----------------- Verification -----------------")
	# Fetch latest email for this student
	latest_email = frappe.db.get_value(
		"Email Queue",
		{"reference_name": student.name, "reference_doctype": "Student Master"},
		"name",
		order_by="creation desc",
	)

	if latest_email:
		q = frappe.get_doc("Email Queue", latest_email)
		print(f"✅ Email found in Queue: {q.name}")
		print(f"   Sender: {q.sender}")
		print(f"   Status: {q.status}")

		# Recipients is a child table
		recipient_emails = [r.recipient for r in q.recipients]
		print(f"   Recipients: {recipient_emails}")

		if target_email in recipient_emails:
			print("   ✅ Target Recipient Confirmed")
		else:
			print(f"   ⚠️ Target Recipient NOT found. Found: {recipient_emails}")
	else:
		print("❌ No Email Queue entry found. Checking logs...")
		logs = frappe.get_all("Error Log", limit=1, order_by="creation desc")
		if logs:
			l = frappe.get_doc("Error Log", logs[0].name)
			if "Registration Email Failed" in l.method or student.name in l.error:
				print(f"⚠️ Found Error Log: {l.error}")
			else:
				print("No relevant error logs found.")


if __name__ == "__main__":
	create_nishanth_record()
