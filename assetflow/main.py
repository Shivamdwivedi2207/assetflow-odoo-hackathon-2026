# main.py
import os
import sys
from datetime import datetime, timedelta

# Import the core pure-Python packages
from models._registry import GLOBAL_DB
from models.employee import UserRole, Employee
from models.asset import AssetStatus, Asset
from models.allocation import Allocation
from models.maintenance import Maintenance, MaintenanceStatus
from data.demo_data import seed_system_demo_data
from security.ir.model.access import check_model_access
from security.security import check_record_rule
from report.asset_report import AssetReportGenerator

# Import transient wizard modules
from wizard.allocation_wizard import AllocationWizard
from wizard.return_wizard import ReturnWizard

# Global state tracker for authentication sessions
current_session_user = None

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def render_ui_header(title: str):
    print("=" * 65)
    print(f"  AssetFlow ERP Center  ||  {title}")
    if current_session_user:
        print(f"  Authenticated: {current_session_user.name} | Role Clearance: [{current_session_user.role}]")
    print("=" * 65)

def run_user_login():
    global current_session_user
    while not current_session_user:
        clear_screen()
        render_ui_header("System Gate Authentication")
        print(" Use Seeded Profiles to Evaluate Permissions:")
        print("  - Manager Profile : sarah@assetflow.com (password123)")
        print("  - Dept Head Profile: john@assetflow.com  (password123)")
        print("  - Standard Employee: alex@assetflow.com  (password123)")
        print("-" * 65)
        
        email = input("Enter Email Address: ").strip()
        password = input("Enter Security Password: ").strip()
        
        # Check against pure-python database engine dict lookup
        match = next((e for e in GLOBAL_DB.employees.values() if e.email == email and e.password == password), None)
        
        if match:
            if not match.is_active:
                print("\n[SECURITY FAILURE] Target account status is flagged inactive."); input(); continue
            current_session_user = match
            GLOBAL_DB.log_activity(f"Session established for user: {match.email}")
        else:
            print("\n[ERROR] Authentication invalid. Matching criteria sequence failed."); input()

def display_dashboard():
    clear_screen()
    render_ui_header("Real-Time KPI Operations Dashboard")
    
    # Calculate Live Aggregated KPIs
    assets = list(GLOBAL_DB.assets.values())
    allocs = list(GLOBAL_DB.allocations.values())
    tickets = list(GLOBAL_DB.maintenance_records.values())
    
    avail_kpi = sum(1 for a in assets if a.status == AssetStatus.AVAILABLE)
    alloc_kpi = sum(1 for a in assets if a.status == AssetStatus.ALLOCATED)
    maint_kpi = sum(1 for m in tickets if m.status == MaintenanceStatus.IN_PROGRESS)
    
    print(f" [KPI Indicators] Available: {avail_kpi}  |  Allocated: {alloc_kpi}  |  In Repair: {maint_kpi}")
    print("-" * 65)
    
    # Process Overdue Check-in Flag Notifications
    print(" OVERDUE RETURN TIMELINE ALERTS:")
    has_overdue = False
    for al in allocs:
        if al.is_active and al.expected_return_date and al.expected_return_date < datetime.now():
            print(f"  [ALERT] Overdue Tag {al.asset.asset_tag} held by {al.employee.name if al.employee else al.department.name} (Due: {al.expected_return_date.strftime('%Y-%m-%d')})")
            has_overdue = True
    if not has_overdue:
        print("  No active discrepancies caught in current return cycle.")
    print("-" * 65)
    
    print(" Workspace Navigation:")
    print("  1. Asset Master Directory Registry")
    print("  2. Maintenance Hub Ticketing")
    print("  3. Run Analytical System Report")
    print("  4. View Immutable Security Activity Logs")
    print("  5. Exit Session / Terminate Connection")
    
    choice = input("\nSelect Workspace Destination (1-5): ").strip()
    if choice == "1": handle_asset_directory_ui()
    elif choice == "2": handle_maintenance_hub_ui()
    elif choice == "3": handle_reporting_ui()
    elif choice == "4": handle_logs_ui()
    elif choice == "5":
        global current_session_user
        GLOBAL_DB.log_activity(f"User {current_session_user.name} logged out.")
        current_session_user = None

def handle_asset_directory_ui():
    while True:
        clear_screen()
        render_ui_header("Asset Registry Console View")
        
        # Pull records and pass through Row-Level Security Rules
        visible_assets = [a for a in GLOBAL_DB.assets.values() if check_record_rule("Asset", a, current_session_user)]
        
        for asset in visible_assets:
            holder = asset.current_holder.name if asset.current_holder else (asset.current_department.name if asset.current_department else "None")
            print(f" * [{asset.asset_tag}] {asset.name:<30} | Status: {asset.status:<18} | Holder: {holder}")
            
        print("\n Operations View Action Options:")
        print("  1. Allocate Asset via Wizard  |  2. Return Asset via Wizard  |  3. Back")
        act = input("Action Code: ").strip()
        
        try:
            if act == "1":
                # Check Global Access Control Rights (Create Perms)
                if not check_model_access("Allocation", current_session_user.role, "create"):
                    raise PermissionError("Access Control List Blocked: Action requires Manager permissions.")
                    
                tag = input("Enter Asset Tag to allocate: ").strip()
                target_asset = next((a for a in visible_assets if a.asset_tag == tag), None)
                if not target_asset: raise ValueError("Asset matching input code not visible or present.")
                
                # Instantiate transient allocation wizard loop
                wizard = AllocationWizard(target_asset.id, current_session_user.id)
                
                print("\n Assignment Routing Options: 1. Assign to Employee | 2. Assign to Department")
                route = input("Route: ").strip()
                if route == "1":
                    email = input("Target Employee Email: ").strip()
                    emp = next((e for e in GLOBAL_DB.employees.values() if e.email == email), None)
                    if not emp: raise ValueError("Target employee email matching instance not found.")
                    wizard.target_employee_id = emp.id
                else:
                    d_name = input("Target Department Name: ").strip()
                    dept = next((d for d in GLOBAL_DB.departments.values() if d.name.lower() == d_name.lower()), None)
                    if not dept: raise ValueError("Target department name entry not found.")
                    wizard.target_department_id = dept.id
                    
                wizard.duration_days = input("Duration length window till return (Days, default 7): ") or 7
                wizard.execute_allocation()
                print("\n Allocation record successfully processed."); input()
                
            elif act == "2":
                tag = input("Enter checking-in Asset Tag: ").strip()
                target_asset = next((a for a in visible_assets if a.asset_tag == tag), None)
                if not target_asset: raise ValueError("Asset matching input code not found.")
                
                # Instantiate transient return wizard loop
                wizard = ReturnWizard(target_asset.id)
                wizard.checkin_notes = input("Enter intake checklist inspection summary: ")
                dmg_flag = input("Is the asset broken or damaged? (y/n): ").lower()
                if dmg_flag == 'y':
                    wizard.is_damaged = True
                    
                res = wizard.execute_return()
                print(f"\n Check-in complete: {res['msg']}"); input()
            else:
                break
        except Exception as err:
            print(f"\n [TRANSACTION CRASHED] -> {err}"); input()

def handle_maintenance_hub_ui():
    while True:
        clear_screen()
        render_ui_header("Maintenance Center & Ticketing Grid")
        
        visible_tickets = [m for m in GLOBAL_DB.maintenance_records.values() if check_record_rule("Maintenance", m, current_session_user)]
        
        for tk in visible_tickets:
            print(f" * Job ID: {tk.id} | Asset: {tk.asset.asset_tag} | Status: {tk.status:<12} | Problem: {tk.description}")
            
        print("\n Action Operations:")
        print("  1. File New Breakdown Ticket | 2. Approve Request Ticket | 3. Complete Repairs | 4. Back")
        act = input("Action Code: ").strip()
        
        try:
            if act == "1":
                tag = input("Enter malfunctioning Asset Tag: ").strip()
                asset = next((a for a in GLOBAL_DB.assets.values() if a.asset_tag == tag), None)
                if not asset: raise ValueError("Asset not located.")
                desc = input("Describe symptoms / structural problems: ")
                
                Maintenance(asset, current_session_user, desc)
                print("\n Ticket successfully pushed into queue pipeline."); input()
                
            elif act == "2":
                if not check_model_access("Maintenance", current_session_user.role, "write"):
                    raise PermissionError("ACL Violation: Only Asset Managers can approve maintenance events.")
                jid = input("Enter target Job ID to authorize: ").strip()
                ticket = GLOBAL_DB.maintenance_records.get(jid)
                if not ticket: raise ValueError("Ticket index missing.")
                
                ticket.approve_request()
                ticket.assign_technician("External Vendor Expert Team")
                print("\n Ticket approved. Asset moved to Under Maintenance and technician deployed."); input()
                
            elif act == "3":
                jid = input("Enter resolved target Job ID: ").strip()
                ticket = GLOBAL_DB.maintenance_records.get(jid)
                if not ticket: raise ValueError("Ticket index missing.")
                
                ticket.resolve_repairs()
                print("\n Asset returned to centralized active operations inventory pool."); input()
            else:
                break
        except Exception as err:
            print(f"\n [WORKFLOW ERROR] -> {err}"); input()

def handle_reporting_ui():
    clear_screen()
    render_ui_header("Analytical QWeb-Replica Management Report")
    report_output = AssetReportGenerator.generate_text_report()
    print(report_output)
    input("\n Press Enter to return to Dashboard...")

def handle_logs_ui():
    clear_screen()
    render_ui_header("Immutable Infrastructure System Logs Ledger")
    for record_line in GLOBAL_DB.logs[-25:]: # Stream last 25 operations
        print(f" {record_line}")
    input("\n Press Enter to return to Dashboard...")

if __name__ == "__main__":
    # 1. Execute transactional bootstrapping setup data seeding
    seed_system_demo_data()
    
    # 2. Start infinite operational console loop
    while True:
        if not current_session_user:
            run_user_login()
        else:
            display_dashboard()