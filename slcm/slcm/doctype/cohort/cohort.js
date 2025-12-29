// Copyright (c) 2025, Nishanth and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Cohort", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Cohort", {
	start_date(frm) {
		frm.trigger("calculate_term_duration");
	},

	end_date(frm) {
		frm.trigger("calculate_term_duration");
	},

	calculate_term_duration(frm) {
		const start = frm.doc.start_date;
		const end = frm.doc.end_date;

		// Reset if dates are missing
		if (!start || !end) {
			frm.set_value("term_days", 0);
			frm.set_value("term_weeks", 0);
			return;
		}

		const startDate = frappe.datetime.str_to_obj(start);
		const endDate = frappe.datetime.str_to_obj(end);

		// Validation: End date cannot be before start date
		if (endDate < startDate) {
			frappe.msgprint({
				title: __("Invalid Date Range"),
				message: __("End Date cannot be before Start Date."),
				indicator: "red",
			});

			frm.set_value("term_days", 0);
			frm.set_value("term_weeks", 0);
			return;
		}

		// Calculate inclusive day count
		const diffMs = endDate - startDate;
		const days = Math.floor(diffMs / (1000 * 60 * 60 * 24)) + 1;
		const weeks = Number((days / 7).toFixed(2));

		frm.set_value("term_days", days);
		frm.set_value("term_weeks", weeks);
	},
});
