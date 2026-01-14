
import frappe

def inspect():
    try:
        meta = frappe.get_meta("Workflow Action Master")
        print(f"Autoname: {meta.autoname}")
        print("Fields:")
        for field in meta.fields:
            print(f"  {field.fieldname} ({field.fieldtype})")
            
        # Also print first 5 rows to see data structure
        print("Data Sample:")
        data = frappe.db.get_all("Workflow Action", fields=["*"], limit=5)
        for d in data:
            print(d)

    except Exception as e:
        print(f"Error: {e}")
