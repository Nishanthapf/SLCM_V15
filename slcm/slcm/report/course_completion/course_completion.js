frappe.query_reports["Course Completion"] = {
    "filters": [
        {
            "fieldname": "academic_year",
            "label": __("Academic Year"),
            "fieldtype": "Link",
            "options": "Academic Year",
            "default": frappe.defaults.get_user_default("academic_year")
        },
        {
            "fieldname": "term",
            "label": __("Term"),
            "fieldtype": "Link",
            "options": "Term"
        }
    ]
};
