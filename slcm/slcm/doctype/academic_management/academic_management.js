// Copyright (c) 2026, CU and contributors
// For license information, please see license.txt

frappe.ui.form.on("Academic Management", {
	refresh(frm) {
		frm.trigger("render_terms_ui");
		frm.trigger("render_class_ui");
	},

	/* --------------------------------------------------------------------------
	 * TERMS UI
	 * -------------------------------------------------------------------------- */
	render_terms_ui(frm) {
		const $wrapper = frm.get_field("terms_ui_container").$wrapper;
		$wrapper.html("<p>Loading Terms...</p>");

		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Term Configuration",
				fields: [
					"name",
					"term_name",
					"academic_year",
					"starts",
					"ends",
					"system",
					"sequence",
				],
				limit_page_length: 100,
				order_by: "starts desc",
			},
			callback(r) {
				const terms = r.message || [];

				let html = `
					<div class="row" style="margin-bottom:15px;">
						<div class="col-xs-12 text-right">
							<button class="btn btn-primary btn-add-term">
								${frappe.utils.icon("add", "sm")} Add Term
							</button>
						</div>
					</div>

					<table class="table table-bordered">
						<thead style="background:#f5f7fa;">
							<tr>
								<th>Term Name</th>
								<th>Academic Year</th>
								<th>Starts</th>
								<th>Ends</th>
								<th>System</th>
								<th>Sequence</th>
							</tr>
						</thead>
						<tbody>
				`;

				if (!terms.length) {
					html += `
						<tr>
							<td colspan="6" class="text-center text-muted">
								No Terms Found
							</td>
						</tr>
					`;
				} else {
					terms.forEach((t) => {
						html += `
							<tr class="term-row" data-name="${t.name}" style="cursor:pointer;">
								<td>${t.term_name || t.name}</td>
								<td>${t.academic_year || "-"}</td>
								<td>${t.starts ? frappe.datetime.str_to_user(t.starts) : "-"}</td>
								<td>${t.ends ? frappe.datetime.str_to_user(t.ends) : "-"}</td>
								<td>${t.system || "-"}</td>
								<td>${t.sequence || "-"}</td>
							</tr>
						`;
					});
				}

				html += `</tbody></table>`;
				$wrapper.html(html);

				$wrapper.find(".btn-add-term").on("click", () => {
					frappe.set_route("Form", "Term Configuration", "new-term-configuration");
				});

				$wrapper.find(".term-row").on("click", function () {
					frappe.set_route(
						"Form",
						"Term Configuration",
						$(this).data("name")
					);
				});
			},
		});
	},

	/* --------------------------------------------------------------------------
	 * CLASS UI
	 * -------------------------------------------------------------------------- */
	render_class_ui(frm) {
		const $wrapper = frm.get_field("class_ui_container").$wrapper;
		$wrapper.html("<p>Loading Classes...</p>");

		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Class Configuration",
				fields: [
					"name",
					"class_name",
					"term",
					"programme",
					"course",
					"type",
					"faculty",
				],
				limit_page_length: 100,
				order_by: "creation desc",
			},
			callback(r) {
				const classes = r.message || [];

				let html = `
					<div class="row" style="margin-bottom:15px;">
						<div class="col-xs-12 text-right">
							<button class="btn btn-primary btn-add-class">
								${frappe.utils.icon("add", "sm")} Add Class
							</button>
						</div>
					</div>

					<table class="table table-bordered">
						<thead style="background:#f5f7fa;">
							<tr>
								<th>Class Name</th>
								<th>Term</th>
								<th>Programme</th>
								<th>Course</th>
								<th>Type</th>
								<th>Faculty</th>
							</tr>
						</thead>
						<tbody>
				`;

				if (!classes.length) {
					html += `
						<tr>
							<td colspan="6" class="text-center text-muted">
								No Classes Found
							</td>
						</tr>
					`;
				} else {
					classes.forEach((c) => {
						html += `
							<tr class="class-row" data-name="${c.name}" style="cursor:pointer;">
								<td>${c.class_name || c.name}</td>
								<td>${c.term || "-"}</td>
								<td>${c.programme || "-"}</td>
								<td>${c.course || "-"}</td>
								<td>${c.type || "-"}</td>
								<td>${c.faculty || "-"}</td>
							</tr>
						`;
					});
				}

				html += `</tbody></table>`;
				$wrapper.html(html);

				$wrapper.find(".btn-add-class").on("click", () => {
					frappe.set_route("Form", "Class Configuration", "new-class-configuration");
				});

				$wrapper.find(".class-row").on("click", function () {
					frappe.set_route(
						"Form",
						"Class Configuration",
						$(this).data("name")
					);
				});
			},
		});
	},

	/* --------------------------------------------------------------------------
	 * SCHEDULE UI
	 * -------------------------------------------------------------------------- */
	render_schedule_ui(frm) {
		const $wrapper = frm.get_field("schedule_ui_container").$wrapper;

		const html = `
			<div class="text-center">
				<p>
					To view the Class Schedule, please check the
					<a href="/app/course-schedule">Course Schedule</a>
					list or Calendar view.
				</p>
				<button class="btn btn-default btn-view-calendar">
					View Calendar
				</button>
			</div>
		`;

		$wrapper.html(html);

		$wrapper.find(".btn-view-calendar").on("click", () => {
			frappe.set_route("List", "Course Schedule", "Calendar");
		});
	},
});
