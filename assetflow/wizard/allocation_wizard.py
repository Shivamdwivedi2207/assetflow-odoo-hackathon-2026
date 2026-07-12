# wizard/allocation_wizard.py
from datetime import datetime, timedelta
from models._registry import GLOBAL_DB
from models.allocation import Allocation

class AllocationWizard:
    def __init__(self, asset_id: str, current_user_id: str):
        self.asset = GLOBAL_DB.assets.get(asset_id)
        self.current_user = GLOBAL_DB.employees.get(current_user_id)
        
        if not self.asset:
            raise ValueError("Target asset entity could not be found.")
            
        self.target_employee_id = None
        self.target_department_id = None
        self.duration_days = 7  # Default allocation timeframe window

    def execute_allocation(self) -> Allocation:
        """Executes the operational allocation loop using the transient fields."""
        employee = GLOBAL_DB.employees.get(self.target_employee_id) if self.target_employee_id else None
        department = GLOBAL_DB.departments.get(self.target_department_id) if self.target_department_id else None

        if self.target_employee_id and not employee:
            raise ValueError("Selected employee does not exist.")
        if self.target_department_id and not department:
            raise ValueError("Selected department does not exist.")
        
        expected_return = datetime.now() + timedelta(days=int(self.duration_days))
        
        # Instantiate the pure python allocation business model
        new_allocation = Allocation(
            asset=self.asset,
            employee=employee,
            department=department,
            expected_return_date=expected_return
        )
        
        GLOBAL_DB.log_activity(f"Wizard action completed: Processed allocation for {self.asset.asset_tag}")
        return new_allocation
