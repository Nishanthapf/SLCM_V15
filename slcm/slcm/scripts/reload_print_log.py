import frappe


def execute():
	frappe.reload_doc("slcm", "doctype", "id_card_print_log")
	print("Reloaded ID Card Print Log successfully.")


if __name__ == "__main__":
	pass
