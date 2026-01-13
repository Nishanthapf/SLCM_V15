import frappe
from frappe import _
from frappe.utils import get_url


def handle_registration_completion(student_name, triggered_by):
	"""
	Background job handler for sending registration completion email.
	Args:
		student_name (str): Name of the Student Master document
		triggered_by (str): Email of the user who triggered the action
	"""
	try:
		student = frappe.get_doc("Student Master", student_name)

		# Double check status to avoid race conditions
		if student.registration_status != "Completed":
			return

		# Generate PDF
		pdf_content = generate_pdf(student)

		# Send Email
		send_email(student, pdf_content, triggered_by)

	except Exception as e:
		frappe.log_error(title=f"Registration Email Failed for {student_name}", message=str(e))


def generate_pdf(student):
	"""
	Generates PDF for the Student Registration Slip.
	"""
	print_format = "Student Registration Slip"

	# Check if print format exists, else fallback to standard
	if not frappe.db.exists("Print Format", print_format):
		# Fallback to standard if custom one not ready yet,
		# or we could create a basic HTML string here.
		# For now, let's assume we will create the Print Format or use 'Standard'.
		print_format = None

	try:
		pdf = frappe.get_print("Student Master", student.name, print_format=print_format, as_pdf=True)
		return pdf
	except Exception as e:
		frappe.log_error(f"Standard PDF Generation Failed: {e!s}", "PDF Error")
		# Robust Fallback: Generate simple PDF from raw HTML to ensure email is sent
		try:
			from frappe.utils.pdf import get_pdf

			simple_html = f"""
				<h1>Registration Slip (Fallback)</h1>
				<p><strong>Name:</strong> {student.first_name} {student.last_name}</p>
				<p><strong>Application Number:</strong> {student.application_number}</p>
				<p><strong>Program:</strong> {student.programme}</p>
				<p><em>Note: Standard format failed to generate.</em></p>
			"""
			return get_pdf(simple_html)
		except Exception as fallback_e:
			frappe.throw(_("Failed to generate PDF (including fallback): {0}").format(str(fallback_e)))


def send_email(student, pdf_content, triggered_by):
	"""
	Sends email with PDF attachment to Student and Parents.
	"""
	recipients = []
	if student.email:
		recipients.append(student.email)

	# Add Parents
	if student.parents:
		for parent in student.parents:
			if parent.email:
				recipients.append(parent.email)

	if not recipients:
		frappe.log_error(f"No recipients found for Student {student.name}", "Registration Email Skipped")
		return

	subject = _("Registration Completed - {0}").format(student.first_name)

	# HTML Body
	message = f"""
	<div style="font-family: Arial, sans-serif; padding: 20px;">
		<h2>Registration Completed</h2>
		<p>Dear {student.first_name},</p>
		<p>Congratulations! Your registration process at SLCM is now officially completed.</p>

		<h3>Details:</h3>
		<ul>
			<li><strong>Application Number:</strong> {student.application_number}</li>
			<li><strong>Programme:</strong> {student.programme}</li>
			<li><strong>Academic Year:</strong> {student.academic_year or 'N/A'}</li>
		</ul>

		<p>Please find attached your Registration Slip.</p>

		<p>Best Regards,<br>
		Office of the Registrar</p>
	</div>
	"""

	attachments = [{"fname": f"Registration_Slip_{student.name}.pdf", "fcontent": pdf_content}]

	# Prevent duplicate sending check (basic implementation via logs)
	# Check if an email with this subject was sent to this student recently is overkill
	# if we rely on the status trigger.
	# But we can add a check if needed. For now, trusting the status trigger.

	frappe.sendmail(
		recipients=recipients,
		sender="nishanthclintona@gmail.com",  # Explicit sender as requested
		subject=subject,
		message=message,
		attachments=attachments,
		reference_doctype="Student Master",
		reference_name=student.name,
		delayed=False,  # Send immediately as requested
	)

	# Log explicitly if needed, but frappe.sendmail logs to Email Queue.
