"""
Complexity Analyzer
Analyzes code complexity using AST parsing for multiple languages
"""

import ast
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ComplexityMetrics:
    """Container for complexity metrics"""
    cyclomatic_complexity: float = 0.0
    cognitive_complexity: float = 0.0
    maintainability_index: float = 0.0
    lines_of_code: int = 0
    function_count: int = 0
    class_count: int = 0
    average_function_length: float = 0.0
    max_function_complexity: float = 0.0


class ComplexityAnalyzer:
    """
    Analyzes code complexity for multiple programming languages
    
    Supports: Python, JavaScript, TypeScript, Java
    """
    
    def __init__(self):
        """Initialize complexity analyzer"""
        self.logger = logger
    
    def analyze_code(
        self,
        code: str,
        language: str,
        filename: str = ""
    ) -> ComplexityMetrics:
        """
        Analyze code complexity
        
        Args:
            code: Source code string
            language: Programming language
            filename: Optional filename
            
        Returns:
            ComplexityMetrics object
        """
        language = language.lower()
        
        try:
            if language == 'python':
                return self._analyze_python(code)
            elif language in ['javascript', 'typescript', 'jsx', 'tsx']:
                return self._analyze_javascript(code)
            elif language == 'java':
                return self._analyze_java(code)
            else:
                # Generic analysis for unsupported languages
                return self._analyze_generic(code)
                
        except Exception as e:
            self.logger.error(f"Error analyzing {language} code: {e}")
            return ComplexityMetrics()
    
    def _analyze_python(self, code: str) -> ComplexityMetrics:
        """
        Analyze Python code using AST
        
        Args:
            code: Python source code
            
        Returns:
            ComplexityMetrics object
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.logger.warning(f"Python syntax error: {e}")
            return self._analyze_generic(code)
        
        metrics = ComplexityMetrics()
        
        # Count lines of code (excluding blank lines and comments)
        lines = [line.strip() for line in code.split('\n')]
        metrics.lines_of_code = sum(
            1 for line in lines
            if line and not line.startswith('#')
        )
        
        # Analyze functions and classes
        function_complexities = []
        function_lengths = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                metrics.class_count += 1
            
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metrics.function_count += 1
                
                # Calculate cyclomatic complexity for function
                complexity = self._calculate_python_cyclomatic(node)
                function_complexities.append(complexity)
                
                # Calculate function length
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    length = node.end_lineno - node.lineno + 1
                    function_lengths.append(length)
        
        # Calculate aggregate metrics
        if function_complexities:
            metrics.cyclomatic_complexity = sum(function_complexities) / len(function_complexities)
            metrics.max_function_complexity = max(function_complexities)
        
        if function_lengths:
            metrics.average_function_length = sum(function_lengths) / len(function_lengths)
        
        # Estimate cognitive complexity (simplified)
        metrics.cognitive_complexity = self._estimate_cognitive_complexity(code)
        
        # Calculate maintainability index
        metrics.maintainability_index = self._calculate_maintainability_index(
            metrics.lines_of_code,
            metrics.cyclomatic_complexity,
            metrics.function_count
        )
        
        return metrics
    
    def _calculate_python_cyclomatic(self, node: ast.AST) -> int:
        """
        Calculate cyclomatic complexity for a Python function
        
        Args:
            node: AST node (function)
            
        Returns:
            Cyclomatic complexity score
        """
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points increase complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _analyze_javascript(self, code: str) -> ComplexityMetrics:
        """
        Analyze JavaScript/TypeScript code
        
        Uses regex-based analysis (simplified)
        
        Args:
            code: JavaScript/TypeScript source code
            
        Returns:
            ComplexityMetrics object
        """
        metrics = ComplexityMetrics()
        
        # Count lines of code
        lines = [line.strip() for line in code.split('\n')]
        metrics.lines_of_code = sum(
            1 for line in lines
            if line and not line.startswith('//') and not line.startswith('/*')
        )
        
        # Count functions
        function_patterns = [
            r'function\s+\w+\s*\(',  # function name()
            r'\w+\s*:\s*function\s*\(',  # name: function()
            r'\w+\s*=\s*function\s*\(',  # name = function()
            r'\w+\s*=\s*\([^)]*\)\s*=>',  # name = () =>
            r'async\s+function\s+\w+\s*\(',  # async function
        ]
        
        for pattern in function_patterns:
            metrics.function_count += len(re.findall(pattern, code))
        
        # Count classes
        class_pattern = r'class\s+\w+'
        metrics.class_count = len(re.findall(class_pattern, code))
        
        # Estimate cyclomatic complexity
        decision_keywords = ['if', 'else', 'for', 'while', 'case', 'catch', '&&', '||', '?']
        complexity_count = sum(
            len(re.findall(r'\b' + keyword + r'\b', code))
            for keyword in decision_keywords
        )
        
        if metrics.function_count > 0:
            metrics.cyclomatic_complexity = (complexity_count + metrics.function_count) / metrics.function_count
        else:
            metrics.cyclomatic_complexity = 1.0
        
        # Estimate cognitive complexity
        metrics.cognitive_complexity = self._estimate_cognitive_complexity(code)
        
        # Calculate maintainability index
        metrics.maintainability_index = self._calculate_maintainability_index(
            metrics.lines_of_code,
            metrics.cyclomatic_complexity,
            metrics.function_count
        )
        
        return metrics
    
    def _analyze_java(self, code: str) -> ComplexityMetrics:
        """
        Analyze Java code
        
        Uses regex-based analysis (simplified)
        
        Args:
            code: Java source code
            
        Returns:
            ComplexityMetrics object
        """
        metrics = ComplexityMetrics()
        
        # Count lines of code
        lines = [line.strip() for line in code.split('\n')]
        metrics.lines_of_code = sum(
            1 for line in lines
            if line and not line.startswith('//') and not line.startswith('/*')
        )
        
        # Count methods
        method_patterns = [
            r'(public|private|protected|static|\s)+[\w\<\>\[\]]+\s+\w+\s*\([^\)]*\)\s*\{',
        ]
        
        for pattern in method_patterns:
            metrics.function_count += len(re.findall(pattern, code))
        
        # Count classes
        class_pattern = r'(public|private|protected)?\s*class\s+\w+'
        metrics.class_count = len(re.findall(class_pattern, code))
        
        # Estimate cyclomatic complexity
        decision_keywords = ['if', 'else', 'for', 'while', 'case', 'catch', '&&', '||', '?']
        complexity_count = sum(
            len(re.findall(r'\b' + keyword + r'\b', code))
            for keyword in decision_keywords
        )
        
        if metrics.function_count > 0:
            metrics.cyclomatic_complexity = (complexity_count + metrics.function_count) / metrics.function_count
        else:
            metrics.cyclomatic_complexity = 1.0
        
        # Estimate cognitive complexity
        metrics.cognitive_complexity = self._estimate_cognitive_complexity(code)
        
        # Calculate maintainability index
        metrics.maintainability_index = self._calculate_maintainability_index(
            metrics.lines_of_code,
            metrics.cyclomatic_complexity,
            metrics.function_count
        )
        
        return metrics
    
    def _analyze_generic(self, code: str) -> ComplexityMetrics:
        """
        Generic code analysis for unsupported languages
        
        Args:
            code: Source code
            
        Returns:
            ComplexityMetrics object
        """
        metrics = ComplexityMetrics()
        
        # Count lines of code
        lines = [line.strip() for line in code.split('\n')]
        metrics.lines_of_code = len([line for line in lines if line])
        
        # Estimate complexity based on common patterns
        decision_keywords = ['if', 'else', 'for', 'while', 'case', 'catch']
        complexity_count = sum(
            len(re.findall(r'\b' + keyword + r'\b', code, re.IGNORECASE))
            for keyword in decision_keywords
        )
        
        metrics.cyclomatic_complexity = max(1.0, complexity_count / 10.0)
        metrics.cognitive_complexity = self._estimate_cognitive_complexity(code)
        
        # Estimate maintainability
        metrics.maintainability_index = max(0, 100 - (metrics.lines_of_code / 10))
        
        return metrics
    
    def _estimate_cognitive_complexity(self, code: str) -> float:
        """
        Estimate cognitive complexity
        
        Cognitive complexity measures how difficult code is to understand
        
        Args:
            code: Source code
            
        Returns:
            Cognitive complexity score
        """
        complexity = 0
        nesting_level = 0
        
        # Track nesting with braces
        for char in code:
            if char == '{':
                nesting_level += 1
            elif char == '}':
                nesting_level = max(0, nesting_level - 1)
        
        # Count decision points with nesting penalty
        decision_keywords = ['if', 'else', 'for', 'while', 'case', 'catch']
        for keyword in decision_keywords:
            matches = re.finditer(r'\b' + keyword + r'\b', code)
            for match in matches:
                # Estimate nesting level at this point
                before = code[:match.start()]
                local_nesting = before.count('{') - before.count('}')
                complexity += 1 + max(0, local_nesting)
        
        return complexity
    
    def _calculate_maintainability_index(
        self,
        loc: int,
        complexity: float,
        function_count: int
    ) -> float:
        """
        Calculate maintainability index
        
        Based on Microsoft's maintainability index formula (simplified)
        
        Args:
            loc: Lines of code
            complexity: Cyclomatic complexity
            function_count: Number of functions
            
        Returns:
            Maintainability index (0-100, higher is better)
        """
        import math
        
        if loc == 0:
            return 100.0
        
        # Simplified maintainability index
        # MI = 171 - 5.2 * ln(V) - 0.23 * G - 16.2 * ln(LOC)
        # Where V = volume, G = complexity, LOC = lines of code
        
        # Estimate volume (simplified)
        volume = loc * math.log(max(1, function_count))
        
        # Calculate MI
        mi = 171 - 5.2 * math.log(max(1, volume)) - 0.23 * complexity - 16.2 * math.log(max(1, loc))
        
        # Normalize to 0-100 scale
        mi = max(0, min(100, mi))
        
        return round(mi, 1)
    
    def analyze_repository(
        self,
        files: List[Tuple[str, str, str]]
    ) -> ComplexityMetrics:
        """
        Analyze complexity for multiple files in a repository
        
        Args:
            files: List of (filename, language, code) tuples
            
        Returns:
            Aggregated ComplexityMetrics
        """
        if not files:
            return ComplexityMetrics()
        
        all_metrics = []
        
        for filename, language, code in files:
            try:
                metrics = self.analyze_code(code, language, filename)
                all_metrics.append(metrics)
            except Exception as e:
                self.logger.error(f"Error analyzing {filename}: {e}")
        
        if not all_metrics:
            return ComplexityMetrics()
        
        # Aggregate metrics
        aggregated = ComplexityMetrics()
        
        aggregated.lines_of_code = sum(m.lines_of_code for m in all_metrics)
        aggregated.function_count = sum(m.function_count for m in all_metrics)
        aggregated.class_count = sum(m.class_count for m in all_metrics)
        
        # Average complexity metrics
        if all_metrics:
            aggregated.cyclomatic_complexity = sum(
                m.cyclomatic_complexity for m in all_metrics
            ) / len(all_metrics)
            
            aggregated.cognitive_complexity = sum(
                m.cognitive_complexity for m in all_metrics
            ) / len(all_metrics)
            
            aggregated.maintainability_index = sum(
                m.maintainability_index for m in all_metrics
            ) / len(all_metrics)
        
        # Calculate average function length
        total_functions = aggregated.function_count
        if total_functions > 0:
            aggregated.average_function_length = aggregated.lines_of_code / total_functions
        
        # Find max complexity
        if all_metrics:
            aggregated.max_function_complexity = max(
                m.max_function_complexity for m in all_metrics
            )
        
        return aggregated
    
    def get_complexity_grade(self, complexity: float) -> str:
        """
        Get letter grade for complexity score
        
        Args:
            complexity: Complexity score
            
        Returns:
            Letter grade (A-F)
        """
        if complexity <= 5:
            return 'A'
        elif complexity <= 10:
            return 'B'
        elif complexity <= 20:
            return 'C'
        elif complexity <= 30:
            return 'D'
        else:
            return 'F'
    
    def get_maintainability_grade(self, mi: float) -> str:
        """
        Get letter grade for maintainability index
        
        Args:
            mi: Maintainability index (0-100)
            
        Returns:
            Letter grade (A-F)
        """
        if mi >= 85:
            return 'A'
        elif mi >= 70:
            return 'B'
        elif mi >= 50:
            return 'C'
        elif mi >= 30:
            return 'D'
        else:
            return 'F'
