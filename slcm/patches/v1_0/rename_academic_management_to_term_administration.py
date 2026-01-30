import frappe

def execute():
	"""Migrate data from Academic Management to Term Administration"""
	
	# Check if the old table exists
	if frappe.db.table_exists("tabAcademic Management"):
		# Since Term Administration doctype already exists from the renamed files,
		# we need to migrate the data from the old table
		
		# Get data from old table
		old_data = frappe.db.sql("""
			SELECT * FROM `tabAcademic Management`
		""", as_dict=True)
		
		if old_data:
			# For single doctype, migrate the data to the new table
			for row in old_data:
				# Check if record already exists in new table
				existing = frappe.db.sql("""
					SELECT name FROM `tabTerm Administration` 
					WHERE name = %s
				""", row.get('name'))
				
				if not existing:
					# Insert into new table
					columns = list(row.keys())
					values = [row.get(col) for col in columns]
					
					placeholders = ', '.join(['%s'] * len(columns))
					column_names = ', '.join([f'`{col}`' for col in columns])
					
					frappe.db.sql(f"""
						INSERT INTO `tabTerm Administration` ({column_names})
						VALUES ({placeholders})
					""", values)
			
			frappe.db.commit()
			print(f"Successfully migrated {len(old_data)} records from Academic Management to Term Administration")
		
		# Drop the old table
		frappe.db.sql("DROP TABLE IF EXISTS `tabAcademic Management`")
		frappe.db.commit()
		print("Dropped old Academic Management table")
	else:
		print("Academic Management table not found, migration already complete or not needed")

