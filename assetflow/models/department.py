# models/department.py
import uuid
from ._registry import GLOBAL_DB

class Department:
    def __init__(self, name: str, parent_department=None):
        if not name.strip():
            raise ValueError("Department name cannot be empty.")
            
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.parent_department = parent_department  # Points to another Department instance
        self.manager = None  # Will hold an Employee reference once promoted
        self.is_active = True
        
        # Self-register into the global database
        GLOBAL_DB.departments[self.id] = self
        GLOBAL_DB.log_activity(f"Created Department node: {self.name} ({self.id})")

    def deactivate(self):
        """Deactivates the department entity."""
        self.is_active = False
        GLOBAL_DB.log_activity(f"Deactivated Department: {self.name}")

    def __repr__(self):
        parent_name = self.parent_department.name if self.parent_department else "None"
        return f"<Department: {self.name} | Parent: {parent_name} | Active: {self.is_active}>"