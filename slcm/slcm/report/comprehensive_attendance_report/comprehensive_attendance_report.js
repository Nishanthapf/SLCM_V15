// Copyright (c) 2026, Nishanth and contributors
// For license information, please see license.txt

frappe.query_reports["Comprehensive Attendance Report"] = {
    "filters": [
        {
            "fieldname": "department",
            "label": __("Department"),
            "fieldtype": "Link",
            "options": "Department",
            "reqd": 0
        },
        {
            "fieldname": "program",
            "label": __("Program"),
            "fieldtype": "Link",
            "options": "Cohort",
            "reqd": 0
        },
        {
            "fieldname": "section",
            "label": __("Section"),
            "fieldtype": "Link",
            "options": "Program Batch Section",
            "reqd": 0
        },
        {
            "fieldname": "course",
            "label": __("Course"),
            "fieldtype": "Link",
            "options": "Course",
            "reqd": 0
        }
    ]
};
