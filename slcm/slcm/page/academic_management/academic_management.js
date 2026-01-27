frappe.pages['academic-management'].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Academic Management - Term Configuration',
        single_column: true
    });

    new AcademicManagement(page);
}

class AcademicManagement {
    constructor(page) {
        this.page = page;
        this.current_tab = 'terms';
        this.setup_page();
    }

    setup_page() {
        this.setup_tabs();
        this.setup_actions();
        this.setup_content_area();
        this.load_terms();
    }

    setup_tabs() {
        // Create tab navigation
        this.page.add_inner_button('Class Schedule', () => {
            this.switch_tab('class_schedule');
        }, 'Tabs');

        this.page.add_inner_button('Class', () => {
            this.switch_tab('class');
        }, 'Tabs');

        this.page.add_inner_button('Terms', () => {
            this.switch_tab('terms');
        }, 'Tabs').addClass('btn-primary');
    }

    setup_actions() {
        // Add Term button
        this.page.set_primary_action('Add Term', () => {
            this.show_add_term_dialog();
        }, 'add');
    }

    setup_content_area() {
        this.page.main.html(`
            <div class="academic-management-container">
                <div class="terms-content" style="display: block;">
                    <div class="terms-table-container">
                        <table class="table table-bordered terms-table">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Academic Year</th>
                                    <th>Starts</th>
                                    <th>Ends</th>
                                    <th>Programme</th>
                                    <th>Next Term</th>
                                </tr>
                            </thead>
                            <tbody class="terms-tbody">
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="class-content" style="display: none;">
                    <div class="class-filters">
                        <div class="row">
                            <div class="col-md-3">
                                <label>Department</label>
                                <select class="form-control department-filter">
                                    <option>Select Department</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    <div class="class-table-container">
                        <table class="table table-bordered class-table">
                            <thead>
                                <tr>
                                    <th>Class</th>
                                    <th>All Types</th>
                                    <th>All Courses</th>
                                    <th>CollPoll Term - Even...</th>
                                    <th>Faculty</th>
                                    <th>Student</th>
                                </tr>
                            </thead>
                            <tbody class="class-tbody">
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="schedule-content" style="display: none;">
                    <p>Class Schedule content will be displayed here</p>
                </div>
            </div>
        `);
    }

    switch_tab(tab) {
        this.current_tab = tab;

        // Hide all content
        this.page.main.find('.terms-content, .class-content, .schedule-content').hide();

        // Clear existing action buttons
        this.page.clear_primary_action();
        this.page.clear_menu();

        // Show selected content
        if (tab === 'terms') {
            this.page.set_title('Academic Management - Term Configuration');
            this.page.main.find('.terms-content').show();
            this.page.set_primary_action('Add Term', () => {
                this.show_add_term_dialog();
            }, 'add');
            this.load_terms();
        } else if (tab === 'class') {
            this.page.set_title('Academic Management - Cohort/ClassGroup Configuration');
            this.page.main.find('.class-content').show();

            // Add Class dropdown button
            this.page.add_menu_item('Add Single Class', () => {
                this.show_add_class_dialog('single');
            });
            this.page.add_menu_item('Add Class by Section', () => {
                this.show_add_class_dialog('section');
            });

            this.page.set_primary_action('Add Class', null, 'add');
            this.load_classes();
            this.load_departments();
        } else if (tab === 'class_schedule') {
            this.page.set_title('Academic Management - Class Schedule');
            this.page.main.find('.schedule-content').show();
        }
    }

    load_terms() {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Term Configuration',
                fields: ['name', 'term_name', 'academic_year', 'starts', 'ends', 'previous_term'],
                limit_page_length: 100,
                order_by: 'starts desc'
            },
            callback: (r) => {
                if (r.message) {
                    this.render_terms(r.message);
                }
            }
        });
    }

    render_terms(terms) {
        const tbody = this.page.main.find('.terms-tbody');
        tbody.empty();

        if (terms.length === 0) {
            tbody.append(`
                <tr>
                    <td colspan="6" class="text-center text-muted">
                        No terms found. Click "Add Term" to create one.
                    </td>
                </tr>
            `);
            return;
        }

        terms.forEach(term => {
            // Get programme mappings for this term
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Term Configuration',
                    name: term.name
                },
                callback: (r) => {
                    if (r.message) {
                        const programmes = r.message.programme_mapping || [];
                        const programmeList = programmes.map(p =>
                            `${p.programme}${p.batch ? ' - ' + p.batch : ''}`
                        ).join(', ') || '-';

                        const row = $(`
                            <tr class="term-row" data-name="${term.name}" style="cursor: pointer;">
                                <td>${term.term_name || term.name}</td>
                                <td>${term.academic_year || '-'}</td>
                                <td>${frappe.datetime.str_to_user(term.starts) || '-'}</td>
                                <td>${frappe.datetime.str_to_user(term.ends) || '-'}</td>
                                <td>${programmeList}</td>
                                <td>${term.previous_term || '-'}</td>
                            </tr>
                        `);

                        row.on('click', () => {
                            frappe.set_route('Form', 'Term Configuration', term.name);
                        });

                        tbody.append(row);
                    }
                }
            });
        });
    }

    load_classes() {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Class Configuration',
                fields: ['name', 'class_name', 'type', 'course', 'term', 'faculty'],
                limit_page_length: 100
            },
            callback: (r) => {
                if (r.message) {
                    this.render_classes(r.message);
                }
            }
        });
    }

    render_classes(classes) {
        const tbody = this.page.main.find('.class-tbody');
        tbody.empty();

        if (classes.length === 0) {
            tbody.append(`
                <tr>
                    <td colspan="6" class="text-center text-muted">
                        No classes found.
                    </td>
                </tr>
            `);
            return;
        }

        classes.forEach(cls => {
            const row = $(`
                <tr class="class-row" data-name="${cls.name}" style="cursor: pointer;">
                    <td>${cls.class_name || cls.name}</td>
                    <td>${cls.type || '-'}</td>
                    <td>${cls.course || '-'}</td>
                    <td>${cls.term || '-'}</td>
                    <td>${cls.faculty || '-'}</td>
                    <td>0</td>
                </tr>
            `);

            row.on('click', () => {
                frappe.set_route('Form', 'Class Configuration', cls.name);
            });

            tbody.append(row);
        });
    }

    show_add_term_dialog() {
        const dialog = new frappe.ui.Dialog({
            title: __('Create Term'),
            fields: [
                {
                    fieldname: 'term_name',
                    fieldtype: 'Data',
                    label: __('Term Name'),
                    placeholder: 'Odd Semester 2022-2023',
                    reqd: 1
                },
                {
                    fieldname: 'academic_year',
                    fieldtype: 'Link',
                    label: __('Academic Year'),
                    options: 'Academic Year',
                    reqd: 1
                },
                {
                    fieldname: 'col_break_1',
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'sequence',
                    fieldtype: 'Int',
                    label: __('Sequence'),
                    default: 1
                },
                {
                    fieldname: 'sec_break_1',
                    fieldtype: 'Section Break'
                },
                {
                    fieldname: 'starts',
                    fieldtype: 'Date',
                    label: __('Starts'),
                    reqd: 1
                },
                {
                    fieldname: 'col_break_2',
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'ends',
                    fieldtype: 'Date',
                    label: __('Ends'),
                    reqd: 1
                },
                {
                    fieldname: 'sec_break_2',
                    fieldtype: 'Section Break'
                },
                {
                    fieldname: 'system',
                    fieldtype: 'Select',
                    label: __('System'),
                    options: ['Semester', 'Trimester', 'Quarter', 'Year'],
                    default: 'Semester',
                    reqd: 1
                },
                {
                    fieldname: 'previous_term',
                    fieldtype: 'Link',
                    label: __('Previous Term'),
                    options: 'Term Configuration'
                }
            ],
            primary_action_label: __('Create'),
            primary_action: (values) => {
                frappe.call({
                    method: 'frappe.client.insert',
                    args: {
                        doc: {
                            doctype: 'Term Configuration',
                            ...values
                        }
                    },
                    callback: (r) => {
                        if (r.message) {
                            frappe.show_alert({
                                message: __('Term created successfully'),
                                indicator: 'green'
                            });
                            dialog.hide();
                            this.load_terms();
                            // Open the new term
                            frappe.set_route('Form', 'Term Configuration', r.message.name);
                        }
                    }
                });
            }
        });

        dialog.show();
    }

    load_departments() {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Department',
                fields: ['name'],
                limit_page_length: 0
            },
            callback: (r) => {
                if (r.message) {
                    const select = this.page.main.find('.department-filter');
                    select.empty();
                    select.append('<option value="">Select Department</option>');
                    r.message.forEach(dept => {
                        select.append(`<option value="${dept.name}">${dept.name}</option>`);
                    });
                }
            }
        });
    }

    show_add_class_dialog(mode) {
        const dialog = new frappe.ui.Dialog({
            title: __(mode === 'single' ? 'Create Single Class' : 'Create Class by Section'),
            fields: [
                {
                    fieldname: 'class_name',
                    fieldtype: 'Data',
                    label: __('Class Name'),
                    placeholder: 'Physics-2022-Semester 1'
                },
                {
                    fieldname: 'term',
                    fieldtype: 'Link',
                    label: __('Term'),
                    options: 'Term Configuration',
                    reqd: 1
                },
                {
                    fieldname: 'col_break_1',
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'department',
                    fieldtype: 'Link',
                    label: __('Department'),
                    options: 'Department'
                },
                {
                    fieldname: 'sec_break_1',
                    fieldtype: 'Section Break'
                },
                {
                    fieldname: 'programme',
                    fieldtype: 'Link',
                    label: __('Programme'),
                    options: 'Program',
                    reqd: 1
                },
                {
                    fieldname: 'batch',
                    fieldtype: 'Data',
                    label: __('Batch')
                },
                {
                    fieldname: 'col_break_2',
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'section',
                    fieldtype: 'Data',
                    label: __('Section')
                },
                {
                    fieldname: 'sec_break_2',
                    fieldtype: 'Section Break',
                    label: __('Course Details')
                },
                {
                    fieldname: 'course',
                    fieldtype: 'Link',
                    label: __('Course'),
                    options: 'Course Master',
                    reqd: 1
                },
                {
                    fieldname: 'type',
                    fieldtype: 'Select',
                    label: __('Type'),
                    options: ['Theory', 'Practical', 'Lab', 'Tutorial'],
                    default: 'Theory',
                    reqd: 1
                },
                {
                    fieldname: 'col_break_3',
                    fieldtype: 'Column Break'
                },
                {
                    fieldname: 'faculty',
                    fieldtype: 'Link',
                    label: __('Faculty'),
                    options: 'Faculty'
                },
                {
                    fieldname: 'seat_limit',
                    fieldtype: 'Int',
                    label: __('Seat Limit')
                }
            ],
            primary_action_label: __('Create'),
            primary_action: (values) => {
                frappe.call({
                    method: 'frappe.client.insert',
                    args: {
                        doc: {
                            doctype: 'Class Configuration',
                            ...values
                        }
                    },
                    callback: (r) => {
                        if (r.message) {
                            frappe.show_alert({
                                message: __('Class created successfully'),
                                indicator: 'green'
                            });
                            dialog.hide();
                            this.load_classes();
                            // Open the new class
                            frappe.set_route('Form', 'Class Configuration', r.message.name);
                        }
                    }
                });
            }
        });

        dialog.show();
    }
}
