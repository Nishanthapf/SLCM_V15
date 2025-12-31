frappe.ui.form.on("Student Enrollment", {
	refresh(frm) {
		// Add quick links to related records
		if (!frm.is_new() && frm.doc.student) {
			frm.set_df_property("html_links", "options", get_quick_links_html(frm));
		}
	},

	program(frm) {
		// 1️⃣ Clear table if program removed
		if (!frm.doc.program) {
			frm.clear_table("table_hxbo");
			frm.refresh_field("table_hxbo");
			return;
		}

		// 2️⃣ Clear existing rows
		frm.clear_table("table_hxbo");

		// 3️⃣ Fetch Program with child table
		frappe.db.get_doc("Program", frm.doc.program).then((program_doc) => {
			console.log(program_doc, "Fetched Program");

			if (!program_doc.table_fela || program_doc.table_fela.length === 0) {
				frm.refresh_field("table_hxbo");
				return;
			}

			// 4️⃣ Copy Program Course → Enrollment Course
			program_doc.table_fela.forEach((pc) => {
				const row = frm.add_child("table_hxbo");

				// ✅ ALWAYS works
				frappe.model.set_value(row.doctype, row.name, "course", pc.course);
				frappe.model.set_value(row.doctype, row.name, "course_name", pc.course_name);

				// ✅ REQUIRED for non-link fields
				frappe.model.set_value(row.doctype, row.name, "course_type", pc.course_type);
				frappe.model.set_value(row.doctype, row.name, "course_status", pc.course_status);
				frappe.model.set_value(row.doctype, row.name, "credit_value", pc.credit_value);
			});

			// 5️⃣ Refresh grid
			frm.refresh_field("table_hxbo");
		});
	},
});

function get_quick_links_html(frm) {
	const student = frm.doc.student;
	const enrollment = frm.doc.name;

	return `
		<div style="padding: 10px;">
			<h6>Quick Links</h6>
			<div style="display: flex; gap: 10px; flex-wrap: wrap;">
				<button class="btn btn-sm btn-default" onclick="frappe.set_route('List', 'Student Attendance', {'student': '${student}'})">
					View Attendance
				</button>
				<button class="btn btn-sm btn-default" onclick="frappe.set_route('List', 'Student Fee Assignment', {'student': '${student}'})">
					View Fees
				</button>
				<button class="btn btn-sm btn-default" onclick="frappe.set_route('List', 'Course Schedule', {'student_group': '${
					frm.doc.cohort || ""
				}'})">
					View Schedule
				</button>
			</div>
		</div>
	`;
}
