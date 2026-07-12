# models/asset.py
import uuid
from datetime import datetime
from ._registry import GLOBAL_DB

class AssetStatus:
    AVAILABLE = "Available"
    ALLOCATED = "Allocated"
    RESERVED = "Reserved"
    UNDER_MAINTENANCE = "Under Maintenance"
    LOST = "Lost"
    RETIRED = "Retired"
    DISPOSED = "Disposed"

class Asset:
    _tag_sequence_counter = 1

    def __init__(self, name: str, category, serial_number: str, cost: float, location: str, is_bookable: bool = False):
        if not name.strip():
            raise ValueError("Asset name cannot be empty.")
        
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.category = category  # Points to an AssetCategory instance
        
        # Pure-Python Auto-incrementing Sequence Generator
        self.asset_tag = f"AF-{Asset._tag_sequence_counter:04d}"
        Asset._tag_sequence_counter += 1
        
        self.serial_number = serial_number
        self.acquisition_date = datetime.now()
        self.acquisition_cost = cost
        self.location = location
        self.is_bookable = is_bookable
        
        # State Machine Initialization
        self.status = AssetStatus.AVAILABLE
        self.current_holder = None  # Points to an Employee instance if allocated
        self.current_department = None  # Points to a Department instance if allocated
        
        # Relationship Logs
        self.allocation_history = []
        self.maintenance_history = []
        
        # Self-register into global state
        GLOBAL_DB.assets[self.id] = self
        GLOBAL_DB.log_activity(f"Registered Asset: {self.asset_tag} - {self.name} [{self.status}]")

    def transit_to(self, new_status: str):
        """Enforces safe asset lifecycle state machine rules."""
        valid_transitions = {
            AssetStatus.AVAILABLE: [AssetStatus.ALLOCATED, AssetStatus.RESERVED, AssetStatus.UNDER_MAINTENANCE, AssetStatus.LOST, AssetStatus.RETIRED],
            AssetStatus.ALLOCATED: [AssetStatus.AVAILABLE, AssetStatus.UNDER_MAINTENANCE, AssetStatus.LOST],
            AssetStatus.RESERVED: [AssetStatus.AVAILABLE, AssetStatus.ALLOCATED],
            AssetStatus.UNDER_MAINTENANCE: [AssetStatus.AVAILABLE, AssetStatus.RETIRED],
            AssetStatus.LOST: [AssetStatus.AVAILABLE, AssetStatus.DISPOSED],
            AssetStatus.RETIRED: [AssetStatus.DISPOSED],
            AssetStatus.DISPOSED: []
        }
        
        if new_status not in valid_transitions.get(self.status, []):
            raise RuntimeError(f"Illegal lifecycle transition: Cannot shift asset from '{self.status}' to '{new_status}'.")
            
        old_status = self.status
        self.status = new_status
        GLOBAL_DB.log_activity(f"Asset {self.asset_tag} shifted status: {old_status} -> {new_status}")

    def __repr__(self):
        return f"<{self.asset_tag}: {self.name} | Status: {self.status} | Location: {self.location}>"