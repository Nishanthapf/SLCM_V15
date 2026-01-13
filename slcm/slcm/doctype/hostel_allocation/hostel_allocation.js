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

		frm.add_custom_button(__("Update Status"), function () {
			let d = new frappe.ui.Dialog({
				title: "Update Allocation Status",
				fields: [
					{
						label: "Status",
						fieldname: "status",
						fieldtype: "Select",
						options: "Allocated\nVacated\nDropped Out\nSuspended\nCancelled",
						default: frm.doc.status,
						reqd: 1
					}
				],
				primary_action_label: "Update",
				primary_action(values) {
					frm.set_value("status", values.status);
					frm.save();
					d.hide();
				}
			});
			d.show();
		});
	},
	hostel: function (frm) {
		frm.set_value("room", "");
	},
});
