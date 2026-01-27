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
};
