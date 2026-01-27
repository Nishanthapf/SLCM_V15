// Copyright (c) 2026, CU and contributors
// For license information, please see license.txt

frappe.ui.form.on('Term Configuration', {
    refresh: function (frm) {
        // Add custom buttons
        if (!frm.is_new()) {
            frm.add_custom_button(__('Add All Programmes'), function () {
                add_all_programmes(frm);
            }, __('Actions'));

            frm.add_custom_button(__('Clear All'), function () {
                clear_all_programmes(frm);
            }, __('Actions'));
        }
    },

    starts: function (frm) {
        validate_dates(frm);
    },

    ends: function (frm) {
        validate_dates(frm);
    },

    academic_year: function (frm) {
        if (frm.doc.academic_year) {
            // Fetch academic year details
            frappe.db.get_value('Academic Year', frm.doc.academic_year, 'academic_system', (r) => {
                if (r && r.academic_system) {
                    frm.set_value('system', r.academic_system);
                }
            });
        }
    }
});

function validate_dates(frm) {
    if (frm.doc.starts && frm.doc.ends) {
        let start_date = frappe.datetime.str_to_obj(frm.doc.starts);
        let end_date = frappe.datetime.str_to_obj(frm.doc.ends);

        if (end_date <= start_date) {
            frappe.msgprint(__('End date must be after start date'));
            frm.set_value('ends', '');
        }
    }
}

function add_all_programmes(frm) {
    frappe.call({
        method: 'frappe.client.get_list',
        args: {
            doctype: 'Program',
            fields: ['name', 'program_name'],
            limit_page_length: 0
        },
        callback: function (r) {
            if (r.message) {
                r.message.forEach(function (program) {
                    let exists = frm.doc.programme_mapping.find(
                        row => row.programme === program.name
                    );

                    if (!exists) {
                        let row = frm.add_child('programme_mapping');
                        row.programme = program.name;
                    }
                });
                frm.refresh_field('programme_mapping');
                frappe.msgprint(__('All programmes added successfully'));
            }
        }
    });
}

function clear_all_programmes(frm) {
    frappe.confirm(
        __('Are you sure you want to clear all programme mappings?'),
        function () {
            frm.clear_table('programme_mapping');
            frm.refresh_field('programme_mapping');
            frappe.msgprint(__('All programme mappings cleared'));
        }
    );
}
