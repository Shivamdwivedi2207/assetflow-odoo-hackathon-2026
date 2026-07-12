# app.py
import streamlit as st
from datetime import datetime, timedelta

# Import your core back-end layers
from models._registry import GLOBAL_DB
from models.employee import UserRole, Employee
from models.asset import AssetStatus, Asset
from models.allocation import Allocation
from models.maintenance import Maintenance, MaintenanceStatus
from data.demo_data import seed_system_demo_data
from security.ir.model.access import check_model_access
from security.security import check_record_rule
from report.asset_report import AssetReportGenerator

# Import wizards
from wizard.allocation_wizard import AllocationWizard
from wizard.return_wizard import ReturnWizard

# Initialize system data session cache state so it doesn't clear on click refresh
if "data_seeded" not in st.session_state:
    seed_system_demo_data()
    st.session_state.data_seeded = True

st.set_page_config(
    page_title="AssetFlow ERP Dashboard",
    page_icon="💼",
    layout="wide"
)

# --- SIDEBAR AUTHENTICATION SIMULATOR ---
st.sidebar.markdown("## 🔐 System Access Gateway")
user_email = st.sidebar.selectbox(
    "Select Authenticated Active Profile:",
    ["sarah@assetflow.com (Asset Manager)", "john@assetflow.com (Dept Head)", "alex@assetflow.com (Employee)"]
)

# Extract actual profile instance from our database matching selection
email_clean = user_email.split(" ")[0]
current_user = next((e for e in GLOBAL_DB.employees.values() if e.email == email_clean), None)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Logged User:** {current_user.name}")
st.sidebar.markdown(f"**Security Role Clearance:** `{current_user.role}`")
st.sidebar.markdown(f"**Department Tree:** {current_user.department.name}")

# --- MAIN APP ROUTING INTERFACE ---
st.title("💼 AssetFlow Corporate ERP Workspace")
st.markdown("An advanced framework-free asset management infrastructure ecosystem.")
st.markdown("---")

# Row-level rule filtering calculations for data visualization lists
visible_assets = [a for a in GLOBAL_DB.assets.values() if check_record_rule("Asset", a, current_user)]
visible_tickets = [m for m in GLOBAL_DB.maintenance_records.values() if check_record_rule("Maintenance", m, current_user)]

# Build functional master tabs
tab_kpi, tab_assets, tab_maint, tab_reports, tab_logs = st.tabs([
    "📊 KPI Control Center", 
    "📦 Asset Master Directory", 
    "🔧 Maintenance Hub", 
    "📈 Performance Analytics", 
    "📜 Immutable Audit Logs"
])

# ==================== TAB 1: KPI CONTROL CENTER ====================
with tab_kpi:
    st.subheader("Real-Time Operational Metrics")
    
    # Render dynamic metric value tiles
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    kpi_col1.metric("Total Viewable Assets", len(visible_assets))
    kpi_col2.metric("Available Status Items", sum(1 for a in visible_assets if a.status == AssetStatus.AVAILABLE))
    kpi_col3.metric("Allocated out to Personnel", sum(1 for a in visible_assets if a.status == AssetStatus.ALLOCATED))
    kpi_col4.metric("Active Repair Jobs Queue", sum(1 for m in visible_tickets if m.status == MaintenanceStatus.IN_PROGRESS))

    st.markdown("---")
    st.markdown("### 🚨 Urgent Allocation Timeline Exceptions")
    
    overdue_found = False
    for al in GLOBAL_DB.allocations.values():
        if al.is_active and al.expected_return_date and al.expected_return_date < datetime.now():
            holder = al.employee.name if al.employee else al.department.name
            st.error(f"⚠️ **Overdue Warning:** Hardware Tag **{al.asset.asset_tag}** held by *{holder}* (Exceeded Target Due Date: {al.expected_return_date.strftime('%Y-%m-%d')})")
            overdue_found = True
            
    if not overdue_found:
        st.success("✅ All outstanding field allocations are clean within default cycle deadlines.")

# ==================== TAB 2: ASSET REGISTRY & WIZARDS ====================
with tab_assets:
    st.subheader("Corporate Assets Records Registry")
    
    # 1. Show interactive data grid
    asset_table_list = []
    for asset in visible_assets:
        holder = asset.current_holder.name if asset.current_holder else (asset.current_department.name if asset.current_department else "Central Vault")
        asset_table_list.append({
            "Asset Tag": asset.asset_tag,
            "Description Name": asset.name,
            "Operational Status": asset.status,
            "Assigned Custody Holder": holder,
            "Physical Location Base": asset.location,
            "Purchase Book Value ($)": f"{asset.acquisition_cost:,.2f}"
        })
        
    if asset_table_list:
        st.dataframe(asset_table_list, use_container_width=True)
    else:
        st.info("No corporate assets visible under current access control scope parameters.")

    st.markdown("#### Add Asset to Inventory")
    if check_model_access("Asset", current_user.role, "create"):
        categories_by_name = {category.name: category for category in GLOBAL_DB.categories.values()}
        with st.form("create_asset_form", clear_on_submit=True):
            new_asset_name = st.text_input("Asset Name")
            new_category_name = st.selectbox("Category", list(categories_by_name))
            new_serial_number = st.text_input("Serial Number")
            new_location = st.text_input("Storage Location")
            new_cost = st.number_input("Acquisition Cost", min_value=0.0, value=0.0, step=1.0)
            new_is_bookable = st.checkbox("Shared / bookable resource")
            submit_new_asset = st.form_submit_button("Add Available Asset")

            if submit_new_asset:
                try:
                    if not new_asset_name.strip() or not new_serial_number.strip() or not new_location.strip():
                        raise ValueError("Name, serial number, and storage location are required.")
                    Asset(
                        name=new_asset_name.strip(),
                        category=categories_by_name[new_category_name],
                        serial_number=new_serial_number.strip(),
                        cost=float(new_cost),
                        location=new_location.strip(),
                        is_bookable=new_is_bookable,
                    )
                    st.success("Asset added with Available status and saved to the database.")
                    st.rerun()
                except Exception as error:
                    st.error(f"Could not add asset: {error}")
    else:
        st.info("Only Asset Managers and Admins can add inventory items.")
        
    # 2. Add structural action forms for handling our wizards
    st.markdown("---")
    wiz_col1, wiz_col2 = st.columns(2)
    
    with wiz_col1:
        st.markdown("#### 🚀 Step-Form: Asset Allocation Wizard")
        if check_model_access("Allocation", current_user.role, "create"):
            available_assets = [asset for asset in visible_assets if asset.status == AssetStatus.AVAILABLE]
            if not available_assets:
                st.info("No available assets can be allocated right now.")
            else:
                employee_options = {
                    f"{employee.name} ({employee.email})": employee
                    for employee in GLOBAL_DB.employees.values() if employee.is_active
                }
                department_options = {
                    department.name: department
                    for department in GLOBAL_DB.departments.values() if department.is_active
                }
                with st.form("allocation_wizard_form", clear_on_submit=True):
                    target_tag = st.selectbox("Select Target Inventory Tag:", [asset.asset_tag for asset in available_assets])
                    assign_type = st.radio("Assignment Type:", ["Employee", "Department"])
                    if assign_type == "Employee":
                        selected_employee = st.selectbox("Assign to Employee:", list(employee_options))
                        selected_department = None
                    else:
                        selected_department = st.selectbox("Assign to Department:", list(department_options))
                        selected_employee = None
                    days_duration = st.number_input("Target Allocation Duration (Days):", min_value=1, max_value=365, value=7)
                    submit_alloc = st.form_submit_button("Execute Asset Dispatch")

                    if submit_alloc:
                        try:
                            asset_obj = next(asset for asset in available_assets if asset.asset_tag == target_tag)
                            wizard = AllocationWizard(asset_obj.id, current_user.id)
                            if selected_employee:
                                wizard.target_employee_id = employee_options[selected_employee].id
                            else:
                                wizard.target_department_id = department_options[selected_department].id
                            wizard.duration_days = int(days_duration)
                            wizard.execute_allocation()
                            st.success(f"Successfully allocated tag {target_tag} via workflow wizard context.")
                            st.rerun()
                        except Exception as error:
                            st.error(f"Execution Error: {error}")
        else:
            st.warning("🔒 Allocation wizard requires Asset Manager or Admin structural tier clearances.")

    with wiz_col2:
        st.markdown("#### 📥 Step-Form: Inventory Return Checklist Wizard")
        with st.form("return_wizard_form", clear_on_submit=True):
            active_allocs = [al.asset.asset_tag for al in GLOBAL_DB.allocations.values() if al.is_active]
            target_return_tag = st.selectbox("Select Returning Inventory Tag:", active_allocs if active_allocs else ["No Active Allocations Out"])
            
            notes = st.text_area("Check-In Surface Inspection Notes:")
            dmg_flag = st.checkbox("Flag System Asset as Structurally Damaged / Defective")
            
            submit_return = st.form_submit_button("Process Central Intake")
            
            if submit_return and target_return_tag and target_return_tag != "No Active Allocations Out":
                try:
                    asset_obj = next((a for a in visible_assets if a.asset_tag == target_return_tag), None)
                    wizard = ReturnWizard(asset_obj.id)
                    wizard.checkin_notes = notes
                    wizard.is_damaged = dmg_flag
                    
                    res = wizard.execute_return()
                    st.success(res["msg"])
                    st.rerun()
                except Exception as e:
                    st.error(f"Execution Error: {str(e)}")

# ==================== TAB 3: MAINTENANCE HUB ====================
with tab_maint:
    st.subheader("Active Structural Maintenance Tickets Pipeline")
    
    maint_list = []
    for tk in visible_tickets:
        maint_list.append({
            "Job Ticket ID": tk.id,
            "Asset Item Tag": tk.asset.asset_tag,
            "Reporting Agent": tk.raised_by.name,
            "Issue Profile Summary": tk.description,
            "State Status Mode": tk.status,
            "Assigned Dispatch Crew": tk.technician or "Unassigned Queue"
        })
        
    if maint_list:
        st.dataframe(maint_list, use_container_width=True)
    else:
        st.info("No open breakdown maintenance tickets tracked on file.")
        
    st.markdown("---")
    st.markdown("#### Action Workflow Drivers")
    btn_col1, btn_col2, btn_col3 = st.columns(3)
    
    with btn_col1:
        st.markdown("**File System Breakdown Ticket**")
        with st.popover("Raise Malfunction Ticket"):
            maint_tag = st.selectbox("Select Broken Hardware Tag:", [a.asset_tag for a in visible_assets])
            maint_desc = st.text_input("Describe internal symptoms/fault code:")
            submit_ticket = st.button("Submit To Dispatch Queue")
            if submit_ticket and maint_tag:
                asset_obj = next((a for a in visible_assets if a.asset_tag == maint_tag), None)
                Maintenance(asset_obj, current_user, maint_desc)
                st.success("Ticket pushed into system registry.")
                st.rerun()

    with btn_col2:
        st.markdown("**Authorize Core Inspection**")
        with st.popover("Approve Open Repair Request"):
            if check_model_access("Maintenance", current_user.role, "write"):
                target_job = st.selectbox("Select Ticket Job ID to Approve:", [tk.id for tk in visible_tickets if tk.status == MaintenanceStatus.PENDING])
                submit_appr = st.button("Confirm Job Deployment")
                if submit_appr and target_job:
                    tk_obj = GLOBAL_DB.maintenance_records.get(target_job)
                    tk_obj.approve_request()
                    tk_obj.assign_technician("External Specialist Vendor Team")
                    st.success("Workflow transitioned: Asset moved to Under Maintenance status.")
                    st.rerun()
            else:
                st.warning("🔒 Manager clearance token required.")

    with btn_col3:
        st.markdown("**Resolve Operations Ticket**")
        with st.popover("Complete Intake Repair Settle"):
            target_resolve_job = st.selectbox("Select Solved Job ID:", [tk.id for tk in visible_tickets if tk.status == MaintenanceStatus.IN_PROGRESS])
            submit_resolve = st.button("Mark Work Order Complete")
            if submit_resolve and target_resolve_job:
                tk_obj = GLOBAL_DB.maintenance_records.get(target_resolve_job)
                tk_obj.resolve_repairs()
                st.success("Workflow complete: Asset returned to Available pool.")
                st.rerun()

# ==================== TAB 4: PERFORMANCE ANALYTICS ====================
with tab_reports:
    st.subheader("Dynamic QWeb-Replica Metrics Engine Output")
    st.markdown("Below is the production-ready consolidated text string report compiled straight from database runtime aggregates:")
    
    # Get text summary metrics and print them directly in a code style wrapper block
    report_output = AssetReportGenerator.generate_text_report()
    st.code(report_output, language="text")

# ==================== TAB 5: AUDIT LOGS ====================
with tab_logs:
    st.subheader("Immutable System Infrastructure Activity Trail")
    st.markdown("System records sequence changes, authorization checks, and wizard actions sequentially:")
    
    # Reverse list array stream sequence to show newest log events right at the top
    for log_record in reversed(GLOBAL_DB.logs):
        st.caption(f"{log_record}")
