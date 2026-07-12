# models/allocation.py
import uuid
from datetime import datetime
from ._registry import GLOBAL_DB
from .asset import AssetStatus

class Allocation:
    def __init__(self, asset, employee=None, department=None, expected_return_date=None):
        if not employee and not department:
            raise ValueError("Allocation assignment target missing: Must specify an Employee or Department.")
        
        # Conflict Validation: Prevent double-allocations
        if asset.status == AssetStatus.ALLOCATED:
            holder_name = asset.current_holder.name if asset.current_holder else asset.current_department.name
            raise RuntimeError(f"Conflict Resolution: Asset '{asset.asset_tag}' is already allocated to {holder_name}.")
            
        self.id = str(uuid.uuid4())[:8]
        self.asset = asset
        self.employee = employee
        self.department = department
        self.allocation_date = datetime.now()
        self.expected_return_date = expected_return_date
        self.actual_return_date = None
        self.is_active = True
        
        # Update Asset Status and Context References
        asset.transit_to(AssetStatus.ALLOCATED)
        asset.current_holder = employee
        asset.current_department = department
        
        # Append to transactional tracking logs
        target_name = employee.name if employee else department.name
        asset.allocation_history.append({
            "action": "Allocated",
            "to": target_name,
            "timestamp": self.allocation_date
        })
        
        # Self-register into the global database registry
        GLOBAL_DB.allocations[self.id] = self

    def complete_return(self, checkin_notes: str):
        """Processes the returning pipeline asset check-in sequence."""
        if not self.is_active:
            raise ValueError("Settlement Error: This allocation instance has already been closed.")
            
        self.actual_return_date = datetime.now()
        self.is_active = False
        
        # Reset target asset fields back to central pool inventory availability
        self.asset.transit_to(AssetStatus.AVAILABLE)
        self.asset.current_holder = None
        self.asset.current_department = None
        
        self.asset.allocation_history.append({
            "action": "Returned",
            "notes": checkin_notes,
            "timestamp": self.actual_return_date
        })
        GLOBAL_DB.log_activity(f"Settled allocation return for asset: {self.asset.asset_tag}")

    def __repr__(self):
        target = self.employee.name if self.employee else self.department.name
        return f"<Allocation: {self.asset.asset_tag} -> {target} | Active: {self.is_active}>"