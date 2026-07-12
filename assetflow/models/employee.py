# models/employee.py
import uuid
from ._registry import GLOBAL_DB

class UserRole:
    EMPLOYEE = "Employee"
    DEPARTMENT_HEAD = "Department Head"
    ASSET_MANAGER = "Asset Manager"
    ADMIN = "Admin"

class Employee:
    def __init__(self, name: str, email: str, password: str, department=None):
        if not name.strip():
            raise ValueError("Employee name cannot be empty.")
        if "@" not in email:
            raise ValueError("Invalid email syntax format.")
            
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.email = email
        self.password = password  # Stored clear text for hackathon mockup
        self.department = department  # Points to a Department instance
        self.role = UserRole.EMPLOYEE  # Defaults to standard employee permissions
        self.is_active = True
        
        # Self-register into the global database
        GLOBAL_DB.employees[self.id] = self
        GLOBAL_DB.log_activity(f"Registered Employee: {self.name} ({self.email})")

    def change_role(self, new_role: str):
        """Allows administration accounts to promote or demote roles."""
        valid_roles = [UserRole.EMPLOYEE, UserRole.DEPARTMENT_HEAD, UserRole.ASSET_MANAGER, UserRole.ADMIN]
        if new_role not in valid_roles:
            raise ValueError(f"Invalid system security role assignment: {new_role}")
            
        self.role = new_role
        GLOBAL_DB.log_activity(f"Updated security role for {self.name} to {new_role}")

    def __repr__(self):
        dept_name = self.department.name if self.department else "Unassigned"
        return f"<Employee: {self.name} | Role: {self.role} | Department: {dept_name}>"