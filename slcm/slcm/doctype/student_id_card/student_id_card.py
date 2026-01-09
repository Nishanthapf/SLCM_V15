import io
import os
import subprocess
import tempfile

import frappe
from frappe.model.document import Document
from frappe.utils import get_url, now
from frappe.utils.file_manager import save_file

try:
	import qrcode
	from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:
	frappe.msgprint("Please install PIL (Pillow) and qrcode libraries.")


def hex_to_rgb(hex_color):
	hex_color = hex_color.lstrip("#")
	return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


class StudentIDCard(Document):
	def validate(self):
		if not self.generate_qr_code_string():
			# Set default QR data if not generated yet
			pass

	def before_save(self):
		if not self.qr_code_data:
			self.qr_code_data = self.generate_qr_code_string()

		self.verification_url = self.generate_verification_url()

		# Status Logging
		old_status = frappe.db.get_value("Student ID Card", self.name, "card_status")
		if self.card_status != old_status:
			self.append("events", {
				"timestamp": now(),
				"card_status": self.card_status,
				"user": frappe.session.user
			})

	def generate_qr_code_string(self):
		# Format: URL or JSON data
		return self.generate_verification_url()

	def generate_verification_url(self):
		base_url = get_url()
		return f"{base_url}/verify-student/{self.student}"

	@frappe.whitelist()
	def generate_card(self):
		if not self.id_card_template:
			frappe.throw("ID Card Template is required.")

		template = frappe.get_doc("ID Card Template", self.id_card_template)
		student = frappe.get_doc("Student Master", self.student)

		# Check for Jinja Template first
		if template.front_html or template.back_html:
			self.generate_card_html(template, student)
		else:
			# Fallback to coordinate system
			# Paths for backgrounds
			front_bg_path = self.get_file_path(template.front_background)
			back_bg_path = self.get_file_path(template.back_background)

			if front_bg_path:
				front_img = Image.open(front_bg_path).convert("RGBA")
				self.process_side(front_img, template, student, "Front")
				self.save_image(front_img, f"{self.name}_Front.png", "front_id_image")

			if back_bg_path:
				back_img = Image.open(back_bg_path).convert("RGBA")
				self.process_side(back_img, template, student, "Back")
				self.save_image(back_img, f"{self.name}_Back.png", "back_id_image")

		self.card_status = "Generated"
		self.save()

	def generate_card_html(self, template, student):
		if template.front_html:
			self.generate_image_from_html(template.front_html, student, template, "front_id_image", "Front")
		if template.back_html:
			self.generate_image_from_html(template.back_html, student, template, "back_id_image", "Back")

	def generate_image_from_html(self, html_content, student, template, fieldname, side):
		# Prepare Context
		# Flatten student and template for easier access
		context = student.as_dict()
		context.update(template.as_dict())
		context.update(
			{
				"doc": self,
				"student": student,
				"template": template,
				"college_name": template.institute_name,
				"logo_url": self.get_file_path(template.institute_logo) if template.institute_logo else None,
				"qr_code_url": self.get_qr_code_url(),  # Helper to get QR image path/url
			}
		)

		# Render Jinja
		rendered_html = frappe.render_template(html_content, context)

		# Create temp file for HTML
		with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
			f.write(rendered_html)
			html_path = f.name

		# Output image path
		output_filename = f"{self.name}_{side}.png"
		output_path = os.path.join(tempfile.gettempdir(), output_filename)

		try:
			# Run wkhtmltoimage
			args = [
				"/usr/bin/wkhtmltoimage",
				"--enable-local-file-access",
				"--width",
				"1011",
				"--height",
				"638",
				"--quality",
				"100",
				"--disable-smart-width",
				html_path,
				output_path,
			]

			# Capture stderr to debug failures
			result = subprocess.run(args, capture_output=True, text=True)
			if result.returncode != 0:
				frappe.throw(f"wkhtmltoimage failed with code {result.returncode}: {result.stderr}")

			# Read generated image
			with open(output_path, "rb") as f:
				img_content = f.read()

			# Save to File Manager
			saved_file = save_file(output_filename, img_content, self.doctype, self.name, is_private=0)
			self.db_set(fieldname, saved_file.file_url)

		except Exception as e:
			frappe.throw(f"Error generating ID Card from HTML: {e}")
		finally:
			# Cleanup
			if os.path.exists(html_path):
				os.remove(html_path)
			if os.path.exists(output_path):
				os.remove(output_path)

	def process_side(self, image, template, student, side):
		draw = ImageDraw.Draw(image)
		fields = [f for f in template.fields if f.side == side]

		for field in fields:
			self.draw_field(draw, image, field, student)

		# Draw Static Elements (Logo, etc) if configured in fields or template
		# TODO: Handle Institute Logo if it's dynamic placement

	def draw_field(self, draw, image, field, student):
		content = self.get_field_value(field.student_fieldname, student)
		if not content:
			return

		x, y = field.position_x, field.position_y
		font_size = field.font_size or 30
		font_color = hex_to_rgb(field.font_color or "#000000")

		# Font Loading
		# Try to load custom font, fallback to default
		try:
			# Need a font path. Using default for now or look for assets
			# In a real scenario, use frappe.get_site_path for custom fonts
			font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
			if field.font_files:
				font_path = self.get_file_path(field.font_files)

			font = ImageFont.truetype(font_path, font_size)
		except Exception:
			font = ImageFont.load_default()

		if field.student_fieldname == "photo":
			# Handle Photo
			self.paste_photo(
				image, content, x, y, field.width, field.width
			)  # Assumption: Square photo or fixed width
		elif field.student_fieldname == "qrcode":
			# Handle QR Code
			self.paste_qr(image, self.qr_code_data, x, y, field.width)
		else:
			# Text Drawing
			if field.alignment == "Center":
				# Calculate text width to center
				text_width = draw.textlength(str(content), font=font)
				x = x - (text_width / 2)
			elif field.alignment == "Right":
				text_width = draw.textlength(str(content), font=font)
				x = x - text_width

			draw.text((x, y), str(content), font=font, fill=font_color)

	def get_field_value(self, fieldname, student):
		if fieldname == "qrcode":
			return "qrcode"  # Marker

		if fieldname == "photo":
			# Try passport_size_photo first, then photo
			if hasattr(student, "passport_size_photo"):
				return student.passport_size_photo
			return None  # Or default placeholder

		if hasattr(student, fieldname):
			val = getattr(student, fieldname)
			return val

		# Static Text check? If fieldname is not in student, treat as static?
		# For now, strict mapping. User can use Virtual Fields in Student if needed.
		return None

	def paste_photo(self, base_image, photo_path, x, y, w, h):
		if not photo_path:
			return
		try:
			full_path = self.get_file_path(photo_path)
			photo = Image.open(full_path).convert("RGBA")

			# Resize
			if w and h:
				photo = photo.resize((w, h), Image.Resampling.LANCZOS)
			elif w:
				ratio = w / photo.width
				h = int(photo.height * ratio)
				photo = photo.resize((w, h), Image.Resampling.LANCZOS)

			base_image.paste(photo, (x, y), photo)
		except Exception as e:
			print(f"Error pasting photo: {e}")

	def paste_qr(self, base_image, data, x, y, size):
		qr = qrcode.QRCode(
			version=1,
			error_correction=qrcode.constants.ERROR_CORRECT_H,
			box_size=10,
			border=1,
		)
		qr.add_data(data)
		qr.make(fit=True)
		img_qr = qr.make_image(fill_color="black", back_color="white").convert("RGBA")

		if size:
			img_qr = img_qr.resize((size, size), Image.Resampling.LANCZOS)

		base_image.paste(img_qr, (x, y), img_qr)

	def get_file_path(self, file_url):
		if not file_url:
			return None
		return frappe.get_site_path("public", file_url.lstrip("/"))

	def save_image(self, image, filename, fieldname):
		# Save to buffer
		img_io = io.BytesIO()
		image.save(img_io, format="PNG", dpi=(300, 300))
		img_content = img_io.getvalue()

		# Save as frappe file
		saved_file = save_file(filename, img_content, self.doctype, self.name, is_private=0)

		self.db_set(fieldname, saved_file.file_url)

	def get_qr_code_url(self):
		if not self.qr_code_data:
			return None

		# Generate QR
		qr = qrcode.QRCode(
			version=1,
			error_correction=qrcode.constants.ERROR_CORRECT_H,
			box_size=10,
			border=1,
		)
		qr.add_data(self.qr_code_data)
		qr.make(fit=True)
		img_qr = qr.make_image(fill_color="black", back_color="white")

		# Save to temp
		temp_filename = f"qr_{self.name}.png"
		temp_path = os.path.join(tempfile.gettempdir(), temp_filename)
		img_qr.save(temp_path)

		return temp_path
