frappe.ui.form.on("Student ID Card", {
	refresh: function (frm) {
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("Generate Card"), function () {
				frm.call("generate_card").then((r) => {
					frm.refresh();
				});
			});
		}
	},
});
