
import frappe
from frappe.modules import reload_doc

def execute():
    try:
        print("Reloading FA MFA Application DocType...")
        reload_doc("slcm", "doctype", "fa_mfa_application")
        
        # Check for Custom DocPerm entries that might override standard permissions
        doctype = "FA MFA Application"
        custom_perms = frappe.get_all("Custom DocPerm", filters={"parent": doctype})
        
        if custom_perms:
            print(f"Found {len(custom_perms)} Custom DocPerm entries. These will override standard JSON permissions.")
            print("Removing Custom DocPerm entries to restore JSON configuration...")
            frappe.db.delete("Custom DocPerm", {"parent": doctype})
            frappe.db.commit()
            print("Custom DocPerm entries removed.")
        else:
            print("No Custom DocPerm entries found.")
        
        # Force update permissions
        from frappe.permissions import reset_perms
        reset_perms(doctype)
        print("Permissions reset to defaults.")
        
        frappe.db.commit()
        print("Success: FA MFA Application reloaded and permissions reset.")
        
    except Exception as e:
        frappe.db.rollback()
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    frappe.connect()
    execute()
