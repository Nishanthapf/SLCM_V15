// Copyright (c) 2026, CU and contributors
// For license information, please see license.txt

frappe.ui.form.on('Academic Management', {
    refresh: function (frm) {
        frm.trigger('render_terms_ui');
        frm.trigger('render_class_ui');
    },

    render_terms_ui: function (frm) {
        const $wrapper = frm.get_field('terms_ui_container').$wrapper;
        $wrapper.html('<p>Loading Terms...</p>');

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Term Configuration',
                fields: ['name', 'term_name', 'academic_year', 'starts', 'ends', 'system', 'sequence'],
                limit_page_length: 100,
                order_by: 'starts desc'
            },
            callback: function (r) {
                const terms = r.message || [];
                let html = `
                    <div class="row" style="margin-bottom: 15px;">
                        <div class="col-xs-12 text-right">
                            <button class="btn btn-primary btn-add-term">
                                ${frappe.utils.icon('add', 'sm')} Add Term
                            </button>
                        </div>
                    </div>
                    <table class="table table-bordered">
                        <thead style="background-color: #f5f7fa;">
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

                if (terms.length === 0) {
                    html += '<tr><td colspan="6" class="text-center text-muted">No Terms Found</td></tr>';
                } else {
                    terms.forEach(term => {
                        html += `
                            <tr style="cursor: pointer;" class="term-row" data-name="${term.name}">
                                <td>${term.term_name || term.name}</td>
                                <td>${term.academic_year || '-'}</td>
                                <td>${frappe.datetime.str_to_user(term.starts) || '-'}</td>
                                <td>${frappe.datetime.str_to_user(term.ends) || '-'}</td>
                                <td>${term.system || '-'}</td>
                                <td>${term.sequence || '-'}</td>
                            </tr>
                        `;
                    });
                }

                html += '</tbody></table>';
                $wrapper.html(html);

                // Bind events
                $wrapper.find('.btn-add-term').on('click', function () {
                    frappe.set_route('Form', 'Term Configuration', 'new-term-configuration');
                });

                $wrapper.find('.term-row').on('click', function () {
                    const name = $(this).data('name');
                    frappe.set_route('Form', 'Term Configuration', name);
                });
            }
        });
    },

    render_class_ui: function (frm) {
        const $wrapper = frm.get_field('class_ui_container').$wrapper;
        $wrapper.html('<p>Loading Classes...</p>');

        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Class Configuration',
                fields: ['name', 'class_name', 'term', 'programme', 'course', 'type', 'faculty'],
                limit_page_length: 100,
                order_by: 'creation desc'
            },
            callback: function (r) {
                const classes = r.message || [];
                let html = `
                    <div class="row" style="margin-bottom: 15px;">
                        <div class="col-xs-12 text-right">
                            <button class="btn btn-primary btn-add-class">
                                ${frappe.utils.icon('add', 'sm')} Add Class
                            </button>
                        </div>
                    </div>
                    <table class="table table-bordered">
                        <thead style="background-color: #f5f7fa;">
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

<<<<<<< HEAD
                if (classes.length === 0) {
                    html += '<tr><td colspan="6" class="text-center text-muted">No Classes Found</td></tr>';
                } else {
                    classes.forEach(cls => {
                        html += `
                            <tr style="cursor: pointer;" class="class-row" data-name="${cls.name}">
                                <td>${cls.class_name || cls.name}</td>
                                <td>${cls.term || '-'}</td>
                                <td>${cls.programme || '-'}</td>
                                <td>${cls.course || '-'}</td>
                                <td>${cls.type || '-'}</td>
                                <td>${cls.faculty || '-'}</td>
                            </tr>
                        `;
                    });
                }

                html += '</tbody></table>';
                $wrapper.html(html);

                // Bind events
                $wrapper.find('.btn-add-class').on('click', function () {
                    frappe.set_route('Form', 'Class Configuration', 'new-class-configuration');
                });

                $wrapper.find('.class-row').on('click', function () {
                    const name = $(this).data('name');
                    frappe.set_route('Form', 'Class Configuration', name);
                });
            }
        });
    }
=======
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
					method: "slcm.slcm.doctype.academic_management.academic_management.create_class",
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
					method: "slcm.slcm.doctype.academic_management.academic_management.create_classes_by_section",
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
>>>>>>> a41b150a68506b5abfbd7c3aa213eb09f140fe4d
});
