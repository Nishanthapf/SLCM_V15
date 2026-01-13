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
				"ID Card Generation",
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
					doc = frappe.get_doc("ID Card Generation", row.current_id_card)
				else:
					doc = frappe.new_doc("ID Card Generation")
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

		# Create Tool Log
		log = frappe.get_doc(
			{
				"doctype": "ID Card Generation Tool Log",
				"generated_on": frappe.utils.now(),
				"generated_by": frappe.session.user,
				"academic_year": self.academic_year,
				"department": self.department,
				"program": self.program,
				"batch": self.batch,
				"template_used": self.id_card_template,
				"total_students_selected": len(self.student_list or []),
				"total_id_cards_generated": generated_count,
				"generation_mode": "Single" if generated_count == 1 else "Bulk",
				"generation_status": "Success"
				if generated_count == len(self.student_list)
				else ("Failed" if generated_count == 0 else "Partial"),
				"remarks": f"Generated {generated_count}/{len(self.student_list)} cards.",
			}
		)
		log.insert(ignore_permissions=True)

		self.save()
		frappe.msgprint(f"Generated {generated_count} ID Cards. Log Run ID: {log.name}")

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
					"ID Card Generation",
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

		# Constants for A4 at 300 DPI
		A4_WIDTH, A4_HEIGHT = 2480, 3508
		CARD_WIDTH_MM, CARD_HEIGHT_MM = 85.6, 53.98
		dpmm = 300 / 25.4

		# Card size in pixels
		card_w_px = int(CARD_WIDTH_MM * dpmm)
		card_h_px = int(CARD_HEIGHT_MM * dpmm)

		# Layout configuration
		margin_x, margin_y = 100, 100
		gap_x, gap_y = 20, 20

		# We want pairs: FRONT (Left) + BACK (Right)
		# So a "unit" is 2 cards wide + gap
		unit_w = (card_w_px * 2) + gap_x
		unit_h = card_h_px

		cols = (A4_WIDTH - 2 * margin_x) // (unit_w + gap_x)
		rows = (A4_HEIGHT - 2 * margin_y) // (unit_h + gap_y)
		units_per_sheet = int(cols * rows)

		if units_per_sheet < 1:
			frappe.throw("Card size too large for print layout dimensions.")

		image_pairs = []

		for row in self.student_list:
			if not row.current_id_card:
				continue

			# Fetch card details
			card_doc = frappe.get_doc("ID Card Generation", row.current_id_card)

			if card_doc.card_status != "Generated":
				# Skip non-generated cards? Or error?
				# Let's skip to prevent printing drafts
				continue

			if card_doc.front_id_image:
				image_pairs.append(
					{"doc": card_doc, "front": card_doc.front_id_image, "back": card_doc.back_id_image}
				)

		if not image_pairs:
			frappe.throw("No valid generated cards found to print.")

		output_files = []

		# Bulk Print Session ID
		bulk_print_id = frappe.utils.generate_hash(length=10)
		total_cards = len(image_pairs)

		for i in range(0, len(image_pairs), units_per_sheet):
			batch_items = image_pairs[i : i + units_per_sheet]
			sheet_no = (i // units_per_sheet) + 1

			# Create Sheet
			sheet = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")

			for idx, item in enumerate(batch_items):
				col = idx % cols
				row_idx = idx // cols

				# Calculate positions
				# Unit X Position
				u_x = margin_x + col * (unit_w + gap_x)
				u_y = margin_y + row_idx * (unit_h + gap_y)

				# Front Image (Left)
				if item["front"]:
					try:
						f_img = Image.open(self._get_full_path(item["front"])).convert("RGBA")
						f_img = f_img.resize((card_w_px, card_h_px), Image.Resampling.LANCZOS)
						sheet.paste(f_img, (u_x, u_y), f_img)
					except Exception:
						pass  # Log error preferably

				# Back Image (Right)
				if item["back"]:
					try:
						b_img = Image.open(self._get_full_path(item["back"])).convert("RGBA")
						b_img = b_img.resize((card_w_px, card_h_px), Image.Resampling.LANCZOS)
						# Position: x + card_width + gap
						b_x = u_x + card_w_px + gap_x
						sheet.paste(b_img, (b_x, u_y), b_img)
					except Exception:
						pass

				# Prepare Log for this user
				item["doc"].log_print(layout="Bulk", bulk_print_id=bulk_print_id, total_cards=total_cards)

			# Save Sheet
			sheet_name = f"Sheet_{sheet_no}.png"
			self._save_temp_image(sheet, sheet_name)
			output_files.append(sheet_name)

		# Name the ZIP/PDF based on convention
		# <AcademicYear>_<DepartmentCode>_<ProgramCode>_<Batch>_ID_Cards.pdf
		# We use the Generation Tool's filters to name it
		ay = self.academic_year or "AY"
		# Get short codes if possible, else use full names passing regex cleanup
		dept_code = self.department or "All_Dept"
		prog_code = self.program or "All_Prog"
		batch_code = self.batch or "Batch"

		# Sanitize filename components
		def sanitize(s):
			return "".join([c for c in s if c.isalnum() or c in ("-", "_")]).strip()

		final_name = (
			f"{sanitize(ay)}_{sanitize(dept_code)}_{sanitize(prog_code)}_{sanitize(batch_code)}_ID_Cards.zip"
		)

		zip_buffer = io.BytesIO()
		with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
			for fname in output_files:
				fpath = get_site_path("public", "files", fname)
				if os.path.exists(fpath):
					zip_file.write(fpath, fname)

		saved_zip = save_file(
			final_name,
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
		id_card = frappe.new_doc("ID Card Generation")
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
