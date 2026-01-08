import io
import os
import zipfile

import frappe
from frappe.model.document import Document
from frappe.utils import get_site_path
from frappe.utils.file_manager import get_file_path, save_file


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
			"Student Master", filters=filters, fields=["name", "first_name", "last_name"]
		)

		self.set("student_list", [])

		for student in students:
			row = self.append("student_list", {})
			row.student = student.name
			row.student_name = f"{student.first_name} {student.last_name or ''}".strip()

			# Check existing card
			existing_card = frappe.db.exists(
				"Student ID Card", {"student": student.name, "card_status": ["!=", "Cancelled"]}
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
				# If we want to skip existing, we can check row.current_id_card
				# But user might want to regenerate.

				doc = None
				if row.current_id_card:
					doc = frappe.get_doc("Student ID Card", row.current_id_card)
				else:
					doc = frappe.new_doc("Student ID Card")
					doc.student = row.student
					doc.issue_date = self.issue_date
					doc.expiry_date = self.expiry_date
					doc.id_card_template = self.id_card_template

				# Check for updates or force regenerate?
				# For now, let's update template and generate
				doc.id_card_template = self.id_card_template
				doc.generate_card()  # This saves the doc

				row.current_id_card = doc.name
				row.status = "Generated"
				generated_count += 1
			except Exception as e:
				row.status = f"Error: {e!s}"
				frappe.log_error(f"ID Card Gen Error for {row.student}: {e!s}")

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

				# Get ID Card Doc (lightweight)
				card_images = frappe.db.get_value(
					"Student ID Card", row.current_id_card, ["front_id_image", "back_id_image"], as_dict=True
				)

				if not card_images:
					continue

				student_id = row.student

				if card_images.front_id_image:
					self.add_to_zip(zip_file, card_images.front_id_image, f"{student_id}_Front.png")

				if card_images.back_id_image:
					self.add_to_zip(zip_file, card_images.back_id_image, f"{student_id}_Back.png")

		# Save ZIP
		zip_filename = f"ID_Cards_{self.name}.zip"
		saved_zip = save_file(zip_filename, zip_buffer.getvalue(), self.doctype, self.name, is_private=0)

		return saved_zip.file_url

	def add_to_zip(self, zip_file, file_url, filename):
		file_path = self.get_full_path(file_url)
		if os.path.exists(file_path):
			zip_file.write(file_path, arcname=filename)

	@frappe.whitelist()
	def generate_print_layout(self):
		# A4 at 300 DPI
		A4_WIDTH, A4_HEIGHT = 2480, 3508
		CARD_WIDTH_MM, CARD_HEIGHT_MM = 86, 54
		# Converting mm to px at 300 DPI (1 mm = 11.8 px approx)
		dpmm = 300 / 25.4
		CARD_W_PX = int(CARD_WIDTH_MM * dpmm)
		CARD_H_PX = int(CARD_HEIGHT_MM * dpmm)

		MARGIN_X = 100
		MARGIN_Y = 100
		GAP_X = 20
		GAP_Y = 20

		# Grid Calculation
		cols = (A4_WIDTH - 2 * MARGIN_X) // (CARD_W_PX + GAP_X)
		rows = (A4_HEIGHT - 2 * MARGIN_Y) // (CARD_H_PX + GAP_Y)

		cards_per_sheet = int(cols * rows)

		# Collect Images
		image_pairs = []
		for row in self.student_list:
			if not row.current_id_card:
				continue

			card_images = frappe.db.get_value(
				"Student ID Card", row.current_id_card, ["front_id_image", "back_id_image"], as_dict=True
			)
			if card_images:
				image_pairs.append(card_images)

		if not image_pairs:
			frappe.throw("No generated cards to print")

		from PIL import Image

		output_files = []

		# Process Batches (Sheets)
		for i in range(0, len(image_pairs), cards_per_sheet):
			batch = image_pairs[i : i + cards_per_sheet]
			sheet_num = (i // cards_per_sheet) + 1

			# Create Front Sheet
			front_sheet = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
			back_sheet = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")

			for idx, pair in enumerate(batch):
				col = idx % cols
				row = idx // cols

				x = MARGIN_X + col * (CARD_W_PX + GAP_X)
				y = MARGIN_Y + row * (CARD_H_PX + GAP_Y)

				# Front
				if pair.front_id_image:
					try:
						f_img = Image.open(self.get_full_path(pair.front_id_image)).convert("RGBA")
						f_img = f_img.resize((CARD_W_PX, CARD_H_PX), Image.Resampling.LANCZOS)
						front_sheet.paste(f_img, (x, y), f_img)
					except Exception:
						pass

				# Back
				if pair.back_id_image:
					try:
						b_img = Image.open(self.get_full_path(pair.back_id_image)).convert("RGBA")
						b_img = b_img.resize((CARD_W_PX, CARD_H_PX), Image.Resampling.LANCZOS)

						# IMPORTANT: Back side alignment usually mirrors front for duplex printing?
						# Standard imposed layout:
						# If duplexing left-to-right (short edge), position is same.
						# If using simple work-and-turn, we keep same position.
						# Let's keep same grid position.
						back_sheet.paste(b_img, (x, y), b_img)
					except Exception:
						pass

			# Save Sheets
			f_name = f"Sheet_{sheet_num}_Front.png"
			b_name = f"Sheet_{sheet_num}_Back.png"

			self.save_temp_image(front_sheet, f_name)
			output_files.append(f_name)

			self.save_temp_image(back_sheet, b_name)
			output_files.append(b_name)

		# Zip Output
		zip_buffer = io.BytesIO()
		with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
			for fname in output_files:
				fpath = get_site_path("public", "files", fname)
				if os.path.exists(fpath):
					zip_file.write(fpath, fname)

		zip_filename = f"Print_Layout_{self.name}.zip"
		saved_zip = save_file(zip_filename, zip_buffer.getvalue(), self.doctype, self.name, is_private=0)

		return saved_zip.file_url

	def get_full_path(self, file_url):
		return frappe.get_site_path("public", file_url.lstrip("/"))

	def save_temp_image(self, image, filename):
		img_io = io.BytesIO()
		image.save(img_io, format="PNG", dpi=(300, 300))
		path = get_site_path("public", "files", filename)
		with open(path, "wb") as f:
			f.write(img_io.getvalue())
