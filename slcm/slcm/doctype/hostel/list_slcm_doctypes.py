import frappe


def list_doctypes():
	doctypes = frappe.get_all("DocType", filters={"module": "SLCM"}, fields=["name"])
	for d in doctypes:
		print(d.name)


if __name__ == "__main__":
	list_doctypes()
