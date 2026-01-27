# Copyright (c) 2026, CU and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import csv
from io import StringIO
from datetime import datetime, timedelta


@frappe.whitelist()
def get_class_list_template(department=None):
    """Generate CSV template for class list"""
    filters = {}
    if department:
        filters["department"] = department
    
    classes = frappe.get_all(
        "Class Configuration",
        filters=filters,
        fields=[
            "name as class_id",
            "course",
            "class_name",
            "department",
            "faculty",
        ],
        order_by="department, course",
    )
    
    # Get faculty details
    result = []
    for cls in classes:
        faculty_email = ""
        faculty_employee_id = ""
        
        if cls.faculty:
            faculty_doc = frappe.get_doc("Faculty", cls.faculty)
            faculty_email = faculty_doc.email if hasattr(faculty_doc, 'email') else ""
            faculty_employee_id = faculty_doc.employee_id if hasattr(faculty_doc, 'employee_id') else ""
        
        result.append({
            "Class ID": cls.class_id,
            "Course Name": cls.course,
            "Course Code": cls.course,
            "Class Name": cls.class_name,
            "Department Name": cls.department,
            "Faculty": faculty_email or cls.faculty,
        })
    
    return result


@frappe.whitelist()
def upload_timetable_csv(csv_data):
    """Upload timetable from CSV"""
    import json
    
    if isinstance(csv_data, str):
        csv_data = json.loads(csv_data)
    
    created = []
    errors = []
    
    for row in csv_data:
        try:
            # Parse the row data
            class_id = row.get("Class ID")
            faculty_email = row.get("Faculty Email")
            start_date = row.get("Start Date (dd/mm/yyyy)")
            start_time = row.get("Start Time (24 hr format)*")
            end_time = row.get("End Time (24 hr format)*")
            repeat_frequency = row.get("Repeat Frequency")
            repeats_till = row.get("Repeats Till (dd/mm/yyyy)")
            infrastructure_id = row.get("Infrastructure ID")
            
            # Validate required fields
            if not class_id or not start_date or not start_time or not end_time:
                errors.append(f"Missing required fields for row: {row}")
                continue
            
            # Get class configuration
            class_config = frappe.get_doc("Class Configuration", class_id)
            
            # Parse dates
            schedule_date = datetime.strptime(start_date, "%d/%m/%Y").strftime("%Y-%m-%d")
            
            # Parse times (handle both HH:MM and HH:MM:SS formats)
            try:
                from_time = datetime.strptime(start_time, "%H:%M").strftime("%H:%M:%S")
            except:
                from_time = start_time
            
            try:
                to_time = datetime.strptime(end_time, "%H:%M").strftime("%H:%M:%S")
            except:
                to_time = end_time
            
            # Parse repeats_till if provided
            repeats_till_date = None
            if repeats_till:
                repeats_till_date = datetime.strptime(repeats_till, "%d/%m/%Y").strftime("%Y-%m-%d")
            
            # Map repeat frequency
            repeat_map = {
                "Every Wednesday": "Weekly",
                "Everyday": "Daily",
                "Every day": "Daily",
                "Daily": "Daily",
                "Weekly": "Weekly",
            }
            repeat_freq = repeat_map.get(repeat_frequency, "Never")
            
            # Create schedule
            doc = frappe.get_doc({
                "doctype": "Class Schedule",
                "class_configuration": class_id,
                "course": class_config.course,
                "instructor": class_config.faculty,
                "term": class_config.term,
                "department": class_config.department,
                "programme": class_config.programme,
                "schedule_date": schedule_date,
                "from_time": from_time,
                "to_time": to_time,
                "room": infrastructure_id,
                "venue": infrastructure_id,
                "repeat_frequency": repeat_freq,
                "repeats_till": repeats_till_date,
            })
            
            doc.insert(ignore_permissions=True)
            
            # Create recurring schedules if needed
            if repeat_freq != "Never" and repeats_till_date:
                doc.create_recurring_schedules()
            
            created.append(doc.name)
            
        except Exception as e:
            errors.append(f"Error processing row {row}: {str(e)}")
    
    return {
        "success": len(created),
        "created": created,
        "errors": errors,
    }
