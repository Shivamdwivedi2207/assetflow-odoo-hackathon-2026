from models._registry import GLOBAL_DB
from models.department import Department
from models.employee import Employee, UserRole
from models.asset_category import AssetCategory
from models.asset import Asset


def seed_system_demo_data():
    """Load saved data, or create the initial database records once."""
    if GLOBAL_DB.restore() and GLOBAL_DB.is_seeded:
        return

    GLOBAL_DB.log_activity("Executing data file seeding initialization...")

    it_dept = Department(name="Information Technology")
    ops_dept = Department(name="Operations & Logistics")
    hr_dept = Department(name="Human Resources")
    ops_dept.parent_department = it_dept

    manager_emp = Employee(name="Sarah Connor", email="sarah@assetflow.com", password="password123", department=it_dept)
    head_emp = Employee(name="John Doe", email="john@assetflow.com", password="password123", department=ops_dept)
    standard_emp = Employee(name="Alex Mercer", email="alex@assetflow.com", password="password123", department=hr_dept)

    manager_emp.change_role(UserRole.ASSET_MANAGER)
    head_emp.change_role(UserRole.DEPARTMENT_HEAD)

    it_dept.manager = manager_emp
    ops_dept.manager = head_emp

    electronics = AssetCategory(name="Enterprise Electronics", specific_attributes={"Warranty Period": "36 Months", "Power Output": "100W"})
    vehicles = AssetCategory(name="Corporate Fleet Vehicles", specific_attributes={"Fuel Profile": "Electric", "Insurance Policy": "Global-Cover"})
    facilities = AssetCategory(name="Shared Facility Spaces", specific_attributes={"Capacity Limit": "25 People"})

    Asset(name="MacBook Pro 16-Inch M3 Max", category=electronics, serial_number="SN-APL-M3MAX-99A", cost=3499.00, location="HQ Server Room Vault")
    Asset(name="Dell UltraSharp 32'' 4K Monitor", category=electronics, serial_number="SN-DELL-4K-882B", cost=899.50, location="HQ Floor 2 - Desk 4")
    Asset(name="Tesla Model Y Long Range", category=vehicles, serial_number="SN-TSLA-MY2026", cost=48000.00, location="Basement Parking Zone A", is_bookable=True)
    Asset(name="Executive Boardroom Gamma", category=facilities, serial_number="ROOM-GAMMA-HQ", cost=0.00, location="HQ Floor 1 East Wing", is_bookable=True)

    GLOBAL_DB.is_seeded = True
    GLOBAL_DB.log_activity("Demo data seeding completed successfully.")
