
import frappe
from frappe.modules import reload_doc
from frappe.permissions import reset_perms

def execute():
    try:
        # Module is SLCM for all
        doctypes = ["Hostel", "Hostel Room", "Hostel Bed"]
        
        for doctype in doctypes:
            print(f"Reloading {doctype} DocType...")
            reload_doc("slcm", "doctype", frappe.scrub(doctype))
            
            # Check for Custom DocPerm entries
            custom_perms = frappe.get_all("Custom DocPerm", filters={"parent": doctype})
            if custom_perms:
                print(f"Found {len(custom_perms)} Custom DocPerm entries for {doctype}. removing...")
                frappe.db.delete("Custom DocPerm", {"parent": doctype})
            
            # Reset perms
            reset_perms(doctype)
            print(f"Permissions reset for {doctype}.\n")
        
        frappe.db.commit()
        print("Success: Hostel, Hostel Room, and Hostel Bed reloaded and permissions reset.")
        
    except Exception as e:
        frappe.db.rollback()
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    frappe.connect()
    execute()
