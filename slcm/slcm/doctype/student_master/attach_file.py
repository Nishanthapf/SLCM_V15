import frappe


def set_document_links(doc, method=None):
	base_url = frappe.utils.get_url()

	field_map = {
		"aadhaar_card": "aadhaar_card",
		"pan_card": "pan_card",
		"std_x_marksheet": "std_x_marksheet",
		"transfer_certificate": "transfer_certificate",
		"pwd_certificate": "pwd_certificate",
		"entrance_exam_score_marksheet": "entrance_exam_score_marksheet",
		"passport_size_photo": "passport_size_photo",
		"posh_anti_ragging_declaration": "posh_anti_ragging_declaration",
		"passport": "passport",
		"offer_letter": "offer_letter",
	}

	for attach_field, link_field in field_map.items():
		file_path = doc.get(attach_field)

		if not file_path:
			doc.set(link_field, "")
			continue

		if file_path.startswith("http://") or file_path.startswith("https://"):
			full_url = file_path
		else:
			full_url = base_url + file_path

		doc.set(link_field, full_url)
