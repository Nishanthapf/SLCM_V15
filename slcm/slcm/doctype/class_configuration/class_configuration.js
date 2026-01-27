// Copyright (c) 2026, CU and contributors
// For license information, please see license.txt

frappe.ui.form.on('Class Configuration', {
    refresh: function (frm) {
        // Add custom buttons
        if (!frm.is_new()) {
            frm.add_custom_button(__('Add Students by Filter'), function () {
                add_students_by_filter(frm);
            }, __('Actions'));

            frm.add_custom_button(__('Clear All Students'), function () {
                clear_all_students(frm);
            }, __('Actions'));
        }

        // Set filters for links
        set_link_filters(frm);
    },

    programme: function (frm) {
        set_link_filters(frm);
    },

    batch: function (frm) {
        set_link_filters(frm);
    },

    section: function (frm) {
        set_link_filters(frm);
    },

    term: function (frm) {
        if (frm.doc.term) {
            // Fetch term details
            frappe.db.get_value('Term Configuration', frm.doc.term,
                ['academic_year', 'system'], (r) => {
                    if (r) {
                        frm.set_df_property('term', 'description',
                            `Academic Year: ${r.academic_year}, System: ${r.system}`);
                    }
                });
        }
    },

    course: function (frm) {
        if (frm.doc.course && !frm.doc.class_name) {
            // Auto-generate class name suggestion
            generate_class_name(frm);
        }
    },

    type: function (frm) {
        if (!frm.doc.class_name) {
            generate_class_name(frm);
        }
    }
});

frappe.ui.form.on('Class Student', {
    student: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.student) {
            // Fetch student details
            frappe.db.get_value('Student Master', row.student,
                ['student_name', 'registration_id', 'email_id'], (r) => {
                    if (r) {
                        frappe.model.set_value(cdt, cdn, 'student_name', r.student_name);
                        frappe.model.set_value(cdt, cdn, 'registration_id', r.registration_id);
                        frappe.model.set_value(cdt, cdn, 'email', r.email_id);
                    }
                });
        }
    }
});

function set_link_filters(frm) {
    // Set filter for students based on programme, batch, section
    if (frm.doc.programme || frm.doc.batch || frm.doc.section) {
        frm.set_query('student', 'students', function () {
            let filters = {};
            if (frm.doc.programme) {
                filters['program'] = frm.doc.programme;
            }
            if (frm.doc.batch) {
                filters['batch'] = frm.doc.batch;
            }
            if (frm.doc.section) {
                filters['section'] = frm.doc.section;
            }
            return { filters: filters };
        });
    }
}

function generate_class_name(frm) {
    let parts = [];
    if (frm.doc.course) {
        parts.push(frm.doc.course);
    }
    if (frm.doc.type) {
        parts.push(frm.doc.type);
    }
    if (frm.doc.batch) {
        parts.push(frm.doc.batch);
    }
    if (frm.doc.section) {
        parts.push(frm.doc.section);
    }

    if (parts.length > 0) {
        frm.set_value('class_name', parts.join(' - '));
    }
}

function add_students_by_filter(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Add Students by Filter'),
        fields: [
            {
                fieldname: 'programme',
                fieldtype: 'Link',
                label: __('Programme'),
                options: 'Program',
                default: frm.doc.programme
            },
            {
                fieldname: 'batch',
                fieldtype: 'Data',
                label: __('Batch'),
                default: frm.doc.batch
            },
            {
                fieldname: 'section',
                fieldtype: 'Data',
                label: __('Section'),
                default: frm.doc.section
            }
        ],
        primary_action_label: __('Add Students'),
        primary_action: function (values) {
            frappe.call({
                method: 'slcm.slcm.doctype.class_configuration.class_configuration.get_students_by_filter',
                args: {
                    programme: values.programme,
                    batch: values.batch,
                    section: values.section
                },
                callback: function (r) {
                    if (r.message && r.message.length > 0) {
                        r.message.forEach(function (student) {
                            // Check if student already exists
                            let exists = frm.doc.students.find(
                                row => row.student === student.name
                            );

                            if (!exists) {
                                let row = frm.add_child('students');
                                row.student = student.name;
                                row.student_name = student.student_name;
                                row.registration_id = student.registration_id;
                                row.email = student.email_id;
                            }
                        });
                        frm.refresh_field('students');
                        frappe.msgprint(__(`${r.message.length} students added successfully`));
                    } else {
                        frappe.msgprint(__('No students found with the given filters'));
                    }
                }
            });
            d.hide();
        }
    });
    d.show();
}

function clear_all_students(frm) {
    frappe.confirm(
        __('Are you sure you want to clear all students?'),
        function () {
            frm.clear_table('students');
            frm.refresh_field('students');
            frappe.msgprint(__('All students cleared'));
        }
    );
}
