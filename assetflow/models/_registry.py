# models/_registry.py
class CentralRegistry:
    def __init__(self):
        self.departments = {}
        self.employees = {}
        self.categories = {}
        self.assets = {}
        self.allocations = {}
        self.maintenance_records = {}
        self.bookings = {}
        self.logs = []

    def log_activity(self, message: str):
        from datetime import datetime
        self.logs.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

# Global singleton database instance
GLOBAL_DB = CentralRegistry()