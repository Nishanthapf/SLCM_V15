/* global slcm */
frappe.ui.form.on("ID Card Generation", {
	refresh: function (frm) {
		// Dynamic Fetch for Faculty/Driver
		frm.fields_dict["faculty"].df.onchange = () => {
			if (frm.doc.faculty) {
				frappe.db.get_doc("Faculty", frm.doc.faculty).then((doc) => {
					frm.set_value("student_name", doc.first_name + " " + (doc.last_name || ""));
					frm.set_value("email", doc.email);
					frm.set_value("phone", doc.phone);
					frm.set_value("department", doc.department);
					frm.set_value("photo", doc.photo);
					frm.set_value("designation", doc.designation);
				});
			}
		};

		frm.fields_dict["driver"].df.onchange = () => {
			if (frm.doc.driver) {
				frappe.db.get_doc("Driver", frm.doc.driver).then((doc) => {
					frm.set_value("student_name", doc.driver_name); // Reusing student_name field for Name on Card
					frm.set_value("phone", doc.phone);
					frm.set_value("photo", doc.photo);
					frm.set_value("designation", "Driver");
				});
			}
		};

		// Naming Series Automations
		frm.fields_dict["card_type"].df.onchange = () => {
			let map = {
				Student: "STU-.#####",
				Faculty: "FAC-.#####",
				Driver: "DRV-.#####",
				Visitor: "VIS-.#####",
				"Non-Faculty": "STF-.#####",
			};
			if (map[frm.doc.card_type]) {
				frm.set_value("naming_series", map[frm.doc.card_type]);
			}
			// Clear fields on type change
			frm.set_value("student", null);
			frm.set_value("faculty", null);
			frm.set_value("driver", null);
			frm.set_value("visitor_name", null);
			frm.set_value("non_faculty_name", null);
			frm.set_value("designation", null);
			frm.set_value("department", null);
			frm.set_value("photo", null);
		};
		if (frm.doc.qr_code_image) {
			frm.set_df_property(
				"qr_code_preview",
				"options",
				`<div style="text-align: center; margin: 10px;">
					<img src="${frappe.utils.get_file_link(
						frm.doc.qr_code_image
					)}" style="max-width: 300px; border: 1px solid #ccc; padding: 10px;">
				</div>`
			);
		} else {
			frm.set_df_property("qr_code_preview", "options", "");
		}

		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("Generate Card"), function () {
				frm.call("generate_card").then((r) => {
					frm.refresh();
				});
			});

			if (frm.doc.front_id_image && frm.doc.card_status === "Generated") {
				frm.add_custom_button(__("Print Card"), function () {
					// Log the print action first
					frm.call({
						doc: frm.doc,
						method: "log_print",
						args: {
							layout: "Single",
						},
						callback: function (r) {
							if (!r.exc) {
								// Open both sides in a print-friendly window
								let front_url = frappe.utils.get_file_link(frm.doc.front_id_image);
								let back_url = frm.doc.back_id_image
									? frappe.utils.get_file_link(frm.doc.back_id_image)
									: null;

								let w = window.open("", "_blank");
								w.document.write(`
									<html>
									<head>
										<title>Print ID Card - ${frm.doc.student_name}</title>
										<style>
											body { margin: 0; padding: 20px; text-align: center; font-family: sans-serif; }
											img { max-width: 100%; border: 1px solid #ccc; margin-bottom: 20px; }
											@media print {
												img { page-break-after: always; }
											}
										</style>
									</head>
									<body>
										<h3>${frm.doc.student_name} (${r.message || "Copy"})</h3>
										<img src="${front_url}" />
										${back_url ? `<br><img src="${back_url}" />` : ""}
										<script>
											window.onload = function() { window.print(); }
										</script>
									</body>
									</html>
								`);
								w.document.close();
							}
						},
					});
				});
			}
		}

		// Load Templates Module
		// Note: Ensure student_id_card_templates.js is available in assets.
		// You may need to add it to build.json or symlink it to public/js.
		try {
			// Try to load if exposed as asset
			frappe.require("/assets/slcm/js/student_id_card_templates.js");
		} catch (e) {
			console.log(
				"Could not load templates via require. Ensure global object slcm.templates is available."
			);
		}
	},

	show_template_dialog: function (frm) {
		if (!val_check_templates()) {
			frappe.msgprint(__("Template module (slcm.templates) not loaded."));
			return;
		}

		const templates = slcm.templates.registry;
		let options = templates.map((t) => ({ label: t.template_name, value: t.template_id }));

		let d = new frappe.ui.Dialog({
			title: "Select ID Card Template",
			fields: [
				{
					label: "Template",
					fieldname: "template_id",
					fieldtype: "Select",
					options: options,
					reqd: 1,
				},
			],
			primary_action_label: "Apply",
			primary_action(values) {
				frm.trigger("apply_template", values.template_id);
				d.hide();
			},
		});

		d.show();
	},

	apply_template: function (frm, template_id) {
		if (!val_check_templates()) return;

		const tmpl = slcm.templates.get(template_id);
		if (!tmpl) {
			frappe.msgprint("Template definition not found.");
			return;
		}

		// We need to apply this template.
		// Since the backend relies on "ID Card Template" doctype, we must ensure a record exists
		// that matches this definition, and link it.

		frappe.call({
			method: "slcm.slcm.doctype.id_card_generation.id_card_generation.create_or_update_template",
			args: {
				template_data: JSON.stringify(tmpl),
			},
			freeze: true,
			freeze_message: "Applying Template...",
			callback: function (r) {
				if (r.message) {
					frm.set_value("id_card_template", r.message);

					// Also set preview HTML if needed or just save
					frappe.msgprint(__("Template applied successfully."));
					frm.save();
				}
			},
		});
	},
});

function val_check_templates() {
	if (typeof slcm === "undefined" || !slcm.templates) {
		frappe.msgprint(__("SLCM Templates module is not loaded correctly."));
		return false;
	}
	return true;
}
