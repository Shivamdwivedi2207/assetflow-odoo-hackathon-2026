# models/asset_category.py
import uuid
from ._registry import GLOBAL_DB

class AssetCategory:
    def __init__(self, name: str, specific_attributes: dict = None):
        if not name.strip():
            raise ValueError("Asset Category name cannot be empty.")
            
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        # Schema dictionary for category-specific fields (e.g., {"Warranty": "2 Years"})
        self.specific_attributes = specific_attributes if specific_attributes else {}
        
        # Self-register into the global database
        GLOBAL_DB.categories[self.id] = self
        GLOBAL_DB.log_activity(f"Created Asset Category: {self.name}")

    def update_attributes(self, new_attributes: dict):
        """Appends or alters category configurations."""
        self.specific_attributes.update(new_attributes)
        GLOBAL_DB.log_activity(f"Updated metadata schema parameters for Category: {self.name}")

    def __repr__(self):
        return f"<AssetCategory: {self.name} | Custom Fields: {list(self.specific_attributes.keys())}>"