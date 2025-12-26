// Copyright (c) 2025, Nishanth and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Cohort", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Cohort", {
	start_date: calculate_weeks,
	end_date: calculate_weeks,
});

function calculate_weeks(frm) {
	if (frm.doc.start_date && frm.doc.end_date) {
		const start = frappe.datetime.str_to_obj(frm.doc.start_date);
		const end = frappe.datetime.str_to_obj(frm.doc.end_date);

		if (end < start) {
			frappe.msgprint(__("End Date cannot be before Start Date"));
			frm.set_value("term_weeks", 0);
			return;
		}

		const diff_in_days = frappe.datetime.get_day_diff(end, start) + 1;
		const weeks = Math.ceil(diff_in_days / 7);

		frm.set_value("term_weeks", weeks);
	}
}
