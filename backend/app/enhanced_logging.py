"""
Enhanced Logging System with User Type Differentiation
Provides differentiated logging with visual markers for internal and external users
"""

import logging
import time
from typing import Optional, Dict, Any, Literal
from datetime import datetime
import json

UserType = Literal["internal", "external"]

class EnhancedLogger:
    """Enhanced logging service with user type differentiation and audit trail"""
    
    def __init__(self, logger_name: str = __name__):
        self.logger = logging.getLogger(logger_name)
        self.audit_trail: list = []
        
    def log_internal_operation(self, message: str, user_id: Optional[str] = None, 
                             operation_type: str = "operation", **kwargs):
        """
        Log internal user operations with 🔐 [INTERNAL] markers
        
        Args:
            message: Log message
            user_id: Internal user ID (with internal_ prefix)
            operation_type: Type of operation being performed
            **kwargs: Additional context data
        """
        # Format the log message with internal markers
        formatted_message = f"🔐 [INTERNAL_{operation_type.upper()}] {message}"
        
        if user_id:
            formatted_message += f" | User: {user_id}"
        
        # Add additional context if provided
        if kwargs:
            context_str = " | ".join([f"{k}: {v}" for k, v in kwargs.items()])
            formatted_message += f" | {context_str}"
        
        # Log the message
        self.logger.info(formatted_message)
        
        # Add to audit trail
        self._add_to_audit_trail("internal", operation_type, message, user_id, kwargs)
    
    def log_external_operation(self, message: str, user_id: Optional[str] = None,
                             operation_type: str = "operation", **kwargs):
        """
        Log external user operations with 🌐 [EXTERNAL] markers
        
        Args:
            message: Log message
            user_id: External user ID (with external_ prefix)
            operation_type: Type of operation being performed
            **kwargs: Additional context data
        """
        # Format the log message with external markers
        formatted_message = f"🌐 [EXTERNAL_{operation_type.upper()}] {message}"
        
        if user_id:
            formatted_message += f" | User: {user_id}"
        
        # Add additional context if provided
        if kwargs:
            context_str = " | ".join([f"{k}: {v}" for k, v in kwargs.items()])
            formatted_message += f" | {context_str}"
        
        # Log the message
        self.logger.info(formatted_message)
        
        # Add to audit trail
        self._add_to_audit_trail("external", operation_type, message, user_id, kwargs)
    
    def log_user_type_decision(self, user_identifier: str, detected_type: UserType, 
                             decision_context: Dict[str, Any]):
        """
        Log user type detection decisions for audit trail
        
        Args:
            user_identifier: Username or user ID
            detected_type: Detected user type
            decision_context: Context that led to the decision
        """
        marker = "🔐" if detected_type == "internal" else "🌐"
        message = f"{marker} [USER_TYPE_DETECTION] {user_identifier} classified as {detected_type.upper()}"
        
        # Add decision context
        context_str = " | ".join([f"{k}: {v}" for k, v in decision_context.items()])
        message += f" | Context: {context_str}"
        
        self.logger.info(message)
        
        # Add to audit trail with special category
        self._add_to_audit_trail(detected_type, "user_type_detection", 
                               f"User {user_identifier} classified as {detected_type}", 
                               user_identifier, decision_context)
    
    def log_database_operation(self, user_type: UserType, database_name: str, 
                             operation: str, collection: str, success: bool,
                             user_id: Optional[str] = None, error: Optional[str] = None):
        """
        Log database operations with detailed tracking
        
        Args:
            user_type: Type of user performing operation
            database_name: Name of database being accessed
            operation: Type of database operation (insert, update, find, etc.)
            collection: Collection being accessed
            success: Whether operation was successful
            user_id: User ID performing operation
            error: Error message if operation failed
        """
        marker = "🔐" if user_type == "internal" else "🌐"
        status = "SUCCESS" if success else "FAILED"
        
        message = f"{marker} [DB_{operation.upper()}] {status} | DB: {database_name} | Collection: {collection}"
        
        if user_id:
            message += f" | User: {user_id}"
        
        if not success and error:
            message += f" | Error: {error}"
        
        # Log as info for success, warning for failure
        if success:
            self.logger.info(message)
        else:
            self.logger.warning(message)
        
        # Add to audit trail
        self._add_to_audit_trail(user_type, f"db_{operation}", 
                               f"{operation} on {database_name}.{collection}", 
                               user_id, {
                                   "database": database_name,
                                   "collection": collection,
                                   "success": success,
                                   "error": error
                               })
    
    def log_migration_operation(self, user_id: str, source_db: str, target_db: str,
                              backup_db: Optional[str] = None, success: bool = True,
                              error: Optional[str] = None, data_size: Optional[int] = None):
        """
        Log data migration operations
        
        Args:
            user_id: User ID being migrated
            source_db: Source database name
            target_db: Target database name
            backup_db: Backup database name (optional)
            success: Whether migration was successful
            error: Error message if migration failed
            data_size: Size of data migrated (optional)
        """
        status = "SUCCESS" if success else "FAILED"
        message = f"🔄 [DATA_MIGRATION] {status} | User: {user_id} | {source_db} → {target_db}"
        
        if backup_db:
            message += f" + backup to {backup_db}"
        
        if data_size:
            message += f" | Size: {data_size} bytes"
        
        if not success and error:
            message += f" | Error: {error}"
        
        # Log as info for success, error for failure
        if success:
            self.logger.info(message)
        else:
            self.logger.error(message)
        
        # Add to audit trail
        self._add_to_audit_trail("internal", "data_migration",
                               f"Migration {user_id}: {source_db} → {target_db}",
                               user_id, {
                                   "source_db": source_db,
                                   "target_db": target_db,
                                   "backup_db": backup_db,
                                   "success": success,
                                   "error": error,
                                   "data_size": data_size
                               })
    
    def log_error_with_context(self, user_type: UserType, error_message: str,
                             operation_context: Dict[str, Any], user_id: Optional[str] = None):
        """
        Log errors with full context for debugging
        
        Args:
            user_type: Type of user when error occurred
            error_message: Error message
            operation_context: Context of the operation that failed
            user_id: User ID if available
        """
        marker = "🔐" if user_type == "internal" else "🌐"
        message = f"{marker} [ERROR] {error_message}"
        
        if user_id:
            message += f" | User: {user_id}"
        
        # Add operation context
        context_str = " | ".join([f"{k}: {v}" for k, v in operation_context.items()])
        message += f" | Context: {context_str}"
        
        self.logger.error(message)
        
        # Add to audit trail
        self._add_to_audit_trail(user_type, "error", error_message, user_id, operation_context)
    
    def _add_to_audit_trail(self, user_type: UserType, operation_type: str, 
                          message: str, user_id: Optional[str], context: Dict[str, Any]):
        """
        Add entry to audit trail for compliance and debugging
        
        Args:
            user_type: Type of user
            operation_type: Type of operation
            message: Log message
            user_id: User ID if available
            context: Additional context data
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_type": user_type,
            "operation_type": operation_type,
            "message": message,
            "user_id": user_id,
            "context": context
        }
        
        # Keep only last 1000 entries to prevent memory issues
        self.audit_trail.append(audit_entry)
        if len(self.audit_trail) > 1000:
            self.audit_trail = self.audit_trail[-1000:]
    
    def get_audit_trail(self, user_type: Optional[UserType] = None, 
                       operation_type: Optional[str] = None,
                       limit: int = 100) -> list:
        """
        Get audit trail entries with optional filtering
        
        Args:
            user_type: Filter by user type (optional)
            operation_type: Filter by operation type (optional)
            limit: Maximum number of entries to return
            
        Returns:
            List of audit trail entries
        """
        filtered_entries = self.audit_trail
        
        if user_type:
            filtered_entries = [e for e in filtered_entries if e["user_type"] == user_type]
        
        if operation_type:
            filtered_entries = [e for e in filtered_entries if e["operation_type"] == operation_type]
        
        # Return most recent entries first
        return list(reversed(filtered_entries))[-limit:]
    
    def clear_audit_trail(self):
        """Clear the audit trail (use with caution)"""
        self.audit_trail.clear()
        self.logger.info("🧹 [AUDIT] Audit trail cleared")

# Global enhanced logger instance
enhanced_logger = EnhancedLogger("database_restructuring")

# Convenience functions for common logging operations
def log_internal_scan(message: str, user_id: str, **kwargs):
    """Log internal scan operations"""
    enhanced_logger.log_internal_operation(message, user_id, "scan", **kwargs)

def log_external_scan(message: str, user_id: str, **kwargs):
    """Log external scan operations"""
    enhanced_logger.log_external_operation(message, user_id, "scan", **kwargs)

def log_internal_analysis(message: str, user_id: str, **kwargs):
    """Log internal analysis operations"""
    enhanced_logger.log_internal_operation(message, user_id, "analysis", **kwargs)

def log_external_analysis(message: str, user_id: str, **kwargs):
    """Log external analysis operations"""
    enhanced_logger.log_external_operation(message, user_id, "analysis", **kwargs)

def log_user_type_detection(user_identifier: str, detected_type: UserType, context: Dict[str, Any]):
    """Log user type detection decisions"""
    enhanced_logger.log_user_type_decision(user_identifier, detected_type, context)

def log_database_op(user_type: UserType, database: str, operation: str, collection: str, 
                   success: bool, user_id: Optional[str] = None, error: Optional[str] = None):
    """Log database operations"""
    enhanced_logger.log_database_operation(user_type, database, operation, collection, 
                                         success, user_id, error)

def log_migration(user_id: str, source_db: str, target_db: str, backup_db: Optional[str] = None,
                 success: bool = True, error: Optional[str] = None, data_size: Optional[int] = None):
    """Log migration operations"""
    enhanced_logger.log_migration_operation(user_id, source_db, target_db, backup_db, 
                                          success, error, data_size)

def log_error_with_context(user_type: UserType, error: str, context: Dict[str, Any], 
                          user_id: Optional[str] = None):
    """Log errors with context"""
    enhanced_logger.log_error_with_context(user_type, error, context, user_id)

def get_audit_trail(user_type: Optional[UserType] = None, operation_type: Optional[str] = None, 
                   limit: int = 100) -> list:
    """Get audit trail entries"""
    return enhanced_logger.get_audit_trail(user_type, operation_type, limit)