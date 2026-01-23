// Copyright (c) 2025, Nishanth and contributors
// For license information, please see license.txt

frappe.ui.form.on("Course Schedule", {
	refresh(frm) {
		if (
			!frm.doc.__islocal &&
			frm.doc.course &&
			frm.doc.student_group &&
			frm.doc.instructor &&
			frm.doc.schedule_date
		) {
			frm.add_custom_button(__("Attendance"), () => {
				frappe.route_options = {
					based_on: "Course Schedule",
					course_schedule: frm.doc.name,
					date: frm.doc.schedule_date,
					student_group: frm.doc.student_group,
				};
				frappe.set_route("Form", "Student Attendance Tool");
			});
		}
	},
});
