"""
Base analyzer interface
All code analysis services should inherit from this
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging


class BaseAnalyzer(ABC):
    """
    Abstract base class for all code analysis services
    
    Provides common functionality for analyzing code
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the analyzer
        
        Args:
            logger: Optional logger instance. If not provided, creates a new one.
        """
        self.logger = logger or logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def analyze(self, code_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze code files
        
        Args:
            code_files: List of code files with content
            
        Returns:
            Analysis results dictionary
            
        Raises:
            ValueError: If input is invalid
            RuntimeError: If analysis fails
        """
        pass
    
    @abstractmethod
    def supports_language(self, language: str) -> bool:
        """
        Check if analyzer supports a specific language
        
        Args:
            language: Programming language name
            
        Returns:
            True if supported, False otherwise
        """
        pass
    
    def validate_code_files(self, code_files: List[Dict[str, Any]]) -> bool:
        """
        Validate code files input
        
        Args:
            code_files: List of code files to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not isinstance(code_files, list):
            return False
        
        for file in code_files:
            if not isinstance(file, dict):
                return False
            if 'content' not in file or 'path' not in file:
                return False
        
        return True
    
    def log_analysis(self, file_count: int, context: str = "") -> None:
        """
        Log analysis completion
        
        Args:
            file_count: Number of files analyzed
            context: Additional context for logging
        """
        self.logger.info(f"Analyzed {file_count} files {context}")
