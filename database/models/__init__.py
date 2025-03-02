# Import all models directly in __init__.py to make them available via the models package
from database.models.company_model import CompanyModel
from database.models.branch_model import BranchModel
from database.models.employee_model import EmployeeModel
from database.models.report_model import ReportModel
from database.models.role_model import RoleModel
from database.models.task_model import TaskModel
from database.models.message_model import MessageModel

# Export all models for easy importing
__all__ = [
    'CompanyModel',
    'BranchModel',
    'EmployeeModel',
    'ReportModel',
    'RoleModel',
    'TaskModel',
    'MessageModel'
]

# Create the necessary __init__.py files for proper Python package structure

# config/__init__.py
# Empty file to make the directory a Python package

# database/__init__.py
# Empty file to make the directory a Python package

# database/models/__init__.py
# Empty file to make the directory a Python package

# pages/__init__.py
# Empty file to make the directory a Python package

# pages/admin/__init__.py
# Empty file to make the directory a Python package

# pages/common/__init__.py
# Empty file to make the directory a Python package

# pages/company/__init__.py
# Empty file to make the directory a Python package

# pages/employee/__init__.py
# Empty file to make the directory a Python package

# pages/login/__init__.py
# Empty file to make the directory a Python package

# styles/__init__.py
# Empty file to make the directory a Python package

# utils/__init__.py
# Empty file to make the directory a Python package
