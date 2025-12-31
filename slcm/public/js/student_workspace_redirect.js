frappe.router.on("change", () => {
	// ---------------------------------
	// Student Enrollment → redirect to own record
	// ---------------------------------
	if (frappe.get_route()[0] === "List" && frappe.get_route()[1] === "Student Enrollment") {
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Student Enrollment",
				filters: {
					user: frappe.session.user,
				},
				limit_page_length: 1,
			},
			callback: function (r) {
				if (r.message && r.message.length) {
					frappe.set_route("Form", "Student Enrollment", r.message[0].name);
				}
			},
		});
	}

	// ---------------------------------
	// Student Master → redirect to own record
	// ---------------------------------
	if (frappe.get_route()[0] === "List" && frappe.get_route()[1] === "Student Master") {
		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Student Master",
				filters: {
					user: frappe.session.user,
				},
				limit_page_length: 1,
			},
			callback: function (r) {
				if (r.message && r.message.length) {
					frappe.set_route("Form", "Student Master", r.message[0].name);
				}
			},
		});
	}
});
