frappe.ui.form.on("Student Enrollment", {
	program(frm) {
		// 1️⃣ If program is cleared → clear courses
		if (!frm.doc.program) {
			frm.clear_table("table_hxbo");
			frm.refresh_field("table_hxbo");
			return;
		}

		// 2️⃣ Clear existing rows
		frm.clear_table("table_hxbo");

		// 3️⃣ Fetch Program document
		frappe.db.get_doc("Program", frm.doc.program).then((program_doc) => {
			console.log("Program Response:", program_doc);

			if (!program_doc.table_fela || program_doc.table_fela.length === 0) {
				frm.refresh_field("table_hxbo");
				return;
			}

			// 4️⃣ Copy Program → Student Enrollment courses
			program_doc.table_fela.forEach((pc) => {
				let row = frm.add_child("table_hxbo");

				// ✅ DIRECT ASSIGNMENT (Correct way)
				row.course_offering = pc.course_offering;
				row.course = pc.course;
				row.credits = pc.credits;
				row.status = pc.status;
			});

			// 5️⃣ Refresh UI once
			frm.refresh_field("table_hxbo");
		});
	},
});
