import frappe


def add_dummy_field():
	frappe.set_user("Administrator")
	print("Adding dummy field to Course DocType...")

	doc = frappe.get_doc("DocType", "Course")

	# Check if field already exists
	found = False
	for field in doc.fields:
		if field.fieldname == "dummy_dynamic_col":
			found = True
			print("Field 'dummy_dynamic_col' already exists.")
			# Ensure in_list_view is set
			if not field.in_list_view:
				field.in_list_view = 1
				doc.save()
				print("Updated in_list_view for existing field.")
			break

	if not found:
		# Add new field
		doc.append(
			"fields",
			{
				"fieldname": "dummy_dynamic_col",
				"fieldtype": "Data",
				"label": "Dummy Dynamic Col",
				"in_list_view": 1,
				"insert_after": "status",
			},
		)
		doc.save()
		print("Created new field 'dummy_dynamic_col'.")

	frappe.db.commit()


add_dummy_field()
