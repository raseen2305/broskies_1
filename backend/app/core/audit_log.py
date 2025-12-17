"""
Audit Logging
Logs sensitive operations for security and compliance
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Logs sensitive operations for audit trail
    
    Stores audit logs in database for compliance and security monitoring
    """
    
    def __init__(self, database: Optional[AsyncIOMotorDatabase] = None):
        """
        Initialize audit logger
        
        Args:
            database: MongoDB database instance (optional)
        """
        self.db = database
        self.logger = logger
    
    async def log_operation(
        self,
        operation: str,
        user_id: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        action: str = "access",
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ):
        """
        Log an auditable operation
        
        Args:
            operation: Operation name (e.g., "quick_scan", "deep_analysis")
            user_id: User performing the operation
            resource_type: Type of resource (e.g., "repository", "user_profile")
            resource_id: ID of the resource (optional)
            action: Action performed (e.g., "access", "create", "update", "delete")
            status: Operation status (e.g., "success", "failure", "denied")
            details: Additional details (optional)
            ip_address: User's IP address (optional)
        """
        try:
            audit_entry = {
                'timestamp': datetime.utcnow(),
                'operation': operation,
                'user_id': user_id,
                'resource_type': resource_type,
                'resource_id': resource_id,
                'action': action,
                'status': status,
                'details': details or {},
                'ip_address': ip_address
            }
            
            # Log to application logger
            self.logger.info(
                f"AUDIT: {operation} - User: {user_id}, "
                f"Resource: {resource_type}/{resource_id}, "
                f"Action: {action}, Status: {status}"
            )
            
            # Store in database if available
            if self.db is not None:
                try:
                    await self.db.audit_logs.insert_one(audit_entry)
                except Exception as db_error:
                    self.logger.error(f"Failed to store audit log in database: {db_error}")
            
        except Exception as e:
            self.logger.error(f"Audit logging failed: {e}")
            # Don't raise - audit logging should never break the application
    
    async def log_authentication(
        self,
        user_id: str,
        auth_method: str,
        status: str,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log authentication attempt
        
        Args:
            user_id: User ID
            auth_method: Authentication method (e.g., "oauth", "jwt")
            status: Authentication status (e.g., "success", "failure")
            ip_address: User's IP address (optional)
            details: Additional details (optional)
        """
        await self.log_operation(
            operation="authentication",
            user_id=user_id,
            resource_type="user",
            resource_id=user_id,
            action="authenticate",
            status=status,
            details={
                'auth_method': auth_method,
                **(details or {})
            },
            ip_address=ip_address
        )
    
    async def log_authorization_failure(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        reason: str,
        ip_address: Optional[str] = None
    ):
        """
        Log authorization failure
        
        Args:
            user_id: User ID
            resource_type: Type of resource
            resource_id: ID of the resource
            action: Attempted action
            reason: Reason for denial
            ip_address: User's IP address (optional)
        """
        await self.log_operation(
            operation="authorization_check",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            status="denied",
            details={'reason': reason},
            ip_address=ip_address
        )
    
    async def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        access_type: str = "read",
        ip_address: Optional[str] = None
    ):
        """
        Log data access
        
        Args:
            user_id: User ID
            resource_type: Type of resource
            resource_id: ID of the resource
            access_type: Type of access (e.g., "read", "write")
            ip_address: User's IP address (optional)
        """
        await self.log_operation(
            operation="data_access",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=access_type,
            status="success",
            ip_address=ip_address
        )
    
    async def log_sensitive_operation(
        self,
        operation: str,
        user_id: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None
    ):
        """
        Log sensitive operation
        
        Args:
            operation: Operation name
            user_id: User ID
            details: Operation details
            ip_address: User's IP address (optional)
        """
        await self.log_operation(
            operation=operation,
            user_id=user_id,
            resource_type="sensitive",
            action="execute",
            status="success",
            details=details,
            ip_address=ip_address
        )


# Global instance
_audit_logger = None


def get_audit_logger(database: Optional[AsyncIOMotorDatabase] = None) -> AuditLogger:
    """
    Get global audit logger instance
    
    Args:
        database: MongoDB database instance (optional)
        
    Returns:
        AuditLogger instance
    """
    global _audit_logger
    
    if _audit_logger is None or (database and _audit_logger.db is None):
        _audit_logger = AuditLogger(database)
    
    return _audit_logger


# Convenience functions
async def audit_log(
    operation: str,
    user_id: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    action: str = "access",
    status: str = "success",
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    database: Optional[AsyncIOMotorDatabase] = None
):
    """
    Log an auditable operation
    
    Args:
        operation: Operation name
        user_id: User performing the operation
        resource_type: Type of resource
        resource_id: ID of the resource (optional)
        action: Action performed
        status: Operation status
        details: Additional details (optional)
        ip_address: User's IP address (optional)
        database: MongoDB database instance (optional)
    """
    logger_instance = get_audit_logger(database)
    await logger_instance.log_operation(
        operation, user_id, resource_type, resource_id,
        action, status, details, ip_address
    )
