frappe.listview_settings["Hostel Allocation"] = {
    onload: function (listview) {
        listview.page.add_inner_button(__("Update Status"), function () {
            const checked_items = listview.get_checked_items();
            if (!checked_items.length) {
                frappe.msgprint(__("Please select at least one hostel allocation."));
                return;
            }

            let d = new frappe.ui.Dialog({
                title: "Update Allocation Status",
                fields: [
                    {
                        label: "Status",
                        fieldname: "status",
                        fieldtype: "Select",
                        options: "Allocated\nVacated\nDropped Out\nSuspended\nCancelled",
                        reqd: 1
                    }
                ],
                primary_action_label: "Update",
                primary_action(values) {
                    frappe.call({
                        method: "slcm.slcm.doctype.hostel_allocation.hostel_allocation.bulk_update_status",
                        args: {
                            names: checked_items.map((doc) => doc.name),
                            status: values.status,
                        },
                        callback: function (r) {
                            if (!r.exc) {
                                listview.refresh();
                                frappe.msgprint(__("Status updated successfully."));
                                d.hide();
                            }
                        },
                    });
                }
            });
            d.show();
        });
    },
};
