# Copyright (c) 2026, CU and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta


class ClassSchedule(Document):
    def validate(self):
        """Validate the Class Schedule"""
        self.validate_time()
        self.validate_repeat_settings()
        self.check_conflicts()

    def validate_time(self):
        """Validate that to_time is after from_time"""
        if self.from_time and self.to_time:
            if self.from_time >= self.to_time:
                frappe.throw("To Time must be after From Time")

    def validate_repeat_settings(self):
        """Validate repeat frequency and repeats_till"""
        if self.repeat_frequency and self.repeat_frequency != "Never":
            if not self.repeats_till:
                frappe.throw("Please specify 'Repeats Till' date for recurring schedules")
            if self.repeats_till < self.schedule_date:
                frappe.throw("Repeats Till date cannot be before Schedule Date")

    def check_conflicts(self):
        """Check for scheduling conflicts"""
        if not self.instructor or not self.schedule_date or not self.from_time or not self.to_time:
            return

        # Check if instructor has another class at the same time
        conflicts = frappe.get_all(
            "Class Schedule",
            filters={
                "name": ["!=", self.name],
                "instructor": self.instructor,
                "schedule_date": self.schedule_date,
            },
            fields=["name", "from_time", "to_time", "course"],
        )

        for conflict in conflicts:
            # Check if times overlap
            if self.times_overlap(
                self.from_time, self.to_time, conflict.from_time, conflict.to_time
            ):
                frappe.msgprint(
                    f"Warning: Instructor {self.instructor} has another class ({conflict.course}) "
                    f"from {conflict.from_time} to {conflict.to_time} on {self.schedule_date}",
                    indicator="orange",
                    alert=True,
                )

    def times_overlap(self, start1, end1, start2, end2):
        """Check if two time ranges overlap"""
        return start1 < end2 and end1 > start2

    def on_submit(self):
        """Create recurring schedules if repeat is enabled"""
        if self.repeat_frequency and self.repeat_frequency != "Never":
            self.create_recurring_schedules()

    def create_recurring_schedules(self):
        """Create recurring class schedules based on repeat frequency"""
        if not self.repeats_till:
            return

        current_date = datetime.strptime(str(self.schedule_date), "%Y-%m-%d")
        end_date = datetime.strptime(str(self.repeats_till), "%Y-%m-%d")

        # Determine increment based on frequency
        if self.repeat_frequency == "Daily":
            increment = timedelta(days=1)
        elif self.repeat_frequency == "Weekly":
            increment = timedelta(weeks=1)
        else:
            return

        # Create schedules
        current_date += increment  # Skip the first date (already created)
        created_count = 0

        while current_date <= end_date:
            # Create a new schedule
            new_schedule = frappe.copy_doc(self)
            new_schedule.schedule_date = current_date.strftime("%Y-%m-%d")
            new_schedule.parent_schedule = self.name
            new_schedule.repeat_frequency = "Never"  # Don't repeat the child schedules
            new_schedule.repeats_till = None
            new_schedule.insert(ignore_permissions=True)
            created_count += 1

            current_date += increment

        if created_count > 0:
            frappe.msgprint(
                f"Created {created_count} recurring class schedule(s)",
                indicator="green",
                alert=True,
            )


@frappe.whitelist()
def get_timetable_data(term=None, course=None, department=None, start_date=None, end_date=None):
    """Get timetable data for calendar view"""
    filters = {}
    
    if term:
        filters["term"] = term
    if course:
        filters["course"] = course
    if department:
        filters["department"] = department
    if start_date and end_date:
        filters["schedule_date"] = ["between", [start_date, end_date]]
    
    schedules = frappe.get_all(
        "Class Schedule",
        filters=filters,
        fields=[
            "name",
            "title",
            "course",
            "instructor",
            "schedule_date",
            "from_time",
            "to_time",
            "room",
            "venue",
            "color",
            "class_configuration",
            "student_group",
        ],
        order_by="schedule_date, from_time",
    )
    
    # Format for calendar
    events = []
    for schedule in schedules:
        events.append({
            "id": schedule.name,
            "title": schedule.title or schedule.course,
            "start": f"{schedule.schedule_date}T{schedule.from_time}",
            "end": f"{schedule.schedule_date}T{schedule.to_time}",
            "backgroundColor": schedule.color or "#3498db",
            "extendedProps": {
                "course": schedule.course,
                "instructor": schedule.instructor,
                "room": schedule.room,
                "venue": schedule.venue,
                "class_configuration": schedule.class_configuration,
                "student_group": schedule.student_group,
            }
        })
    
    return events


@frappe.whitelist()
def create_class_schedule(data):
    """Create a class schedule from timetable configuration"""
    import json
    
    if isinstance(data, str):
        data = json.loads(data)
    
    # Create the schedule
    doc = frappe.get_doc({
        "doctype": "Class Schedule",
        "class_configuration": data.get("class_configuration"),
        "course": data.get("course"),
        "instructor": data.get("instructor"),
        "schedule_date": data.get("schedule_date"),
        "from_time": data.get("from_time"),
        "to_time": data.get("to_time"),
        "room": data.get("room"),
        "venue": data.get("venue"),
        "repeat_frequency": data.get("repeat_frequency", "Never"),
        "repeats_till": data.get("repeats_till"),
        "term": data.get("term"),
        "department": data.get("department"),
        "programme": data.get("programme"),
        "student_group": data.get("student_group"),
    })
    
    doc.insert(ignore_permissions=True)
    
    # If repeat is enabled, create recurring schedules
    if doc.repeat_frequency and doc.repeat_frequency != "Never":
        doc.create_recurring_schedules()
    
    return doc.name


@frappe.whitelist()
def get_events(start, end, filters=None):
    """
    Custom method to get events for FullCalendar.
    Handles the split date (schedule_date) and time (from_time, to_time) fields.
    """
    if not filters:
        filters = []
        
    import json
    if isinstance(filters, str):
        filters = json.loads(filters)

    # Base Query
    query = """
        SELECT 
            name, 
            class_configuration, 
            course,
            instructor,
            schedule_date, 
            from_time, 
            to_time, 
            room,
            venue,
            color,
            title,
            student_group
        FROM `tabClass Schedule`
        WHERE 
            schedule_date BETWEEN %(start)s AND %(end)s
            AND docstatus < 2
    """
    
    # Add filters if present
    # This is a basic implementation. For complex standard filters, 
    # we might need frappe.get_list logic or get_event_conditions
    condition_values = {"start": start, "end": end}
    
    # Execute
    data = frappe.db.sql(query, condition_values, as_dict=True)

    result = []
    for d in data:
        # Construct ISO datetime strings for FullCalendar
        start_dt = f"{d.schedule_date} {d.from_time}"
        end_dt = f"{d.schedule_date} {d.to_time}"
        
        title = d.title
        if not title:
            # Fallback title: Course (Room)
            parts = [d.course, d.instructor]
            title = " - ".join([p for p in parts if p])
            if d.room:
                title += f" ({d.room})"

        result.append({
            "name": d.name,
            "id": d.name,
            "title": title,
            "start": start_dt,
            "end": end_dt,
            "color": d.color or "#3498db", # Default blue
            "allDay": 0,
            "extendedProps": {
                "room": d.room,
                "instructor": d.instructor,
                "student_group": d.student_group
            }
        })
    
    return result


@frappe.whitelist()
def create_class_schedule_on_select(start, end, filters=None):
    """
    Create a Class Schedule when a user selects a time range in the calendar.
    Uses current filters to populate mandatory fields.
    """
    import json
    from frappe.utils import get_datetime

    start_dt = get_datetime(start)
    end_dt = get_datetime(end)

    # Extract date and time
    schedule_date = start_dt.date()
    from_time = start_dt.time()
    to_time = end_dt.time()

    # Create new doc
    doc = frappe.new_doc("Class Schedule")
    doc.schedule_date = schedule_date
    doc.from_time = from_time
    doc.to_time = to_time
    
    # Process filters to populate fields
    if filters:
        if isinstance(filters, str):
            filters = json.loads(filters)
        
        # filters structure is usually [[doctype, fieldname, operator, value], ...]
        # We only care about simple '=' filters to pre-fill data
        for f in filters:
            if len(f) >= 4 and f[2] == "=":
                fieldname = f[1]
                value = f[3]
                if doc.meta.has_field(fieldname):
                    doc.set(fieldname, value)

    doc.insert()
    return doc.name
