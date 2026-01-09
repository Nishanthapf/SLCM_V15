import frappe


def execute():
	file_part = "7C8B3284_0058333ee.jpg"
	docs = frappe.get_all(
		"Student Master",
		filters={"aadhaar_card": ["like", f"%{file_part}%"]},
		fields=["name", "aadhaar_card", "pan_card", "std_x_marksheet"],
	)

	print(f"Found {len(docs)} records matching {file_part}")
	for d in docs:
		print(f"Record: {d.name}")
		print(f"  Aadhaar: '{d.aadhaar_card}'")
		print(f"  PAN:     '{d.pan_card}'")
		print(f"  Std X:   '{d.std_x_marksheet}'")

	# Check for Client Scripts
	scripts = frappe.get_list("Client Script", filters={"dt": "Student Master"}, fields=["name", "script"])
	print(f"Found {len(scripts)} Client Scripts for Student Master")
	for s in scripts:
		print(f"script: {s.name}")
		print(s.script)

	# Check Property Setters
	props = frappe.get_list(
		"Property Setter",
		filters={"doc_type": "Student Master", "field_name": "aadhaar_card"},
		fields=["property", "value"],
	)
	print(f"Found {len(props)} Property Setters for aadhaar_card")
	for p in props:
		print(f"{p.property}: {p.value}")

	# Check Property Setters for std_x_marksheet
	props_x = frappe.get_list(
		"Property Setter",
		filters={"doc_type": "Student Master", "field_name": "std_x_marksheet"},
		fields=["property", "value"],
	)
	print(f"Found {len(props_x)} Property Setters for std_x_marksheet")
	for p in props_x:
		print(f"{p.property}: {p.value}")
