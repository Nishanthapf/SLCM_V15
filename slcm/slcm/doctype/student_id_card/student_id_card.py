import io
import json
import os
import subprocess
import tempfile

import frappe
from frappe.model.document import Document
from frappe.utils import get_url, now
from frappe.utils.file_manager import save_file

# Lazy imports for qrcode and PIL - imported when needed to avoid errors during migration
# import qrcode
# from PIL import Image, ImageDraw, ImageFont, ImageOps


def hex_to_rgb(hex_color):
	hex_color = hex_color.lstrip("#")
	return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


class StudentIDCard(Document):
	def validate(self):
		if self.card_status != "Cancelled":
			if self.card_type == "Student" and self.student:
				existing = frappe.db.exists(
					"Student ID Card",
					{"student": self.student, "card_status": ["!=", "Cancelled"], "name": ["!=", self.name]},
				)
				if existing:
					frappe.throw(f"Active ID Card {existing} already exists for Student {self.student}")

			elif self.card_type == "Faculty" and self.faculty:
				existing = frappe.db.exists(
					"Student ID Card",
					{"faculty": self.faculty, "card_status": ["!=", "Cancelled"], "name": ["!=", self.name]},
				)
				if existing:
					frappe.throw(f"Active ID Card {existing} already exists for Faculty {self.faculty}")

			elif self.card_type == "Driver" and self.driver:
				existing = frappe.db.exists(
					"Student ID Card",
					{"driver": self.driver, "card_status": ["!=", "Cancelled"], "name": ["!=", self.name]},
				)
				if existing:
					frappe.throw(f"Active ID Card {existing} already exists for Driver {self.driver}")

		if not self.generate_qr_code_string():
			# Set default QR data if not generated yet
			pass

	def before_insert(self):
		if self.card_type == "Student" and self.student:
			student = frappe.get_doc("Student Master", self.student)
			self.student_name = f"{student.first_name} {student.last_name or ''}".strip()
			self.email = student.email
			self.phone = student.phone
			if not self.photo:
				self.photo = student.passport_size_photo
			self.department = student.department
			self.program = student.programme

		elif self.card_type == "Faculty" and self.faculty:
			faculty = frappe.get_doc("Faculty", self.faculty)
			self.student_name = f"{faculty.first_name} {faculty.last_name or ''}".strip()
			self.email = faculty.email
			self.phone = faculty.phone
			self.department = faculty.department
			self.designation = faculty.designation
			if not self.photo:
				self.photo = getattr(faculty, "photo", None)

		elif self.card_type == "Driver" and self.driver:
			driver = frappe.get_doc("Driver", self.driver)
			self.student_name = driver.driver_name
			self.phone = driver.phone
			if not self.photo:
				self.photo = getattr(driver, "photo", None)

		elif self.card_type == "Visitor":
			self.student_name = self.visitor_name
			self.designation = "Visitor"  # Default for Visitor

		elif self.card_type == "Non-Faculty":
			self.student_name = self.non_faculty_name
			# Designation is manually entered

	def get_person_doc(self):
		if self.card_type == "Student" and self.student:
			return frappe.get_doc("Student Master", self.student)
		elif self.card_type == "Faculty" and self.faculty:
			return frappe.get_doc("Faculty", self.faculty)
		elif self.card_type == "Driver" and self.driver:
			return frappe.get_doc("Driver", self.driver)
		elif self.card_type == "Visitor":
			return frappe._dict(
				{
					"first_name": self.visitor_name,
					"full_name": self.visitor_name,
					"company": self.visitor_company,
					"phone": self.phone,
					"designation": "Visitor",
				}
			)
		elif self.card_type == "Non-Faculty":
			return frappe._dict(
				{
					"first_name": self.non_faculty_name,
					"full_name": self.non_faculty_name,
					"designation": self.designation,
					"phone": self.phone,
					"email": self.email,
					"department": self.department,
					"company": self.visitor_company,  # Stored in generic company field
				}
			)
		return None

	def after_insert(self):
		frappe.enqueue(
			"slcm.slcm.doctype.student_id_card.tasks.generate_id_card_images",
			queue="short",
			docname=self.name,
		)

	def before_save(self):
		self.qr_code_data = self.generate_qr_code_string()
		self.generate_and_save_qr_image()

		self.verification_url = self.generate_verification_url()

		# Status Logging
		old_status = frappe.db.get_value("Student ID Card", self.name, "card_status")
		if self.card_status != old_status:
			self.append(
				"events", {"timestamp": now(), "card_status": self.card_status, "user": frappe.session.user}
			)

	def get_qr_code_url(self):
		return self.qr_code_image or None

	def generate_and_save_qr_image(self):
		if not self.qr_code_data:
			return

		# Lazy import
		import qrcode

		# Generate QR Image
		qr = qrcode.QRCode(
			version=1,
			error_correction=qrcode.constants.ERROR_CORRECT_M,
			box_size=10,
			border=4,
		)
		qr.add_data(self.qr_code_data)
		qr.make(fit=True)

		img = qr.make_image(fill_color="black", back_color="white")

		# Save to BytesIO
		fname = f"{self.name}-QR.png"
		buffer = io.BytesIO()
		img.save(buffer, format="PNG")
		img_content = buffer.getvalue()

		# Save file
		saved_file = save_file(fname, img_content, self.doctype, self.name, is_private=0)
		self.qr_code_image = saved_file.file_url

	def generate_qr_code_string(self):
		"""Generate QR payload string for verification"""
		person = self.get_person_doc()
		if not person:
			return ""

		parts = []
		if self.card_type == "Student":
			parts = [
				person.first_name or "",
				person.academic_year or "",
				person.programme or "",
				person.department or "",
				person.blood_group or "",
				person.email or "",
			]
		elif self.card_type == "Faculty":
			parts = [
				person.faculty_id or "",
				person.first_name or "",
				person.department or "",
				person.designation or "",
				person.email or "",
			]
		elif self.card_type == "Driver":
			parts = [
				person.driver_id or "",
				person.driver_name or "",
				person.license_number or "",
			]
		elif self.card_type == "Visitor":
			parts = [
				"VISITOR",
				self.visitor_name or "",
				self.visitor_company or "",
				self.issue_date or "",
			]
		elif self.card_type == "Non-Faculty":
			parts = [
				"STAFF",
				self.non_faculty_name or "",
				self.designation or "",
				self.department or "",
			]

		return " | ".join(filter(None, [str(p) for p in parts]))

	def generate_verification_url(self):
		base_url = get_url()
		return f"{base_url}/verify-student/{self.student}"

	@frappe.whitelist()
	def generate_card(self):
		if self.is_new():
			self.save()

		if not self.id_card_template:
			frappe.throw("ID Card Template is required.")

		template = frappe.get_doc("ID Card Template", self.id_card_template)
		# student = frappe.get_doc("Student Master", self.student) # OLD
		person = self.get_person_doc()  # NEW

		# Check for different modes
		if template.template_creation_mode == "Drag and Drop":
			self.generate_card_from_canvas(template, person)
		elif template.template_creation_mode == "Jinja Template":
			self.generate_card_html(template, person)
		else:
			# Fallback to field mapping / coordinate system (Field Mapping mode)
			# Paths for backgrounds
			front_bg_path = self.get_file_path(template.front_background)
			back_bg_path = self.get_file_path(template.back_background)

			if front_bg_path:
				# Lazy import
				from PIL import Image

				front_img = Image.open(front_bg_path).convert("RGBA")
				self.process_side(front_img, template, person, "Front")
				self.save_image(front_img, f"{self.name}_Front.png", "front_id_image")

			if back_bg_path:
				# Lazy import
				from PIL import Image

				back_img = Image.open(back_bg_path).convert("RGBA")
				self.process_side(back_img, template, person, "Back")
				self.save_image(back_img, f"{self.name}_Back.png", "back_id_image")

		self.card_status = "Generated"
		self.save()

	def generate_card_from_canvas(self, template, student):
		if not template.canvas_data:
			frappe.throw("No design data found in the selected Drag & Drop Template.")

		try:
			data = json.loads(template.canvas_data)
		except Exception:
			frappe.throw("Invalid Canvas Data in Template.")

		# Orientation dimensions
		if data.get("orientation") == "horizontal":
			width, height = 1011, 638  # High res for print
			# Canvas is 337 x 212 (~ 3x scaling for print)
			scale_factor = 3
		else:
			width, height = 638, 1011
			scale_factor = 3

		for side in ["front", "back"]:
			elements = data.get(side, [])
			bg_color = data.get("bg_color", {}).get(side, "#ffffff")

			# Build HTML for this side
			html_content = f"""
			<html>
			<head>
				<style>
					body {{ margin: 0; padding: 0; background-color: {bg_color}; }}
					.container {{
						position: relative;
						width: {width}px;
						height: {height}px;
						overflow: hidden;
					}}
					.element {{ position: absolute; }}
				</style>
			</head>
			<body>
				<div class="container">
			"""

			for el in elements:
				# Scale coordinates
				x = float(el.get("x", 0)) * scale_factor
				y = float(el.get("y", 0)) * scale_factor
				w = float(el.get("width", 0)) * scale_factor
				h = float(el.get("height", 0)) * scale_factor
				style = el.get("style", {})

				# Styles
				css_style = f"left: {x}px; top: {y}px;"
				if "fontSize" in style:
					# Scale font size? Yes, rough approx
					size_px = float(style["fontSize"].replace("px", "")) * scale_factor
					css_style += f" font-size: {size_px}px;"
				if "fontWeight" in style:
					css_style += f" font-weight: {style['fontWeight']};"
				if "color" in style:
					css_style += f" color: {style['color']};"
				if "opacity" in style:
					css_style += f" opacity: {style['opacity']};"
				if "fontFamily" in style:
					css_style += f" font-family: {style['fontFamily']}, sans-serif;"
				if "backgroundColor" in style:
					css_style += f" background-color: {style['backgroundColor']};"
				if "borderRadius" in style:
					css_style += f" border-radius: {style['borderRadius']};"
				if "clipPath" in style and style["clipPath"] != "none":
					css_style += f" clip-path: {style['clipPath']}; -webkit-clip-path: {style['clipPath']};"

				# Borders
				for border_side in ["Top", "Bottom", "Left", "Right"]:
					style_prop = f"border{border_side}Style"
					width_prop = f"border{border_side}Width"
					color_prop = f"border{border_side}Color"

					if style_prop in style:
						b_style = style[style_prop]
						b_width = style.get(width_prop, "0px")
						b_color = style.get(color_prop, "#000000")

						# Scale Width
						try:
							w_val = float(str(b_width).replace("px", "")) * scale_factor
							w_css = f"{w_val}px"
						except Exception:
							w_css = b_width  # Fallback

						css_side = border_side.lower()
						css_style += f" border-{css_side}-style: {b_style}; border-{css_side}-width: {w_css}; border-{css_side}-color: {b_color};"

				content = el.get("content", "")

				if el.get("type") == "text":
					html_content += (
						f'<div class="element" style="{css_style} white-space: nowrap;">{content}</div>'
					)
				elif el.get("type") == "image":
					# Resolve image content if mapped
					if el.get("mapping"):
						mapping = el.get("mapping")
						if mapping == "photo":
							content = (
								self.get_file_path(self.photo) or "/assets/frappe/images/default-avatar.png"
							)
						elif mapping == "institute_logo":
							content = self.get_file_path(template.institute_logo) or ""
						elif mapping == "authority_signature":
							content = self.get_file_path(template.authority_signature)
							if not content:
								frappe.log_error(
									f"Missing Authority Signature for Template: {template.name}",
									"ID Card Generation Warning",
								)
								content = ""
						elif mapping == "qr_code_image":
							content = self.get_file_path(self.qr_code_image)
							if not content:
								frappe.log_error(
									f"Missing QR Code Image for Card: {self.name}",
									"ID Card Generation Warning",
								)
								content = ""
						# Ensure path is suitable for wkhtmltoimage (absolute local path preferable or base64)
						# get_file_path returns absolute path

					html_content += f'<div class="element" style="{css_style} width: {w}px; height: {h}px; overflow: hidden;">'
					if content:
						# Inherit border radius for inner image if parent has it? Or just overflow hidden
						# Ensure image fits
						html_content += f'<img src="{content}" style="width: 100%; height: 100%; object-fit: cover; display: block;">'
					html_content += "</div>"
				elif el.get("type") == "rect":
					html_content += (
						f'<div class="element" style="{css_style} width: {w}px; height: {h}px;"></div>'
					)

			html_content += """
				</div>
			</body>
			</html>
			"""

			# Use existing generation method
			# We need to render the content first to resolve {{ jinja }} in Text elements
			# But our editor stores text like [Student Name] or custom text.
			# The editor 'add_field' sets content like [Student Name].
			# We need to map these brackets to actual values.

			# Replace placeholders
			# Helper map
			field_map = {
				"[Student Name]": self.student_name,
				"[Student ID]": self.name,
				"[Blood Group]": getattr(student, "blood_group", ""),
				"[Phone]": self.phone,
				"[Email]": self.email,
				"[Program]": self.program,
				"[Academic Year]": self.academic_year,
				"[Date of Birth]": frappe.utils.format_date(self.date_of_birth) if self.date_of_birth else "",
				"[Department]": self.department,
				"[Institute Name]": template.institute_name,
				"[Institute Address]": template.institute_address,
				"[Address]": getattr(student, "state_of_domicile", ""),
			}

			for key, val in field_map.items():
				if val is None:
					val = ""
				html_content = html_content.replace(key, str(val))

			# Now call generator
			# We use a custom flow since we ALREADY have the full HTML, we don't need the jinja render step of generate_image_from_html
			# But we need wkhtmltoimage logic.

			self.generate_image_from_raw_html(html_content, f"{side}_id_image", side.capitalize())

	def generate_image_from_raw_html(self, html_content, fieldname, side_label):
		# Create temp file
		with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w") as f:
			f.write(html_content)
			html_path = f.name

		output_filename = f"{self.name}_{side_label}.png"
		output_path = os.path.join(tempfile.gettempdir(), output_filename)

		try:
			args = [
				"/usr/bin/wkhtmltoimage",
				"--enable-local-file-access",
				"--width",
				"1011",
				"--height",
				"638",  # This should swap for portrait...
				# Actually we set container size in CSS, wkhtmltoimage size should match or be larger?
				# If portrait, we should probably flip these args or rely on CSS size.
				# Let's check orientation again?
				# For now, let's just make the window large enough.
				"--quality",
				"100",
				html_path,
				output_path,
			]

			# Adjust args for portrait if needed, but since we define container size, maybe just large viewport is enough
			# But wkhtmltoimage crops? No, defaults to A4 or smart width.
			# Be safe:
			if "width: 638px;" in html_content:  # Portrait check hack or pass arg
				args[3] = "638"
				args[5] = "1011"

			result = subprocess.run(args, capture_output=True, text=True)
			if result.returncode != 0:
				frappe.throw(f"wkhtmltoimage failed: {result.stderr}")

			with open(output_path, "rb") as f:
				img_content = f.read()

			saved_file = save_file(output_filename, img_content, self.doctype, self.name, is_private=0)
			self.db_set(fieldname, saved_file.file_url)

		except Exception as e:
			frappe.throw(f"Error generating from canvas: {e}")
		finally:
			if os.path.exists(html_path):
				os.remove(html_path)
			if os.path.exists(output_path):
				os.remove(output_path)

	def generate_card_html(self, template, student):
		if template.front_html:
			self.generate_image_from_html(template.front_html, student, template, "front_id_image", "Front")
		if template.back_html:
			self.generate_image_from_html(template.back_html, student, template, "back_id_image", "Back")

	def generate_image_from_html(self, html_content, person, template, fieldname, side):
		# Prepare Context
		# 1. Start with Person data (e.g. first_name, blood_group)
		# 1. Start with Person data (e.g. first_name, blood_group)
		if hasattr(person, "as_dict") and callable(person.as_dict):
			context = person.as_dict()
		else:
			context = person.copy() if person else {}

		# 2. Add ID Card Doc data (e.g. student_name, phone, email, photo)
		# This ensures {{ student_name }} works as it's defined on the ID Card doc
		context.update(self.as_dict())

		# 3. Add Template data (e.g. institute_name)
		context.update(template.as_dict())

		# 4. Add overrides and helpers
		# Handle photo field based on person/card type
		person_photo = ""
		if self.card_type == "Student":
			person_photo = getattr(person, "passport_size_photo", "")
		elif self.card_type in ["Faculty", "Driver"]:
			person_photo = getattr(person, "photo", "")

		context.update(
			{
				"doc": self,
				"student": person,  # Backwards compat: use 'student' as key for person
				"person": person,  # New standard key
				"template": template,
				# Institute details
				"institute_name": template.institute_name,
				"institute_address": template.institute_address,
				# LOGO (IMPORTANT)
				"institute_logo": self.get_file_path(template.institute_logo) or "",
				"logo_url": self.get_file_path(template.institute_logo) or "",
				# AUTHORITY SIGNATURE
				"authority_signature": self.get_file_path(template.authority_signature) or "",
				# STUDENT/PERSON PHOTO
				"passport_size_photo": self.get_file_path(person_photo) or "",  # For compatibility
				"photo": self.get_file_path(person_photo) or "",  # Standard
				# QR CODE (IMPORTANT)
				"qr_code_image": self.get_file_path(self.qr_code_image) or "",
				"qr_code": self.get_file_path(self.qr_code_image) or "",  # Alias
				"institute_logo_url": get_url(template.institute_logo)
				if template.institute_logo
				else "",  # Helper
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
		# Lazy import
		from PIL import ImageDraw

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
		# Lazy import
		from PIL import ImageFont

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
			if hasattr(student, "passport_size_photo") and student.passport_size_photo:
				return student.passport_size_photo
			if hasattr(student, "photo") and student.photo:
				return student.photo
			return None  # Or default placeholder

		if hasattr(student, fieldname):
			val = getattr(student, fieldname)
			return val

		# Static Text check? If fieldname is not in student, treat as static?
		# For now, strict mapping. User can use Virtual Fields in Student if needed.
		return None

	def paste_photo(self, base_image, photo_path, x, y, w, h):
		# Lazy import
		from PIL import Image

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
		# Lazy imports
		import qrcode
		from PIL import Image

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

		# Handle http/https urls (leave them as is for wkhtmltoimage, it might handle them if network allowed)
		if file_url.startswith("http"):
			return file_url

		path = None

		# Handle Assets (e.g., /assets/frappe/images/default-avatar.png)
		if file_url.startswith("/assets/"):
			# Standard bench structure: ./sites/assets/
			asset_path = file_url.replace("/assets/", "", 1)
			bench_path = frappe.utils.get_bench_path()
			full_path = os.path.join(bench_path, "sites", "assets", asset_path)

			if os.path.exists(full_path):
				path = full_path

			# Fallback for standard Frappe assets (if not in sites/assets yet)
			elif "default-avatar.png" in file_url:
				path = frappe.get_app_path("frappe", "public", "images", "default-avatar.png")

		# Handle Private Files
		elif file_url.startswith("/private/files/"):
			file_name = file_url.replace("/private/files/", "", 1)
			path = frappe.get_site_path("private", "files", file_name)

		# Handle Public Files (default)
		# Should span /files/ and others
		elif file_url.startswith("/"):
			path = frappe.get_site_path("public", file_url.lstrip("/"))

		else:
			path = frappe.get_site_path("public", file_url)

		if path:
			return os.path.abspath(path)

		return None

	def save_image(self, image, filename, fieldname):
		# Save to buffer
		img_io = io.BytesIO()
		image.save(img_io, format="PNG", dpi=(300, 300))
		img_content = img_io.getvalue()

		# Save as frappe file
		saved_file = save_file(filename, img_content, self.doctype, self.name, is_private=0)

		self.db_set(fieldname, saved_file.file_url)


@frappe.whitelist()
def create_or_update_template(template_data):
	"""
	Create or update an ID Card Template based on JS definition.
	This ensures the backend has a record matching the selected template.
	"""
	if isinstance(template_data, str):
		data = json.loads(template_data)
	else:
		data = template_data

	template_name = data.get("template_name")
	if not template_name:
		frappe.throw("Template Name is missing.")

	# Check if exists
	# Use template name as ID if possible or search
	if not frappe.db.exists("ID Card Template", {"template_name": template_name}):
		doc = frappe.new_doc("ID Card Template")
		doc.template_name = template_name
	else:
		existing = frappe.db.get_value("ID Card Template", {"template_name": template_name}, "name")
		doc = frappe.get_doc("ID Card Template", existing)

	# Map fields
	doc.template_creation_mode = "Jinja Template"  # Forced
	doc.front_html = data.get("front_template_html")
	doc.back_html = data.get("back_template_html")
	doc.card_size = data.get("card_size")
	doc.orientation = data.get("orientation")

	doc.save(ignore_permissions=True)
	return doc.name
