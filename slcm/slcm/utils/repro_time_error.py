
import frappe
from frappe.utils import to_timedelta
from datetime import timedelta

def run():
    # Simulate the scenario
    # Class Schedule 1 (Existing in DB) -> Returns timedelta
    # Class Schedule 2 (New, Unsaved) -> Has string time
    
    # 1. string vs timedelta
    t1_str = "10:00:00"
    t2_timedelta = timedelta(seconds=36000) # 10:00:00
    
    print(f"t1_str type: {type(t1_str)}")
    print(f"t2_timedelta type: {type(t2_timedelta)}")
    
    try:
        print(t1_str < t2_timedelta)
    except TypeError as e:
        print(f"Caught expected error: {e}")

    val1 = to_timedelta(t1_str)
    val2 = to_timedelta(t2_timedelta)
    
    print(f"Converted types: {type(val1)}, {type(val2)}")
    print(f"Comparison: {val1 == val2}")

if __name__ == "__main__":
    run()
