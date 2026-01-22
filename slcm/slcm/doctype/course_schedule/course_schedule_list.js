frappe.listview_settings["Course Schedule"] = {
	gantt: {
		field_map: {
			start: "schedule_date",
			end: "schedule_date",
			id: "name",
			title: "course",
			allDay: "all_day",
		},
		order_by: "schedule_date asc",
	},
};
