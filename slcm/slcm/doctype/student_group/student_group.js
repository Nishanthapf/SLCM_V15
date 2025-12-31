// Copyright (c) 2025, Nishanth and contributors
// For license information, please see license.txt

frappe.ui.form.on("Student Group", {
	onload: function (frm) {
		frm.set_query("academic_term", function () {
			return {
				filters: {
					academic_year: frm.doc.academic_year,
				},
			};
		});

		if (!frm.__islocal) {
			frm.set_query("student", "students", function () {
				let filters = {
					group_based_on: frm.doc.group_based_on,
				};

				if (!(frm.doc.group_based_on === "Activity")) {
					filters = {
						...filters,
						academic_year: frm.doc.academic_year,
						academic_term: frm.doc.academic_term,
						program: frm.doc.program,
						batch: frm.doc.batch,
						student_category: frm.doc.student_category,
						course: frm.doc.course,
						student_group: frm.doc.name,
					};
				}

				return {
					query: "slcm.slcm.doctype.student_group.student_group.fetch_students",
					filters: filters,
				};
			});
		}
	},

	refresh: function (frm) {
		if (!frm.doc.__islocal) {
			// Add custom button for Student Attendance Tool
			frm.add_custom_button(
				__("Student Attendance Tool"),
				function () {
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

	group_based_on: function (frm) {
		if (frm.doc.group_based_on == "Batch") {
			frm.doc.course = null;
			frm.set_df_property("program", "reqd", 1);
			frm.set_df_property("course", "reqd", 0);
		} else if (frm.doc.group_based_on == "Course") {
			frm.set_df_property("program", "reqd", 0);
			frm.set_df_property("course", "reqd", 1);
		} else if (frm.doc.group_based_on == "Activity") {
			frm.set_df_property("program", "reqd", 0);
			frm.set_df_property("course", "reqd", 0);
		}
		frm.refresh_field("course");
		frm.refresh_field("program");
	},

	get_students: function (frm) {
		if (frm.doc.group_based_on == "Batch" || frm.doc.group_based_on == "Course") {
			var student_list = [];
			var max_roll_no = 0;
			$.each(frm.doc.students, function (_i, d) {
				student_list.push(d.student);
				if (d.group_roll_number > max_roll_no) {
					max_roll_no = d.group_roll_number;
				}
			});

			if (frm.doc.academic_year) {
				frappe.call({
					method: "slcm.slcm.doctype.student_group.student_group.get_students",
					args: {
						academic_year: frm.doc.academic_year,
						academic_term: frm.doc.academic_term,
						group_based_on: frm.doc.group_based_on,
						program: frm.doc.program,
						batch: frm.doc.batch,
						student_category: frm.doc.student_category,
						course: frm.doc.course,
					},
					callback: function (r) {
						if (r.message) {
							$.each(r.message, function (i, d) {
								if (!in_list(student_list, d.student)) {
									var s = frm.add_child("students");
									s.student = d.student;
									s.student_name = d.student_name;
									if (d.active === 0) {
										s.active = 0;
									}
									s.group_roll_number = ++max_roll_no;
								}
							});
							refresh_field("students");
							frm.save();
						} else {
							frappe.msgprint(__("Student Group is already updated."));
						}
					},
				});
			}
		} else {
			frappe.msgprint(__("Select students manually for the Activity based Group"));
		}
	},
});

frappe.ui.form.on("Student Group Student", {
	student: function (frm, cdt, cdn) {
		var row = locals[cdt][cdn];
		if (row.student) {
			frappe.db.get_value("Student Master", row.student, "first_name", function (r) {
				if (r && r.first_name) {
					frappe.model.set_value(cdt, cdn, "student_name", r.first_name);
				}
			});
		}
	},
});

frappe.ui.form.on("Student Group Instructor", {
	instructors_add: function (frm) {
		frm.fields_dict["instructors"].grid.get_field("instructor").get_query = function (doc) {
			let instructor_list = [];
			$.each(doc.instructors, function (idx, val) {
				instructor_list.push(val.instructor);
			});
			return { filters: [["Faculty", "name", "not in", instructor_list]] };
		};
	},
});
