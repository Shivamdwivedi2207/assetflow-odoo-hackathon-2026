# models/_init_.py
from .department import Department
from .employee import Employee
from .asset_category import AssetCategory
from .asset import Asset
from .allocation import Allocation
from .maintenance import Maintenance

__all__ = [
    'Department',
    'Employee',
    'AssetCategory',
    'Asset',
    'Allocation',
    'Maintenance'
]