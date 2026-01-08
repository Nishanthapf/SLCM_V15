frappe.ui.form.on("ID Card Generation Tool", {
	refresh: function (frm) {
		frm.disable_save();

		// Add Preview Field HTML
		if (!frm.fields_dict["preview_html"]) {
			// This assumes we add a 'preview_html' HTML field to the DocType using JSON editor
			// But user asked to "add the Preview", implying I might need to add the field to JSON first.
			// Let's assume I will add it.
		}

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

	id_card_template: function (frm) {
		if (frm.doc.id_card_template && frm.doc.student_list && frm.doc.student_list.length > 0) {
			// Trigger preview update
			frm.trigger("render_preview");
		}
	},

	render_preview: function (frm) {
		if (!frm.doc.id_card_template) return;

		// Take first student for preview
		let student = null;
		if (frm.doc.student_list && frm.doc.student_list.length > 0) {
			student = frm.doc.student_list[0].student;
		} else {
			return;
		}

		frappe.call({
			method: "slcm.slcm.doctype.id_card_generation_tool.id_card_generation_tool.get_preview_html",
			args: {
				template_name: frm.doc.id_card_template,
				student: student,
			},
			callback: function (r) {
				if (r.message) {
					frm.set_df_property("preview_section", "hidden", 0);
					$(frm.fields_dict["preview_html"].wrapper).html(r.message);
				}
			},
		});
	},
});
