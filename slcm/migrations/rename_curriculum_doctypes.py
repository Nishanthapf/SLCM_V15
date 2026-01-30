import frappe

def execute():
    """Rename Curriculum and Curriculum Enrollment Type DocTypes"""
    try:
        print("=" * 70)
        print("Starting DocType Rename Operations")
        print("=" * 70)
        
        # Rename 1: Curriculum → Course List
        print("\n[1/2] Renaming 'Curriculum' to 'Course List'...")
        if frappe.db.exists("DocType", "Curriculum"):
            if frappe.db.exists("DocType", "Course List"):
                print("  ✗ 'Course List' already exists. Skipping rename.")
            else:
                frappe.rename_doc(
                    "DocType",
                    "Curriculum",
                    "Course List",
                    force=True,
                    merge=False
                )
                print("  ✓ Successfully renamed 'Curriculum' to 'Course List'")
        else:
            print("  ✗ 'Curriculum' DocType not found")
        
        # Rename 2: Curriculum Enrollment Type → Course Enrollment Type
        print("\n[2/2] Renaming 'Curriculum Enrollment Type' to 'Course Enrollment Type'...")
        if frappe.db.exists("DocType", "Curriculum Enrollment Type"):
            if frappe.db.exists("DocType", "Course Enrollment Type"):
                print("  ✗ 'Course Enrollment Type' already exists. Skipping rename.")
            else:
                frappe.rename_doc(
                    "DocType",
                    "Curriculum Enrollment Type",
                    "Course Enrollment Type",
                    force=True,
                    merge=False
                )
                print("  ✓ Successfully renamed 'Curriculum Enrollment Type' to 'Course Enrollment Type'")
        else:
            print("  ✗ 'Curriculum Enrollment Type' DocType not found")
        
        # Commit the transaction
        frappe.db.commit()
        
        print("\n" + "=" * 70)
        print("✓ SUCCESS: All DocTypes renamed successfully!")
        print("=" * 70)
        print("\nNext steps:")
        print("1. Update code references")
        print("2. Move and rename files")
        print("3. Clear cache: bench clear-cache")
        print("4. Restart server: bench restart")
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"✗ ERROR: {str(e)}")
        print("=" * 70)
        frappe.db.rollback()
        raise
