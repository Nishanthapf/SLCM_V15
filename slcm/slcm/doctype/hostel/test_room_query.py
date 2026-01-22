import frappe

from slcm.slcm.doctype.hostel_allocation.hostel_allocation import get_room_query


def test_query():
	# Setup
	hostel_name = "Test Hostel A"
	# Ensure items exist (relying on previous test's artifacts or existing ones)
	if not frappe.db.exists("Hostel", hostel_name):
		print("Hostel not found, creating setup...")
		# (Assuming previous test ran, but let's be safe or just fail if not found since we are in same env)

	# Test query
	filters = {"hostel": hostel_name}
	results = get_room_query(None, "", None, 0, 20, filters)
	print(f"Query Results for {hostel_name}: {len(results)}")
	for r in results:
		print(r)


if __name__ == "__main__":
	test_query()
