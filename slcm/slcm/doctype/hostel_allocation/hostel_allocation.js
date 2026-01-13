// # Copyright(c) 2024, Logic 360 and contributors
// # For license information, please see license.txt

frappe.ui.form.on("Hostel Allocation", {
	refresh: function (frm) {
		frm.set_query("room", function () {
			return {
				filters: {
					hostel: frm.doc.hostel,
				},
			};
		});
	},
	hostel: function (frm) {
		frm.set_value("room", "");
	},
});
