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
    update_event_method: "slcm.slcm.doctype.class_schedule.class_schedule.update_event",
    options: {
        editable: true,
        select: function (startDate, endDate, jsEvent, view) {
            // Prevent single day click in month view
            if (view.name === "month" && endDate - startDate === 86400000) {
                return;
            }

            // Create new Class Schedule document
            var new_doc = frappe.model.get_new_doc("Class Schedule");

            // Extract date and time from startDate
            var start_moment = moment(startDate);
            new_doc.schedule_date = start_moment.format("YYYY-MM-DD");
            new_doc.from_time = start_moment.format("HH:mm:ss");

            // Extract end time from endDate
            if (endDate) {
                var end_moment = moment(endDate);
                new_doc.to_time = end_moment.format("HH:mm:ss");
            }

            // Navigate to the new form
            frappe.set_route("Form", "Class Schedule", new_doc.name);
        }
    },
};