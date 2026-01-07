// Copyright (c) 2025, Nishanth and contributors
// For license information, please see license.txt

frappe.listview_settings["Student Master"] = {
	add_fields: ["registration_status", "status_updated_by", "status_updated_on"],

	onload(listview) {
		inject_status_css();
		add_listview_status_actions(listview);
		add_listview_status_button(listview);
		add_bulk_delete_button(listview);
		// Ensure status column is visible
		ensure_status_column_visible(listview);
	},

	get_indicator(doc) {
		const status = doc.registration_status || "Draft";

		const status_config = {
			Draft: ["Draft", "grey", "registration_status,=,Draft"],
			"Pending REGO": ["Pending REGO", "orange", "registration_status,=,Pending REGO"],
			"Pending FINO": ["Pending FINO", "red", "registration_status,=,Pending FINO"],
			"Pending Registration": [
				"Pending Registration",
				"blue",
				"registration_status,=,Pending Registration",
			],
			"Pending Print & Scan": [
				"Pending Print & Scan",
				"yellow",
				"registration_status,=,Pending Print & Scan",
			],
			"Pending Residences": [
				"Pending Residences",
				"purple",
				"registration_status,=,Pending Residences",
			],
			"Pending IT": ["Pending IT", "pink", "registration_status,=,Pending IT"],
			Completed: ["Completed", "green", "registration_status,=,Completed"],
		};

		if (status_config[status]) {
			return status_config[status];
		}

		return [__(status), "grey", `registration_status,=,${status}`];
	},

	formatters: {
		registration_status(value, field, doc) {
			const status = value || "Draft";
			const status_colors = {
				Draft: "grey",
				"Pending REGO": "orange",
				"Pending FINO": "red",
				"Pending Registration": "blue",
				"Pending Print & Scan": "yellow",
				"Pending Residences": "purple",
				"Pending IT": "pink",
				Completed: "green",
			};

			const color = status_colors[status] || "grey";
			return `<span class="indicator-pill ${color}">${status}</span>`;
		},
	},
};

/* --------------------------------------------------
   List View → Custom Button in Toolbar
-------------------------------------------------- */
function add_listview_status_button(listview) {
	// Add custom button in toolbar for bulk status update
	listview.page.add_inner_button(
		__("Update Status"),
		function () {
			const selected = listview.get_checked_items();

			if (selected.length === 0) {
				frappe.msgprint({
					title: __("No Selection"),
					message: __("Please select at least one student to update status."),
					indicator: "orange",
				});
				return;
			}

			show_bulk_status_dialog(listview, selected);
		},
		__("Actions")
	);
}

/* --------------------------------------------------
   List View → Actions → Status (Bulk Update) - Menu Item
-------------------------------------------------- */
function add_listview_status_actions(listview) {
	// Add Status menu to list view actions
	listview.page.add_menu_item(__("Update Status"), function () {
		const selected = listview.get_checked_items();

		if (selected.length === 0) {
			frappe.msgprint({
				title: __("No Selection"),
				message: __("Please select at least one student to update status."),
				indicator: "orange",
			});
			return;
		}

		show_bulk_status_dialog(listview, selected);
	});
}

/* --------------------------------------------------
   List View → Bulk Delete (System Manager only)
-------------------------------------------------- */
function add_bulk_delete_button(listview) {
	// Show only for System Manager or Administrator
	if (!frappe.user.has_role("System Manager") && frappe.session.user !== "Administrator") return;

	listview.page.add_inner_button(
		__("Delete Selected"),
		function () {
			const selected = listview.get_checked_items();

			if (!selected.length) {
				frappe.msgprint({
					title: __("No Selection"),
					message: __("Please select at least one student to delete."),
					indicator: "orange",
				});
				return;
			}

			frappe.confirm(
				__("Are you sure you want to delete {0} student(s)?", [selected.length]),
				function () {
					const names = selected.map((row) => row.name);
					frappe.call({
						method: "frappe.desk.reportview.delete_items",
						args: {
							items: names,
							doctype: "Student Master",
						},
						freeze: true,
						freeze_message: __("Deleting records..."),
						callback: function () {
							frappe.show_alert({
								message: __("Deleted {0} student(s)", [names.length]),
								indicator: "green",
							});
							listview.refresh();
						},
						error: function (r) {
							frappe.msgprint({
								title: __("Error"),
								message: r.message || __("Failed to delete records"),
								indicator: "red",
							});
						},
					});
				}
			);
		},
		__("Actions")
	);
}

function show_bulk_status_dialog(listview, selected) {
	const statuses = [
		"Draft",
		"Pending REGO",
		"Pending FINO",
		"Pending Registration",
		"Pending Print & Scan",
		"Pending Residences",
		"Pending IT",
		"Completed",
	];

	// Get current statuses for selected students
	const status_summary = {};
	selected.forEach((student) => {
		const status = student.registration_status || "Draft";
		status_summary[status] = (status_summary[status] || 0) + 1;
	});

	const status_html = Object.entries(status_summary)
		.map(([status, count]) => `<strong>${status}:</strong> ${count} student(s)`)
		.join("<br>");

	let dialog = new frappe.ui.Dialog({
		title: __("Bulk Update Status"),
		fields: [
			{
				fieldtype: "HTML",
				options: `<div class="alert alert-info">
					<strong>Selected:</strong> ${selected.length} student(s)<br><br>
					<strong>Current Status Distribution:</strong><br>
					${status_html}
				</div>`,
			},
			{
				fieldtype: "Select",
				fieldname: "new_status",
				label: __("New Status"),
				options: statuses.join("\n"),
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

			frappe.confirm(
				__("Update status to <b>{0}</b> for {1} student(s)?", [
					values.new_status,
					selected.length,
				]),
				function () {
					// Yes - Update status
					dialog.hide();

					let success_count = 0;
					let error_count = 0;
					let errors = [];

					// Process each student
					selected.forEach((student, index) => {
						frappe.call({
							method: "slcm.slcm.doctype.student_master.student_master.update_registration_status",
							args: {
								student_id: student.name,
								new_status: values.new_status,
								remarks: values.remarks,
							},
							async: false,
							callback: function (r) {
								if (r.message && r.message.status === "success") {
									success_count++;
								} else {
									error_count++;
									errors.push(
										`${student.name}: ${
											r.message
												? r.message.message || r.message
												: "Unknown error"
										}`
									);
								}

								// Check if all processed
								if (success_count + error_count === selected.length) {
									if (error_count === 0) {
										frappe.show_alert({
											message: __(
												"Status updated successfully for {0} student(s)",
												[success_count]
											),
											indicator: "green",
										});
									} else {
										frappe.msgprint({
											title: __("Update Status - Partial Success"),
											message: __(
												"Successfully updated: {0}<br>Failed: {1}<br><br>Errors:<br>{2}",
												[success_count, error_count, errors.join("<br>")]
											),
											indicator: "orange",
										});
									}
									listview.refresh();
								}
							},
							error: function (r) {
								error_count++;
								errors.push(
									`${student.name}: ${r.message || "Error updating status"}`
								);

								if (success_count + error_count === selected.length) {
									frappe.msgprint({
										title: __("Update Status - Errors"),
										message: __(
											"Successfully updated: {0}<br>Failed: {1}<br><br>Errors:<br>{2}",
											[success_count, error_count, errors.join("<br>")]
										),
										indicator: "red",
									});
									listview.refresh();
								}
							},
						});
					});
				},
				function () {
					// No - Cancel
					dialog.hide();
				}
			);
		},
	});

	dialog.show();
}

/* --------------------------------------------------
   Ensure Status Column is Visible
-------------------------------------------------- */
function ensure_status_column_visible(listview) {
	// Add registration_status to visible columns if not already there
	setTimeout(() => {
		const columns = listview.columns || [];
		const has_status = columns.some((col) => col.fieldname === "registration_status");

		if (!has_status) {
			// Status column will be shown via get_indicator and formatters
			// The field is already set to in_list_view: 1 in JSON
		}
	}, 500);
}

/* --------------------------------------------------
   Status Indicator Styling
-------------------------------------------------- */
function inject_status_css() {
	if (document.getElementById("student-status-css")) {
		return;
	}

	const style = document.createElement("style");
	style.id = "student-status-css";
	style.innerHTML = `
		.indicator-pill.grey {
			background-color: #e9ecef !important;
			color: #495057 !important;
			font-weight: 600;
		}
		.indicator-pill.orange {
			background-color: #fff3cd !important;
			color: #856404 !important;
			font-weight: 600;
		}
		.indicator-pill.red {
			background-color: #f8d7da !important;
			color: #721c24 !important;
			font-weight: 600;
		}
		.indicator-pill.blue {
			background-color: #d1ecf1 !important;
			color: #0c5460 !important;
			font-weight: 600;
		}
		.indicator-pill.yellow {
			background-color: #fff3cd !important;
			color: #856404 !important;
			font-weight: 600;
		}
		.indicator-pill.purple {
			background-color: #e2d9f3 !important;
			color: #6f42c1 !important;
			font-weight: 600;
		}
		.indicator-pill.pink {
			background-color: #fce4ec !important;
			color: #c2185b !important;
			font-weight: 600;
		}
		.indicator-pill.green {
			background-color: #d4edda !important;
			color: #155724 !important;
			font-weight: 600;
		}
	`;

	document.head.appendChild(style);
}
