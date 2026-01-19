// Copyright (c) 2025, Nishanth and contributors
// For license information, please see license.txt

frappe.ui.form.on("Student Master", {
	refresh(frm) {
		// Hide default left sidebar
		$(".layout-side-section").hide();

		// Render custom right-side profile panel
		frm.trigger("render_profile_sidebar");

		// Custom Status Button
		if (!frm.is_new()) {
			frm.add_custom_button(
				__("Status"),
				function () {
					frm.trigger("show_status_dialog");
				},
				__("Update Status")
			).addClass("btn-primary");

			// Check Enrollment Eligibility and Add Button
			frappe.call({
				method: "slcm.slcm.doctype.student_master.student_master.validate_new_enrollment",
				args: {
					student_id: frm.doc.name,
				},
				callback: function (r) {
					if (r.message && r.message.allowed) {
						frm.add_custom_button(__("Enroll"), function () {
							// Re-validate on click to prevent race conditions
							frappe.call({
								method: "slcm.slcm.doctype.student_master.student_master.validate_new_enrollment",
								args: {
									student_id: frm.doc.name,
								},
								callback: function (r2) {
									if (r2.message && r2.message.allowed) {
										frappe.new_doc("Student Enrollment", {
											student: frm.doc.name,
											student_name: [
												frm.doc.first_name,
												frm.doc.middle_name,
												frm.doc.last_name,
											]
												.filter(Boolean)
												.join(" "),
											cohort: frm.doc.programme,
											data_xgxm: frm.doc.batch_year, // Batch
											academic_year: frm.doc.academic_year,
										});
									} else {
										frappe.msgprint({
											title: __("Not Allowed"),
											message: r2.message
												? r2.message.message
												: __("Enrollment not allowed."),
											indicator: "orange",
										});
									}
								},
							});
						}).addClass("btn-primary");
					}
				},
			});
		}
	},

	show_status_dialog(frm) {
		// Fetch available actions
		frappe.call({
			method: "slcm.slcm.doctype.student_master.student_master.get_available_status_actions",
			args: {
				student_id: frm.doc.name,
			},
			callback: function (r) {
				if (r.message) {
					show_status_transition_dialog(frm, r.message);
				}
			},
		});
	},

	render_profile_sidebar(frm) {
		if (frm.is_new()) {
			return;
		}

		const image = frm.doc.student_image || "/assets/frappe/images/default-avatar.png";

		const html = `
			<div class="student-profile-card">
				<img src="${image}" class="student-avatar" />
				<button class="btn btn-sm btn-primary upload-btn">
					Upload Image
				</button>
				<hr />
				<div class="attachment-area">
					<h6>Attachments</h6>
					<div class="attachments"></div>
				</div>
			</div>
		`;

		if (frm.fields_dict.profile_sidebar) {
			frm.fields_dict.profile_sidebar.$wrapper.html(html);

			frm.fields_dict.profile_sidebar.$wrapper.find(".upload-btn").on("click", () => {
				new frappe.ui.FileUploader({
					doctype: frm.doctype,
					docname: frm.doc.name,
					on_success(file) {
						if (file.file_url && file.file_url.match(/\.(jpg|jpeg|png|webp)$/i)) {
							frm.set_value("student_image", file.file_url);
							frm.save().then(() => {
								frm.reload_doc();
							});
						}
					},
				});
			});
		}
	},

	total_program_fee(frm) {
		frm.trigger("calculate_fees");
	},

	scholarship_percentage(frm) {
		frm.trigger("calculate_fees");
	},

	total_paid_amount(frm) {
		frm.trigger("calculate_fees");
	},

	applying_scholarship(frm) {
		if (frm.doc.applying_scholarship !== "Yes") {
			frm.set_value("scholarship_percentage", 0);
		}
		frm.trigger("calculate_fees");
	},

	calculate_fees(frm) {
		let total_fee = frm.doc.total_program_fee || 0;
		let scholarship_pct = frm.doc.scholarship_percentage || 0;
		let paid_amount = frm.doc.total_paid_amount || 0;

		if (frm.doc.applying_scholarship !== "Yes") {
			scholarship_pct = 0;
		}

		let discount = (total_fee * scholarship_pct) / 100;
		let net_fee = total_fee - discount;
		let balance = net_fee - paid_amount;

		frm.set_value("discount_amount", discount);
		frm.set_value("net_program_fee", net_fee);
		frm.set_value("outstanding_balance", balance);
	},
});

function show_status_transition_dialog(frm, data) {
	const current_status = data.current_status || "Selected";
	const available_actions = data.available_actions || [];

	if (available_actions.length === 0) {
		frappe.msgprint({
			title: __("No Actions Available"),
			message: __("You do not have permission to change the status from {0}.", [
				current_status,
			]),
			indicator: "orange",
		});
		return;
	}

	// Create dialog
	let dialog = new frappe.ui.Dialog({
		title: __("Update Registration Status"),
		fields: [
			{
				fieldtype: "HTML",
				options: `<div class="alert alert-info">
					<strong>Current Status:</strong> ${current_status}
				</div>`,
			},
			{
				fieldtype: "Select",
				fieldname: "new_status",
				label: __("New Status"),
				options: available_actions.map((a) => a.next_state).join("\n"),
				reqd: 1,
			},
			{
				fieldtype: "Small Text",
				fieldname: "remarks",
				label: __("Remarks"),
				reqd: 1,
			},
		],
		primary_action_label: __("Update Status"),
		primary_action: function () {
			const values = dialog.get_values();
			if (!values.new_status) {
				frappe.msgprint({
					title: __("Required"),
					message: __("Please select a new status"),
					indicator: "orange",
				});
				return;
			}

			if (!values.remarks || !values.remarks.trim()) {
				frappe.msgprint({
					title: __("Required"),
					message: __("Please enter remarks"),
					indicator: "orange",
				});
				return;
			}

			// Confirm action
			frappe.confirm(
				__("Are you sure you want to change status from <b>{0}</b> to <b>{1}</b>?", [
					current_status,
					values.new_status,
				]),
				function () {
					// Yes
					frappe.call({
						method: "slcm.slcm.doctype.student_master.student_master.update_registration_status",
						args: {
							student_id: frm.doc.name,
							new_status: values.new_status,
							remarks: values.remarks,
						},
						freeze: true,
						freeze_message: __("Updating status..."),
						callback: function (r) {
							if (r.message && r.message.status === "success") {
								frappe.show_alert({
									message: r.message.message,
									indicator: "green",
								});
								dialog.hide();
								frm.reload_doc();
							} else {
								frappe.msgprint({
									title: __("Error"),
									message: r.message
										? r.message.message || r.message
										: __("Failed to update status"),
									indicator: "red",
								});
							}
						},
						error: function (r) {
							frappe.msgprint({
								title: __("Error"),
								message:
									r.message || __("Failed to update status. Please try again."),
								indicator: "red",
							});
						},
					});
				},
				function () {
					// No
					dialog.hide();
				}
			);
		},
	});

	dialog.show();
}
