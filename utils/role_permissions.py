import datetime
from datetime import timedelta

class RolePermissions:
    """Define role-based permissions and access controls"""
    
    # Role level definitions (lower number = higher authority)
    MANAGER = 1
    ASST_MANAGER = 2
    GENERAL_EMPLOYEE = 3
    
    @staticmethod
    def get_role_level(role_name):
        """Convert role name to role level."""
        role_map = {
            "Manager": RolePermissions.MANAGER,
            "Asst. Manager": RolePermissions.ASST_MANAGER,
            "General Employee": RolePermissions.GENERAL_EMPLOYEE
        }
        return role_map.get(role_name, RolePermissions.GENERAL_EMPLOYEE)
    
    @staticmethod
    def get_role_name(role_level):
        """Convert role level to role name."""
        role_map = {
            RolePermissions.MANAGER: "Manager",
            RolePermissions.ASST_MANAGER: "Asst. Manager",
            RolePermissions.GENERAL_EMPLOYEE: "General Employee"
        }
        return role_map.get(role_level, "General Employee")
    
    @staticmethod
    def can_create_employees(user_role_level):
        """Check if the role can create employee accounts."""
        return user_role_level <= RolePermissions.ASST_MANAGER  # Manager and Asst. Manager can create
    
    @staticmethod
    def can_assign_tasks_to(user_role_level, target_role_level):
        """Check if user role can assign tasks to target role."""
        if user_role_level == RolePermissions.MANAGER:
            # Manager can assign to Asst. Manager and General Employee
            return target_role_level >= RolePermissions.ASST_MANAGER
        elif user_role_level == RolePermissions.ASST_MANAGER:
            # Asst. Manager can only assign to General Employee
            return target_role_level == RolePermissions.GENERAL_EMPLOYEE
        else:
            # General Employee cannot assign tasks
            return False
    
    @staticmethod
    def can_view_reports_of(user_role_level, target_role_level):
        """Check if user role can view reports from target role."""
        if user_role_level == RolePermissions.MANAGER:
            # Manager can view all reports in their branch
            return True
        elif user_role_level == RolePermissions.ASST_MANAGER:
            # Asst. Manager can view their own and General Employee reports
            return target_role_level >= RolePermissions.ASST_MANAGER
        else:
            # General Employee can only view their own reports
            return user_role_level == target_role_level
    
    @staticmethod
    def can_deactivate_role(user_role_level, target_role_level):
        """Check if user role can deactivate/reactivate target role."""
        if user_role_level == RolePermissions.MANAGER:
            # Manager can deactivate Asst. Manager and General Employee
            return target_role_level > user_role_level
        elif user_role_level == RolePermissions.ASST_MANAGER:
            # Asst. Manager can only deactivate General Employees
            return target_role_level == RolePermissions.GENERAL_EMPLOYEE
        else:
            # General Employee cannot deactivate anyone
            return False
