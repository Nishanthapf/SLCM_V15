// Copyright (c) 2025, Nishanth and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Student Placement Profile", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Student Placement Profile", {
	refresh(frm) {
		if (frm.doc.profile_status === "Locked" && frappe.user.has_role("Student")) {
			frm.set_read_only();
			frm.disable_save();
		}
	},
});
