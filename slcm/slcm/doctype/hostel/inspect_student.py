import frappe


def inspect():
	try:
		if frappe.db.exists("DocType", "Student"):
			doc = frappe.get_doc("DocType", "Student")
			print(f"Module: {doc.module}")
			print(f"Custom: {doc.custom}")
		else:
			print("Student DocType not found in DB")
	except Exception as e:
		print(f"Error: {e}")


if __name__ == "__main__":
	inspect()
