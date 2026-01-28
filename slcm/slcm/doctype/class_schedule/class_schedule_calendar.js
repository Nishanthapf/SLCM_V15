frappe.views.calendar["Class Schedule"] = {
    field_map: {
        start: "start",
        end: "end",
        id: "name",
        title: "title",
        allDay: "allDay",
        color: "color",
    },
    get_events_method: "slcm.slcm.doctype.class_schedule.class_schedule.get_events",
    options: {
        selectable: true,
        select: function (info) {
            // Auto-save on selection
            let args = {
                start: info.startStr,
                end: info.endStr,
                filters: cur_list.filter_area.get(),
            };

            frappe.call({
                method: "slcm.slcm.doctype.class_schedule.class_schedule.create_class_schedule_on_select",
                args: args,
                callback: function (r) {
                    if (!r.exc) {
                        frappe.show_alert({
                            message: __("Class Schedule Created"),
                            indicator: "green",
                        });
                        cur_list.refresh();
                    }
                },
            });
        },
    },
    onload: function (view) {
        view.page.add_inner_button(__("Event creation"), function () {
            frappe.new_doc("Class Schedule", {
                schedule_date: frappe.datetime.get_today(),
            });
        });
    },
};
