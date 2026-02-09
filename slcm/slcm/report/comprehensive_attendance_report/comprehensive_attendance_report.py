# Copyright (c) 2026, Nishanth and contributors
# For license information, please see license.txt

import frappe
import os

def execute(filters=None):
    if not filters:
        filters = {}
        
    # Ensure defaults for all filters to avoid KeyError in SQL
    filters.setdefault("department", None)
    filters.setdefault("program", None)
    filters.setdefault("batch", None)
    filters.setdefault("section", None)
    filters.setdefault("course", None)

    # Read the SQL file
    sql_file_path = os.path.join(os.path.dirname(__file__), "comprehensive_attendance_report.sql")
    with open(sql_file_path, "r") as f:
        sql_query = f.read()

    # Execute SQL
    data = frappe.db.sql(sql_query, filters, as_dict=True)
    
    # Define Columns explicitly
    columns = [
        {"fieldname": "S.No", "label": "S.No", "fieldtype": "Int", "width": 50},
        {"fieldname": "Student ID", "label": "Student ID", "fieldtype": "Link", "options": "Student Master", "width": 120},
        {"fieldname": "Student Name", "label": "Student Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "Section", "label": "Section", "fieldtype": "Data", "width": 80},
        {"fieldname": "Course Name", "label": "Course Name", "fieldtype": "Data", "width": 150},
        {"fieldname": "Applied for Condonation", "label": "Applied for Condonation", "fieldtype": "Data", "width": 120},
        {"fieldname": "Condonation Attachment", "label": "Condonation Attachment", "fieldtype": "Data", "width": 100},
        {"fieldname": "Condonation Status", "label": "Condonation Status", "fieldtype": "Data", "width": 100},
        {"fieldname": "Condonation Reason", "label": "Condonation Reason", "fieldtype": "Data", "width": 150},
        {"fieldname": "Condonation Remarks", "label": "Condonation Remarks", "fieldtype": "Data", "width": 150},
        {"fieldname": "Condonation Hours", "label": "Condonation Hours", "fieldtype": "Float", "width": 100},
        {"fieldname": "Applied for FA / MFA", "label": "Applied for FA / MFA", "fieldtype": "Data", "width": 120},
        {"fieldname": "FA / MFA Attachment", "label": "FA / MFA Attachment", "fieldtype": "Data", "width": 100},
        {"fieldname": "FA / MFA Status", "label": "FA / MFA Status", "fieldtype": "Data", "width": 100},
        {"fieldname": "FA / MFA Reason", "label": "FA / MFA Reason", "fieldtype": "Data", "width": 150},
        {"fieldname": "FA / MFA Remarks", "label": "FA / MFA Remarks", "fieldtype": "Data", "width": 150},
        {"fieldname": "FA / MFA Hours", "label": "FA / MFA Hours", "fieldtype": "Float", "width": 100},
        {"fieldname": "Total Classes Held", "label": "Total Classes Held", "fieldtype": "Float", "width": 100},
        {"fieldname": "Total Office Hours Held", "label": "Total Office Hours Held", "fieldtype": "Float", "width": 100},
        {"fieldname": "Total Hours", "label": "Total Hours", "fieldtype": "Float", "width": 100},
        {"fieldname": "Attendance Percentage Before", "label": "Attendance % Before", "fieldtype": "Percent", "width": 100},
        {"fieldname": "Hours Absent", "label": "Hours Absent", "fieldtype": "Float", "width": 100},
        {"fieldname": "Final Attended Hours", "label": "Final Attended Hours", "fieldtype": "Float", "width": 100},
        {"fieldname": "Attendance Percentage After", "label": "Attendance % After", "fieldtype": "Percent", "width": 100},
    ]

    return columns, data
