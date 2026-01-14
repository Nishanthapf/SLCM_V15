
import frappe

def inspect():
    try:
        meta = frappe.get_meta("Workflow Transition")
        print("Fields:")
        for field in meta.fields:
            if field.fieldname == "action":
                print(f"  {field.fieldname} ({field.fieldtype}) - Options: {field.options}")
    except Exception as e:
        print(f"Error: {e}")
