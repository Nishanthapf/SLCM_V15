// Copyright (c) 2025, Nishanth and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Student Placement Profile", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on("Student Placement Profile", {
	refresh(frm) {
		$("span.sidebar-toggle-btn").hide();
		$(".col-lg-2.layout-side-section").hide();
		if (frm.doc.profile_status === "Locked" && frappe.user.has_role("Student")) {
			frm.set_read_only();
			frm.disable_save();
		}
	},
});
