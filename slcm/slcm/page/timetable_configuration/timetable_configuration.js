frappe.pages['timetable-configuration'].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: 'Timetable Configuration',
        single_column: true
    });

    new TimetableConfiguration(page);
};

class TimetableConfiguration {
    constructor(page) {
        this.page = page;
        this.wrapper = $(this.page.body);
        this.current_week_start = moment().startOf('week');
        this.filters = {
            term: null,
            department: null,
            course: null,
            type: null
        };

        this.setup();
    }

    setup() {
        this.setup_filters();
        this.setup_buttons();
        this.render_calendar();
        this.load_timetable_data();
    }

    setup_filters() {
        // Term Filter
        this.term_filter = frappe.ui.form.make_control({
            parent: this.wrapper.find('#term-filter'),
            df: {
                fieldtype: 'Link',
                options: 'Term Configuration',
                fieldname: 'term',
                placeholder: 'Select Term',
                change: () => {
                    this.filters.term = this.term_filter.get_value();
                    this.load_timetable_data();
                }
            },
            render_input: true
        });

        // Department Filter
        this.department_filter = frappe.ui.form.make_control({
            parent: this.wrapper.find('#department-filter'),
            df: {
                fieldtype: 'Link',
                options: 'Department',
                fieldname: 'department',
                placeholder: 'All Departments',
                change: () => {
                    this.filters.department = this.department_filter.get_value();
                    this.load_timetable_data();
                }
            },
            render_input: true
        });

        // Course Filter
        this.course_filter = frappe.ui.form.make_control({
            parent: this.wrapper.find('#course-filter'),
            df: {
                fieldtype: 'Link',
                options: 'Course Master',
                fieldname: 'course',
                placeholder: 'All Courses',
                change: () => {
                    this.filters.course = this.course_filter.get_value();
                    this.load_timetable_data();
                }
            },
            render_input: true
        });

        // Type Filter
        this.type_filter = frappe.ui.form.make_control({
            parent: this.wrapper.find('#type-filter'),
            df: {
                fieldtype: 'Select',
                options: '\nTheory\nPractical\nLab\nTutorial',
                fieldname: 'type',
                placeholder: 'All Types',
                change: () => {
                    this.filters.type = this.type_filter.get_value();
                    this.load_timetable_data();
                }
            },
            render_input: true
        });
    }

    setup_buttons() {
        // Add Class button
        this.wrapper.find('#btn-add-class').on('click', () => {
            this.show_add_class_dialog();
        });

        // Upload Timetable button
        this.wrapper.find('#btn-upload-timetable').on('click', () => {
            this.show_upload_dialog();
        });

        // Download Report button
        this.wrapper.find('#btn-download-report').on('click', () => {
            this.download_report();
        });

        // Week navigation
        this.wrapper.find('#btn-prev-week').on('click', () => {
            this.current_week_start.subtract(1, 'week');
            this.render_calendar();
            this.load_timetable_data();
        });

        this.wrapper.find('#btn-next-week').on('click', () => {
            this.current_week_start.add(1, 'week');
            this.render_calendar();
            this.load_timetable_data();
        });
    }

    render_calendar() {
        const week_end = moment(this.current_week_start).endOf('week');
        this.wrapper.find('#calendar-title').text(
            `${this.current_week_start.format('MMM D')} - ${week_end.format('D, YYYY')}`
        );

        // Create calendar grid
        let html = '<div class="calendar-grid">';

        // Header row
        html += '<div class="calendar-header-cell">Time</div>';
        for (let i = 0; i < 7; i++) {
            const day = moment(this.current_week_start).add(i, 'days');
            html += `<div class="calendar-header-cell">
                ${day.format('ddd D')}<br>
                <small>${day.format('MMM')}</small>
            </div>`;
        }

        // Time slots (8am to 6pm)
        const time_slots = [];
        for (let hour = 8; hour <= 18; hour++) {
            time_slots.push(`${hour.toString().padStart(2, '0')}:00`);
        }

        // Create grid cells
        for (let time of time_slots) {
            html += `<div class="calendar-time-cell">${time}</div>`;
            for (let i = 0; i < 7; i++) {
                const day = moment(this.current_week_start).add(i, 'days');
                html += `<div class="calendar-event-cell" data-date="${day.format('YYYY-MM-DD')}" data-time="${time}"></div>`;
            }
        }

        html += '</div>';
        this.wrapper.find('#timetable-calendar').html(html);
    }

    load_timetable_data() {
        const start_date = this.current_week_start.format('YYYY-MM-DD');
        const end_date = moment(this.current_week_start).endOf('week').format('YYYY-MM-DD');

        frappe.call({
            method: 'slcm.slcm.doctype.class_schedule.class_schedule.get_timetable_data',
            args: {
                term: this.filters.term,
                course: this.filters.course,
                department: this.filters.department,
                start_date: start_date,
                end_date: end_date
            },
            callback: (r) => {
                if (r.message) {
                    this.render_events(r.message);
                }
            }
        });
    }

    render_events(events) {
        // Clear existing events
        this.wrapper.find('.calendar-event-cell').empty();

        // Render each event
        events.forEach(event => {
            const date = event.start.split('T')[0];
            const time = event.start.split('T')[1].substring(0, 5);
            const cell = this.wrapper.find(`.calendar-event-cell[data-date="${date}"][data-time="${time}"]`);

            if (cell.length) {
                const event_html = `
                    <div class="calendar-event" data-id="${event.id}" style="background-color: ${event.backgroundColor}20; border-left-color: ${event.backgroundColor}">
                        <div class="calendar-event-title">${event.title}</div>
                        <div class="calendar-event-time">${time} - ${event.end.split('T')[1].substring(0, 5)}</div>
                        ${event.extendedProps.instructor ? `<div class="calendar-event-instructor">${event.extendedProps.instructor}</div>` : ''}
                        ${event.extendedProps.room ? `<div class="calendar-event-instructor">${event.extendedProps.room}</div>` : ''}
                    </div>
                `;
                cell.append(event_html);
            }
        });

        // Add click handlers
        this.wrapper.find('.calendar-event').on('click', (e) => {
            const schedule_id = $(e.currentTarget).data('id');
            frappe.set_route('Form', 'Class Schedule', schedule_id);
        });
    }

    show_add_class_dialog() {
        const dialog = new frappe.ui.Dialog({
            title: __('Add New Class'),
            fields: [
                {
                    fieldtype: 'Link',
                    label: __('Class/Section'),
                    fieldname: 'class_configuration',
                    options: 'Class Configuration',
                    reqd: 1,
                    onchange: function () {
                        const class_config = this.get_value();
                        if (class_config) {
                            frappe.db.get_value('Class Configuration', class_config,
                                ['course', 'faculty', 'term', 'department', 'programme'], (r) => {
                                    if (r) {
                                        dialog.set_value('course', r.course);
                                        dialog.set_value('instructor', r.faculty);
                                        dialog.set_value('term', r.term);
                                        dialog.set_value('department', r.department);
                                        dialog.set_value('programme', r.programme);
                                    }
                                });
                        }
                    }
                },
                {
                    fieldtype: 'Link',
                    label: __('Course'),
                    fieldname: 'course',
                    options: 'Course Master',
                    reqd: 1
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldtype: 'Link',
                    label: __('Faculty Member'),
                    fieldname: 'instructor',
                    options: 'Faculty',
                    reqd: 1
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'Date',
                    label: __('Date'),
                    fieldname: 'schedule_date',
                    reqd: 1,
                    default: frappe.datetime.get_today()
                },
                {
                    fieldtype: 'Time',
                    label: __('Start Time'),
                    fieldname: 'from_time',
                    reqd: 1
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldtype: 'Time',
                    label: __('End Time'),
                    fieldname: 'to_time',
                    reqd: 1
                },
                {
                    fieldtype: 'Data',
                    label: __('Venue'),
                    fieldname: 'venue'
                },
                {
                    fieldtype: 'Section Break',
                    label: __('Repeat Settings')
                },
                {
                    fieldtype: 'Select',
                    label: __('Repeat'),
                    fieldname: 'repeat_frequency',
                    options: 'Never\nDaily\nWeekly',
                    default: 'Never',
                    onchange: function () {
                        const repeat = this.get_value();
                        dialog.fields_dict.repeats_till.df.hidden = (repeat === 'Never');
                        dialog.fields_dict.repeats_till.refresh();

                        if (repeat === 'Weekly') {
                            dialog.fields_dict.weekly_days.df.hidden = 0;
                        } else {
                            dialog.fields_dict.weekly_days.df.hidden = 1;
                        }
                        dialog.fields_dict.weekly_days.refresh();
                    }
                },
                {
                    fieldtype: 'Column Break'
                },
                {
                    fieldtype: 'Date',
                    label: __('Repeats Till'),
                    fieldname: 'repeats_till',
                    hidden: 1
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'HTML',
                    fieldname: 'weekly_days',
                    hidden: 1,
                    options: `
                        <div style="margin: 10px 0;">
                            <label>Select Days</label>
                            <div class="btn-group" role="group" id="weekly-days-selector">
                                <button type="button" class="btn btn-default btn-sm" data-day="0">S</button>
                                <button type="button" class="btn btn-default btn-sm" data-day="1">M</button>
                                <button type="button" class="btn btn-default btn-sm" data-day="2">T</button>
                                <button type="button" class="btn btn-default btn-sm" data-day="3">W</button>
                                <button type="button" class="btn btn-default btn-sm" data-day="4">T</button>
                                <button type="button" class="btn btn-default btn-sm" data-day="5">F</button>
                                <button type="button" class="btn btn-default btn-sm" data-day="6">S</button>
                            </div>
                        </div>
                    `
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'term',
                    hidden: 1
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'department',
                    hidden: 1
                },
                {
                    fieldtype: 'Data',
                    fieldname: 'programme',
                    hidden: 1
                }
            ],
            primary_action_label: __('Create'),
            primary_action: (values) => {
                frappe.call({
                    method: 'slcm.slcm.doctype.class_schedule.class_schedule.create_class_schedule',
                    args: { data: values },
                    callback: (r) => {
                        if (r.message) {
                            frappe.show_alert({
                                message: __('Class Schedule created successfully'),
                                indicator: 'green'
                            });
                            dialog.hide();
                            this.load_timetable_data();
                        }
                    }
                });
            }
        });

        dialog.show();

        // Setup weekly days selector
        setTimeout(() => {
            dialog.$wrapper.find('#weekly-days-selector button').on('click', function () {
                $(this).toggleClass('btn-primary');
            });
        }, 500);
    }

    show_upload_dialog() {
        const upload_dialog = new frappe.ui.Dialog({
            title: __('Upload Timetable'),
            fields: [
                {
                    fieldtype: 'HTML',
                    options: `
                        <div class="upload-instructions">
                            <p><strong>Note:</strong></p>
                            <ol>
                                <li>Mandatory fields are Class Id, Faculty Email or Faculty Employee Id, Start Date, Start Time, End Time</li>
                                <li>Download the following CSVs to make the timetable setup easier:</li>
                            </ol>
                        </div>
                    `
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'Link',
                    label: __('Department'),
                    fieldname: 'department',
                    options: 'Department'
                },
                {
                    fieldtype: 'Button',
                    label: __('Download Class List'),
                    fieldname: 'download_class_list',
                    click: () => {
                        const dept = upload_dialog.get_value('department');
                        this.download_class_list(dept);
                    }
                },
                {
                    fieldtype: 'Section Break'
                },
                {
                    fieldtype: 'Attach',
                    label: __('Upload CSV'),
                    fieldname: 'csv_file',
                    reqd: 1
                },
                {
                    fieldtype: 'HTML',
                    options: `
                        <div style="margin-top: 10px;">
                            <p><strong>Not sure how to get started?</strong></p>
                            <p><a href="#" id="download-csv-template">Download the CSV template</a>, edit and then upload</p>
                        </div>
                    `
                }
            ],
            primary_action_label: __('Upload'),
            primary_action: (values) => {
                if (!values.csv_file) {
                    frappe.msgprint(__('Please select a CSV file'));
                    return;
                }

                // Parse CSV and upload
                this.process_csv_upload(values.csv_file);
                upload_dialog.hide();
            }
        });

        upload_dialog.show();

        // Setup template download
        setTimeout(() => {
            upload_dialog.$wrapper.find('#download-csv-template').on('click', (e) => {
                e.preventDefault();
                this.download_csv_template();
            });
        }, 500);
    }

    download_class_list(department) {
        frappe.call({
            method: 'slcm.slcm.page.timetable_configuration.timetable_configuration.get_class_list_template',
            args: { department: department },
            callback: (r) => {
                if (r.message) {
                    this.export_to_csv(r.message, 'class_list.csv');
                }
            }
        });
    }

    download_csv_template() {
        const template_data = [
            {
                'Class ID': '',
                'Faculty Email': '',
                'Faculty Employee ID': '',
                'Infrastructure ID': '',
                'Start Date (dd/mm/yyyy)': '',
                'Start Time (24 hr format)*': '',
                'End Time (24 hr format)*': '',
                'Repeat Frequency': '',
                'Repeats Till (dd/mm/yyyy)': ''
            }
        ];
        this.export_to_csv(template_data, 'timetable_template.csv');
    }

    process_csv_upload(file_url) {
        // Read the CSV file
        frappe.call({
            method: 'frappe.client.get_file',
            args: { file_url: file_url },
            callback: (r) => {
                if (r.message) {
                    const csv_data = this.parse_csv(r.message);

                    frappe.call({
                        method: 'slcm.slcm.page.timetable_configuration.timetable_configuration.upload_timetable_csv',
                        args: { csv_data: csv_data },
                        callback: (r) => {
                            if (r.message) {
                                frappe.msgprint({
                                    title: __('Upload Complete'),
                                    message: `Successfully created ${r.message.success} schedules.<br>
                                             ${r.message.errors.length > 0 ? 'Errors: ' + r.message.errors.join('<br>') : ''}`,
                                    indicator: 'green'
                                });
                                this.load_timetable_data();
                            }
                        }
                    });
                }
            }
        });
    }

    parse_csv(csv_text) {
        const lines = csv_text.split('\n');
        const headers = lines[0].split(',').map(h => h.trim());
        const data = [];

        for (let i = 1; i < lines.length; i++) {
            if (lines[i].trim()) {
                const values = lines[i].split(',').map(v => v.trim());
                const row = {};
                headers.forEach((header, index) => {
                    row[header] = values[index] || '';
                });
                data.push(row);
            }
        }

        return data;
    }

    export_to_csv(data, filename) {
        if (!data || data.length === 0) {
            frappe.msgprint(__('No data to export'));
            return;
        }

        const headers = Object.keys(data[0]);
        let csv = headers.join(',') + '\n';

        data.forEach(row => {
            csv += headers.map(header => row[header] || '').join(',') + '\n';
        });

        // Download
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    }

    download_report() {
        frappe.msgprint(__('Downloading report...'));
        // This would generate a report of the current timetable
        const start_date = this.current_week_start.format('YYYY-MM-DD');
        const end_date = moment(this.current_week_start).endOf('week').format('YYYY-MM-DD');

        window.open(`/api/method/frappe.desk.reportview.export_query?
            doctype=Class Schedule&
            file_format_type=Excel&
            filters=[["schedule_date","between",["${start_date}","${end_date}"]]]`
        );
    }
}
