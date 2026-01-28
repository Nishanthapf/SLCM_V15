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
            // Redirect to new Class Schedule form with pre-filled date/time
            let schedule_date = null;
            let from_time = null;
            let to_time = null;

            // Extract date and time from the selection
            if (info.start) {
                schedule_date = frappe.datetime.obj_to_str(info.start);
                from_time = frappe.datetime.get_time(info.start);
            }

            if (info.end) {
                to_time = frappe.datetime.get_time(info.end);
            }

            // Get current filters to pre-populate fields
            let filters = cur_list.filter_area.get();
            let doc_fields = {
                schedule_date: schedule_date,
                from_time: from_time,
                to_time: to_time
            };

            // Parse filters and add them to the new doc
            if (filters && filters.length > 0) {
                filters.forEach(filter => {
                    // Filter format: [doctype, fieldname, operator, value, hidden]
                    if (filter.length >= 4 && filter[2] === "=") {
                        let fieldname = filter[1];
                        let value = filter[3];
                        doc_fields[fieldname] = value;
                    }
                });
            }

            // Open new Class Schedule form with pre-filled values
            frappe.new_doc("Class Schedule", doc_fields);
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
