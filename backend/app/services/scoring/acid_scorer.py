"""
ACID Scorer
Calculates ACID scores for code quality assessment
100% deterministic scoring - same input always produces same output
"""

import re
import ast
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

from .complexity_analyzer import ComplexityAnalyzer, ComplexityMetrics

logger = logging.getLogger(__name__)


@dataclass
class ACIDScores:
    """Container for ACID scores"""
    atomicity: float = 0.0
    consistency: float = 0.0
    isolation: float = 0.0
    durability: float = 0.0
    overall: float = 0.0


class ACIDScorer:
    """
    ACID Scorer for code quality assessment
    
    ACID Components:
    - Atomicity: Modularity, single responsibility, function size, cohesion
    - Consistency: Naming conventions, code style, documentation
    - Isolation: Dependencies, architecture, coupling
    - Durability: Tests, documentation, maintainability
    
    All scoring is deterministic - same input produces same output
    """
    
    def __init__(self):
        """Initialize ACID scorer"""
        self.logger = logger
        self.complexity_analyzer = ComplexityAnalyzer()
    
    def calculate_acid_scores(
        self,
        files: List[Tuple[str, str, str]],
        repo_metadata: Dict[str, Any]
    ) -> ACIDScores:
        """
        Calculate ACID scores for a repository
        
        Args:
            files: List of (filename, language, code) tuples
            repo_metadata: Repository metadata (has_tests, has_ci_cd, etc.)
            
        Returns:
            ACIDScores object
        """
        if not files:
            return ACIDScores()
        
        # Calculate complexity metrics
        complexity = self.complexity_analyzer.analyze_repository(files)
        
        # Calculate each ACID component
        atomicity = self._calculate_atomicity(files, complexity)
        consistency = self._calculate_consistency(files, complexity)
        isolation = self._calculate_isolation(files, repo_metadata)
        durability = self._calculate_durability(files, repo_metadata, complexity)
        
        # Calculate overall score (weighted average)
        overall = (atomicity + consistency + isolation + durability) / 4.0
        
        return ACIDScores(
            atomicity=round(atomicity, 1),
            consistency=round(consistency, 1),
            isolation=round(isolation, 1),
            durability=round(durability, 1),
            overall=round(overall, 1)
        )
    
    def _calculate_atomicity(
        self,
        files: List[Tuple[str, str, str]],
        complexity: ComplexityMetrics
    ) -> float:
        """
        Calculate Atomicity score
        
        Measures: Modularity, single responsibility, function size, cohesion
        
        Args:
            files: List of code files
            complexity: Complexity metrics
            
        Returns:
            Atomicity score (0-100)
        """
        score = 100.0
        
        # 1. Function size (25 points)
        # Smaller functions are better
        if complexity.average_function_length > 0:
            if complexity.average_function_length <= 20:
                function_size_score = 25.0
            elif complexity.average_function_length <= 50:
                function_size_score = 20.0
            elif complexity.average_function_length <= 100:
                function_size_score = 15.0
            elif complexity.average_function_length <= 200:
                function_size_score = 10.0
            else:
                function_size_score = 5.0
        else:
            function_size_score = 15.0  # Default for no functions
        
        # 2. Function complexity (25 points)
        # Lower complexity indicates better single responsibility
        if complexity.cyclomatic_complexity <= 5:
            complexity_score = 25.0
        elif complexity.cyclomatic_complexity <= 10:
            complexity_score = 20.0
        elif complexity.cyclomatic_complexity <= 15:
            complexity_score = 15.0
        elif complexity.cyclomatic_complexity <= 20:
            complexity_score = 10.0
        else:
            complexity_score = 5.0
        
        # 3. Modularity (25 points)
        # More files with reasonable size indicates better modularity
        file_count = len(files)
        total_loc = complexity.lines_of_code
        
        if file_count > 0 and total_loc > 0:
            avg_file_size = total_loc / file_count
            
            if avg_file_size <= 200:
                modularity_score = 25.0
            elif avg_file_size <= 500:
                modularity_score = 20.0
            elif avg_file_size <= 1000:
                modularity_score = 15.0
            else:
                modularity_score = 10.0
        else:
            modularity_score = 15.0
        
        # 4. Class/Function ratio (25 points)
        # Good balance indicates proper organization
        if complexity.function_count > 0:
            if complexity.class_count > 0:
                ratio = complexity.function_count / complexity.class_count
                if 2 <= ratio <= 10:
                    ratio_score = 25.0
                elif 1 <= ratio <= 15:
                    ratio_score = 20.0
                else:
                    ratio_score = 15.0
            else:
                # No classes - functional style
                ratio_score = 20.0
        else:
            ratio_score = 10.0
        
        score = function_size_score + complexity_score + modularity_score + ratio_score
        
        return min(100.0, max(0.0, score))
    
    def _calculate_consistency(
        self,
        files: List[Tuple[str, str, str]],
        complexity: ComplexityMetrics
    ) -> float:
        """
        Calculate Consistency score
        
        Measures: Naming conventions, code style, documentation
        
        Args:
            files: List of code files
            complexity: Complexity metrics
            
        Returns:
            Consistency score (0-100)
        """
        score = 0.0
        
        # Analyze all files
        naming_scores = []
        comment_scores = []
        style_scores = []
        
        for filename, language, code in files:
            # 1. Naming conventions (33 points)
            naming_score = self._analyze_naming_conventions(code, language)
            naming_scores.append(naming_score)
            
            # 2. Documentation/Comments (33 points)
            comment_score = self._analyze_documentation(code, language)
            comment_scores.append(comment_score)
            
            # 3. Code style consistency (34 points)
            style_score = self._analyze_code_style(code, language)
            style_scores.append(style_score)
        
        # Average scores across all files
        if naming_scores:
            score += sum(naming_scores) / len(naming_scores)
        if comment_scores:
            score += sum(comment_scores) / len(comment_scores)
        if style_scores:
            score += sum(style_scores) / len(style_scores)
        
        return min(100.0, max(0.0, score))
    
    def _analyze_naming_conventions(self, code: str, language: str) -> float:
        """
        Analyze naming conventions
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            Naming score (0-33)
        """
        score = 33.0
        
        # Check for consistent naming patterns
        if language.lower() == 'python':
            # Python: snake_case for functions/variables, PascalCase for classes
            snake_case_count = len(re.findall(r'\b[a-z_][a-z0-9_]*\b', code))
            pascal_case_count = len(re.findall(r'\b[A-Z][a-zA-Z0-9]*\b', code))
            
            # Good if we have both patterns (functions and classes)
            if snake_case_count > 0 and pascal_case_count > 0:
                score = 33.0
            elif snake_case_count > 0 or pascal_case_count > 0:
                score = 25.0
            else:
                score = 15.0
        
        elif language.lower() in ['javascript', 'typescript', 'java']:
            # camelCase for functions/variables, PascalCase for classes
            camel_case_count = len(re.findall(r'\b[a-z][a-zA-Z0-9]*\b', code))
            pascal_case_count = len(re.findall(r'\b[A-Z][a-zA-Z0-9]*\b', code))
            
            if camel_case_count > 0 and pascal_case_count > 0:
                score = 33.0
            elif camel_case_count > 0 or pascal_case_count > 0:
                score = 25.0
            else:
                score = 15.0
        
        # Check for descriptive names (not single letters except in loops)
        single_letter_vars = len(re.findall(r'\b[a-z]\b', code))
        total_identifiers = len(re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code))
        
        if total_identifiers > 0:
            single_letter_ratio = single_letter_vars / total_identifiers
            if single_letter_ratio > 0.3:
                score *= 0.8  # Penalty for too many single-letter variables
        
        return score
    
    def _analyze_documentation(self, code: str, language: str) -> float:
        """
        Analyze documentation and comments
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            Documentation score (0-33)
        """
        lines = code.split('\n')
        total_lines = len([l for l in lines if l.strip()])
        
        if total_lines == 0:
            return 0.0
        
        # Count comment lines
        comment_lines = 0
        
        if language.lower() == 'python':
            # Python comments and docstrings
            comment_lines = len([l for l in lines if l.strip().startswith('#')])
            # Count docstrings
            docstring_count = len(re.findall(r'"""[\s\S]*?"""', code))
            docstring_count += len(re.findall(r"'''[\s\S]*?'''", code))
            comment_lines += docstring_count * 3  # Estimate 3 lines per docstring
        
        elif language.lower() in ['javascript', 'typescript', 'java']:
            # Single-line comments
            comment_lines = len([l for l in lines if l.strip().startswith('//')])
            # Multi-line comments
            multiline_count = len(re.findall(r'/\*[\s\S]*?\*/', code))
            comment_lines += multiline_count * 3  # Estimate 3 lines per block
        
        # Calculate comment ratio
        comment_ratio = comment_lines / total_lines
        
        # Score based on comment ratio
        if 0.10 <= comment_ratio <= 0.30:
            # Ideal range: 10-30% comments
            score = 33.0
        elif 0.05 <= comment_ratio < 0.10:
            score = 25.0
        elif 0.30 < comment_ratio <= 0.50:
            score = 25.0
        elif comment_ratio > 0:
            score = 15.0
        else:
            score = 5.0
        
        return score
    
    def _analyze_code_style(self, code: str, language: str) -> float:
        """
        Analyze code style consistency
        
        Args:
            code: Source code
            language: Programming language
            
        Returns:
            Style score (0-34)
        """
        score = 34.0
        
        lines = code.split('\n')
        
        # 1. Indentation consistency
        indents = []
        for line in lines:
            if line and not line.strip().startswith('#') and not line.strip().startswith('//'):
                leading_spaces = len(line) - len(line.lstrip())
                if leading_spaces > 0:
                    indents.append(leading_spaces)
        
        if indents:
            # Check if indentation is consistent (multiples of 2 or 4)
            indent_2 = sum(1 for i in indents if i % 2 == 0)
            indent_4 = sum(1 for i in indents if i % 4 == 0)
            
            consistency_ratio = max(indent_2, indent_4) / len(indents)
            
            if consistency_ratio >= 0.9:
                indent_score = 17.0
            elif consistency_ratio >= 0.7:
                indent_score = 12.0
            else:
                indent_score = 7.0
        else:
            indent_score = 10.0
        
        # 2. Line length consistency
        long_lines = sum(1 for line in lines if len(line) > 120)
        if lines:
            long_line_ratio = long_lines / len(lines)
            
            if long_line_ratio < 0.1:
                length_score = 17.0
            elif long_line_ratio < 0.3:
                length_score = 12.0
            else:
                length_score = 7.0
        else:
            length_score = 10.0
        
        score = indent_score + length_score
        
        return score
    
    def _calculate_isolation(
        self,
        files: List[Tuple[str, str, str]],
        repo_metadata: Dict[str, Any]
    ) -> float:
        """
        Calculate Isolation score
        
        Measures: Dependencies, architecture, coupling
        
        Args:
            files: List of code files
            repo_metadata: Repository metadata
            
        Returns:
            Isolation score (0-100)
        """
        score = 0.0
        
        # 1. Dependency management (40 points)
        # Check for dependency files
        has_requirements = any('requirements' in f[0].lower() for f in files)
        has_package_json = any('package.json' in f[0].lower() for f in files)
        has_pom = any('pom.xml' in f[0].lower() for f in files)
        has_gradle = any('build.gradle' in f[0].lower() for f in files)
        
        if has_requirements or has_package_json or has_pom or has_gradle:
            dependency_score = 40.0
        else:
            dependency_score = 20.0
        
        # 2. Architecture separation (30 points)
        # Check for organized directory structure
        unique_dirs = set()
        for filename, _, _ in files:
            parts = filename.split('/')
            if len(parts) > 1:
                unique_dirs.add(parts[0])
        
        if len(unique_dirs) >= 3:
            architecture_score = 30.0
        elif len(unique_dirs) >= 2:
            architecture_score = 20.0
        else:
            architecture_score = 10.0
        
        # 3. Import/coupling analysis (30 points)
        # Analyze imports to estimate coupling
        coupling_scores = []
        
        for filename, language, code in files:
            if language.lower() == 'python':
                imports = len(re.findall(r'^import\s+', code, re.MULTILINE))
                imports += len(re.findall(r'^from\s+\w+\s+import', code, re.MULTILINE))
            elif language.lower() in ['javascript', 'typescript']:
                imports = len(re.findall(r'import\s+.*\s+from', code))
                imports += len(re.findall(r'require\(', code))
            elif language.lower() == 'java':
                imports = len(re.findall(r'^import\s+', code, re.MULTILINE))
            else:
                imports = 0
            
            # Score based on import count (moderate is good)
            if 0 < imports <= 10:
                coupling_scores.append(30.0)
            elif 10 < imports <= 20:
                coupling_scores.append(20.0)
            elif imports > 20:
                coupling_scores.append(10.0)
            else:
                coupling_scores.append(15.0)
        
        coupling_score = sum(coupling_scores) / len(coupling_scores) if coupling_scores else 15.0
        
        score = dependency_score + architecture_score + coupling_score
        
        return min(100.0, max(0.0, score))
    
    def _calculate_durability(
        self,
        files: List[Tuple[str, str, str]],
        repo_metadata: Dict[str, Any],
        complexity: ComplexityMetrics
    ) -> float:
        """
        Calculate Durability score
        
        Measures: Tests, documentation, maintainability
        
        Args:
            files: List of code files
            repo_metadata: Repository metadata
            complexity: Complexity metrics
            
        Returns:
            Durability score (0-100)
        """
        score = 0.0
        
        # 1. Test coverage (40 points)
        has_tests = repo_metadata.get('has_tests', False)
        
        # Count test files
        test_files = sum(
            1 for f in files
            if 'test' in f[0].lower() or 'spec' in f[0].lower()
        )
        
        if has_tests and test_files > 0:
            # Estimate test coverage based on test file ratio
            test_ratio = test_files / len(files)
            
            if test_ratio >= 0.3:
                test_score = 40.0
            elif test_ratio >= 0.2:
                test_score = 30.0
            elif test_ratio >= 0.1:
                test_score = 20.0
            else:
                test_score = 10.0
        elif has_tests:
            test_score = 15.0
        else:
            test_score = 0.0
        
        # 2. Documentation (30 points)
        has_readme = repo_metadata.get('has_readme', False)
        has_license = repo_metadata.get('has_license', False)
        
        doc_score = 0.0
        if has_readme:
            doc_score += 20.0
        if has_license:
            doc_score += 10.0
        
        # 3. Maintainability (30 points)
        # Based on maintainability index from complexity analysis
        mi = complexity.maintainability_index
        
        if mi >= 85:
            maintainability_score = 30.0
        elif mi >= 70:
            maintainability_score = 25.0
        elif mi >= 50:
            maintainability_score = 20.0
        elif mi >= 30:
            maintainability_score = 15.0
        else:
            maintainability_score = 10.0
        
        score = test_score + doc_score + maintainability_score
        
        return min(100.0, max(0.0, score))
    
    def get_acid_grade(self, score: float) -> str:
        """
        Get letter grade for ACID score
        
        Args:
            score: ACID score (0-100)
            
        Returns:
            Letter grade (A-F)
        """
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def get_component_description(self, component: str) -> str:
        """
        Get description for an ACID component
        
        Args:
            component: Component name (atomicity/consistency/isolation/durability)
            
        Returns:
            Component description
        """
        descriptions = {
            'atomicity': 'Modularity, single responsibility, function size, and cohesion',
            'consistency': 'Naming conventions, code style, and documentation',
            'isolation': 'Dependencies, architecture separation, and coupling',
            'durability': 'Test coverage, documentation, and maintainability'
        }
        
        return descriptions.get(component.lower(), 'Unknown component')
