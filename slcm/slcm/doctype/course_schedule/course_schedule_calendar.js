frappe.views.calendar["Course Schedule"] = {
	field_map: {
		start: "start",
		end: "end",
		id: "name",
		title: "title",
		allDay: "allDay",
		color: "color",
	},
	get_events_method: "slcm.slcm.doctype.course_schedule.course_schedule.get_events",
};
