import frappe

def execute():
    """Rename Curriculum Management to Course Management"""
    try:
        print("=" * 60)
        print("Starting DocType Rename Operation")
        print("=" * 60)
        
        # Check if old DocType exists
        if not frappe.db.exists("DocType", "Curriculum Management"):
            print("✗ 'Curriculum Management' DocType not found!")
            print("  Checking if 'Course Management' already exists...")
            if frappe.db.exists("DocType", "Course Management"):
                print("✓ 'Course Management' already exists. No rename needed.")
                return
            else:
                print("✗ Neither DocType found. Please check your setup.")
                return
        
        print("✓ Found 'Curriculum Management' DocType")
        print("  Starting rename process...")
        
        # Perform the rename
        frappe.rename_doc(
            "DocType", 
            "Curriculum Management", 
            "Course Management", 
            force=True,
            merge=False
        )
        
        # Commit the transaction
        frappe.db.commit()
        
        print("=" * 60)
        print("✓ SUCCESS: DocType renamed successfully!")
        print("  Old name: Curriculum Management")
        print("  New name: Course Management")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Clear cache: bench clear-cache")
        print("2. Restart server: bench restart")
        print("3. Update code references")
        
    except Exception as e:
        print("=" * 60)
        print(f"✗ ERROR: {str(e)}")
        print("=" * 60)
        frappe.db.rollback()
        raise
