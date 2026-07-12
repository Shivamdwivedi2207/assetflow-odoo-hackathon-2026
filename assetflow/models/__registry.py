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
        self.is_seeded = False

    def restore(self) -> bool:
        """Load the last committed application state from SQLite."""
        from data.database import SQLiteStateStore

        saved_registry = SQLiteStateStore().load()
        if not saved_registry:
            return False
        self.__dict__.update(saved_registry.__dict__)
        return True

    def persist(self) -> None:
        """Commit the current application state to SQLite."""
        from data.database import SQLiteStateStore

        SQLiteStateStore().save(self)

    def log_activity(self, message: str):
        from datetime import datetime
        self.logs.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")
        self.persist()

# Global singleton database instance
GLOBAL_DB = CentralRegistry()
