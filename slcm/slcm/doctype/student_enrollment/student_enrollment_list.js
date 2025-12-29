frappe.listview_settings["Student Enrollment"] = {
	onload(listview) {
		inject_enrollment_status_css();
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

		return [__(doc.status), "gray"];
	},
};

function inject_enrollment_status_css() {
	if (document.getElementById("enrollment-status-css")) {
		return;
	}

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
