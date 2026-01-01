// Copyright (c) 2025, Nishanth and contributors
// For license information, please see license.txt

frappe.ui.form.on("Student Group", {
	// --------------------------------------------------
	// ONLOAD
	// --------------------------------------------------
	onload(frm) {
		// Limit Academic Term by Academic Year (safe to keep)
		frm.set_query("academic_term", () => {
			return {
				filters: {
					academic_year: frm.doc.academic_year,
				},
			};
		});
	},

	// --------------------------------------------------
	// REFRESH
	// --------------------------------------------------
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(
				__("Student Attendance Tool"),
				() => {
					frappe.route_options = {
						based_on: "Student Group",
						student_group: frm.doc.name,
					};
					frappe.set_route("Form", "Student Attendance Tool", "Student Attendance Tool");
				},
				__("Tools")
			);
		}
	},

	// --------------------------------------------------
	// GET STUDENTS BUTTON (PROGRAM BASED)
	// --------------------------------------------------
	get_students(frm) {
		// ---------------- VALIDATION ----------------
		if (!frm.doc.program) {
			frappe.msgprint({
				title: __("Missing Program"),
				message: __("Please select a Program to fetch students."),
				indicator: "red",
			});
			return;
		}

		// ---------------- CLEAR OLD DATA ----------------
		frm.clear_table("students");

		let max_roll_no = 0;

		// ---------------- API CALL ----------------
		frappe.call({
			method: "slcm.slcm.doctype.student_group.student_group.get_students",
			args: {
				program: frm.doc.program, // ✅ ONLY PROGRAM
			},
			callback(r) {
				if (!r.message || r.message.length === 0) {
					frappe.msgprint({
						message: __("No students found for the selected Program."),
						indicator: "orange",
					});
					return;
				}

				// ---------------- POPULATE CHILD TABLE ----------------
				r.message.forEach((student) => {
					let row = frm.add_child("students");
					row.student = student.student;
					row.student_name = student.student_name;
					row.active = student.active;
					row.group_roll_number = ++max_roll_no;
				});

				frm.refresh_field("students");

				frappe.show_alert({
					message: __(`${r.message.length} students loaded successfully`),
					indicator: "green",
				});
			},
		});
	},
});

// --------------------------------------------------
// CHILD TABLE: STUDENT
// --------------------------------------------------
frappe.ui.form.on("Student Group Student", {
	student(frm, cdt, cdn) {
		const row = locals[cdt][cdn];

		if (row.student) {
			frappe.db.get_value("Student Master", row.student, "first_name").then((r) => {
				if (r && r.message) {
					frappe.model.set_value(cdt, cdn, "student_name", r.message.first_name);
				}
			});
		}
	},
});

// --------------------------------------------------
// CHILD TABLE: INSTRUCTOR
// --------------------------------------------------
frappe.ui.form.on("Student Group Instructor", {
	instructors_add(frm) {
		frm.fields_dict.instructors.grid.get_field("instructor").get_query = (doc) => {
			const used = (doc.instructors || []).map((d) => d.instructor);

			return {
				filters: [["Faculty", "name", "not in", used]],
			};
		};
	},
});
