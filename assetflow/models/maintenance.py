# models/maintenance.py
import uuid
from ._registry import GLOBAL_DB
from .asset import AssetStatus

class MaintenanceStatus:
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"

class Maintenance:
    def __init__(self, asset, raised_by, description: str, priority: str = "Medium"):
        if not description.strip():
            raise ValueError("Maintenance issue description cannot be empty.")
            
        self.id = str(uuid.uuid4())[:8]
        self.asset = asset
        self.raised_by = raised_by  # Points to an Employee instance
        self.description = description
        self.priority = priority
        self.status = MaintenanceStatus.PENDING
        self.technician = None
        
        # Link to the asset's direct maintenance log history
        asset.maintenance_history.append(self)
        
        # Self-register into the global database registry
        GLOBAL_DB.maintenance_records[self.id] = self
        GLOBAL_DB.log_activity(f"Logged Maintenance Request {self.id} for Asset {asset.asset_tag}")

    def approve_request(self):
        """Manager workflow: Approves the ticket and flags the asset as out-of-service."""
        if self.status != MaintenanceStatus.PENDING:
            raise RuntimeError(f"Cannot approve a maintenance request that is in '{self.status}' state.")
            
        self.status = MaintenanceStatus.APPROVED
        self.asset.transit_to(AssetStatus.UNDER_MAINTENANCE)
        GLOBAL_DB.log_activity(f"Approved Maintenance {self.id}; Asset {self.asset.asset_tag} pulled out of service.")

    def assign_technician(self, technician_name: str):
        """Assigns a technician and starts work execution."""
        if self.status != MaintenanceStatus.APPROVED:
            raise RuntimeError("Cannot assign a technician until the request has been approved.")
        
        self.technician = technician_name
        self.status = MaintenanceStatus.IN_PROGRESS
        GLOBAL_DB.log_activity(f"Technician '{technician_name}' assigned to Job {self.id}")

    def resolve_repairs(self):
        """Closes out the maintenance cycle and restores the asset to service availability."""
        if self.status != MaintenanceStatus.IN_PROGRESS:
            raise RuntimeError("Cannot resolve repairs that are not currently in progress.")
            
        self.status = MaintenanceStatus.RESOLVED
        self.asset.transit_to(AssetStatus.AVAILABLE)
        GLOBAL_DB.log_activity(f"Resolved Maintenance {self.id}; Asset {self.asset.asset_tag} restored to central pool.")

    def reject_request(self):
        """Manager workflow: Rejects the request ticket."""
        if self.status != MaintenanceStatus.PENDING:
            raise RuntimeError("Can only reject pending requests.")
        self.status = MaintenanceStatus.REJECTED
        GLOBAL_DB.log_activity(f"Rejected Maintenance Request {self.id}")

    def __repr__(self):
        return f"<Maintenance: Job {self.id} | Asset: {self.asset.asset_tag} | Status: {self.status}>"