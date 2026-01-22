import frappe

from slcm.slcm.doctype.curriculum_management.curriculum_management import get_curriculum, save_curriculum


def verify():
	print("Verifying Curriculum Management...")

	# 1. Check Default Settings
	cm = frappe.get_doc("Curriculum Management", "Curriculum Management")
	# Force onload if not triggered automatically by validation? Single doctypes usually run onload on get...
	# But get_doc might not trigger onload.
	# Let's check if rows exist.
	if not cm.enrollment_types:
		print("Enrollment Types empty, triggering onload...")
		cm.onload()
		cm.save()

	print(f"Enrollment Types count: {len(cm.enrollment_types)}")
	core_type = next((x for x in cm.enrollment_types if x.enrollment_type == "Core"), None)
	if core_type and core_type.is_active:
		print("Core enrollment type is active - OK")
	else:
		print("Core enrollment type missing or inactive - FAILED")

	# 2. Test Curriculum Create/Save
	program = "Test Program"
	academic_year = "2024-2025"
	dept = "Test Dept"

	# Create dummy Department, Program, Academic Year if needed or just mock strings if link validation isn't strict in python call with ignore_links
	# But save_curriculum uses frappe.get_doc/new_doc which validates links.
	# We should try to use existing ones or create fake ones.

	if not frappe.db.exists("Department", "Test Dept"):
		frappe.get_doc(
			{"doctype": "Department", "department_name": "Test Dept", "department_id": "TD-01"}
		).insert()

	if not frappe.db.exists("Academic Year", "2024-2025"):
		frappe.get_doc(
			{
				"doctype": "Academic Year",
				"academic_year_name": "2024-2025",
				"year_start_date": "2024-01-01",
				"year_end_date": "2024-12-31",
			}
		).insert()

	if not frappe.db.exists("Program", "Test Program"):
		p = frappe.new_doc("Program")
		p.program_name = "Test Program"
		p.program_shortcode = "TP"
		p.department = "Test Dept"
		p.reqd = 0  # Hack to bypass mandatory? No.
		# program has mandatory fields.
		# Let's try to fetch an existing program or just skip strict validation if possible
		pass

	# Let's just create raw data and mock the dependencies if possible, or use existing.
	# I'll try to find existing first.
	existing_progs = frappe.get_all("Program", limit=1)
	if existing_progs:
		program = existing_progs[0].name
		# Fetch dept from program
		p_doc = frappe.get_doc("Program", program)
		dept = p_doc.department

	existing_year = frappe.get_all("Academic Year", limit=1)
	if existing_year:
		academic_year = existing_year[0].name

	print(f"Testing with Program: {program}, Year: {academic_year}, Dept: {dept}")

	courses_data = [
		{
			"semester": "Semester 1",
			"course_group_type": "Course",
			"course": "TEST-COURSE",  # Needs to be real course link usually
			"enrollment_type": "Core",
			"credits": 4,
		}
	]

	# Create Course Master if not exists
	# Create Course Master if not exists
	if not frappe.db.exists("Course Master", "TEST-COURSE"):
		cm = frappe.new_doc("Course Master")
		cm.course_name = "TEST-COURSE"
		cm.name = "TEST-COURSE"
		cm.insert()

	# Create a dummy course if not exists
	if not frappe.db.exists("Course", "TEST-COURSE"):
		c = frappe.new_doc("Course")
		c.course_name = "TEST-COURSE"  # Link to Course Master
		c.course_code = "TC101"
		c.department = dept
		c.credit_value = 4
		c.insert()

	try:
		doc_name = save_curriculum(program, academic_year, dept, courses_data)
		print(f"Saved Curriculum: {doc_name}")
	except Exception as e:
		print(f"Error saving curriculum: {e}")
		return

	# 3. Test Get
	fetched = get_curriculum(program, academic_year)
	if fetched and len(fetched.get("curriculum_courses")) == 1:
		print("Fetch successfully returned 1 course - OK")
	else:
		print(f"Fetch failed or returned wrong data: {fetched}")


verify()
