
import frappe

def execute():
    # Remove the conflicting Client Script
    script_name = "Attach File Path"
    if frappe.db.exists("Client Script", {"name": script_name}):
        frappe.delete_doc("Client Script", script_name, ignore_permissions=True)
        print(f"Deleted Client Script: {script_name}")
    
    # Also clear the description from the Property Setter if any exists (just in case)
    # The script used set_df_property which is transient (client side), so no property setter persist.
    # But good to check.
