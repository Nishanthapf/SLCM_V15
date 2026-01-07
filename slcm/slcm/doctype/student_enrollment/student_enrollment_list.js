// frappe.listview_settings["Student Enrollment"] = {
// 	onload(listview) {
// 		inject_enrollment_status_css();
// 	},

// 	get_indicator(doc) {
// 		if (doc.status === "Enrolled") {
// 			return [__("Enrolled"), "green", "status,=,Enrolled"];
// 		}

// 		if (doc.status === "Dropped") {
// 			return [__("Dropped"), "red", "status,=,Dropped"];
// 		}

// 		if (doc.status === "Completed") {
// 			return [__("Completed"), "blue", "status,=,Completed"];
// 		}

// 		return [__(doc.status), "gray"];
// 	},
// };

// function inject_enrollment_status_css() {
// 	if (document.getElementById("enrollment-status-css")) {
// 		return;
// 	}

// 	const style = document.createElement("style");
// 	style.id = "enrollment-status-css";
// 	style.innerHTML = `
// 		.indicator.green {
// 			background-color: #e6f4ea !important;
// 			color: #1e7e34 !important;
// 			font-weight: 600;
// 		}

// 		.indicator.red {
// 			background-color: #fdecea !important;
// 			color: #b02a37 !important;
// 			font-weight: 600;
// 		}

// 		.indicator.blue {
// 			background-color: #e7f1ff !important;
// 			color: #0d6efd !important;
// 			font-weight: 600;
// 		}
// 	`;

// 	document.head.appendChild(style);
// }

// frappe.ui.form.on("Student Enrollment", {
// 	refresh(frm) {
// 		// Do not show buttons for unsaved documents
// 		if (frm.is_new()) return;

// 		add_status_action_buttons(frm);
// 	},
// });

// /* --------------------------------------------------
//    Add Actions → Status buttons (Form View)
// -------------------------------------------------- */
// function add_status_action_buttons(frm) {
// 	// Clear existing buttons to avoid duplication
// 	frm.clear_custom_buttons();

// 	const statuses = [
// 		{ label: __("Enrolled"), value: "Enrolled" },
// 		{ label: __("Dropped"), value: "Dropped" },
// 		{ label: __("Completed"), value: "Completed" },
// 		{ label: __("Pending"), value: "Pending" },
// 	];

// 	statuses.forEach((status) => {
// 		frm.add_custom_button(
// 			status.label,
// 			() => update_enrollment_status(frm, status.value),
// 			__("Actions")
// 		);
// 	});
// }

// /* --------------------------------------------------
//    Update status safely (Single Record)
// -------------------------------------------------- */
// function update_enrollment_status(frm, status) {
// 	// Prevent unnecessary updates
// 	if (frm.doc.status === status) {
// 		frappe.msgprint({
// 			title: __("No Change"),
// 			message: __("Status is already <b>{0}</b>.", [status]),
// 			indicator: "blue",
// 		});
// 		return;
// 	}

// 	frappe.confirm(
// 		__("Are you sure you want to change status to <b>{0}</b>?", [status]),
// 		() => {
// 			frm.set_value("status", status);

// 			frm.save()
// 				.then(() => {
// 					frappe.show_alert(
// 						{
// 							message: __("Status updated to {0}", [status]),
// 							indicator: "green",
// 						},
// 						5
// 					);
// 				})
// 				.catch(() => {
// 					frappe.msgprint({
// 						title: __("Error"),
// 						message: __("Failed to update status. Please try again."),
// 						indicator: "red",
// 					});
// 				});
// 		}
// 	);
// }

/*****************************************************
 * LIST VIEW CONFIGURATION
 *****************************************************/
frappe.listview_settings["Student Enrollment"] = {
	onload(listview) {
		$("span.sidebar-toggle-btn").hide();
		$(".col-lg-2.layout-side-section").hide();
		inject_enrollment_status_css();
		add_listview_status_actions(listview);
	},

	get_indicator(doc) {
		if (doc.status === "Enrolled") {
			return [__("Enrolled"), "green", "status,=,Enrolled"];
		}

		if (doc.status === "Dropped") {
			return [__("Dropped"), "red", "status,=,Dropped"];
		}

		if (doc.status === "Completed") {
			return [__("Completed"), "blue", "status,=,Completed"];
		}

		if (doc.status === "Pending") {
			return [__("Pending"), "yellow", "status,=,Pending"];
		}

		return [__(doc.status), "gray"];
	},
};

/* --------------------------------------------------
   List View → Actions → Status (Bulk Update)
-------------------------------------------------- */
function add_listview_status_actions(listview) {
	const statuses = [
		{ label: __("Enrolled"), value: "Enrolled" },
		{ label: __("Dropped"), value: "Dropped" },
		{ label: __("Completed"), value: "Completed" },
		{ label: __("Pending"), value: "Pending" },
	];

	statuses.forEach((status) => {
		listview.page.add_action_item(status.label, () => {
			update_listview_status(listview, status.value);
		});
	});
}

/* --------------------------------------------------
   Bulk status update logic
-------------------------------------------------- */
function update_listview_status(listview, status) {
	const selected = listview.get_checked_items();

	if (!selected.length) {
		frappe.msgprint({
			title: __("No Records Selected"),
			message: __("Please select at least one Student Enrollment."),
			indicator: "orange",
		});
		return;
	}

	frappe.confirm(
		__("Are you sure you want to change status to <b>{0}</b> for {1} record(s)?", [
			status,
			selected.length,
		]),
		() => {
			const updates = selected.map((doc) =>
				frappe.db.set_value("Student Enrollment", doc.name, "status", status)
			);

			Promise.all(updates).then(() => {
				frappe.show_alert(
					{
						message: __("Status updated to {0}", [status]),
						indicator: "green",
					},
					5
				);
				listview.refresh();
			});
		}
	);
}

/*****************************************************
 * STATUS INDICATOR STYLING (LIST VIEW ONLY)
 *****************************************************/
function inject_enrollment_status_css() {
	if (document.getElementById("enrollment-status-css")) return;

	const style = document.createElement("style");
	style.id = "enrollment-status-css";
	style.innerHTML = `
		.indicator.green {
			background-color: #e6f4ea !important;
			color: #1e7e34 !important;
			font-weight: 600;
		}
		.indicator.red {
			background-color: #fdecea !important;
			color: #b02a37 !important;
			font-weight: 600;
		}
		.indicator.blue {
			background-color: #e7f1ff !important;
			color: #0d6efd !important;
			font-weight: 600;
		}
	`;
	document.head.appendChild(style);
}

/*****************************************************
 * FORM VIEW CONFIGURATION (SINGLE RECORD)
 *****************************************************/
frappe.ui.form.on("Student Enrollment", {
	refresh(frm) {
		// Do not show action buttons for unsaved records
		if (frm.is_new()) return;

		add_form_status_action_buttons(frm);
	},
});

/* --------------------------------------------------
   Form View → Actions → Status
-------------------------------------------------- */
function add_form_status_action_buttons(frm) {
	// Prevent duplicate buttons
	frm.clear_custom_buttons();

	const statuses = [
		{ label: __("Enrolled"), value: "Enrolled" },
		{ label: __("Dropped"), value: "Dropped" },
		{ label: __("Completed"), value: "Completed" },
		{ label: __("Pending"), value: "Pending" },
	];

	statuses.forEach((status) => {
		frm.add_custom_button(
			status.label,
			() => update_form_status(frm, status.value),
			__("Actions")
		);
	});
}

/* --------------------------------------------------
   Single record status update logic
-------------------------------------------------- */
function update_form_status(frm, status) {
	if (frm.doc.status === status) {
		frappe.msgprint({
			title: __("No Change"),
			message: __("Status is already <b>{0}</b>.", [status]),
			indicator: "blue",
		});
		return;
	}

	frappe.confirm(__("Are you sure you want to change status to <b>{0}</b>?", [status]), () => {
		frm.set_value("status", status);

		frm.save().then(() => {
			frappe.show_alert(
				{
					message: __("Status updated to {0}", [status]),
					indicator: "green",
				},
				5
			);
		});
	});
}
