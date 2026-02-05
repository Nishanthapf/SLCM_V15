// Copyright (c) 2026, CU and contributors
// For license information, please see license.txt

frappe.ui.form.on('Class Schedule', {
    refresh: function (frm) {
        // Auto-generate title if not set
        if (!frm.doc.title && frm.doc.course) {
            frm.trigger('generate_title');
        }

        if (!frm.is_new()) {
            frm.add_custom_button(__('Mark Attendance'), function () {
                frappe.route_options = {
                    'based_on': 'Student Group',
                    'student_group': frm.doc.student_group,
                    'date': frm.doc.schedule_date
                };
                frappe.set_route('Form', 'Student Attendance Tool');
            });
        }
    },

    class_configuration: function (frm) {
        if (frm.doc.class_configuration) {
            // Fetch details from Class Configuration
            frappe.db.get_value('Class Configuration', frm.doc.class_configuration,
                ['course', 'faculty', 'programme', 'term', 'department'], (r) => {
                    if (r) {
                        frm.set_value('course', r.course);
                        frm.set_value('instructor', r.faculty);
                        frm.set_value('programme', r.programme);
                        frm.set_value('term', r.term);
                        frm.set_value('department', r.department);
                    }
                });
        }
    },

    course: function (frm) {
        frm.trigger('generate_title');
    },

    class_schedule_color: function (frm) {
        // Map color name to hex color
        const colorMap = {
            'Blue': '#3498db',
            'Green': '#2ecc71',
            'Red': '#e74c3c',
            'Yellow': '#f39c12',
            'Orange': '#e67e22',
            'Purple': '#9b59b6',
            'Pink': '#e91e63',
            'Gray': '#95a5a6'
        };

        if (frm.doc.class_schedule_color && colorMap[frm.doc.class_schedule_color]) {
            frm.set_value('color', colorMap[frm.doc.class_schedule_color]);
        }
    },

    generate_title: function (frm) {
        if (frm.doc.course) {
            let title = frm.doc.course;
            if (frm.doc.room) {
                title += ' - ' + frm.doc.room;
            }
            frm.set_value('title', title);
        }
    },

    repeat_frequency: function (frm) {
        if (frm.doc.repeat_frequency === 'Never' || !frm.doc.repeat_frequency) {
            frm.set_value('repeats_till', null);
        }
    },

    validate: function (frm) {
        // Validate repeat settings
        if (frm.doc.repeat_frequency && frm.doc.repeat_frequency !== 'Never') {
            if (!frm.doc.repeats_till) {
                frappe.msgprint(__('Please specify "Repeats Till" date for recurring schedules'));
                frappe.validated = false;
            }
            if (frm.doc.repeats_till && frm.doc.repeats_till < frm.doc.schedule_date) {
                frappe.msgprint(__('Repeats Till date cannot be before Schedule Date'));
                frappe.validated = false;
            }
        }

        // Validate time
        if (frm.doc.from_time && frm.doc.to_time && frm.doc.from_time >= frm.doc.to_time) {
            frappe.msgprint(__('To Time must be after From Time'));
            frappe.validated = false;
        }
    }
});
