import frappe

def execute():
    """Fix partial rename - drop old tables and update DocType records"""
    try:
        print("=" * 70)
        print("Fixing Partial DocType Renames")
        print("=" * 70)
        
        # Fix 1: Drop old Curriculum table if Course List exists
        print("\n[1/2] Fixing 'Curriculum' → 'Course List'...")
        if frappe.db.exists("DocType", "Course List"):
            # Check if old table exists
            old_table_exists = frappe.db.sql("""
                SELECT COUNT(*) as count 
                FROM information_schema.tables 
                WHERE table_schema = DATABASE() 
                AND table_name = 'tabCurriculum'
            """)[0][0]
            
            if old_table_exists:
                print("  ⚠ Old table 'tabCurriculum' still exists. Dropping it...")
                frappe.db.sql("DROP TABLE IF EXISTS `tabCurriculum`")
                print("  ✓ Dropped old table 'tabCurriculum'")
            else:
                print("  ✓ Old table already removed")
                
            print("  ✓ 'Course List' DocType is ready")
        else:
            print("  ✗ 'Course List' DocType not found in database")
        
        # Fix 2: Rename Curriculum Enrollment Type
        print("\n[2/2] Renaming 'Curriculum Enrollment Type' → 'Course Enrollment Type'...")
        if frappe.db.exists("DocType", "Curriculum Enrollment Type"):
            # Check if target already exists
            if frappe.db.exists("DocType", "Course Enrollment Type"):
                print("  ✗ 'Course Enrollment Type' already exists. Skipping.")
            else:
                frappe.rename_doc(
                    "DocType",
                    "Curriculum Enrollment Type",
                    "Course Enrollment Type",
                    force=True,
                    merge=False
                )
                print("  ✓ Successfully renamed to 'Course Enrollment Type'")
        else:
            if frappe.db.exists("DocType", "Course Enrollment Type"):
                print("  ✓ 'Course Enrollment Type' already exists")
            else:
                print("  ✗ Neither old nor new DocType found")
        
        # Commit the transaction
        frappe.db.commit()
        
        print("\n" + "=" * 70)
        print("✓ SUCCESS: Database cleanup completed!")
        print("=" * 70)
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"✗ ERROR: {str(e)}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        frappe.db.rollback()
        raise
