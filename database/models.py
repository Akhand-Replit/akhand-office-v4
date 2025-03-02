# This file serves as an import aggregator to maintain backward compatibility
# Import all model classes from their respective files
from database.models.company_model import CompanyModel
from database.models.branch_model import BranchModel
from database.models.employee_model import EmployeeModel 
from database.models.report_model import ReportModel
from database.models.role_model import RoleModel
from database.models.task_model import TaskModel
from database.models.message_model import MessageModel

# Export all models for backward compatibility
__all__ = [
    'CompanyModel',
    'BranchModel',
    'EmployeeModel',
    'ReportModel',
    'RoleModel',
    'TaskModel',
    'MessageModel'
]