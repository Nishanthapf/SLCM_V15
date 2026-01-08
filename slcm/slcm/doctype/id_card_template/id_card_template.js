frappe.ui.form.on("ID Card Template", {
	refresh(frm) {
		frm.add_custom_button(__("Show Preview"), () => {
			frm.call("get_preview").then((r) => {
				if (!r.message) return;

				// Unhide section
				frm.set_df_property("preview_section", "hidden", 0);

				// Inject HTML
				frm.fields_dict.preview_html.$wrapper.html(r.message);

				// Force repaint
				frm.refresh_field("preview_html");
			});
		});
	},
});
