"""
Database package for comprehensive GitHub integration.
"""

# Import from the main database module
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import the main database functions
try:
    from .connection import db_manager, get_database
    from .collections import Collections
except ImportError:
    # Fallback imports
    db_manager = None
    get_database = None
    Collections = None

from .schema_manager import SchemaManager, initialize_database_schema, get_database_health
from .migrations import DatabaseMigrator, run_full_migration, cleanup_database, validate_database_integrity
from .utils import DatabaseUtils, ensure_indexes_exist, convert_object_ids, validate_document_schema

__all__ = [
    "db_manager", "get_database", "Collections",
    "SchemaManager", "initialize_database_schema", "get_database_health",
    "DatabaseMigrator", "run_full_migration", "cleanup_database", "validate_database_integrity",
    "DatabaseUtils", "ensure_indexes_exist", "convert_object_ids", "validate_document_schema"
]