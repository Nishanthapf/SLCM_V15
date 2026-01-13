import frappe


def execute():
	frappe.reload_doc("slcm", "doctype", "id_card_generation_tool_log")
	print("Reloaded ID Card Generation Tool Log successfully.")


if __name__ == "__main__":
	pass
