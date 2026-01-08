import io
import os
import zipfile

import frappe
from frappe.model.document import Document
from frappe.utils import get_site_path
from frappe.utils.file_manager import save_file


class IDCardGenerationTool(Document):
	@frappe.whitelist()
	def get_students(self):
		filters = {"student_status": "Active"}

		if self.academic_year:
			filters["academic_year"] = self.academic_year
		if self.department:
			filters["department"] = self.department
		if self.program:
			filters["programme"] = self.program
		if self.batch:
			filters["batch_year"] = self.batch

		students = frappe.get_all(
			"Student Master",
			filters=filters,
			fields=["name", "first_name", "last_name"],
		)

		self.set("student_list", [])

		for student in students:
			row = self.append("student_list", {})
			row.student = student.name
			row.student_name = f"{student.first_name} {student.last_name or ''}".strip()

			existing_card = frappe.db.exists(
				"Student ID Card",
				{"student": student.name, "card_status": ["!=", "Cancelled"]},
			)

			if existing_card:
				row.current_id_card = existing_card
				row.status = "Already Exists"
			else:
				row.status = "Pending"

		self.save()

	@frappe.whitelist()
	def generate_cards(self):
		if not self.id_card_template:
			frappe.throw("Please select an ID Card Template")

		generated_count = 0

		for row in self.student_list:
			try:
				if row.current_id_card:
					doc = frappe.get_doc("Student ID Card", row.current_id_card)
				else:
					doc = frappe.new_doc("Student ID Card")
					doc.student = row.student
					doc.issue_date = self.issue_date
					doc.expiry_date = self.expiry_date

				doc.id_card_template = self.id_card_template
				doc.generate_card()

				row.current_id_card = doc.name
				row.status = "Generated"
				generated_count += 1

			except Exception as e:
				row.status = f"Error: {e!s}"
				error_msg = f"ID Card Gen Error for {row.student}: {e!s}"
				frappe.log_error(error_msg[:140], "ID Card Generation Error")

		self.save()
		frappe.msgprint(f"Generated {generated_count} ID Cards.")

	@frappe.whitelist()
	def download_zip(self):
		if not self.student_list:
			frappe.throw("No students selected")

		zip_buffer = io.BytesIO()

		with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
			for row in self.student_list:
				if not row.current_id_card:
					continue

				card_images = frappe.db.get_value(
					"Student ID Card",
					row.current_id_card,
					["front_id_image", "back_id_image"],
					as_dict=True,
				)

				if not card_images:
					continue

				student_id = row.student

				if card_images.front_id_image:
					self._add_to_zip(
						zip_file,
						card_images.front_id_image,
						f"{student_id}_Front.png",
					)

				if card_images.back_id_image:
					self._add_to_zip(
						zip_file,
						card_images.back_id_image,
						f"{student_id}_Back.png",
					)

		zip_filename = f"ID_Cards_{self.name}.zip"
		saved_zip = save_file(
			zip_filename,
			zip_buffer.getvalue(),
			self.doctype,
			self.name,
			is_private=0,
		)

		return saved_zip.file_url

	def _add_to_zip(self, zip_file, file_url, filename):
		file_path = self._get_full_path(file_url)
		if os.path.exists(file_path):
			zip_file.write(file_path, arcname=filename)

	@frappe.whitelist()
	def generate_print_layout(self):
		from PIL import Image

		A4_WIDTH, A4_HEIGHT = 2480, 3508
		CARD_WIDTH_MM, CARD_HEIGHT_MM = 86, 54
		dpmm = 300 / 25.4

		card_w_px = int(CARD_WIDTH_MM * dpmm)
		card_h_px = int(CARD_HEIGHT_MM * dpmm)

		margin_x, margin_y = 100, 100
		gap_x, gap_y = 20, 20

		cols = (A4_WIDTH - 2 * margin_x) // (card_w_px + gap_x)
		rows = (A4_HEIGHT - 2 * margin_y) // (card_h_px + gap_y)
		cards_per_sheet = int(cols * rows)

		image_pairs = []

		for row in self.student_list:
			if not row.current_id_card:
				continue

			card_images = frappe.db.get_value(
				"Student ID Card",
				row.current_id_card,
				["front_id_image", "back_id_image"],
				as_dict=True,
			)

			if card_images:
				image_pairs.append(card_images)

		if not image_pairs:
			frappe.throw("No generated cards to print")

		output_files = []

		for i in range(0, len(image_pairs), cards_per_sheet):
			batch = image_pairs[i : i + cards_per_sheet]
			sheet_no = (i // cards_per_sheet) + 1

			front_sheet = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
			back_sheet = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")

			for idx, pair in enumerate(batch):
				col = idx % cols
				row = idx // cols

				x = margin_x + col * (card_w_px + gap_x)
				y = margin_y + row * (card_h_px + gap_y)

				if pair.front_id_image:
					try:
						img = Image.open(self._get_full_path(pair.front_id_image)).convert("RGBA")
						img = img.resize(
							(card_w_px, card_h_px),
							Image.Resampling.LANCZOS,
						)
						front_sheet.paste(img, (x, y), img)
					except Exception as e:
						frappe.log_error(
							f"Front image paste failed: {e!s}",
							"ID Card Print Layout",
						)

				if pair.back_id_image:
					try:
						img = Image.open(self._get_full_path(pair.back_id_image)).convert("RGBA")
						img = img.resize(
							(card_w_px, card_h_px),
							Image.Resampling.LANCZOS,
						)
						back_sheet.paste(img, (x, y), img)
					except Exception as e:
						frappe.log_error(
							f"Back image paste failed: {e!s}",
							"ID Card Print Layout",
						)

			front_name = f"Sheet_{sheet_no}_Front.png"
			back_name = f"Sheet_{sheet_no}_Back.png"

			self._save_temp_image(front_sheet, front_name)
			self._save_temp_image(back_sheet, back_name)

			output_files.extend([front_name, back_name])

		zip_buffer = io.BytesIO()
		with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
			for fname in output_files:
				fpath = get_site_path("public", "files", fname)
				if os.path.exists(fpath):
					zip_file.write(fpath, fname)

		zip_filename = f"Print_Layout_{self.name}.zip"
		saved_zip = save_file(
			zip_filename,
			zip_buffer.getvalue(),
			self.doctype,
			self.name,
			is_private=0,
		)

		return saved_zip.file_url

	def _get_full_path(self, file_url):
		return frappe.get_site_path("public", file_url.lstrip("/"))

	def _save_temp_image(self, image, filename):
		img_io = io.BytesIO()
		image.save(img_io, format="PNG", dpi=(300, 300))

		path = get_site_path("public", "files", filename)
		with open(path, "wb") as f:
			f.write(img_io.getvalue())

	@frappe.whitelist()
	def get_preview_html(self, template_name, student):
		if not template_name or not student:
			return ""

		template = frappe.get_doc("ID Card Template", template_name)
		student_doc = frappe.get_doc("Student Master", student)

		# Create a dummy ID Card doc for context
		id_card = frappe.new_doc("Student ID Card")
		id_card.student = student

		# Create context (Flattened)
		context = student_doc.as_dict()
		context.update(template.as_dict())
		context.update(
			{
				"doc": id_card,
				"student": student_doc,
				"template": template,
				"college_name": template.institute_name,
				"logo_url": template.institute_logo,
				"qr_code_url": None,
			}
		)

		html = "<div class='row'>"
		if template.front_html:
			html += "<div class='col-md-6'><h5 class='text-muted'>Front View</h5>"
			html += f"<div style='border: 1px solid #ddd; padding: 10px; background: white;'>{frappe.render_template(template.front_html, context)}</div>"
			html += "</div>"

		if template.back_html:
			html += "<div class='col-md-6'><h5 class='text-muted'>Back View</h5>"
			html += f"<div style='border: 1px solid #ddd; padding: 10px; background: white;'>{frappe.render_template(template.back_html, context)}</div>"
			html += "</div>"

		html += "</div>"
		return html
