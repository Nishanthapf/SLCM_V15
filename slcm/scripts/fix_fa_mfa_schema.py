import frappe

def execute():
    table = "tabFA MFA Application"
    try:
        # Check column type
        res = frappe.db.sql(f"DESC `{table}`", as_dict=True)
        name_col = next((r for r in res if r['Field'] == 'name'), None)
        print(f"Current name column: {name_col}")
        
        if name_col and "int" in name_col['Type'].lower():
            print("Name column is INT. Dropping table to allow recreation with VARCHAR...")
            frappe.db.sql(f"DROP TABLE `{table}`")
            print("Table dropped.")
        else:
            print("Table not found or name column is not INT.")
            
    except Exception as e:
        print(f"Error checking/dropping table: {e}")

    # Reload
    print("Reloading DocType to recreate table...")
    try:
        frappe.reload_doc("slcm", "doctype", "fa_mfa_application", force=True)
        print("Reload complete.")
    except Exception as e:
        print(f"Error reloading doctype: {e}")
        # Fallback: try using the full module path/name if slcm isn't the app name
        # But 'slcm' is the module name in the json.

if __name__ == "__main__":
    frappe.connect("slcm.local")
    execute()
    frappe.db.commit()
