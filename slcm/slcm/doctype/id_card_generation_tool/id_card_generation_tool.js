frappe.ui.form.on("ID Card Generation Tool", {
	refresh: function (frm) {
		frm.disable_save();

		frm.page.set_primary_action("Generate Cards", () => {
			frappe.confirm(
				"Are you sure you want to generate ID cards for all listed students?",
				() => {
					frm.call("generate_cards").then((r) => {
						frm.reload_doc();
					});
				}
			);
		});

		frm.add_custom_button(__("Get Students"), function () {
			frm.call("get_students").then((r) => {
				frm.refresh_field("student_list");
			});
		});

		if (frm.doc.student_list && frm.doc.student_list.length > 0) {
			frm.add_custom_button(__("Download ZIP"), function () {
				frm.call("download_zip").then((r) => {
					if (r.message) {
						window.open(r.message, "_blank");
					}
				});
			});

			frm.add_custom_button(__("Download Print Layout"), function () {
				frm.call("generate_print_layout").then((r) => {
					if (r.message) {
						window.open(r.message, "_blank");
					}
				});
			});
		}
	},
});
