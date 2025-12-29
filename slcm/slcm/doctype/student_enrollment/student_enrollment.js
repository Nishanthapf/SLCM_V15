frappe.ui.form.on("Student Enrollment", {
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
