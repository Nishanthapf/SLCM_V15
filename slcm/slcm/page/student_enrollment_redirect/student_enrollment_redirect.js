frappe.pages["student-enrollment-redirect"].on_page_load = function (wrapper) {
	$(wrapper).html("<p style='padding:20px'>Redirecting to your enrollment…</p>");

	// STEP 1: Get Student Master linked to logged-in user
	frappe.call({
		method: "frappe.client.get_list",
		args: {
			doctype: "Student Master",
			filters: {
				user: frappe.session.user,
			},
			fields: ["name"],
			limit_page_length: 1,
		},
		callback: function (student_res) {
			if (!student_res.message || !student_res.message.length) {
				frappe.msgprint("Student profile not linked to this user.");
				return;
			}

			const student_name = student_res.message[0].name;

			// STEP 2: Get Student Enrollment using Student Master
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Student Enrollment",
					filters: {
						student: student_name,
					},
					fields: ["name"],
					limit_page_length: 1,
				},
				callback: function (enroll_res) {
					if (enroll_res.message && enroll_res.message.length) {
						frappe.set_route("Form", "Student Enrollment", enroll_res.message[0].name);
					} else {
						frappe.msgprint("No enrollment record found for this student.");
					}
				},
			});
		},
	});
};
