# wizard/return_wizard.py
from models._registry import GLOBAL_DB

class ReturnWizard:
    def __init__(self, asset_id: str):
        self.asset = GLOBAL_DB.assets.get(asset_id)
        if not self.asset:
            raise ValueError("Target asset entity could not be found.")
            
        # Find the active allocation link for this asset
        self.active_allocation = next(
            (al for al in GLOBAL_DB.allocations.values() if al.asset.id == asset_id and al.is_active), 
            None
        )
        
        if not self.active_allocation:
            raise ValueError("No active allocation instance found for this asset.")
            
        self.checkin_notes = ""
        self.is_damaged = False

    def execute_return(self):
        """Finalizes the allocation tracking record and saves the inspection notes."""
        if not self.checkin_notes.strip():
            raise ValueError("Inspection check-in notes are required to complete the return workflow.")
            
        # Update asset condition state if marked as damaged during check-in
        if self.is_damaged:
            self.checkin_notes = f"[ALERT: DAMAGED] {self.checkin_notes}"
            
        # Execute the core domain method on the allocation model
        self.active_allocation.complete_return(checkin_notes=self.checkin_notes)
        
        # If damaged, automatically prompt state shift for manager review
        if self.is_damaged:
            GLOBAL_DB.log_activity(f"Wizard flagged return asset {self.asset.asset_tag} as DAMAGED.")
            
        return {"status": "success", "msg": f"Asset {self.asset.asset_tag} checked back into central inventory."}