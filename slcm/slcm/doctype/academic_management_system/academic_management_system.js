// Copyright (c) 2026, Frappe Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on("Academic Management System", {
	refresh: function (frm) {
		frm.trigger("render_term_ui");
		frm.trigger("render_class_ui");
		frm.trigger("render_schedule_ui");
	},

	render_term_ui: function (frm) {
		const $wrapper = frm.get_field("term_ui_container").$wrapper;
		$wrapper.html("<p>Loading Terms...</p>");

		frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Academic Term",
				fields: [
					"name",
					"term_name",
					"academic_year",
					"term_start_date",
					"term_end_date",
					"system",
					"sequence",
					"previous_term",
				],
				order_by: "term_start_date desc",
			},
			callback: function (r) {
				const terms = r.message || [];
				let html = `
					<div class="row">
						<div class="col-xs-12 text-right">
							<button class="btn btn-primary btn-add-term">
								${frappe.utils.icon("add", "sm")} Add Term
							</button>
						</div>
					</div>
					<br>
					<table class="table table-bordered">
						<thead>
							<tr>
								<th>Name</th>
								<th>Academic Year</th>
								<th>Starts</th>
								<th>Ends</th>
								<th>System</th>
								<th>Sequence</th>
								<th>Previous Term</th>
							</tr>
						</thead>
						<tbody>
				`;

				if (terms.length === 0) {
					html += `<tr><td colspan="7" class="text-center">No Terms Found</td></tr>`;
				} else {
					terms.forEach((term) => {
						html += `
							<tr>
								<td><a href="/app/academic-term/${term.name}">${term.term_name}</a></td>
								<td>${term.academic_year}</td>
								<td>${frappe.datetime.str_to_user(term.term_start_date)}</td>
								<td>${frappe.datetime.str_to_user(term.term_end_date)}</td>
								<td>${term.system || ""}</td>
								<td>${term.sequence || ""}</td>
								<td>${term.previous_term || ""}</td>
							</tr>
						`;
					});
				}

				html += `</tbody></table>`;
				$wrapper.html(html);

				$wrapper.find(".btn-add-term").on("click", function () {
					frm.events.show_add_term_dialog(frm);
				});
			},
		});
	},

	show_add_term_dialog: function (frm) {
		const d = new frappe.ui.Dialog({
			title: "Create Term",
			fields: [
				{
					label: "Term Name",
					fieldname: "term_name",
					fieldtype: "Data",
					reqd: 1,
				},
				{
					label: "Academic Year",
					fieldname: "academic_year",
					fieldtype: "Link",
					options: "Academic Year",
					reqd: 1,
				},
				{
					fieldname: "col_break1",
					fieldtype: "Column Break",
				},
				{
					label: "Starts",
					fieldname: "term_start_date",
					fieldtype: "Date",
					reqd: 1,
				},
				{
					label: "Ends",
					fieldname: "term_end_date",
					fieldtype: "Date",
					reqd: 1,
				},
				{
					fieldname: "sec_break1",
					fieldtype: "Section Break",
				},
				{
					label: "System",
					fieldname: "system",
					fieldtype: "Select",
					options: "Semester\nTrimester\nQuarter\nYear",
					reqd: 1,
				},
				{
					label: "Sequence",
					fieldname: "sequence",
					fieldtype: "Int",
				},
				{
					fieldname: "col_break2",
					fieldtype: "Column Break",
				},
				{
					label: "Previous Term",
					fieldname: "previous_term",
					fieldtype: "Link",
					options: "Academic Term",
				},
			],
			primary_action_label: "Create",
			primary_action: function (values) {
				// Map system to term_type for compatibility
				values.term_type = values.system;

				frappe.call({
					method: "frappe.client.insert",
					args: {
						doc: {
							doctype: "Academic Term",
							...values,
						},
					},
					callback: function (r) {
						if (!r.exc) {
							frappe.msgprint("Term created successfully");
							d.hide();
							frm.trigger("render_term_ui");
						}
					},
				});
			},
		});
		d.show();
	},

	render_class_ui: function (frm) {
		const $wrapper = frm.get_field("class_ui_container").$wrapper;

		// Initialize storage for filter controls
		frm.class_filters = {};

		// Build Filter UI
		let filter_html = `
            <div class="row form-section">
                <div class="col-sm-3">
                    <div class="form-group">
                        <label class="control-label">Department</label>
                        <div data-fieldname="department"></div>
                    </div>
                </div>
                <div class="col-sm-9 text-right">
                    <div class="btn-group">
                        <button type="button" class="btn btn-primary dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                            ${frappe.utils.icon("add", "sm")} Add Class <span class="caret"></span>
                        </button>
                        <ul class="dropdown-menu dropdown-menu-right">
                            <li><a href="#" class="btn-add-single-class"> + Add Single Class</a></li>
                            <li><a href="#" class="btn-add-class-by-section"> + Add Class by Section</a></li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="row form-section" style="background-color: #f7fafc; padding: 10px; margin-bottom: 15px; border: 1px solid #d1d8dd;">
                <div class="col-sm-3">
                    <div data-filter="student_group"></div>
                </div>
                <div class="col-sm-2">
                    <div data-filter="class_type"></div>
                </div>
                <div class="col-sm-3">
                     <div data-filter="course"></div>
                </div>
                <div class="col-sm-2">
                     <div data-filter="academic_term"></div>
                </div>
                <div class="col-sm-2">
                     <div data-filter="faculty"></div>
                </div>
            </div>
            <div class="class-list-container"></div>
        `;

		$wrapper.html(filter_html);

		// Helper to create control
		const make_filter = (fieldname, fieldtype, options, placeholder, parent_selector) => {
			frm.class_filters[fieldname] = frappe.ui.form.make_control({
				parent: $wrapper.find(parent_selector),
				df: {
					fieldtype: fieldtype,
					options: options,
					fieldname: fieldname,
					placeholder: placeholder,
					change: function () {
						frm.events.load_classes(frm, $wrapper);
					},
				},
				render_input: true,
			});
		};

		// Bind Fields
		make_filter(
			"department",
			"Link",
			"Department",
			"Select Department",
			'[data-fieldname="department"]'
		);
		make_filter(
			"student_group",
			"Link",
			"Student Group",
			"Class (Search)",
			'[data-filter="student_group"]'
		);
		make_filter(
			"class_type",
			"Select",
			"All Types\nTheory\nPractical\nTutorial\nLab",
			"All Types",
			'[data-filter="class_type"]'
		);
		make_filter("course", "Link", "Course", "All Courses", '[data-filter="course"]');
		make_filter(
			"academic_term",
			"Link",
			"Academic Term",
			"Term",
			'[data-filter="academic_term"]'
		);
		make_filter("faculty", "Link", "Faculty", "Faculty", '[data-filter="faculty"]');

		// Initial Load
		frm.events.load_classes(frm, $wrapper);

		// Bind Actions
		$wrapper.find(".btn-add-single-class").on("click", function (e) {
			e.preventDefault();
			frm.events.show_add_single_class_dialog(frm);
		});

		$wrapper.find(".btn-add-class-by-section").on("click", function (e) {
			e.preventDefault();
			frm.events.show_add_bulk_class_dialog(frm);
		});
	},

	load_classes: function (frm, $wrapper) {
		const $container = $wrapper.find(".class-list-container");
		$container.html('<p class="text-muted">Loading...</p>');

		// Gather Filters safely from controls
		let filters = {};

		if (frm.class_filters) {
			filters.department = frm.class_filters.department.get_value();
			filters.search_text = frm.class_filters.student_group.get_value(); // student_group link
			filters.class_type = frm.class_filters.class_type.get_value();
			if (filters.class_type === "All Types") filters.class_type = "";

			filters.course = frm.class_filters.course.get_value();
			filters.academic_term = frm.class_filters.academic_term.get_value();
			filters.faculty = frm.class_filters.faculty.get_value();
		}

		frappe.call({
			method: "slcm.slcm.doctype.academic_management_system.academic_management_system.get_classes",
			args: { filters: filters },
			callback: function (r) {
				const classes = r.message || [];
				let html = `
                    <table class="table table-bordered table-hover">
                        <thead>
                            <tr style="background-color: #f0f4f7;">
                                <th>Class</th>
                                <th>Type</th>
                                <th>Course</th>
                                <th>Term</th>
                                <th>Faculty</th>
                                <th>Capacity</th>
                                <th>Section</th>
                            </tr>
                        </thead>
                        <tbody>
                `;

				if (classes.length === 0) {
					html += `<tr><td colspan="7" class="text-center text-muted">No Classes Found</td></tr>`;
				} else {
					classes.forEach((c) => {
						html += `
                            <tr>
                                <td><a href="/app/student-group/${c.name
							}" style="font-weight: bold;">${c.student_group_name}</a></td>
                                <td>${c.class_type || "-"}</td>
                                <td>${c.course || "-"}</td>
                                <td>${c.academic_term || "-"}</td>
                                <td>${c.faculty || "-"}</td>
                                <td>${c.max_strength || 0}</td>
                                <td>${c.section || "-"}</td>
                            </tr>
                        `;
					});
				}
				html += `</tbody></table>`;
				$container.html(html);
			},
		});
	},

	show_add_single_class_dialog: function (frm) {
		const d = new frappe.ui.Dialog({
			title: "Add Single Class",
			fields: [
				{
					label: "Department",
					fieldname: "department",
					fieldtype: "Link",
					options: "Department",
					reqd: 1,
				},
				{
					label: "Program",
					fieldname: "program",
					fieldtype: "Link",
					options: "Program",
					reqd: 1,
				},
				{
					label: "Academic Year",
					fieldname: "academic_year",
					fieldtype: "Link",
					options: "Academic Year",
					reqd: 1,
				},
				{
					label: "Term",
					fieldname: "academic_term",
					fieldtype: "Link",
					options: "Academic Term",
					reqd: 1,
				},
				{ fieldtype: "Column Break" },
				{
					label: "Course",
					fieldname: "course",
					fieldtype: "Link",
					options: "Course",
					reqd: 1,
				},
				{
					label: "Class Type",
					fieldname: "class_type",
					fieldtype: "Select",
					options: "Theory\nPractical\nTutorial\nLab",
					reqd: 1,
				},
				{ label: "Faculty", fieldname: "faculty", fieldtype: "Link", options: "Faculty" },
				{
					label: "Capacity",
					fieldname: "max_strength",
					fieldtype: "Int",
					default: 60,
					reqd: 1,
				},
				{
					label: "Section",
					fieldname: "section",
					fieldtype: "Link",
					options: "Program Batch Section",
					description: "Optional: Link to a specific batch section",
				},
				{
					label: "Name (Auto-generated if empty)",
					fieldname: "student_group_name",
					fieldtype: "Data",
				},
			],
			primary_action_label: "Create",
			primary_action: function (values) {
				if (!values.student_group_name) {
					values.student_group_name = `${values.course}-${values.class_type
						}-${frappe.datetime.now_date()}`; // Fallback, better to let server handle
				}

				frappe.call({
					method: "slcm.slcm.doctype.academic_management_system.academic_management_system.create_class",
					args: { data: values },
					callback: function (r) {
						if (!r.exc) {
							frappe.msgprint("Class Created Successfully");
							d.hide();
							// Refresh list
							frm.events.load_classes(
								frm,
								frm.get_field("class_ui_container").$wrapper
							);
						}
					},
				});
			},
		});
		d.show();
	},

	show_add_bulk_class_dialog: function (frm) {
		const d = new frappe.ui.Dialog({
			title: "Add Class by Section (Bulk)",
			fields: [
				{
					label: "Department",
					fieldname: "department",
					fieldtype: "Link",
					options: "Department",
					reqd: 1,
				},
				{
					label: "Program",
					fieldname: "program",
					fieldtype: "Link",
					options: "Program",
					reqd: 1,
				},
				{
					label: "Academic Year",
					fieldname: "academic_year",
					fieldtype: "Link",
					options: "Academic Year",
					reqd: 1,
				},
				{
					label: "Batch",
					fieldname: "batch",
					fieldtype: "Link",
					options: "Student Batch Name",
					reqd: 1,
				},
				{ fieldtype: "Section Break", label: "Configuration" },
				{
					label: "Term",
					fieldname: "academic_term",
					fieldtype: "Link",
					options: "Academic Term",
					reqd: 1,
				},
				{
					label: "Course",
					fieldname: "course",
					fieldtype: "Link",
					options: "Course",
					reqd: 1,
				},
				{
					label: "Class Type",
					fieldname: "class_type",
					fieldtype: "Select",
					options: "Theory\nPractical\nTutorial\nLab",
					reqd: 1,
				},
				{
					label: "Faculty",
					fieldname: "faculty",
					fieldtype: "Link",
					options: "Faculty",
					description: "Default faculty for all sections (can change later)",
				},
			],
			primary_action_label: "Bulk Create",
			primary_action: function (values) {
				frappe.call({
					method: "slcm.slcm.doctype.academic_management_system.academic_management_system.create_classes_by_section",
					args: values,
					callback: function (r) {
						if (!r.exc) {
							frappe.msgprint(r.message);
							d.hide();
							// Refresh list
							frm.events.load_classes(
								frm,
								frm.get_field("class_ui_container").$wrapper
							);
						}
					},
				});
			},
		});
		d.show();
	},

	render_schedule_ui: function (frm) {
		const $wrapper = frm.get_field("schedule_ui_container").$wrapper;

		// Simple placeholder for Timetable - better implemented with full calendar library later
		let html = `
			<div class="text-center">
				<p>To view the Class Schedule, please check the <a href="/app/course-schedule">Course Schedule</a> list or Calendar view.</p>
				<button class="btn btn-default btn-view-calendar">View Calendar</button>
			</div>
		`;
		$wrapper.html(html);

		$wrapper.find(".btn-view-calendar").on("click", function () {
			frappe.set_route("List", "Course Schedule", "Calendar");
		});
	},
});
