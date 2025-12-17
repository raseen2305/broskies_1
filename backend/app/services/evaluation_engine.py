import re
import ast
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import math
import logging
from collections import Counter, defaultdict
import statistics
import subprocess
import tempfile
import os

logger = logging.getLogger(__name__)


class PenaltySystem:
    """
    Comprehensive penalty system for code quality violations.
    Applies penalties based on code smells, security vulnerabilities,
    complexity violations, and missing essentials.
    """

    def __init__(self, penalty_multipliers: Dict[str, Any]):
        """
        Initialize the penalty system with multipliers.

        Args:
            penalty_multipliers: Dictionary containing penalty multipliers for different categories
        """
        self.penalty_multipliers = penalty_multipliers
        self.penalties_applied = {
            'code_smells': {},
            'security': {},
            'complexity': {},
            'missing_essentials': {}
        }

    def apply_code_smell_penalties(self, code_smells: Dict[str, int], base_score: float) -> Tuple[float, Dict[str, float]]:
        """
        Apply penalties for code smells detected in the repository.

        Args:
            code_smells: Dictionary of code smell types and their counts
            base_score: The base score before penalties

        Returns:
            Tuple of (penalized_score, penalties_detail)
        """
        total_penalty = 0.0
        penalties_detail = {}

        for smell_type, count in code_smells.items():
            if count > 0 and smell_type in self.penalty_multipliers['code_smells']:
                multiplier = self.penalty_multipliers['code_smells'][smell_type]
                penalty = count * multiplier
                total_penalty += penalty
                penalties_detail[smell_type] = penalty
                logger.debug(f"Code smell penalty: {smell_type} x{count} = -{penalty:.2f} points")

        penalized_score = max(0, base_score - total_penalty)
        self.penalties_applied['code_smells'] = penalties_detail

        return penalized_score, penalties_detail

    def apply_complexity_penalty(self, complexity_metrics: Dict[str, Any],
                                  thresholds: Dict[str, Dict[str, float]],
                                  base_score: float) -> Tuple[float, Dict[str, float]]:
        """
        Apply exponential penalties for complexity violations.

        Args:
            complexity_metrics: Dictionary containing complexity measurements
            thresholds: Dictionary of complexity thresholds
            base_score: The base score before penalties

        Returns:
            Tuple of (penalized_score, penalties_detail)
        """
        total_penalty = 0.0
        penalties_detail = {}

        # Check cyclomatic complexity
        if 'average_cyclomatic' in complexity_metrics:
            avg_cyclomatic = complexity_metrics['average_cyclomatic']
            threshold = thresholds.get('cyclomatic', {}).get('acceptable', 12)

            if avg_cyclomatic > threshold:
                excess = avg_cyclomatic - threshold
                # Exponential penalty: penalty = excess^1.5 * multiplier
                multiplier = self.penalty_multipliers['complexity']['per_point_over_threshold']
                penalty = (excess ** 1.5) * multiplier
                total_penalty += penalty
                penalties_detail['cyclomatic_complexity'] = penalty
                logger.debug(f"Cyclomatic complexity penalty: {avg_cyclomatic:.1f} > {threshold} = -{penalty:.2f} points")

        # Check cognitive complexity
        if 'average_cognitive' in complexity_metrics:
            avg_cognitive = complexity_metrics['average_cognitive']
            threshold = thresholds.get('cognitive', {}).get('acceptable', 15)

            if avg_cognitive > threshold:
                excess = avg_cognitive - threshold
                multiplier = self.penalty_multipliers['complexity']['per_point_over_threshold']
                penalty = (excess ** 1.5) * multiplier
                total_penalty += penalty
                penalties_detail['cognitive_complexity'] = penalty
                logger.debug(f"Cognitive complexity penalty: {avg_cognitive:.1f} > {threshold} = -{penalty:.2f} points")

        # Check maintainability index
        if 'maintainability_index' in complexity_metrics:
            maintainability = complexity_metrics['maintainability_index']
            threshold = thresholds.get('maintainability', {}).get('acceptable', 65)

            if maintainability < threshold:
                deficit = threshold - maintainability
                # Exponential penalty for low maintainability
                multiplier = self.penalty_multipliers['complexity']['per_point_over_threshold']
                penalty = (deficit ** 1.5) * multiplier
                total_penalty += penalty
                penalties_detail['low_maintainability'] = penalty
                logger.debug(f"Maintainability penalty: {maintainability:.1f} < {threshold} = -{penalty:.2f} points")

        penalized_score = max(0, base_score - total_penalty)
        self.penalties_applied['complexity'] = penalties_detail

        return penalized_score, penalties_detail

    def apply_security_penalties(self, security_vulnerabilities: Dict[str, List[Any]],
                                  base_score: float) -> Tuple[float, Dict[str, float]]:
        """
        Apply penalties for security vulnerabilities by severity.

        Args:
            security_vulnerabilities: Dictionary of vulnerability types and their occurrences
            base_score: The base score before penalties

        Returns:
            Tuple of (penalized_score, penalties_detail)
        """
        total_penalty = 0.0
        penalties_detail = {}

        # Map vulnerability types to severity levels
        severity_mapping = {
            'sql_injection': 'critical',
            'xss': 'high',
            'hardcoded_secrets': 'critical',
            'unsafe_functions': 'high',
            'insecure_crypto': 'medium',
            'path_traversal': 'high',
            'command_injection': 'critical'
        }

        for vuln_type, occurrences in security_vulnerabilities.items():
            if isinstance(occurrences, list):
                count = len(occurrences)
            else:
                count = occurrences

            if count > 0:
                severity = severity_mapping.get(vuln_type, 'low')
                multiplier = self.penalty_multipliers['security'].get(severity, 3.0)
                penalty = count * multiplier
                total_penalty += penalty
                penalties_detail[f"{vuln_type}_{severity}"] = penalty
                logger.warning(f"Security penalty: {vuln_type} ({severity}) x{count} = -{penalty:.2f} points")

        penalized_score = max(0, base_score - total_penalty)
        self.penalties_applied['security'] = penalties_detail

        return penalized_score, penalties_detail

    def apply_missing_essentials_penalties(self, repo_analysis: Dict[str, Any],
                                            base_score: float) -> Tuple[float, Dict[str, float]]:
        """
        Apply severe penalties for missing essential project components.

        Args:
            repo_analysis: Dictionary containing repository analysis data
            base_score: The base score before penalties

        Returns:
            Tuple of (penalized_score, penalties_detail)
        """
        total_penalty = 0.0
        penalties_detail = {}

        # Check for missing tests
        test_file_count = repo_analysis.get('test_file_count', 0)
        test_coverage = repo_analysis.get('test_coverage', 0)
        if test_file_count == 0 or test_coverage < 0.05:
            penalty = self.penalty_multipliers['missing_essentials']['no_tests']
            total_penalty += penalty
            penalties_detail['no_tests'] = penalty
            logger.warning(f"Missing tests penalty: -{penalty:.2f} points")

        # Check for missing README
        has_readme = repo_analysis.get('has_readme', False)
        if not has_readme:
            penalty = self.penalty_multipliers['missing_essentials']['no_readme']
            total_penalty += penalty
            penalties_detail['no_readme'] = penalty
            logger.warning(f"Missing README penalty: -{penalty:.2f} points")

        # Check for missing documentation
        documentation_coverage = repo_analysis.get('documentation_coverage', 0)
        if documentation_coverage < 0.05:
            penalty = self.penalty_multipliers['missing_essentials']['no_documentation']
            total_penalty += penalty
            penalties_detail['no_documentation'] = penalty
            logger.warning(f"Missing documentation penalty: -{penalty:.2f} points")

        # Check for missing license
        has_license = repo_analysis.get('has_license', False)
        if not has_license:
            penalty = self.penalty_multipliers['missing_essentials']['no_license']
            total_penalty += penalty
            penalties_detail['no_license'] = penalty
            logger.warning(f"Missing license penalty: -{penalty:.2f} points")

        # Check for missing CI/CD
        has_ci_cd = repo_analysis.get('has_ci_cd', False)
        if not has_ci_cd:
            penalty = self.penalty_multipliers['missing_essentials']['no_ci_cd']
            total_penalty += penalty
            penalties_detail['no_ci_cd'] = penalty
            logger.warning(f"Missing CI/CD penalty: -{penalty:.2f} points")

        penalized_score = max(0, base_score - total_penalty)
        self.penalties_applied['missing_essentials'] = penalties_detail

        return penalized_score, penalties_detail

    def get_total_penalties(self) -> Dict[str, Any]:
        """
        Get a summary of all penalties applied.

        Returns:
            Dictionary containing penalty summary
        """
        total = 0.0
        for category, penalties in self.penalties_applied.items():
            total += sum(penalties.values())

        return {
            'total_penalty_points': round(total, 2),
            'by_category': {
                'code_smells': round(sum(self.penalties_applied['code_smells'].values()), 2),
                'security': round(sum(self.penalties_applied['security'].values()), 2),
                'complexity': round(sum(self.penalties_applied['complexity'].values()), 2),
                'missing_essentials': round(sum(self.penalties_applied['missing_essentials'].values()), 2)
            },
            'details': self.penalties_applied
        }

    def reset_penalties(self):
        """Reset all applied penalties."""
        self.penalties_applied = {
            'code_smells': {},
            'security': {},
            'complexity': {},
            'missing_essentials': {}
        }


class EvaluationEngine:
    def __init__(self):
        self.language_analyzers = {
            'Python': self._analyze_python_code,
            'JavaScript': self._analyze_javascript_code,
            'TypeScript': self._analyze_typescript_code,
            'Java': self._analyze_java_code,
            'Go': self._analyze_go_code,
            'C++': self._analyze_cpp_code,
            'C#': self._analyze_csharp_code,
            'Ruby': self._analyze_ruby_code,
            'PHP': self._analyze_php_code,
            'Swift': self._analyze_swift_code,
            'Kotlin': self._analyze_kotlin_code,
            'Rust': self._analyze_rust_code,
        }
        
        # Enhanced language support for 12 programming languages
        self.supported_languages = {
            'Python': {
                'extensions': ['.py', '.pyw', '.pyi'],
                'ast_parser': True,
                'complexity_patterns': [r'\bif\b', r'\belif\b', r'\bwhile\b', r'\bfor\b', r'\btry\b', r'\bexcept\b', r'\band\b', r'\bor\b'],
                'function_patterns': [r'def\s+\w+\s*\('],
                'class_patterns': [r'class\s+\w+'],
                'comment_patterns': [r'#.*', r'""".*?"""', r"'''.*?'''"]
            },
            'JavaScript': {
                'extensions': ['.js', '.jsx', '.mjs'],
                'ast_parser': False,
                'complexity_patterns': [r'\bif\b', r'\belse\s+if\b', r'\bwhile\b', r'\bfor\b', r'\btry\b', r'\bcatch\b', r'&&', r'\|\|', r'\?'],
                'function_patterns': [r'function\s+\w+\s*\(', r'\w+\s*:\s*function\s*\(', r'const\s+\w+\s*=\s*\([^)]*\)\s*=>', r'let\s+\w+\s*=\s*\([^)]*\)\s*=>'],
                'class_patterns': [r'class\s+\w+'],
                'comment_patterns': [r'//.*', r'/\*.*?\*/']
            },
            'TypeScript': {
                'extensions': ['.ts', '.tsx'],
                'ast_parser': False,
                'complexity_patterns': [r'\bif\b', r'\belse\s+if\b', r'\bwhile\b', r'\bfor\b', r'\btry\b', r'\bcatch\b', r'&&', r'\|\|', r'\?'],
                'function_patterns': [r'function\s+\w+\s*\(', r'\w+\s*:\s*function\s*\(', r'const\s+\w+\s*=\s*\([^)]*\)\s*=>', r'let\s+\w+\s*=\s*\([^)]*\)\s*=>'],
                'class_patterns': [r'class\s+\w+', r'interface\s+\w+'],
                'comment_patterns': [r'//.*', r'/\*.*?\*/']
            },
            'Java': {
                'extensions': ['.java'],
                'ast_parser': False,
                'complexity_patterns': [r'\bif\b', r'\belse\s+if\b', r'\bwhile\b', r'\bfor\b', r'\btry\b', r'\bcatch\b', r'&&', r'\|\|', r'\?', r'\bcase\b'],
                'function_patterns': [r'(public|private|protected)\s+\w+\s+\w+\s*\([^)]*\)\s*{'],
                'class_patterns': [r'(public\s+)?class\s+\w+', r'interface\s+\w+'],
                'comment_patterns': [r'//.*', r'/\*.*?\*/']
            },
            'Go': {
                'extensions': ['.go'],
                'ast_parser': False,
                'complexity_patterns': [r'\bif\b', r'\bfor\b', r'\bswitch\b', r'\bcase\b', r'&&', r'\|\|'],
                'function_patterns': [r'func\s+\w+\s*\([^)]*\)'],
                'class_patterns': [r'type\s+\w+\s+struct', r'type\s+\w+\s+interface'],
                'comment_patterns': [r'//.*', r'/\*.*?\*/']
            },
            'C++': {
                'extensions': ['.cpp', '.cc', '.cxx', '.c++', '.h', '.hpp'],
                'ast_parser': False,
                'complexity_patterns': [r'\bif\b', r'\belse\s+if\b', r'\bwhile\b', r'\bfor\b', r'\btry\b', r'\bcatch\b', r'&&', r'\|\|', r'\?'],
                'function_patterns': [r'\w+\s+\w+\s*\([^)]*\)\s*{'],
                'class_patterns': [r'class\s+\w+', r'struct\s+\w+'],
                'comment_patterns': [r'//.*', r'/\*.*?\*/']
            },
            'C#': {
                'extensions': ['.cs'],
                'ast_parser': False,
                'complexity_patterns': [r'\bif\b', r'\belse\s+if\b', r'\bwhile\b', r'\bfor\b', r'\btry\b', r'\bcatch\b', r'&&', r'\|\|', r'\?'],
                'function_patterns': [r'(public|private|protected)\s+\w+\s+\w+\s*\([^)]*\)'],
                'class_patterns': [r'(public\s+)?class\s+\w+', r'interface\s+\w+'],
                'comment_patterns': [r'//.*', r'/\*.*?\*/']
            },
            'Ruby': {
                'extensions': ['.rb'],
                'ast_parser': False,
                'complexity_patterns': [r'\bif\b', r'\bwhile\b', r'\bfor\b', r'\bcase\b', r'\bwhen\b', r'&&', r'\|\|'],
                'function_patterns': [r'def\s+\w+'],
                'class_patterns': [r'class\s+\w+', r'module\s+\w+'],
                'comment_patterns': [r'#.*']
            },
            'PHP': {
                'extensions': ['.php'],
                'ast_parser': False,
                'complexity_patterns': [r'\bif\b', r'\belse\s+if\b', r'\bwhile\b', r'\bfor\b', r'\btry\b', r'\bcatch\b', r'&&', r'\|\|', r'\?'],
                'function_patterns': [r'function\s+\w+\s*\('],
                'class_patterns': [r'class\s+\w+'],
                'comment_patterns': [r'//.*', r'#.*', r'/\*.*?\*/']
            },
            'Swift': {
                'extensions': ['.swift'],
                'ast_parser': False,
                'complexity_patterns': [r'\bif\b', r'\bwhile\b', r'\bfor\b', r'\bswitch\b', r'\bcase\b', r'&&', r'\|\|'],
                'function_patterns': [r'func\s+\w+\s*\('],
                'class_patterns': [r'class\s+\w+', r'struct\s+\w+'],
                'comment_patterns': [r'//.*', r'/\*.*?\*/']
            },
            'Kotlin': {
                'extensions': ['.kt', '.kts'],
                'ast_parser': False,
                'complexity_patterns': [r'\bif\b', r'\belse\s+if\b', r'\bwhile\b', r'\bfor\b', r'\btry\b', r'\bcatch\b', r'&&', r'\|\|', r'\?'],
                'function_patterns': [r'fun\s+\w+\s*\('],
                'class_patterns': [r'class\s+\w+', r'interface\s+\w+'],
                'comment_patterns': [r'//.*', r'/\*.*?\*/']
            },
            'Rust': {
                'extensions': ['.rs'],
                'ast_parser': False,
                'complexity_patterns': [r'\bif\b', r'\bwhile\b', r'\bfor\b', r'\bmatch\b', r'&&', r'\|\|'],
                'function_patterns': [r'fn\s+\w+\s*\('],
                'class_patterns': [r'struct\s+\w+', r'enum\s+\w+', r'trait\s+\w+'],
                'comment_patterns': [r'//.*', r'/\*.*?\*/']
            }
        }
        
        # Framework detection patterns
        self.framework_patterns = {
            'React': [r'import.*react', r'from\s+["\']react["\']', r'React\.', r'jsx', r'useState', r'useEffect'],
            'Vue.js': [r'import.*vue', r'from\s+["\']vue["\']', r'Vue\.', r'\.vue', r'v-if', r'v-for'],
            'Angular': [r'@angular', r'import.*@angular', r'@Component', r'@Injectable', r'@NgModule'],
            'Express.js': [r'express\(\)', r'require\(["\']express["\']', r'app\.get\(', r'app\.post\('],
            'Django': [r'from django', r'import django', r'models\.Model', r'HttpResponse', r'urls\.py'],
            'Flask': [r'from flask', r'import flask', r'Flask\(__name__\)', r'@app\.route'],
            'FastAPI': [r'from fastapi', r'import fastapi', r'FastAPI\(\)', r'@app\.(get|post)'],
            'Spring': [r'@SpringBootApplication', r'@RestController', r'@Service', r'springframework'],
            'Node.js': [r'require\(', r'module\.exports', r'process\.', r'__dirname'],
            'Pandas': [r'import pandas', r'pd\.', r'DataFrame', r'read_csv'],
            'NumPy': [r'import numpy', r'np\.', r'array\(', r'ndarray'],
            'Android': [r'android\.', r'Activity', r'Fragment', r'onCreate']
        }
        
        # Security vulnerability patterns
        self.security_patterns = {
            'sql_injection': [
                r'SELECT.*FROM.*WHERE.*=.*\$',
                r'INSERT.*INTO.*VALUES.*\$',
                r'UPDATE.*SET.*WHERE.*=.*\$',
                r'DELETE.*FROM.*WHERE.*=.*\$'
            ],
            'xss': [
                r'innerHTML\s*=',
                r'document\.write\s*\(',
                r'eval\s*\(',
                r'setTimeout\s*\(\s*["\']',
                r'setInterval\s*\(\s*["\']'
            ],
            'hardcoded_secrets': [
                r'password\s*=\s*["\'][^"\']{8,}["\']',
                r'api_key\s*=\s*["\'][^"\']{16,}["\']',
                r'secret\s*=\s*["\'][^"\']{16,}["\']',
                r'token\s*=\s*["\'][^"\']{20,}["\']'
            ],
            'unsafe_functions': [
                r'exec\s*\(',
                r'system\s*\(',
                r'shell_exec\s*\(',
                r'passthru\s*\(',
                r'eval\s*\('
            ]
        }
        
        # Code quality patterns
        self.quality_patterns = {
            'comments': [
                r'#.*',  # Python, Ruby, Shell
                r'//.*',  # JavaScript, Java, C++, C#
                r'/\*.*?\*/',  # Multi-line comments
                r'""".*?"""',  # Python docstrings
                r"'''.*?'''"   # Python docstrings
            ],
            'functions': [
                r'def\s+\w+\s*\(',  # Python
                r'function\s+\w+\s*\(',  # JavaScript
                r'public\s+\w+\s+\w+\s*\(',  # Java
                r'private\s+\w+\s+\w+\s*\(',  # Java
                r'func\s+\w+\s*\(',  # Go
                r'fn\s+\w+\s*\('   # Rust
            ],
            'classes': [
                r'class\s+\w+',  # Python, Java, C++, C#
                r'interface\s+\w+',  # Java, TypeScript
                r'struct\s+\w+',  # Go, Rust, C++
                r'enum\s+\w+'     # Java, C#, Rust
            ]
        }
        
        # Advanced code complexity metrics - STRICT THRESHOLDS
        self.complexity_thresholds = {
            'cyclomatic': {
                'excellent': 5,
                'good': 8,
                'acceptable': 12,
                'poor': 20,
                'critical': 25
            },
            'cognitive': {
                'excellent': 5,
                'good': 10,
                'acceptable': 15,
                'poor': 25,
                'critical': 35
            },
            'halstead_volume': {
                'excellent': 100,
                'good': 300,
                'acceptable': 500,
                'poor': 1000,
                'critical': 2000
            },
            'maintainability': {
                'excellent': 85,
                'good': 75,
                'acceptable': 65,
                'poor': 50,
                'critical': 40
            }
        }
        
        # Code quality thresholds - STRICT
        self.quality_thresholds = {
            'comment_ratio': {
                'minimum': 0.10,
                'optimal_min': 0.15,
                'optimal_max': 0.30,
                'excessive': 0.50
            },
            'function_density': {
                'minimum': 3,
                'optimal_min': 5,
                'optimal_max': 15,
                'excessive': 25
            },
            'test_coverage': {
                'excellent': 0.30,
                'good': 0.20,
                'minimum': 0.10,
                'required': 0.05
            },
            'function_size': {
                'excellent': 15,
                'good': 30,
                'acceptable': 50,
                'poor': 100
            },
            'class_size': {
                'excellent': 10,
                'good': 15,
                'acceptable': 25,
                'poor': 50
            },
            'nesting_depth': {
                'excellent': 2,
                'good': 3,
                'acceptable': 4,
                'poor': 6
            },
            'parameters': {
                'excellent': 3,
                'good': 5,
                'acceptable': 7,
                'poor': 10
            }
        }
        
        # Penalty multipliers for code quality violations
        self.penalty_multipliers = {
            'code_smells': {
                'long_function': 2.0,
                'long_line': 0.5,
                'deep_nesting': 3.0,
                'magic_numbers': 1.0,
                'duplicate_code': 2.5,
                'too_many_parameters': 2.0
            },
            'security': {
                'critical': 30.0,
                'high': 15.0,
                'medium': 7.0,
                'low': 3.0
            },
            'complexity': {
                'per_point_over_threshold': 1.5
            },
            'missing_essentials': {
                'no_tests': 40.0,
                'no_readme': 25.0,
                'no_documentation': 20.0,
                'no_license': 15.0,
                'no_ci_cd': 20.0
            }
        }
        
        # Best practice rewards
        self.best_practice_rewards = {
            'high_test_coverage': 5.0,  # >80% coverage
            'comprehensive_documentation': 5.0,
            'modern_language_features': 3.0,
            'low_coupling_high_cohesion': 5.0,
            'active_maintenance': 3.0
        }
        
        # Strictness level configuration
        self.strictness_level = 'STRICT'  # Options: STRICT, MODERATE, LENIENT
        self.evaluation_version = '5.0'
        
        # ACID scoring weights and criteria
        self.acid_criteria = {
            'atomicity': {
                'modularity_weight': 0.3,
                'single_responsibility_weight': 0.25,
                'function_size_weight': 0.2,
                'class_cohesion_weight': 0.25
            },
            'consistency': {
                'naming_conventions_weight': 0.25,
                'code_style_weight': 0.25,
                'documentation_weight': 0.25,
                'commit_patterns_weight': 0.25
            },
            'isolation': {
                'dependency_management_weight': 0.3,
                'architecture_separation_weight': 0.3,
                'coupling_weight': 0.2,
                'security_weight': 0.2
            },
            'durability': {
                'test_coverage_weight': 0.3,
                'documentation_weight': 0.25,
                'maintainability_weight': 0.25,
                'version_control_weight': 0.2
            }
        }
        
        # Validate configuration on initialization
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate all threshold configurations and weights"""
        logger.info("Validating EvaluationEngine configuration...")
        
        # Validate complexity thresholds
        for metric, thresholds in self.complexity_thresholds.items():
            required_keys = ['excellent', 'good', 'acceptable', 'poor', 'critical']
            for key in required_keys:
                if key not in thresholds:
                    logger.error(f"Missing threshold '{key}' for complexity metric '{metric}'")
                    raise ValueError(f"Invalid configuration: Missing threshold '{key}' for '{metric}'")
            
            # Validate threshold ordering (except maintainability which is inverted)
            if metric == 'maintainability':
                # For maintainability, higher is better
                if not (thresholds['excellent'] > thresholds['good'] > thresholds['acceptable'] > 
                       thresholds['poor'] > thresholds['critical']):
                    logger.error(f"Invalid threshold ordering for maintainability metric")
                    raise ValueError(f"Maintainability thresholds must be in descending order")
            else:
                # For other metrics, lower is better
                if not (thresholds['excellent'] < thresholds['good'] < thresholds['acceptable'] < 
                       thresholds['poor'] < thresholds['critical']):
                    logger.error(f"Invalid threshold ordering for complexity metric '{metric}'")
                    raise ValueError(f"Complexity thresholds must be in ascending order for '{metric}'")
        
        # Validate quality thresholds
        for metric, thresholds in self.quality_thresholds.items():
            for key, value in thresholds.items():
                if not isinstance(value, (int, float)):
                    logger.error(f"Invalid threshold value for quality metric '{metric}.{key}'")
                    raise ValueError(f"Threshold values must be numeric for '{metric}.{key}'")
                
                # Validate ranges for ratio-based metrics
                if 'ratio' in metric or 'coverage' in metric:
                    if not (0 <= value <= 1):
                        logger.error(f"Ratio threshold out of range for '{metric}.{key}': {value}")
                        raise ValueError(f"Ratio thresholds must be between 0 and 1 for '{metric}.{key}'")
        
        # Validate ACID criteria weights sum to 1.0 for each category
        for acid_type, weights in self.acid_criteria.items():
            weight_sum = sum(weights.values())
            if not (0.99 <= weight_sum <= 1.01):  # Allow small floating point errors
                logger.error(f"ACID weights for '{acid_type}' do not sum to 1.0: {weight_sum}")
                raise ValueError(f"ACID criteria weights must sum to 1.0 for '{acid_type}' (got {weight_sum})")
        
        # Validate penalty multipliers
        for category, penalties in self.penalty_multipliers.items():
            for penalty_type, value in penalties.items():
                if not isinstance(value, (int, float)) or value < 0:
                    logger.error(f"Invalid penalty multiplier for '{category}.{penalty_type}': {value}")
                    raise ValueError(f"Penalty multipliers must be non-negative numbers")
        
        # Validate best practice rewards
        for reward_type, value in self.best_practice_rewards.items():
            if not isinstance(value, (int, float)) or value < 0:
                logger.error(f"Invalid reward value for '{reward_type}': {value}")
                raise ValueError(f"Reward values must be non-negative numbers")
        
        # Validate strictness level
        valid_strictness_levels = ['STRICT', 'MODERATE', 'LENIENT']
        if self.strictness_level not in valid_strictness_levels:
            logger.warning(f"Invalid strictness level '{self.strictness_level}', defaulting to 'STRICT'")
            self.strictness_level = 'STRICT'
        
        logger.info(f"Configuration validation successful. Strictness level: {self.strictness_level}, Version: {self.evaluation_version}")
    
    async def evaluate_repository(self, repo_data: Dict[str, Any], contents: List[Dict[str, Any]], 
                                commit_history: Dict[str, Any], structure_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive repository evaluation with quality assessment
        
        Args:
            repo_data: Basic repository metadata
            contents: Repository file contents for code analysis
            commit_history: Commit history and statistics
            structure_analysis: Repository structure analysis
        """
        
        logger.info(f"Starting comprehensive evaluation for repository: {repo_data.get('name', 'unknown')}")
        
        # Enhanced file structure analysis
        file_structure_analysis = await self._analyze_file_structure(contents, repo_data)
        
        # Analyze repository structure and metadata
        repo_stats = self._analyze_repository_metadata(repo_data, structure_analysis)
        
        # Enhanced code content analysis with framework detection
        code_analysis = await self._analyze_code_content_enhanced(contents)
        
        # Programming language and framework identification
        language_framework_analysis = await self._analyze_languages_and_frameworks(contents, repo_data)
        
        # Code complexity analysis with maintainability scoring
        complexity_analysis = await self._analyze_code_complexity_comprehensive(contents)
        
        # Documentation coverage assessment
        documentation_analysis = await self._analyze_documentation_coverage(contents, repo_data)
        
        # Analyze commit patterns and development practices
        commit_analysis = self._analyze_commit_patterns(commit_history)
        
        # Security vulnerability analysis
        security_analysis = self._analyze_security_vulnerabilities(contents)
        
        # Best practices assessment
        best_practices_analysis = await self._analyze_best_practices(contents, repo_data, commit_history)
        
        # Perform comprehensive code complexity analysis
        comprehensive_complexity_analysis = {}
        for file_info in contents:
            if file_info.get("content") and file_info.get("language"):
                file_complexity = self._analyze_code_complexity_strict(
                    file_info["content"], 
                    file_info["language"], 
                    file_info.get("path", "")
                )
                if file_info["language"] not in comprehensive_complexity_analysis:
                    comprehensive_complexity_analysis[file_info["language"]] = []
                comprehensive_complexity_analysis[file_info["language"]].append(file_complexity)
        
        # Aggregate complexity metrics across all files
        aggregated_complexity = self._aggregate_complexity_metrics(comprehensive_complexity_analysis)
        
        # Calculate comprehensive ACID scores with enhanced algorithms
        acid_scores = self._calculate_comprehensive_acid_scores(
            repo_data, repo_stats, code_analysis, commit_analysis, security_analysis, aggregated_complexity
        )
        
        # Calculate comprehensive quality metrics
        quality_metrics = self._calculate_enhanced_quality_metrics(
            repo_data, repo_stats, code_analysis, commit_analysis, security_analysis
        )
        
        # Calculate complexity and maintainability scores
        complexity_metrics = self._calculate_complexity_metrics(code_analysis, repo_stats)
        
        # Calculate technology and skill assessment
        technology_assessment = self._assess_technology_usage(repo_data, code_analysis)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            acid_scores, quality_metrics, complexity_metrics, technology_assessment
        )
        
        # Calculate overall repository score
        overall_score = self._calculate_overall_score(acid_scores, quality_metrics, complexity_metrics)
        
        evaluation_result = {
            "repository_id": repo_data.get("id"),
            "repository_name": repo_data.get("name"),
            "acid_scores": acid_scores,
            "quality_metrics": quality_metrics,
            "complexity_metrics": complexity_metrics,
            "security_analysis": security_analysis,
            "technology_assessment": technology_assessment,
            "commit_analysis": commit_analysis,
            "code_analysis": code_analysis,
            "repository_stats": repo_stats,
            "recommendations": recommendations,
            "overall_score": overall_score,
            "file_structure_analysis": file_structure_analysis,
            "language_framework_analysis": language_framework_analysis,
            "complexity_analysis": complexity_analysis,
            "documentation_analysis": documentation_analysis,
            "best_practices_analysis": best_practices_analysis,
            "comprehensive_complexity_analysis": aggregated_complexity,
            "detailed_code_metrics": {
                "supported_languages": list(self.supported_languages.keys()),
                "complexity_thresholds": self.complexity_thresholds,
                "acid_criteria_weights": self.acid_criteria,
                "total_files_analyzed": len(contents),
                "languages_detected": list(comprehensive_complexity_analysis.keys())
            },
            "evaluation_timestamp": datetime.utcnow().isoformat(),
            "evaluation_version": "4.0"
        }
        
        logger.info(f"Evaluation completed for {repo_data.get('name')} with overall score: {overall_score}")
        
        return evaluation_result
    
    async def _analyze_code_content(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Comprehensive code content analysis"""
        
        analysis = {
            "total_files": len(contents),
            "total_lines": 0,
            "code_lines": 0,
            "comment_lines": 0,
            "blank_lines": 0,
            "function_count": 0,
            "class_count": 0,
            "complexity_indicators": {},
            "language_breakdown": defaultdict(int),
            "file_type_breakdown": defaultdict(int),
            "code_quality_indicators": {},
            "documentation_coverage": 0.0,
            "test_file_count": 0,
            "config_file_count": 0
        }
        
        for file_info in contents:
            if not file_info.get("content"):
                continue
                
            content = file_info["content"]
            file_name = file_info.get("name", "")
            file_path = file_info.get("path", "")
            language = file_info.get("language", "Unknown")
            
            # Count lines
            lines = content.split('\n')
            analysis["total_lines"] += len(lines)
            
            # Analyze line types
            code_lines, comment_lines, blank_lines = self._analyze_line_types(content, language)
            analysis["code_lines"] += code_lines
            analysis["comment_lines"] += comment_lines
            analysis["blank_lines"] += blank_lines
            
            # Language breakdown
            analysis["language_breakdown"][language] += len(lines)
            
            # File type analysis
            file_type = self._get_file_type(file_name)
            analysis["file_type_breakdown"][file_type] += 1
            
            # Count functions and classes
            functions, classes = self._count_code_structures(content, language)
            analysis["function_count"] += functions
            analysis["class_count"] += classes
            
            # Complexity analysis
            complexity = self._analyze_code_complexity(content, language)
            if language not in analysis["complexity_indicators"]:
                analysis["complexity_indicators"][language] = []
            analysis["complexity_indicators"][language].append(complexity)
            
            # Check for test files
            if self._is_test_file(file_name, file_path):
                analysis["test_file_count"] += 1
                
            # Check for config files
            if self._is_config_file(file_name):
                analysis["config_file_count"] += 1
        
        # Calculate averages and ratios
        if analysis["total_lines"] > 0:
            analysis["comment_ratio"] = analysis["comment_lines"] / analysis["total_lines"]
            analysis["code_ratio"] = analysis["code_lines"] / analysis["total_lines"]
        else:
            analysis["comment_ratio"] = 0.0
            analysis["code_ratio"] = 0.0
            
        # Calculate documentation coverage
        analysis["documentation_coverage"] = self._calculate_documentation_coverage(analysis)
        
        # Calculate average complexity per language
        for language, complexities in analysis["complexity_indicators"].items():
            if complexities:
                analysis["complexity_indicators"][language] = {
                    "average": statistics.mean(complexities),
                    "max": max(complexities),
                    "min": min(complexities),
                    "files": len(complexities)
                }
        
        return analysis
    
    async def _analyze_file_structure(self, contents: List[Dict[str, Any]], repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive file structure analysis"""
        
        structure_analysis = {
            "directory_structure": {},
            "file_organization": {},
            "project_type": "unknown",
            "architecture_patterns": [],
            "organization_score": 0,
            "depth_analysis": {},
            "naming_conventions": {},
            "file_distribution": {}
        }
        
        # Analyze directory structure
        directories = defaultdict(int)
        file_paths = []
        max_depth = 0
        
        for file_info in contents:
            file_path = file_info.get("path", "")
            file_name = file_info.get("name", "")
            
            if not file_path:
                continue
                
            file_paths.append(file_path)
            
            # Analyze directory depth
            path_parts = file_path.split('/')
            depth = len(path_parts) - 1
            max_depth = max(max_depth, depth)
            
            # Count files per directory
            if depth > 0:
                directory = '/'.join(path_parts[:-1])
                directories[directory] += 1
        
        structure_analysis["directory_structure"] = dict(directories)
        structure_analysis["max_depth"] = max_depth
        
        # Identify project type and architecture patterns
        structure_analysis["project_type"] = self._identify_project_type(file_paths, repo_data)
        structure_analysis["architecture_patterns"] = self._identify_architecture_patterns(file_paths)
        
        # Analyze file organization quality
        structure_analysis["organization_score"] = self._calculate_organization_score(directories, file_paths)
        
        # Analyze naming conventions
        structure_analysis["naming_conventions"] = self._analyze_naming_conventions(file_paths)
        
        # File distribution analysis
        structure_analysis["file_distribution"] = self._analyze_file_distribution(file_paths)
        
        return structure_analysis
    
    async def _analyze_code_content_enhanced(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhanced code content analysis with framework detection"""
        
        # Start with base analysis
        analysis = await self._analyze_code_content(contents)
        
        # Add enhanced metrics
        analysis["framework_usage"] = {}
        analysis["design_patterns"] = {}
        analysis["code_smells"] = {}
        analysis["maintainability_index"] = 0
        analysis["technical_debt_indicators"] = {}
        
        for file_info in contents:
            content = file_info.get("content", "")
            language = file_info.get("language", "Unknown")
            file_name = file_info.get("name", "")
            
            if not content:
                continue
            
            # Detect frameworks and libraries
            frameworks = self._detect_frameworks_comprehensive(content, language, file_name)
            for framework, confidence in frameworks.items():
                if framework not in analysis["framework_usage"]:
                    analysis["framework_usage"][framework] = {"files": 0, "confidence": 0}
                analysis["framework_usage"][framework]["files"] += 1
                analysis["framework_usage"][framework]["confidence"] = max(
                    analysis["framework_usage"][framework]["confidence"], confidence
                )
            
            # Detect design patterns
            patterns = self._detect_design_patterns(content, language)
            for pattern in patterns:
                if pattern not in analysis["design_patterns"]:
                    analysis["design_patterns"][pattern] = 0
                analysis["design_patterns"][pattern] += 1
            
            # Detect code smells
            smells = self._detect_code_smells(content, language)
            for smell, count in smells.items():
                if smell not in analysis["code_smells"]:
                    analysis["code_smells"][smell] = 0
                analysis["code_smells"][smell] += count
        
        # Calculate maintainability index
        analysis["maintainability_index"] = self._calculate_maintainability_index(analysis)
        
        # Identify technical debt indicators
        analysis["technical_debt_indicators"] = self._identify_technical_debt(analysis)
        
        return analysis
    
    async def _analyze_languages_and_frameworks(self, contents: List[Dict[str, Any]], repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive programming language and framework identification"""
        
        analysis = {
            "primary_languages": {},
            "secondary_languages": {},
            "frameworks_detected": {},
            "language_ecosystem": {},
            "technology_stack": [],
            "proficiency_indicators": {},
            "modern_practices": {}
        }
        
        language_stats = defaultdict(lambda: {"lines": 0, "files": 0, "complexity": 0})
        framework_confidence = defaultdict(float)
        
        for file_info in contents:
            content = file_info.get("content", "")
            language = file_info.get("language", "Unknown")
            file_name = file_info.get("name", "")
            
            if not content or language == "Unknown":
                continue
            
            lines = len([line for line in content.split('\n') if line.strip()])
            language_stats[language]["lines"] += lines
            language_stats[language]["files"] += 1
            
            # Analyze language-specific features
            features = self._analyze_language_features(content, language)
            language_stats[language]["complexity"] += features.get("complexity", 0)
            
            # Detect frameworks with confidence scoring
            frameworks = self._detect_frameworks_comprehensive(content, language, file_name)
            for framework, confidence in frameworks.items():
                framework_confidence[framework] = max(framework_confidence[framework], confidence)
        
        # Categorize languages by usage
        total_lines = sum(stats["lines"] for stats in language_stats.values())
        
        for language, stats in language_stats.items():
            percentage = (stats["lines"] / total_lines * 100) if total_lines > 0 else 0
            
            lang_info = {
                "lines": stats["lines"],
                "files": stats["files"],
                "percentage": round(percentage, 1),
                "avg_complexity": stats["complexity"] / max(stats["files"], 1)
            }
            
            if percentage >= 20:
                analysis["primary_languages"][language] = lang_info
            elif percentage >= 5:
                analysis["secondary_languages"][language] = lang_info
        
        # Process framework detections
        for framework, confidence in framework_confidence.items():
            if confidence >= 0.7:
                analysis["frameworks_detected"][framework] = {
                    "confidence": confidence,
                    "category": self._get_framework_category(framework)
                }
        
        # Build technology stack
        analysis["technology_stack"] = self._build_technology_stack(
            analysis["primary_languages"], 
            analysis["frameworks_detected"]
        )
        
        # Assess proficiency indicators
        analysis["proficiency_indicators"] = self._assess_language_proficiency(language_stats)
        
        # Detect modern practices
        analysis["modern_practices"] = self._detect_modern_practices(contents)
        
        return analysis
    
    async def _analyze_code_complexity_comprehensive(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Comprehensive code complexity analysis with maintainability scoring"""
        
        analysis = {
            "cyclomatic_complexity": {},
            "cognitive_complexity": {},
            "halstead_metrics": {},
            "maintainability_scores": {},
            "complexity_distribution": {},
            "hotspots": [],
            "refactoring_candidates": []
        }
        
        file_complexities = []
        
        for file_info in contents:
            content = file_info.get("content", "")
            language = file_info.get("language", "Unknown")
            file_name = file_info.get("name", "")
            file_path = file_info.get("path", "")
            
            if not content or self._is_non_code_file(file_name):
                continue
            
            # Calculate various complexity metrics
            cyclomatic = self._calculate_cyclomatic_complexity(content, language)
            cognitive = self._calculate_cognitive_complexity(content, language)
            halstead = self._calculate_halstead_metrics(content, language)
            maintainability = self._calculate_file_maintainability(content, language)
            
            file_complexity = {
                "file": file_name,
                "path": file_path,
                "language": language,
                "cyclomatic_complexity": cyclomatic,
                "cognitive_complexity": cognitive,
                "halstead_metrics": halstead,
                "maintainability_score": maintainability,
                "lines_of_code": len([line for line in content.split('\n') if line.strip()])
            }
            
            file_complexities.append(file_complexity)
            
            # Identify complexity hotspots
            if cyclomatic > 15 or cognitive > 20:
                analysis["hotspots"].append({
                    "file": file_name,
                    "type": "high_complexity",
                    "cyclomatic": cyclomatic,
                    "cognitive": cognitive,
                    "severity": "high" if cyclomatic > 25 else "medium"
                })
            
            # Identify refactoring candidates
            if maintainability < 60:
                analysis["refactoring_candidates"].append({
                    "file": file_name,
                    "maintainability_score": maintainability,
                    "reason": "low_maintainability"
                })
        
        # Aggregate complexity metrics
        if file_complexities:
            analysis["cyclomatic_complexity"] = {
                "average": statistics.mean([f["cyclomatic_complexity"] for f in file_complexities]),
                "max": max([f["cyclomatic_complexity"] for f in file_complexities]),
                "distribution": self._calculate_complexity_distribution([f["cyclomatic_complexity"] for f in file_complexities])
            }
            
            analysis["cognitive_complexity"] = {
                "average": statistics.mean([f["cognitive_complexity"] for f in file_complexities]),
                "max": max([f["cognitive_complexity"] for f in file_complexities])
            }
            
            analysis["maintainability_scores"] = {
                "average": statistics.mean([f["maintainability_score"] for f in file_complexities]),
                "min": min([f["maintainability_score"] for f in file_complexities])
            }
        
        return analysis
    
    async def _analyze_documentation_coverage(self, contents: List[Dict[str, Any]], repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive documentation coverage assessment"""
        
        analysis = {
            "documentation_files": [],
            "inline_documentation": {},
            "api_documentation": {},
            "coverage_score": 0,
            "documentation_quality": {},
            "missing_documentation": [],
            "documentation_types": {}
        }
        
        doc_files = []
        code_files_with_docs = 0
        total_code_files = 0
        inline_doc_lines = 0
        total_code_lines = 0
        
        # Documentation file patterns
        doc_patterns = {
            "readme": r"readme\.(md|txt|rst)$",
            "changelog": r"(changelog|changes|history)\.(md|txt|rst)$",
            "license": r"(license|licence|copying)(\.(md|txt|rst))?$",
            "contributing": r"contributing\.(md|txt|rst)$",
            "api_docs": r"(api|docs?)\.(md|txt|rst)$",
            "installation": r"(install|setup)\.(md|txt|rst)$"
        }
        
        for file_info in contents:
            content = file_info.get("content", "")
            file_name = file_info.get("name", "").lower()
            language = file_info.get("language", "Unknown")
            
            # Check for documentation files
            for doc_type, pattern in doc_patterns.items():
                if re.match(pattern, file_name, re.IGNORECASE):
                    doc_files.append({
                        "type": doc_type,
                        "file": file_info.get("name", ""),
                        "size": len(content),
                        "quality_score": self._assess_doc_quality(content, doc_type)
                    })
                    break
            
            # Analyze inline documentation in code files
            if self._is_code_file(file_name, language):
                total_code_files += 1
                lines = content.split('\n')
                code_lines = len([line for line in lines if line.strip() and not self._is_comment_line(line.strip(), language)])
                comment_lines = len([line for line in lines if line.strip() and self._is_comment_line(line.strip(), language)])
                
                total_code_lines += code_lines
                inline_doc_lines += comment_lines
                
                # Check for function/class documentation
                has_docstrings = self._has_adequate_docstrings(content, language)
                if has_docstrings:
                    code_files_with_docs += 1
        
        analysis["documentation_files"] = doc_files
        
        # Calculate coverage metrics
        if total_code_files > 0:
            analysis["inline_documentation"] = {
                "comment_ratio": inline_doc_lines / max(total_code_lines, 1),
                "files_with_docs": code_files_with_docs,
                "total_code_files": total_code_files,
                "documentation_ratio": code_files_with_docs / total_code_files
            }
        
        # Assess documentation types present
        doc_types_present = {doc["type"] for doc in doc_files}
        analysis["documentation_types"] = {
            "readme": "readme" in doc_types_present,
            "license": "license" in doc_types_present,
            "changelog": "changelog" in doc_types_present,
            "contributing": "contributing" in doc_types_present,
            "api_docs": "api_docs" in doc_types_present,
            "installation": "installation" in doc_types_present
        }
        
        # Calculate overall coverage score
        analysis["coverage_score"] = self._calculate_documentation_coverage_score(analysis)
        
        # Identify missing documentation
        analysis["missing_documentation"] = self._identify_missing_documentation(analysis, repo_data)
        
        return analysis
    
    async def _analyze_best_practices(self, contents: List[Dict[str, Any]], repo_data: Dict[str, Any], commit_history: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze adherence to software development best practices"""
        
        analysis = {
            "project_structure": {},
            "code_organization": {},
            "testing_practices": {},
            "ci_cd_practices": {},
            "security_practices": {},
            "documentation_practices": {},
            "version_control_practices": {},
            "overall_score": 0
        }
        
        # Analyze project structure best practices
        analysis["project_structure"] = self._analyze_project_structure_practices(contents)
        
        # Analyze code organization practices
        analysis["code_organization"] = self._analyze_code_organization_practices(contents)
        
        # Analyze testing practices
        analysis["testing_practices"] = self._analyze_testing_practices(contents)
        
        # Analyze CI/CD practices
        analysis["ci_cd_practices"] = self._analyze_ci_cd_practices(contents)
        
        # Analyze security practices
        analysis["security_practices"] = self._analyze_security_practices(contents)
        
        # Analyze documentation practices
        analysis["documentation_practices"] = self._analyze_documentation_practices(contents, repo_data)
        
        # Analyze version control practices
        analysis["version_control_practices"] = self._analyze_version_control_practices(commit_history)
        
        # Calculate overall best practices score
        analysis["overall_score"] = self._calculate_best_practices_score(analysis)
        
        return analysis
    
    def _analyze_repository_metadata(self, repo_data: Dict[str, Any], structure_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analyze repository metadata for scoring"""
        stats = {
            "has_readme": False,
            "has_license": False,
            "has_tests": False,
            "has_ci": False,
            "has_documentation": False,
            "commit_frequency": 0,
            "contributor_count": 1,
            "issue_ratio": 0,
            "star_ratio": 0,
            "fork_ratio": 0,
            "size_score": 0,
            "language_diversity": 0,
            "topic_relevance": 0
        }
        
        # Check for README
        if repo_data.get("description") and len(repo_data["description"]) > 20:
            stats["has_readme"] = True
        
        # Check for license
        if repo_data.get("license"):
            stats["has_license"] = True
        
        # Check topics for test indicators
        topics = repo_data.get("topics", [])
        test_indicators = ["testing", "test", "jest", "pytest", "junit", "mocha"]
        stats["has_tests"] = any(indicator in " ".join(topics).lower() for indicator in test_indicators)
        
        # Check for CI/CD indicators
        ci_indicators = ["ci", "cd", "github-actions", "travis", "jenkins", "circleci"]
        stats["has_ci"] = any(indicator in " ".join(topics).lower() for indicator in ci_indicators)
        
        # Calculate ratios
        stars = repo_data.get("stargazers_count", 0)
        forks = repo_data.get("forks_count", 0)
        size = repo_data.get("size", 0)
        
        stats["star_ratio"] = min(stars / 100, 1.0)  # Normalize to 0-1
        stats["fork_ratio"] = min(forks / 50, 1.0)   # Normalize to 0-1
        stats["size_score"] = min(size / 10000, 1.0) # Normalize to 0-1
        
        # Language diversity
        languages = repo_data.get("languages", {})
        if languages:
            total_bytes = sum(languages.values())
            if total_bytes > 0:
                # Calculate entropy for language diversity
                entropy = 0
                for bytes_count in languages.values():
                    if bytes_count > 0:
                        p = bytes_count / total_bytes
                        entropy -= p * math.log2(p)
                stats["language_diversity"] = min(entropy / 3, 1.0)  # Normalize
        
        return stats
    
    def _calculate_acid_scores(self, repo_data: Dict[str, Any], repo_stats: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate ACID scores using penalty-first approach for accurate differentiation.
        Start with 100 points and subtract penalties for missing features and quality issues.
        """
        
        # ATOMICITY: Code modularity and single responsibility
        # Start with perfect score, subtract penalties
        atomicity = 100.0
        
        # Penalties for poor modularity
        if not repo_stats.get("has_tests"):
            atomicity -= 40.0  # Critical: No tests
        elif repo_stats.get("test_file_count", 0) < 3:
            atomicity -= 20.0  # Few tests
            
        if repo_data.get("size", 0) < 100:
            atomicity -= 25.0  # Too small/trivial
        elif repo_data.get("size", 0) > 50000:
            atomicity -= 15.0  # Too large/monolithic
            
        if repo_stats.get("language_diversity", 0) > 0.7:
            atomicity -= 20.0  # Too many languages, poor focus
        elif repo_stats.get("language_diversity", 0) < 0.1:
            atomicity -= 10.0  # Too limited
            
        if len(repo_data.get("topics", [])) < 2:
            atomicity -= 15.0  # Poor categorization
        
        # CONSISTENCY: Code standards and formatting
        consistency = 100.0
        
        # Penalties for inconsistency
        if not repo_stats.get("has_readme"):
            consistency -= 30.0  # Critical: No README
        elif repo_data.get("description", "") and len(repo_data["description"]) < 30:
            consistency -= 15.0  # Poor description
            
        if not repo_stats.get("has_license"):
            consistency -= 25.0  # No license
            
        if not repo_data.get("language"):
            consistency -= 20.0  # No primary language
            
        if len(repo_data.get("topics", [])) == 0:
            consistency -= 20.0  # No topics
        elif len(repo_data.get("topics", [])) < 3:
            consistency -= 10.0  # Few topics
            
        comment_ratio = repo_stats.get("comment_ratio", 0)
        if comment_ratio < 0.05:
            consistency -= 25.0  # Almost no comments
        elif comment_ratio < 0.10:
            consistency -= 15.0  # Few comments
        
        # ISOLATION: Dependencies and architecture
        isolation = 100.0
        
        # Penalties for poor isolation
        if not repo_stats.get("has_ci"):
            isolation -= 30.0  # No CI/CD
            
        if repo_stats.get("language_diversity", 0) > 0.8:
            isolation -= 25.0  # Too many dependencies
            
        if repo_data.get("forks_count", 0) == 0 and repo_data.get("stargazers_count", 0) < 5:
            isolation -= 20.0  # No community validation
            
        config_files = repo_stats.get("config_file_count", 0)
        if config_files == 0:
            isolation -= 15.0  # No configuration management
        
        # DURABILITY: Maintainability and testing
        durability = 100.0
        
        # Penalties for poor durability
        if not repo_stats.get("has_tests"):
            durability -= 45.0  # Critical: No tests
        elif repo_stats.get("test_coverage", 0) < 0.30:
            durability -= 25.0  # Low test coverage
        elif repo_stats.get("test_coverage", 0) < 0.50:
            durability -= 15.0  # Moderate test coverage
            
        if not repo_stats.get("has_documentation"):
            durability -= 25.0  # No documentation
        elif repo_stats.get("documentation_coverage", 0) < 0.20:
            durability -= 15.0  # Poor documentation
            
        if not repo_stats.get("has_license"):
            durability -= 20.0  # No license
            
        # Check for recent activity
        if repo_data.get("updated_at"):
            from datetime import datetime, timedelta
            try:
                last_update = datetime.fromisoformat(repo_data["updated_at"].replace('Z', '+00:00'))
                days_since_update = (datetime.now(last_update.tzinfo) - last_update).days
                if days_since_update > 365:
                    durability -= 20.0  # Abandoned (>1 year)
                elif days_since_update > 180:
                    durability -= 10.0  # Stale (>6 months)
            except:
                pass
        
        # Ensure scores don't go below 0
        atomicity = max(0, atomicity)
        consistency = max(0, consistency)
        isolation = max(0, isolation)
        durability = max(0, durability)
        
        overall = (atomicity + consistency + isolation + durability) / 4
        
        logger.info(f"ACID Scores - A:{atomicity:.1f} C:{consistency:.1f} I:{isolation:.1f} D:{durability:.1f} Overall:{overall:.1f}")
        
        return {
            "atomicity": round(atomicity, 1),
            "consistency": round(consistency, 1),
            "isolation": round(isolation, 1),
            "durability": round(durability, 1),
            "overall": round(overall, 1)
        }
    
    def _calculate_quality_metrics(self, repo_data: Dict[str, Any], repo_stats: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate quality metrics using penalty-first approach.
        Start with 100 and subtract for quality issues.
        """
        
        # READABILITY: Start with 100, subtract penalties
        readability = 100.0
        if not repo_stats.get("has_readme"):
            readability -= 35.0  # Critical
        if not repo_data.get("description") or len(repo_data.get("description", "")) < 30:
            readability -= 25.0  # Poor description
        if len(repo_data.get("topics", [])) < 2:
            readability -= 20.0  # Poor categorization
        comment_ratio = repo_stats.get("comment_ratio", 0)
        if comment_ratio < 0.10:
            readability -= 20.0  # Poor code comments
        
        # MAINTAINABILITY: Start with 100, subtract penalties
        maintainability = 100.0
        if not repo_stats.get("has_tests"):
            maintainability -= 40.0  # Critical
        if not repo_stats.get("has_license"):
            maintainability -= 25.0  # Important
        if not repo_stats.get("has_ci"):
            maintainability -= 25.0  # Important
        if repo_data.get("size", 0) > 50000:
            maintainability -= 10.0  # Too large
        
        # SECURITY: Start with 100, subtract penalties
        security = 100.0
        if not repo_stats.get("has_license"):
            security -= 30.0  # Legal/security risk
        if not repo_stats.get("has_ci"):
            security -= 25.0  # No automated checks
        # Note: Actual security vulnerabilities would be checked in code analysis
        # This is just basic security hygiene
        if repo_data.get("size", 0) < 100:
            security -= 15.0  # Too trivial to assess
        
        # TEST COVERAGE: Start with 100, subtract penalties
        test_coverage = 100.0
        if not repo_stats.get("has_tests"):
            test_coverage -= 70.0  # Critical penalty
        elif repo_stats.get("test_file_count", 0) < 3:
            test_coverage -= 40.0  # Few tests
        elif repo_stats.get("test_file_count", 0) < 5:
            test_coverage -= 20.0  # Some tests
        if not repo_stats.get("has_ci"):
            test_coverage -= 20.0  # No automated testing
        
        # DOCUMENTATION: Start with 100, subtract penalties
        documentation = 100.0
        if not repo_stats.get("has_readme"):
            documentation -= 45.0  # Critical
        if not repo_data.get("description") or len(repo_data.get("description", "")) < 20:
            documentation -= 25.0  # Poor description
        if len(repo_data.get("topics", [])) < 2:
            documentation -= 20.0  # Poor metadata
        if repo_stats.get("documentation_coverage", 0) < 0.10:
            documentation -= 10.0  # Poor inline docs
        
        # Ensure no negative scores
        readability = max(0, readability)
        maintainability = max(0, maintainability)
        security = max(0, security)
        test_coverage = max(0, test_coverage)
        documentation = max(0, documentation)
        
        return {
            "readability": round(readability, 1),
            "maintainability": round(maintainability, 1),
            "security": round(security, 1),
            "test_coverage": round(test_coverage, 1),
            "documentation": round(documentation, 1)
        }
    
    def _calculate_complexity_score(self, repo_data: Dict[str, Any]) -> float:
        """Calculate complexity score based on repository characteristics"""
        complexity = 0.0
        
        # Size complexity
        size = repo_data.get("size", 0)
        if size > 0:
            complexity += min(math.log10(size) * 20, 60)
        
        # Language complexity
        languages = repo_data.get("languages", {})
        if languages:
            complexity += min(len(languages) * 10, 40)
        
        return round(min(complexity, 100), 1)
    
    def _calculate_best_practices_score(self, repo_data: Dict[str, Any], repo_stats: Dict[str, Any]) -> float:
        """Calculate best practices adherence score"""
        score = 0.0
        
        # Repository structure
        score += 15 if repo_stats["has_readme"] else 0
        score += 15 if repo_stats["has_license"] else 0
        score += 20 if repo_stats["has_tests"] else 0
        score += 15 if repo_stats["has_ci"] else 0
        
        # Community engagement
        score += 10 if repo_data.get("stargazers_count", 0) > 0 else 0
        score += 10 if repo_data.get("forks_count", 0) > 0 else 0
        score += 5 if len(repo_data.get("topics", [])) > 0 else 0
        
        # Code quality indicators
        score += 10 * min(repo_stats["language_diversity"], 0.5)
        
        return round(min(score, 100), 1)
    
    def _analyze_python_code(self, code: str) -> Dict[str, Any]:
        """Enhanced Python code analysis with AST parsing and advanced metrics"""
        try:
            tree = ast.parse(code)
            
            # Basic counts
            functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
            imports = sum(1 for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom)))
            
            # Advanced complexity analysis
            complexity_analysis = self._calculate_python_complexity_ast(tree)
            
            # Code quality metrics
            quality_metrics = self._analyze_python_quality_ast(tree, code)
            
            # Language-specific features
            language_features = {
                "list_comprehensions": len([n for n in ast.walk(tree) if isinstance(n, ast.ListComp)]),
                "decorators": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.decorator_list]),
                "async_functions": len([n for n in ast.walk(tree) if isinstance(n, ast.AsyncFunctionDef)]),
                "generators": len([n for n in ast.walk(tree) if isinstance(n, ast.GeneratorExp)]),
                "context_managers": len([n for n in ast.walk(tree) if isinstance(n, ast.With)]),
                "exception_handling": len([n for n in ast.walk(tree) if isinstance(n, ast.Try)]),
                "type_annotations": len([n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.arg)) and n.annotation])
            }
            
            # Function and class analysis
            function_analysis = self._analyze_python_functions_ast(tree)
            class_analysis = self._analyze_python_classes_ast(tree)
            
            return {
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "complexity": complexity_analysis["cyclomatic_complexity"],
                "language_features": language_features,
                "quality_metrics": quality_metrics,
                "complexity_analysis": complexity_analysis,
                "function_analysis": function_analysis,
                "class_analysis": class_analysis,
                "ast_analysis": True
            }
        except Exception as e:
            logger.debug(f"Python AST parsing failed: {e}")
            return self._fallback_analysis(code, "Python")
    
    def _calculate_python_complexity_ast(self, tree: ast.AST) -> Dict[str, Any]:
        """Calculate comprehensive complexity metrics using AST"""
        
        complexity_metrics = {
            "cyclomatic_complexity": 1,  # Base complexity
            "cognitive_complexity": 0,
            "nesting_depth": 0,
            "decision_points": 0,
            "loop_complexity": 0,
            "conditional_complexity": 0
        }
        
        nesting_stack = []
        max_nesting = 0
        
        for node in ast.walk(tree):
            # Cyclomatic complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With, ast.ExceptHandler)):
                complexity_metrics["cyclomatic_complexity"] += 1
                complexity_metrics["decision_points"] += 1
                
                # Track nesting for cognitive complexity
                current_nesting = len(nesting_stack)
                complexity_metrics["cognitive_complexity"] += current_nesting + 1
                max_nesting = max(max_nesting, current_nesting + 1)
                
                if isinstance(node, (ast.While, ast.For)):
                    complexity_metrics["loop_complexity"] += 1
                elif isinstance(node, ast.If):
                    complexity_metrics["conditional_complexity"] += 1
                    
            elif isinstance(node, ast.BoolOp):
                # Boolean operators add complexity
                complexity_metrics["cyclomatic_complexity"] += len(node.values) - 1
                complexity_metrics["decision_points"] += len(node.values) - 1
        
        complexity_metrics["nesting_depth"] = max_nesting
        
        return complexity_metrics
    
    def _analyze_python_quality_ast(self, tree: ast.AST, code: str) -> Dict[str, Any]:
        """Analyze Python code quality using AST"""
        
        quality_metrics = {
            "docstring_coverage": 0,
            "function_length_distribution": {},
            "class_method_distribution": {},
            "import_organization": {},
            "naming_conventions": {},
            "code_smells": {}
        }
        
        # Analyze docstrings
        functions_with_docstrings = 0
        classes_with_docstrings = 0
        total_functions = 0
        total_classes = 0
        
        function_lengths = []
        class_method_counts = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                total_functions += 1
                
                # Check for docstring
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    functions_with_docstrings += 1
                
                # Function length
                function_length = len(node.body)
                function_lengths.append(function_length)
                
            elif isinstance(node, ast.ClassDef):
                total_classes += 1
                
                # Check for docstring
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    classes_with_docstrings += 1
                
                # Count methods in class
                method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
                class_method_counts.append(method_count)
        
        # Calculate docstring coverage
        if total_functions > 0:
            quality_metrics["docstring_coverage"] = functions_with_docstrings / total_functions
        
        # Function length distribution
        if function_lengths:
            quality_metrics["function_length_distribution"] = {
                "average": statistics.mean(function_lengths),
                "max": max(function_lengths),
                "min": min(function_lengths),
                "std_dev": statistics.stdev(function_lengths) if len(function_lengths) > 1 else 0
            }
        
        # Class method distribution
        if class_method_counts:
            quality_metrics["class_method_distribution"] = {
                "average": statistics.mean(class_method_counts),
                "max": max(class_method_counts),
                "min": min(class_method_counts)
            }
        
        # Analyze imports
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        quality_metrics["import_organization"] = {
            "total_imports": len(imports),
            "from_imports": len([n for n in imports if isinstance(n, ast.ImportFrom)]),
            "direct_imports": len([n for n in imports if isinstance(n, ast.Import)])
        }
        
        return quality_metrics
    
    def _analyze_python_functions_ast(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze Python functions using AST"""
        
        function_analysis = {
            "total_functions": 0,
            "async_functions": 0,
            "private_functions": 0,
            "decorated_functions": 0,
            "functions_with_args": 0,
            "functions_with_defaults": 0,
            "average_parameters": 0,
            "max_parameters": 0
        }
        
        parameter_counts = []
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                function_analysis["total_functions"] += 1
                
                if isinstance(node, ast.AsyncFunctionDef):
                    function_analysis["async_functions"] += 1
                
                # Check if private (starts with _)
                if node.name.startswith('_'):
                    function_analysis["private_functions"] += 1
                
                # Check for decorators
                if node.decorator_list:
                    function_analysis["decorated_functions"] += 1
                
                # Analyze parameters
                args = node.args
                param_count = len(args.args) + len(args.posonlyargs) + len(args.kwonlyargs)
                if args.vararg:
                    param_count += 1
                if args.kwarg:
                    param_count += 1
                
                parameter_counts.append(param_count)
                
                if param_count > 0:
                    function_analysis["functions_with_args"] += 1
                
                if args.defaults or args.kw_defaults:
                    function_analysis["functions_with_defaults"] += 1
        
        if parameter_counts:
            function_analysis["average_parameters"] = statistics.mean(parameter_counts)
            function_analysis["max_parameters"] = max(parameter_counts)
        
        return function_analysis
    
    def _analyze_python_classes_ast(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze Python classes using AST"""
        
        class_analysis = {
            "total_classes": 0,
            "classes_with_inheritance": 0,
            "abstract_classes": 0,
            "classes_with_properties": 0,
            "average_methods_per_class": 0,
            "max_methods_per_class": 0
        }
        
        method_counts = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_analysis["total_classes"] += 1
                
                # Check for inheritance
                if node.bases:
                    class_analysis["classes_with_inheritance"] += 1
                
                # Count methods and properties
                methods = 0
                properties = 0
                
                for class_node in node.body:
                    if isinstance(class_node, ast.FunctionDef):
                        methods += 1
                        
                        # Check for property decorator
                        for decorator in class_node.decorator_list:
                            if (isinstance(decorator, ast.Name) and decorator.id == 'property') or \
                               (isinstance(decorator, ast.Attribute) and decorator.attr == 'property'):
                                properties += 1
                                break
                
                method_counts.append(methods)
                
                if properties > 0:
                    class_analysis["classes_with_properties"] += 1
        
        if method_counts:
            class_analysis["average_methods_per_class"] = statistics.mean(method_counts)
            class_analysis["max_methods_per_class"] = max(method_counts)
        
        return class_analysis
    
    def _analyze_javascript_code(self, code: str) -> Dict[str, Any]:
        """Analyze JavaScript code for quality metrics"""
        
        # Function patterns
        function_patterns = [
            r'function\s+\w+\s*\(',
            r'\w+\s*:\s*function\s*\(',
            r'const\s+\w+\s*=\s*\([^)]*\)\s*=>',
            r'let\s+\w+\s*=\s*\([^)]*\)\s*=>',
            r'var\s+\w+\s*=\s*function'
        ]
        
        functions = sum(len(re.findall(pattern, code)) for pattern in function_patterns)
        classes = len(re.findall(r'class\s+\w+', code))
        
        # ES6+ features
        es6_features = {
            "arrow_functions": len(re.findall(r'=>', code)),
            "template_literals": len(re.findall(r'`[^`]*`', code)),
            "destructuring": len(re.findall(r'const\s*{[^}]+}\s*=|let\s*{[^}]+}\s*=', code)),
            "async_await": len(re.findall(r'async\s+function|await\s+', code)),
            "modules": len(re.findall(r'import\s+|export\s+', code))
        }
        
        # Calculate complexity
        complexity = self._calculate_js_complexity(code)
        
        return {
            "functions": functions,
            "classes": classes,
            "complexity": complexity,
            "es6_features": es6_features,
            "framework_indicators": self._detect_js_frameworks(code)
        }
    
    def _analyze_typescript_code(self, code: str) -> Dict[str, Any]:
        """Analyze TypeScript code for quality metrics"""
        
        # Start with JavaScript analysis
        js_analysis = self._analyze_javascript_code(code)
        
        # TypeScript-specific features
        ts_features = {
            "interfaces": len(re.findall(r'interface\s+\w+', code)),
            "types": len(re.findall(r'type\s+\w+\s*=', code)),
            "generics": len(re.findall(r'<[^>]+>', code)),
            "decorators": len(re.findall(r'@\w+', code)),
            "enums": len(re.findall(r'enum\s+\w+', code))
        }
        
        js_analysis["typescript_features"] = ts_features
        return js_analysis
    
    def _analyze_java_code(self, code: str) -> Dict[str, Any]:
        """Analyze Java code for quality metrics"""
        
        # Method patterns
        methods = len(re.findall(r'(public|private|protected)\s+\w+\s+\w+\s*\([^)]*\)\s*{', code))
        classes = len(re.findall(r'(public\s+)?class\s+\w+', code))
        interfaces = len(re.findall(r'interface\s+\w+', code))
        
        # Java-specific features
        java_features = {
            "annotations": len(re.findall(r'@\w+', code)),
            "generics": len(re.findall(r'<[^>]+>', code)),
            "lambda_expressions": len(re.findall(r'->', code)),
            "streams": len(re.findall(r'\.stream\(\)', code)),
            "try_catch": len(re.findall(r'try\s*{|catch\s*\(', code))
        }
        
        complexity = self._calculate_java_complexity(code)
        
        return {
            "functions": methods,
            "classes": classes,
            "interfaces": interfaces,
            "complexity": complexity,
            "java_features": java_features
        }
    
    def _analyze_go_code(self, code: str) -> Dict[str, Any]:
        """Analyze Go code for quality metrics"""
        
        functions = len(re.findall(r'func\s+\w+\s*\([^)]*\)', code))
        structs = len(re.findall(r'type\s+\w+\s+struct', code))
        interfaces = len(re.findall(r'type\s+\w+\s+interface', code))
        
        # Go-specific features
        go_features = {
            "goroutines": len(re.findall(r'go\s+\w+\(', code)),
            "channels": len(re.findall(r'chan\s+\w+|<-\s*chan|chan\s*<-', code)),
            "defer": len(re.findall(r'defer\s+', code)),
            "error_handling": len(re.findall(r'if\s+err\s*!=\s*nil', code)),
            "packages": len(re.findall(r'package\s+\w+', code))
        }
        
        complexity = self._calculate_go_complexity(code)
        
        return {
            "functions": functions,
            "structs": structs,
            "interfaces": interfaces,
            "complexity": complexity,
            "go_features": go_features
        }
    
    def _analyze_cpp_code(self, code: str) -> Dict[str, Any]:
        """Analyze C++ code for quality metrics"""
        
        functions = len(re.findall(r'\w+\s+\w+\s*\([^)]*\)\s*{', code))
        classes = len(re.findall(r'class\s+\w+', code))
        
        cpp_features = {
            "templates": len(re.findall(r'template\s*<', code)),
            "namespaces": len(re.findall(r'namespace\s+\w+', code)),
            "smart_pointers": len(re.findall(r'std::(unique_ptr|shared_ptr|weak_ptr)', code)),
            "lambdas": len(re.findall(r'\[[^\]]*\]\s*\([^)]*\)', code))
        }
        
        return {
            "functions": functions,
            "classes": classes,
            "complexity": self._calculate_cpp_complexity(code),
            "cpp_features": cpp_features
        }
    
    def _analyze_csharp_code(self, code: str) -> Dict[str, Any]:
        """Analyze C# code for quality metrics"""
        
        methods = len(re.findall(r'(public|private|protected)\s+\w+\s+\w+\s*\([^)]*\)', code))
        classes = len(re.findall(r'(public\s+)?class\s+\w+', code))
        
        csharp_features = {
            "properties": len(re.findall(r'{\s*get\s*;\s*set\s*;}', code)),
            "linq": len(re.findall(r'\.Where\(|\.Select\(|\.OrderBy\(', code)),
            "async_await": len(re.findall(r'async\s+\w+|await\s+', code)),
            "attributes": len(re.findall(r'\[\w+\]', code))
        }
        
        return {
            "functions": methods,
            "classes": classes,
            "complexity": self._calculate_csharp_complexity(code),
            "csharp_features": csharp_features
        }
    
    def _analyze_ruby_code(self, code: str) -> Dict[str, Any]:
        """Analyze Ruby code for quality metrics"""
        
        methods = len(re.findall(r'def\s+\w+', code))
        classes = len(re.findall(r'class\s+\w+', code))
        modules = len(re.findall(r'module\s+\w+', code))
        
        return {
            "functions": methods,
            "classes": classes,
            "modules": modules,
            "complexity": self._calculate_ruby_complexity(code)
        }
    
    def _analyze_php_code(self, code: str) -> Dict[str, Any]:
        """Analyze PHP code for quality metrics"""
        
        functions = len(re.findall(r'function\s+\w+\s*\(', code))
        classes = len(re.findall(r'class\s+\w+', code))
        
        return {
            "functions": functions,
            "classes": classes,
            "complexity": self._calculate_php_complexity(code)
        }
    
    def _analyze_swift_code(self, code: str) -> Dict[str, Any]:
        """Analyze Swift code for quality metrics"""
        
        functions = len(re.findall(r'func\s+\w+\s*\(', code))
        classes = len(re.findall(r'class\s+\w+', code))
        structs = len(re.findall(r'struct\s+\w+', code))
        
        return {
            "functions": functions,
            "classes": classes,
            "structs": structs,
            "complexity": self._calculate_swift_complexity(code)
        }
    
    def _analyze_kotlin_code(self, code: str) -> Dict[str, Any]:
        """Analyze Kotlin code for quality metrics"""
        
        functions = len(re.findall(r'fun\s+\w+\s*\(', code))
        classes = len(re.findall(r'class\s+\w+', code))
        
        return {
            "functions": functions,
            "classes": classes,
            "complexity": self._calculate_kotlin_complexity(code)
        }
    
    def _analyze_rust_code(self, code: str) -> Dict[str, Any]:
        """Analyze Rust code for quality metrics"""
        
        functions = len(re.findall(r'fn\s+\w+\s*\(', code))
        structs = len(re.findall(r'struct\s+\w+', code))
        enums = len(re.findall(r'enum\s+\w+', code))
        
        rust_features = {
            "match_expressions": len(re.findall(r'match\s+\w+', code)),
            "lifetimes": len(re.findall(r"'[a-zA-Z]\w*", code)),
            "traits": len(re.findall(r'trait\s+\w+', code)),
            "macros": len(re.findall(r'\w+!', code))
        }
        
        return {
            "functions": functions,
            "structs": structs,
            "enums": enums,
            "complexity": self._calculate_rust_complexity(code),
            "rust_features": rust_features
        }
    
    def _fallback_analysis(self, code: str, language: str) -> Dict[str, Any]:
        """Fallback analysis when language-specific parsing fails"""
        
        lines = code.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        # Generic patterns
        function_indicators = ['def ', 'function ', 'func ', 'fn ', 'method ']
        class_indicators = ['class ', 'struct ', 'interface ']
        
        functions = sum(len([line for line in non_empty_lines if indicator in line.lower()]) 
                       for indicator in function_indicators)
        classes = sum(len([line for line in non_empty_lines if indicator in line.lower()]) 
                     for indicator in class_indicators)
        
        # Basic complexity estimate
        complexity_indicators = ['if', 'while', 'for', 'switch', 'case', 'try', 'catch']
        complexity = sum(code.lower().count(indicator) for indicator in complexity_indicators)
        
        return {
            "functions": functions,
            "classes": classes,
            "complexity": max(1, complexity),
            "lines": len(non_empty_lines),
            "analysis_method": "fallback"
        }
    
    # Language-specific complexity calculators
    def _calculate_js_complexity(self, code: str) -> int:
        """Calculate JavaScript-specific complexity"""
        complexity = 1
        patterns = [r'if\s*\(', r'while\s*\(', r'for\s*\(', r'switch\s*\(', 
                   r'catch\s*\(', r'\?\s*:', r'&&', r'\|\|']
        
        for pattern in patterns:
            complexity += len(re.findall(pattern, code))
        
        return complexity
    
    def _calculate_java_complexity(self, code: str) -> int:
        """Calculate Java-specific complexity"""
        complexity = 1
        patterns = [r'if\s*\(', r'while\s*\(', r'for\s*\(', r'switch\s*\(',
                   r'catch\s*\(', r'case\s+\w+:', r'&&', r'\|\|']
        
        for pattern in patterns:
            complexity += len(re.findall(pattern, code))
        
        return complexity
    
    def _calculate_go_complexity(self, code: str) -> int:
        """Calculate Go-specific complexity"""
        complexity = 1
        patterns = [r'if\s+', r'for\s+', r'switch\s+', r'case\s+', r'&&', r'\|\|']
        
        for pattern in patterns:
            complexity += len(re.findall(pattern, code))
        
        return complexity
    
    def _calculate_cpp_complexity(self, code: str) -> int:
        """Calculate C++-specific complexity"""
        complexity = 1
        patterns = [r'if\s*\(', r'while\s*\(', r'for\s*\(', r'switch\s*\(',
                   r'catch\s*\(', r'case\s+\w+:', r'&&', r'\|\|']
        
        for pattern in patterns:
            complexity += len(re.findall(pattern, code))
        
        return complexity
    
    def _calculate_csharp_complexity(self, code: str) -> int:
        """Calculate C#-specific complexity"""
        return self._calculate_java_complexity(code)  # Similar patterns
    
    def _calculate_ruby_complexity(self, code: str) -> int:
        """Calculate Ruby-specific complexity"""
        complexity = 1
        patterns = [r'if\s+', r'while\s+', r'for\s+', r'case\s+', r'when\s+', r'&&', r'\|\|']
        
        for pattern in patterns:
            complexity += len(re.findall(pattern, code))
        
        return complexity
    
    def _calculate_php_complexity(self, code: str) -> int:
        """Calculate PHP-specific complexity"""
        return self._calculate_js_complexity(code)  # Similar patterns
    
    def _calculate_swift_complexity(self, code: str) -> int:
        """Calculate Swift-specific complexity"""
        complexity = 1
        patterns = [r'if\s+', r'while\s+', r'for\s+', r'switch\s+', r'case\s+', r'&&', r'\|\|']
        
        for pattern in patterns:
            complexity += len(re.findall(pattern, code))
        
        return complexity
    
    def _calculate_kotlin_complexity(self, code: str) -> int:
        """Calculate Kotlin-specific complexity"""
        return self._calculate_java_complexity(code)  # Similar patterns
    
    def _calculate_rust_complexity(self, code: str) -> int:
        """Calculate Rust-specific complexity"""
        complexity = 1
        patterns = [r'if\s+', r'while\s+', r'for\s+', r'match\s+', r'&&', r'\|\|']
        
        for pattern in patterns:
            complexity += len(re.findall(pattern, code))
        
        return complexity
    
    def _detect_js_frameworks(self, code: str) -> Dict[str, bool]:
        """Detect JavaScript frameworks and libraries"""
        
        frameworks = {
            "react": bool(re.search(r'import.*react|from\s+["\']react["\']', code, re.IGNORECASE)),
            "vue": bool(re.search(r'import.*vue|from\s+["\']vue["\']', code, re.IGNORECASE)),
            "angular": bool(re.search(r'@angular|import.*@angular', code, re.IGNORECASE)),
            "express": bool(re.search(r'express\(\)|require\(["\']express["\']', code, re.IGNORECASE)),
            "lodash": bool(re.search(r'import.*lodash|require\(["\']lodash["\']', code, re.IGNORECASE)),
            "jquery": bool(re.search(r'\$\(|\$\.', code)),
            "node": bool(re.search(r'require\(|module\.exports|process\.', code))
        }
        
        return frameworks
    
    # ==================== COMPREHENSIVE CODE COMPLEXITY ANALYSIS ====================
    
    def _analyze_code_complexity_strict(self, content: str, language: str, file_path: str) -> Dict[str, Any]:
        """
        Strict and comprehensive code complexity analysis for all supported languages
        """
        
        complexity_analysis = {
            "cyclomatic_complexity": 0,
            "cognitive_complexity": 0,
            "halstead_metrics": {},
            "maintainability_index": 0,
            "nesting_depth": 0,
            "function_complexity": [],
            "class_complexity": [],
            "code_smells": {},
            "quality_score": 0,
            "language_specific_metrics": {}
        }
        
        # Language-specific analysis
        if language == "Python" and self.supported_languages[language]['ast_parser']:
            complexity_analysis = self._analyze_python_complexity_comprehensive(content, file_path)
        else:
            complexity_analysis = self._analyze_generic_complexity_comprehensive(content, language, file_path)
        
        # Calculate overall quality score
        complexity_analysis["quality_score"] = self._calculate_code_quality_score(complexity_analysis)
        
        return complexity_analysis
    
    def _analyze_python_complexity_comprehensive(self, content: str, file_path: str) -> Dict[str, Any]:
        """Comprehensive Python complexity analysis using AST"""
        
        try:
            tree = ast.parse(content)
            
            complexity_analysis = {
                "cyclomatic_complexity": 0,
                "cognitive_complexity": 0,
                "halstead_metrics": {},
                "maintainability_index": 0,
                "nesting_depth": 0,
                "function_complexity": [],
                "class_complexity": [],
                "code_smells": {},
                "language_specific_metrics": {}
            }
            
            # Analyze each function and class
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_complexity = self._analyze_python_function_complexity(node)
                    complexity_analysis["function_complexity"].append(func_complexity)
                    
                elif isinstance(node, ast.ClassDef):
                    class_complexity = self._analyze_python_class_complexity(node)
                    complexity_analysis["class_complexity"].append(class_complexity)
            
            # Calculate overall metrics
            complexity_analysis["cyclomatic_complexity"] = self._calculate_overall_cyclomatic_complexity(tree)
            complexity_analysis["cognitive_complexity"] = self._calculate_overall_cognitive_complexity(tree)
            complexity_analysis["nesting_depth"] = self._calculate_max_nesting_depth(tree)
            complexity_analysis["halstead_metrics"] = self._calculate_halstead_metrics_ast(tree, content)
            complexity_analysis["code_smells"] = self._detect_python_code_smells(tree, content)
            complexity_analysis["language_specific_metrics"] = self._analyze_python_specific_metrics(tree)
            
            # Calculate maintainability index
            complexity_analysis["maintainability_index"] = self._calculate_maintainability_index_python(
                complexity_analysis, content
            )
            
            return complexity_analysis
            
        except Exception as e:
            logger.error(f"Python AST analysis failed for {file_path}: {e}")
            return self._analyze_generic_complexity_comprehensive(content, "Python", file_path)
    
    def _analyze_python_function_complexity(self, func_node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze complexity of a single Python function"""
        
        func_complexity = {
            "name": func_node.name,
            "cyclomatic_complexity": 1,  # Base complexity
            "cognitive_complexity": 0,
            "nesting_depth": 0,
            "parameter_count": 0,
            "lines_of_code": 0,
            "return_statements": 0,
            "complexity_rating": "low"
        }
        
        # Count parameters
        args = func_node.args
        func_complexity["parameter_count"] = (
            len(args.args) + len(args.posonlyargs) + len(args.kwonlyargs) +
            (1 if args.vararg else 0) + (1 if args.kwarg else 0)
        )
        
        # Analyze function body
        nesting_level = 0
        max_nesting = 0
        
        for node in ast.walk(func_node):
            # Cyclomatic complexity
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With, ast.ExceptHandler)):
                func_complexity["cyclomatic_complexity"] += 1
                nesting_level += 1
                max_nesting = max(max_nesting, nesting_level)
                func_complexity["cognitive_complexity"] += nesting_level
                
            elif isinstance(node, ast.BoolOp):
                func_complexity["cyclomatic_complexity"] += len(node.values) - 1
                
            elif isinstance(node, ast.Return):
                func_complexity["return_statements"] += 1
        
        func_complexity["nesting_depth"] = max_nesting
        func_complexity["lines_of_code"] = len(func_node.body)
        
        # Determine complexity rating
        cc = func_complexity["cyclomatic_complexity"]
        if cc <= 5:
            func_complexity["complexity_rating"] = "low"
        elif cc <= 10:
            func_complexity["complexity_rating"] = "medium"
        elif cc <= 20:
            func_complexity["complexity_rating"] = "high"
        else:
            func_complexity["complexity_rating"] = "very_high"
        
        return func_complexity
    
    def _analyze_python_class_complexity(self, class_node: ast.ClassDef) -> Dict[str, Any]:
        """Analyze complexity of a single Python class"""
        
        class_complexity = {
            "name": class_node.name,
            "method_count": 0,
            "property_count": 0,
            "inheritance_depth": len(class_node.bases),
            "total_complexity": 0,
            "average_method_complexity": 0,
            "cohesion_score": 0,
            "complexity_rating": "low"
        }
        
        method_complexities = []
        
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef):
                class_complexity["method_count"] += 1
                method_complexity = self._analyze_python_function_complexity(node)
                method_complexities.append(method_complexity["cyclomatic_complexity"])
                
                # Check for property decorator
                for decorator in node.decorator_list:
                    if (isinstance(decorator, ast.Name) and decorator.id == 'property') or \
                       (isinstance(decorator, ast.Attribute) and decorator.attr == 'property'):
                        class_complexity["property_count"] += 1
                        break
        
        if method_complexities:
            class_complexity["total_complexity"] = sum(method_complexities)
            class_complexity["average_method_complexity"] = statistics.mean(method_complexities)
        
        # Calculate cohesion score (simplified)
        if class_complexity["method_count"] > 0:
            class_complexity["cohesion_score"] = min(100, (10 / class_complexity["method_count"]) * 100)
        
        # Determine complexity rating
        avg_complexity = class_complexity["average_method_complexity"]
        if avg_complexity <= 3:
            class_complexity["complexity_rating"] = "low"
        elif avg_complexity <= 7:
            class_complexity["complexity_rating"] = "medium"
        elif avg_complexity <= 15:
            class_complexity["complexity_rating"] = "high"
        else:
            class_complexity["complexity_rating"] = "very_high"
        
        return class_complexity
    
    def _calculate_overall_cyclomatic_complexity(self, tree: ast.AST) -> float:
        """Calculate overall cyclomatic complexity for the entire file"""
        
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.And, ast.Or)):
                complexity += 1
        
        return complexity
    
    def _calculate_overall_cognitive_complexity(self, tree: ast.AST) -> float:
        """Calculate overall cognitive complexity"""
        
        cognitive_complexity = 0
        nesting_stack = []
        
        def visit_node(node, nesting_level=0):
            nonlocal cognitive_complexity
            
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                cognitive_complexity += nesting_level + 1
                nesting_level += 1
            elif isinstance(node, ast.BoolOp):
                cognitive_complexity += len(node.values) - 1
            
            for child in ast.iter_child_nodes(node):
                visit_node(child, nesting_level)
        
        visit_node(tree)
        return cognitive_complexity
    
    def _calculate_max_nesting_depth(self, tree: ast.AST) -> int:
        """Calculate maximum nesting depth"""
        
        max_depth = 0
        
        def visit_node(node, current_depth=0):
            nonlocal max_depth
            
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With, ast.FunctionDef, ast.ClassDef)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(node):
                visit_node(child, current_depth)
        
        visit_node(tree)
        return max_depth
    
    def _calculate_halstead_metrics_ast(self, tree: ast.AST, content: str) -> Dict[str, float]:
        """Calculate Halstead metrics using AST"""
        
        operators = set()
        operands = set()
        operator_count = 0
        operand_count = 0
        
        for node in ast.walk(tree):
            # Operators
            if isinstance(node, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow)):
                operators.add(type(node).__name__)
                operator_count += 1
            elif isinstance(node, (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE)):
                operators.add(type(node).__name__)
                operator_count += 1
            elif isinstance(node, (ast.And, ast.Or, ast.Not)):
                operators.add(type(node).__name__)
                operator_count += 1
            elif isinstance(node, ast.Assign):
                operators.add('Assign')
                operator_count += 1
            
            # Operands
            elif isinstance(node, ast.Name):
                operands.add(node.id)
                operand_count += 1
            elif isinstance(node, ast.Constant):
                operands.add(str(node.value))
                operand_count += 1
        
        # Halstead metrics
        n1 = len(operators)  # Number of distinct operators
        n2 = len(operands)   # Number of distinct operands
        N1 = operator_count  # Total operators
        N2 = operand_count   # Total operands
        
        vocabulary = n1 + n2
        length = N1 + N2
        volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
        difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
        effort = difficulty * volume
        time_to_program = effort / 18  # Stroud number
        bugs_delivered = volume / 3000  # Empirical formula
        
        return {
            "vocabulary": vocabulary,
            "length": length,
            "volume": volume,
            "difficulty": difficulty,
            "effort": effort,
            "time_to_program": time_to_program,
            "bugs_delivered": bugs_delivered
        }
    
    def _detect_python_code_smells(self, tree: ast.AST, content: str) -> Dict[str, int]:
        """Detect Python-specific code smells"""
        
        code_smells = {
            "long_functions": 0,
            "long_classes": 0,
            "too_many_parameters": 0,
            "deep_nesting": 0,
            "duplicate_code": 0,
            "magic_numbers": 0,
            "god_class": 0,
            "dead_code": 0
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Long functions (> 50 lines)
                if len(node.body) > 50:
                    code_smells["long_functions"] += 1
                
                # Too many parameters (> 7)
                args = node.args
                param_count = len(args.args) + len(args.posonlyargs) + len(args.kwonlyargs)
                if param_count > 7:
                    code_smells["too_many_parameters"] += 1
                
                # Deep nesting (> 4 levels)
                max_nesting = self._get_function_nesting_depth(node)
                if max_nesting > 4:
                    code_smells["deep_nesting"] += 1
            
            elif isinstance(node, ast.ClassDef):
                # Long classes (> 500 lines or > 20 methods)
                method_count = sum(1 for n in node.body if isinstance(n, ast.FunctionDef))
                if len(node.body) > 100 or method_count > 20:
                    code_smells["long_classes"] += 1
                
                # God class (> 30 methods)
                if method_count > 30:
                    code_smells["god_class"] += 1
            
            elif isinstance(node, ast.Constant):
                # Magic numbers (numeric constants > 1)
                if isinstance(node.value, (int, float)) and abs(node.value) > 1:
                    code_smells["magic_numbers"] += 1
        
        # Duplicate code detection (simplified)
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        unique_lines = set(lines)
        code_smells["duplicate_code"] = len(lines) - len(unique_lines)
        
        return code_smells
    
    def _get_function_nesting_depth(self, func_node: ast.FunctionDef) -> int:
        """Get maximum nesting depth within a function"""
        
        max_depth = 0
        
        def visit_node(node, current_depth=0):
            nonlocal max_depth
            
            if isinstance(node, (ast.If, ast.While, ast.For, ast.Try, ast.With)):
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            
            for child in ast.iter_child_nodes(node):
                visit_node(child, current_depth)
        
        for child in func_node.body:
            visit_node(child)
        
        return max_depth
    
    def _analyze_python_specific_metrics(self, tree: ast.AST) -> Dict[str, Any]:
        """Analyze Python-specific language metrics"""
        
        metrics = {
            "pythonic_features": {
                "list_comprehensions": 0,
                "dict_comprehensions": 0,
                "set_comprehensions": 0,
                "generator_expressions": 0,
                "context_managers": 0,
                "decorators": 0,
                "lambda_functions": 0,
                "f_strings": 0
            },
            "modern_python_features": {
                "type_hints": 0,
                "async_await": 0,
                "dataclasses": 0,
                "pathlib_usage": 0,
                "walrus_operator": 0
            },
            "code_organization": {
                "imports_at_top": True,
                "proper_main_guard": False,
                "docstring_coverage": 0
            }
        }
        
        # Count Pythonic features
        for node in ast.walk(tree):
            if isinstance(node, ast.ListComp):
                metrics["pythonic_features"]["list_comprehensions"] += 1
            elif isinstance(node, ast.DictComp):
                metrics["pythonic_features"]["dict_comprehensions"] += 1
            elif isinstance(node, ast.SetComp):
                metrics["pythonic_features"]["set_comprehensions"] += 1
            elif isinstance(node, ast.GeneratorExp):
                metrics["pythonic_features"]["generator_expressions"] += 1
            elif isinstance(node, ast.With):
                metrics["pythonic_features"]["context_managers"] += 1
            elif isinstance(node, ast.Lambda):
                metrics["pythonic_features"]["lambda_functions"] += 1
            elif isinstance(node, ast.AsyncFunctionDef):
                metrics["modern_python_features"]["async_await"] += 1
            elif isinstance(node, (ast.FunctionDef, ast.arg)) and hasattr(node, 'annotation') and node.annotation:
                metrics["modern_python_features"]["type_hints"] += 1
        
        # Check for main guard
        for node in ast.walk(tree):
            if (isinstance(node, ast.If) and 
                isinstance(node.test, ast.Compare) and
                isinstance(node.test.left, ast.Name) and
                node.test.left.id == '__name__'):
                metrics["code_organization"]["proper_main_guard"] = True
                break
        
        return metrics
    
    def _calculate_maintainability_index_python(self, complexity_analysis: Dict[str, Any], content: str) -> float:
        """Calculate maintainability index for Python code"""
        
        # Halstead Volume
        halstead_volume = complexity_analysis["halstead_metrics"].get("volume", 0)
        
        # Cyclomatic Complexity
        cyclomatic_complexity = complexity_analysis["cyclomatic_complexity"]
        
        # Lines of Code
        lines_of_code = len([line for line in content.split('\n') if line.strip()])
        
        # Comment Ratio
        comment_lines = len([line for line in content.split('\n') 
                           if line.strip().startswith('#') or '"""' in line or "'''" in line])
        comment_ratio = comment_lines / max(lines_of_code, 1)
        
        # Maintainability Index formula (Microsoft's version)
        if halstead_volume > 0 and lines_of_code > 0:
            mi = (171 - 5.2 * math.log(halstead_volume) - 
                  0.23 * cyclomatic_complexity - 
                  16.2 * math.log(lines_of_code) + 
                  50 * math.sin(math.sqrt(2.4 * comment_ratio)))
        else:
            mi = 50  # Default moderate score
        
        return max(0, min(100, mi))
    
    def _analyze_generic_complexity_comprehensive(self, content: str, language: str, file_path: str) -> Dict[str, Any]:
        """Comprehensive complexity analysis for non-Python languages using regex patterns"""
        
        complexity_analysis = {
            "cyclomatic_complexity": 1,  # Base complexity
            "cognitive_complexity": 0,
            "halstead_metrics": {},
            "maintainability_index": 0,
            "nesting_depth": 0,
            "function_complexity": [],
            "class_complexity": [],
            "code_smells": {},
            "language_specific_metrics": {}
        }
        
        if language not in self.supported_languages:
            return complexity_analysis
        
        lang_config = self.supported_languages[language]
        
        # Calculate cyclomatic complexity
        for pattern in lang_config['complexity_patterns']:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            complexity_analysis["cyclomatic_complexity"] += matches
        
        # Calculate cognitive complexity (simplified)
        lines = content.split('\n')
        nesting_level = 0
        max_nesting = 0
        
        for line in lines:
            stripped = line.strip()
            
            # Increase nesting for control structures
            for pattern in lang_config['complexity_patterns'][:4]:  # First 4 are usually control structures
                if re.search(pattern, stripped, re.IGNORECASE):
                    nesting_level += 1
                    max_nesting = max(max_nesting, nesting_level)
                    complexity_analysis["cognitive_complexity"] += nesting_level
                    break
            
            # Decrease nesting for closing braces
            if stripped in ['}', 'end', 'endif', 'endfor', 'endwhile']:
                nesting_level = max(0, nesting_level - 1)
        
        complexity_analysis["nesting_depth"] = max_nesting
        
        # Analyze functions and classes
        complexity_analysis["function_complexity"] = self._analyze_functions_generic(content, language)
        complexity_analysis["class_complexity"] = self._analyze_classes_generic(content, language)
        
        # Calculate Halstead metrics (simplified)
        complexity_analysis["halstead_metrics"] = self._calculate_halstead_metrics_generic(content, language)
        
        # Detect code smells
        complexity_analysis["code_smells"] = self._detect_code_smells_generic(content, language)
        
        # Language-specific metrics
        complexity_analysis["language_specific_metrics"] = self._analyze_language_specific_features(content, language)
        
        # Calculate maintainability index
        complexity_analysis["maintainability_index"] = self._calculate_maintainability_index_generic(
            complexity_analysis, content
        )
        
        return complexity_analysis
    
    def _analyze_functions_generic(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Analyze functions for non-Python languages"""
        
        if language not in self.supported_languages:
            return []
        
        lang_config = self.supported_languages[language]
        function_complexities = []
        
        for pattern in lang_config['function_patterns']:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                func_start = match.start()
                func_name = self._extract_function_name(match.group(), language)
                
                # Find function end (simplified)
                func_content = self._extract_function_content(content, func_start, language)
                
                func_complexity = {
                    "name": func_name,
                    "cyclomatic_complexity": 1,
                    "lines_of_code": len(func_content.split('\n')),
                    "complexity_rating": "low"
                }
                
                # Calculate function complexity
                for complexity_pattern in lang_config['complexity_patterns']:
                    func_complexity["cyclomatic_complexity"] += len(
                        re.findall(complexity_pattern, func_content, re.IGNORECASE)
                    )
                
                # Determine complexity rating
                cc = func_complexity["cyclomatic_complexity"]
                if cc <= 5:
                    func_complexity["complexity_rating"] = "low"
                elif cc <= 10:
                    func_complexity["complexity_rating"] = "medium"
                elif cc <= 20:
                    func_complexity["complexity_rating"] = "high"
                else:
                    func_complexity["complexity_rating"] = "very_high"
                
                function_complexities.append(func_complexity)
        
        return function_complexities
    
    def _analyze_classes_generic(self, content: str, language: str) -> List[Dict[str, Any]]:
        """Analyze classes for non-Python languages"""
        
        if language not in self.supported_languages:
            return []
        
        lang_config = self.supported_languages[language]
        class_complexities = []
        
        for pattern in lang_config['class_patterns']:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                class_start = match.start()
                class_name = self._extract_class_name(match.group(), language)
                
                # Find class content (simplified)
                class_content = self._extract_class_content(content, class_start, language)
                
                # Count methods in class
                method_count = 0
                for func_pattern in lang_config['function_patterns']:
                    method_count += len(re.findall(func_pattern, class_content, re.IGNORECASE))
                
                class_complexity = {
                    "name": class_name,
                    "method_count": method_count,
                    "lines_of_code": len(class_content.split('\n')),
                    "complexity_rating": "low"
                }
                
                # Determine complexity rating based on method count
                if method_count <= 5:
                    class_complexity["complexity_rating"] = "low"
                elif method_count <= 15:
                    class_complexity["complexity_rating"] = "medium"
                elif method_count <= 30:
                    class_complexity["complexity_rating"] = "high"
                else:
                    class_complexity["complexity_rating"] = "very_high"
                
                class_complexities.append(class_complexity)
        
        return class_complexities
    
    def _extract_function_name(self, match_text: str, language: str) -> str:
        """Extract function name from regex match"""
        
        # Language-specific function name extraction
        if language in ["JavaScript", "TypeScript"]:
            # Handle various JS function patterns
            if "function" in match_text:
                name_match = re.search(r'function\s+(\w+)', match_text)
            elif "=>" in match_text:
                name_match = re.search(r'(const|let|var)\s+(\w+)', match_text)
                return name_match.group(2) if name_match else "anonymous"
            else:
                name_match = re.search(r'(\w+)\s*:', match_text)
        elif language == "Python":
            name_match = re.search(r'def\s+(\w+)', match_text)
        elif language in ["Java", "C#"]:
            name_match = re.search(r'\w+\s+(\w+)\s*\(', match_text)
        elif language == "Go":
            name_match = re.search(r'func\s+(\w+)', match_text)
        elif language == "Rust":
            name_match = re.search(r'fn\s+(\w+)', match_text)
        else:
            name_match = re.search(r'(\w+)', match_text)
        
        return name_match.group(1) if name_match else "unknown"
    
    def _extract_class_name(self, match_text: str, language: str) -> str:
        """Extract class name from regex match"""
        
        if language in ["Java", "C#", "C++", "JavaScript", "TypeScript", "Python"]:
            name_match = re.search(r'class\s+(\w+)', match_text)
        elif language == "Go":
            name_match = re.search(r'type\s+(\w+)\s+struct', match_text)
        elif language == "Rust":
            name_match = re.search(r'struct\s+(\w+)', match_text)
        else:
            name_match = re.search(r'(\w+)', match_text)
        
        return name_match.group(1) if name_match else "unknown"
    
    def _extract_function_content(self, content: str, start_pos: int, language: str) -> str:
        """Extract function content (simplified implementation)"""
        
        lines = content[start_pos:].split('\n')
        
        if language in ["JavaScript", "TypeScript", "Java", "C#", "C++", "Go", "Rust"]:
            # Brace-based languages
            brace_count = 0
            func_lines = []
            
            for line in lines:
                func_lines.append(line)
                brace_count += line.count('{') - line.count('}')
                
                if brace_count == 0 and '{' in ''.join(func_lines):
                    break
            
            return '\n'.join(func_lines)
        
        else:
            # Indentation-based or other languages
            return '\n'.join(lines[:50])  # Simplified: take first 50 lines
    
    def _extract_class_content(self, content: str, start_pos: int, language: str) -> str:
        """Extract class content (simplified implementation)"""
        
        return self._extract_function_content(content, start_pos, language)
    
    def _calculate_halstead_metrics_generic(self, content: str, language: str) -> Dict[str, float]:
        """Calculate Halstead metrics for generic languages"""
        
        # Generic operator and operand patterns
        operator_patterns = [r'\+', r'-', r'\*', r'/', r'=', r'==', r'!=', r'<', r'>', r'<=', r'>=', r'&&', r'\|\|']
        operand_patterns = [r'\b[a-zA-Z_]\w*\b', r'\b\d+\b', r'["\'][^"\']*["\']']
        
        operators = set()
        operands = set()
        operator_count = 0
        operand_count = 0
        
        # Count operators
        for pattern in operator_patterns:
            matches = re.findall(pattern, content)
            operators.update(matches)
            operator_count += len(matches)
        
        # Count operands
        for pattern in operand_patterns:
            matches = re.findall(pattern, content)
            operands.update(matches)
            operand_count += len(matches)
        
        # Calculate Halstead metrics
        n1 = len(operators)
        n2 = len(operands)
        N1 = operator_count
        N2 = operand_count
        
        vocabulary = n1 + n2
        length = N1 + N2
        volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
        difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
        effort = difficulty * volume
        
        return {
            "vocabulary": vocabulary,
            "length": length,
            "volume": volume,
            "difficulty": difficulty,
            "effort": effort
        }
    
    def _detect_code_smells_generic(self, content: str, language: str) -> Dict[str, int]:
        """Detect code smells for generic languages"""
        
        code_smells = {
            "long_functions": 0,
            "long_lines": 0,
            "deep_nesting": 0,
            "duplicate_code": 0,
            "magic_numbers": 0,
            "too_many_parameters": 0
        }
        
        lines = content.split('\n')
        
        # Long lines (> 120 characters)
        code_smells["long_lines"] = len([line for line in lines if len(line) > 120])
        
        # Magic numbers
        magic_number_pattern = r'\b\d{2,}\b'
        code_smells["magic_numbers"] = len(re.findall(magic_number_pattern, content))
        
        # Duplicate code (simplified)
        stripped_lines = [line.strip() for line in lines if line.strip()]
        unique_lines = set(stripped_lines)
        code_smells["duplicate_code"] = len(stripped_lines) - len(unique_lines)
        
        # Deep nesting (> 4 levels of indentation)
        for line in lines:
            if language == "Python":
                indent_level = (len(line) - len(line.lstrip())) // 4
            else:
                indent_level = line.count('{') - line.count('}')
            
            if indent_level > 4:
                code_smells["deep_nesting"] += 1
        
        return code_smells
    
    def _analyze_language_specific_features(self, content: str, language: str) -> Dict[str, Any]:
        """Analyze language-specific features and modern practices"""
        
        features = {
            "modern_features": [],
            "best_practices": [],
            "framework_usage": [],
            "language_version_indicators": []
        }
        
        # Language-specific feature detection
        if language == "JavaScript":
            if re.search(r'=>', content):
                features["modern_features"].append("arrow_functions")
            if re.search(r'const\s+|let\s+', content):
                features["modern_features"].append("es6_variables")
            if re.search(r'async\s+function|await\s+', content):
                features["modern_features"].append("async_await")
            if re.search(r'`[^`]*\$\{[^}]+\}[^`]*`', content):
                features["modern_features"].append("template_literals")
        
        elif language == "TypeScript":
            if re.search(r':\s*\w+(\[\])?(\s*\|\s*\w+)*', content):
                features["modern_features"].append("type_annotations")
            if re.search(r'interface\s+\w+', content):
                features["modern_features"].append("interfaces")
            if re.search(r'<[^>]+>', content):
                features["modern_features"].append("generics")
        
        elif language == "Java":
            if re.search(r'@\w+', content):
                features["modern_features"].append("annotations")
            if re.search(r'->', content):
                features["modern_features"].append("lambda_expressions")
            if re.search(r'\.stream\(\)', content):
                features["modern_features"].append("streams")
        
        elif language == "C#":
            if re.search(r'{\s*get\s*;\s*set\s*;}', content):
                features["modern_features"].append("properties")
            if re.search(r'\.Where\(|\.Select\(|\.OrderBy\(', content):
                features["modern_features"].append("linq")
            if re.search(r'async\s+\w+|await\s+', content):
                features["modern_features"].append("async_await")
        
        elif language == "Go":
            if re.search(r'go\s+\w+\(', content):
                features["modern_features"].append("goroutines")
            if re.search(r'chan\s+\w+|<-\s*chan|chan\s*<-', content):
                features["modern_features"].append("channels")
            if re.search(r'defer\s+', content):
                features["modern_features"].append("defer")
        
        elif language == "Rust":
            if re.search(r'match\s+\w+', content):
                features["modern_features"].append("pattern_matching")
            if re.search(r"'[a-zA-Z]\w*", content):
                features["modern_features"].append("lifetimes")
            if re.search(r'trait\s+\w+', content):
                features["modern_features"].append("traits")
        
        # Framework detection
        for framework, patterns in self.framework_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    features["framework_usage"].append(framework)
                    break
        
        return features
    
    def _calculate_maintainability_index_generic(self, complexity_analysis: Dict[str, Any], content: str) -> float:
        """Calculate maintainability index for generic languages"""
        
        # Simplified maintainability index calculation
        cyclomatic_complexity = complexity_analysis["cyclomatic_complexity"]
        lines_of_code = len([line for line in content.split('\n') if line.strip()])
        
        # Comment ratio
        comment_lines = 0
        for line in content.split('\n'):
            if re.search(r'//|#|/\*|\*/', line.strip()):
                comment_lines += 1
        
        comment_ratio = comment_lines / max(lines_of_code, 1)
        
        # Simplified maintainability index
        mi = 100 - (cyclomatic_complexity * 2) - (lines_of_code * 0.01) + (comment_ratio * 20)
        
        return max(0, min(100, mi))
    
    def _calculate_code_quality_score(self, complexity_analysis: Dict[str, Any]) -> float:
        """Calculate overall code quality score"""
        
        score = 100.0
        
        # Penalize high complexity
        cc = complexity_analysis.get("cyclomatic_complexity", 0)
        if cc > 20:
            score -= 30
        elif cc > 10:
            score -= 15
        elif cc > 5:
            score -= 5
        
        # Penalize deep nesting
        nesting = complexity_analysis.get("nesting_depth", 0)
        if nesting > 5:
            score -= 20
        elif nesting > 3:
            score -= 10
        
        # Penalize code smells
        code_smells = complexity_analysis.get("code_smells", {})
        total_smells = sum(code_smells.values())
        score -= min(total_smells * 2, 25)
        
        # Reward good maintainability
        mi = complexity_analysis.get("maintainability_index", 50)
        if mi > 80:
            score += 10
        elif mi < 40:
            score -= 15
        
        return max(0, min(100, score))   
 
    def _analyze_line_types(self, content: str, language: str) -> Tuple[int, int, int]:
        """Analyze code lines, comment lines, and blank lines"""
        lines = content.split('\n')
        code_lines = 0
        comment_lines = 0
        blank_lines = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                blank_lines += 1
            elif self._is_comment_line(stripped, language):
                comment_lines += 1
            else:
                code_lines += 1
                
        return code_lines, comment_lines, blank_lines
    
    def _is_comment_line(self, line: str, language: str) -> bool:
        """Check if a line is a comment"""
        comment_patterns = {
            'Python': [r'^\s*#', r'^\s*"""', r'^\s*\'\'\''],
            'JavaScript': [r'^\s*//', r'^\s*/\*'],
            'TypeScript': [r'^\s*//', r'^\s*/\*'],
            'Java': [r'^\s*//', r'^\s*/\*'],
            'C++': [r'^\s*//', r'^\s*/\*'],
            'C#': [r'^\s*//', r'^\s*/\*'],
            'Go': [r'^\s*//', r'^\s*/\*'],
            'Rust': [r'^\s*//', r'^\s*/\*'],
            'Ruby': [r'^\s*#'],
            'PHP': [r'^\s*//', r'^\s*#', r'^\s*/\*'],
            'Swift': [r'^\s*//', r'^\s*/\*'],
            'Kotlin': [r'^\s*//', r'^\s*/\*']
        }
        
        patterns = comment_patterns.get(language, [r'^\s*//', r'^\s*#'])
        return any(re.match(pattern, line) for pattern in patterns)
    
    def _get_file_type(self, filename: str) -> str:
        """Determine file type from filename"""
        if '.' not in filename:
            return 'no_extension'
            
        extension = filename.split('.')[-1].lower()
        
        type_mapping = {
            'py': 'source', 'js': 'source', 'ts': 'source', 'java': 'source',
            'cpp': 'source', 'c': 'source', 'h': 'source', 'cs': 'source',
            'go': 'source', 'rs': 'source', 'rb': 'source', 'php': 'source',
            'swift': 'source', 'kt': 'source',
            'json': 'config', 'yaml': 'config', 'yml': 'config', 'toml': 'config',
            'ini': 'config', 'cfg': 'config', 'xml': 'config',
            'md': 'documentation', 'txt': 'documentation', 'rst': 'documentation',
            'html': 'markup', 'css': 'style', 'scss': 'style', 'sass': 'style',
            'sql': 'database', 'sh': 'script', 'bat': 'script', 'ps1': 'script'
        }
        
        return type_mapping.get(extension, 'other')
    
    def _count_code_structures(self, content: str, language: str) -> Tuple[int, int]:
        """Count functions and classes in code"""
        function_count = 0
        class_count = 0
        
        # Language-specific patterns
        if language == 'Python':
            function_count = len(re.findall(r'^\s*def\s+\w+\s*\(', content, re.MULTILINE))
            class_count = len(re.findall(r'^\s*class\s+\w+', content, re.MULTILINE))
        elif language in ['JavaScript', 'TypeScript']:
            function_count = len(re.findall(r'function\s+\w+\s*\(|=>\s*{|\w+\s*:\s*function', content))
            class_count = len(re.findall(r'class\s+\w+', content))
        elif language == 'Java':
            function_count = len(re.findall(r'(public|private|protected)\s+\w+\s+\w+\s*\(', content))
            class_count = len(re.findall(r'(public\s+)?class\s+\w+', content))
        elif language in ['C++', 'C#']:
            function_count = len(re.findall(r'\w+\s+\w+\s*\([^)]*\)\s*{', content))
            class_count = len(re.findall(r'class\s+\w+', content))
        elif language == 'Go':
            function_count = len(re.findall(r'func\s+\w+\s*\(', content))
            class_count = len(re.findall(r'type\s+\w+\s+struct', content))
        elif language == 'Rust':
            function_count = len(re.findall(r'fn\s+\w+\s*\(', content))
            class_count = len(re.findall(r'struct\s+\w+|enum\s+\w+', content))
        
        return function_count, class_count
    
    def _analyze_code_complexity(self, content: str, language: str) -> float:
        """Calculate cyclomatic complexity estimate"""
        complexity = 1  # Base complexity
        
        # Count decision points
        decision_keywords = [
            'if', 'else', 'elif', 'while', 'for', 'switch', 'case',
            'try', 'catch', 'except', 'finally', 'and', 'or', '&&', '||'
        ]
        
        for keyword in decision_keywords:
            complexity += len(re.findall(rf'\b{keyword}\b', content, re.IGNORECASE))
        
        # Normalize by lines of code
        lines = len([line for line in content.split('\n') if line.strip()])
        if lines > 0:
            complexity = complexity / lines * 100  # Complexity per 100 lines
        
        return min(complexity, 100)  # Cap at 100
    
    def _is_test_file(self, filename: str, filepath: str) -> bool:
        """Check if file is a test file"""
        test_indicators = [
            'test', 'spec', '__test__', '.test.', '.spec.',
            'tests/', 'test/', '__tests__/', 'spec/'
        ]
        
        filename_lower = filename.lower()
        filepath_lower = filepath.lower()
        
        return any(indicator in filename_lower or indicator in filepath_lower 
                  for indicator in test_indicators)
    
    def _is_config_file(self, filename: str) -> bool:
        """Check if file is a configuration file"""
        config_files = [
            'package.json', 'requirements.txt', 'pom.xml', 'build.gradle',
            'Cargo.toml', 'composer.json', 'Gemfile', 'setup.py',
            'tsconfig.json', 'webpack.config.js', 'babel.config.js',
            '.gitignore', '.dockerignore', 'Dockerfile', 'docker-compose.yml'
        ]
        
        config_extensions = ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf']
        
        return (filename in config_files or 
                any(filename.endswith(ext) for ext in config_extensions))
    
    def _calculate_documentation_coverage(self, analysis: Dict[str, Any]) -> float:
        """Calculate documentation coverage score"""
        total_files = analysis["total_files"]
        if total_files == 0:
            return 0.0
        
        # Base score from comment ratio
        comment_score = min(analysis["comment_ratio"] * 100, 40)
        
        # Bonus for documentation files
        doc_files = analysis["file_type_breakdown"].get("documentation", 0)
        doc_bonus = min(doc_files / total_files * 30, 30)
        
        # Bonus for config files (shows project setup)
        config_bonus = min(analysis["config_file_count"] / total_files * 20, 20)
        
        # Penalty for no README or documentation
        if doc_files == 0:
            comment_score *= 0.7
        
        return min(comment_score + doc_bonus + config_bonus, 100)
    
    def _analyze_commit_patterns(self, commit_history: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze commit patterns for development practices"""
        
        commits = commit_history.get("commits", [])
        statistics_data = commit_history.get("statistics", {})
        
        if not commits:
            return {
                "commit_frequency": 0,
                "average_commit_size": 0,
                "commit_message_quality": 0,
                "contributor_diversity": 0,
                "development_consistency": 0,
                "recent_activity": 0
            }
        
        # Analyze commit messages
        message_quality = self._analyze_commit_message_quality(commits)
        
        # Calculate commit frequency and consistency
        frequency_analysis = self._analyze_commit_frequency(commits)
        
        # Analyze contributor patterns
        contributor_analysis = self._analyze_contributors(commits)
        
        # Analyze commit sizes
        size_analysis = self._analyze_commit_sizes(commits)
        
        return {
            "commit_frequency": frequency_analysis["frequency_score"],
            "average_commit_size": size_analysis["average_size"],
            "commit_message_quality": message_quality,
            "contributor_diversity": contributor_analysis["diversity_score"],
            "development_consistency": frequency_analysis["consistency_score"],
            "recent_activity": frequency_analysis["recent_activity_score"],
            "total_commits": len(commits),
            "unique_contributors": contributor_analysis["unique_count"]
        }
    
    def _analyze_commit_message_quality(self, commits: List[Dict[str, Any]]) -> float:
        """Analyze quality of commit messages"""
        if not commits:
            return 0.0
        
        quality_score = 0
        total_commits = len(commits)
        
        for commit in commits:
            message = commit.get("message", "")
            if not message:
                continue
            
            score = 0
            
            # Length check (good messages are descriptive)
            if len(message) > 10:
                score += 20
            if len(message) > 50:
                score += 20
            
            # Check for conventional commit format
            if re.match(r'^(feat|fix|docs|style|refactor|test|chore)(\(.+\))?: .+', message):
                score += 30
            
            # Check for issue references
            if re.search(r'#\d+|fixes|closes|resolves', message, re.IGNORECASE):
                score += 15
            
            # Avoid generic messages
            generic_messages = ['update', 'fix', 'changes', 'wip', 'temp']
            if not any(generic in message.lower() for generic in generic_messages):
                score += 15
            
            quality_score += min(score, 100)
        
        return quality_score / total_commits if total_commits > 0 else 0
    
    def _analyze_commit_frequency(self, commits: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze commit frequency patterns"""
        if not commits:
            return {"frequency_score": 0, "consistency_score": 0, "recent_activity_score": 0}
        
        # Group commits by date
        commit_dates = []
        for commit in commits:
            date_str = commit.get("date")
            if date_str:
                try:
                    commit_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    commit_dates.append(commit_date)
                except:
                    continue
        
        if not commit_dates:
            return {"frequency_score": 0, "consistency_score": 0, "recent_activity_score": 0}
        
        commit_dates.sort()
        
        # Calculate frequency score
        total_days = (commit_dates[-1] - commit_dates[0]).days + 1
        frequency_score = min((len(commits) / max(total_days, 1)) * 100, 100)
        
        # Calculate consistency (standard deviation of intervals)
        if len(commit_dates) > 1:
            intervals = [(commit_dates[i] - commit_dates[i-1]).days 
                        for i in range(1, len(commit_dates))]
            if intervals:
                consistency_score = max(0, 100 - statistics.stdev(intervals) * 2)
            else:
                consistency_score = 50
        else:
            consistency_score = 0
        
        # Recent activity (commits in last 30 days)
        recent_cutoff = datetime.now() - timedelta(days=30)
        recent_commits = [d for d in commit_dates if d.replace(tzinfo=None) > recent_cutoff]
        recent_activity_score = min(len(recent_commits) * 10, 100)
        
        return {
            "frequency_score": frequency_score,
            "consistency_score": consistency_score,
            "recent_activity_score": recent_activity_score
        }
    
    def _analyze_contributors(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze contributor diversity"""
        contributors = set()
        
        for commit in commits:
            author = commit.get("author")
            if author:
                contributors.add(author)
        
        unique_count = len(contributors)
        
        # Diversity score based on number of contributors
        if unique_count == 1:
            diversity_score = 30  # Solo project
        elif unique_count <= 3:
            diversity_score = 60  # Small team
        elif unique_count <= 10:
            diversity_score = 85  # Medium team
        else:
            diversity_score = 100  # Large team
        
        return {
            "unique_count": unique_count,
            "diversity_score": diversity_score
        }
    
    def _analyze_commit_sizes(self, commits: List[Dict[str, Any]]) -> Dict[str, float]:
        """Analyze commit size patterns"""
        sizes = []
        
        for commit in commits:
            additions = commit.get("additions", 0)
            deletions = commit.get("deletions", 0)
            total_changes = additions + deletions
            sizes.append(total_changes)
        
        if not sizes:
            return {"average_size": 0, "size_consistency": 0}
        
        average_size = statistics.mean(sizes)
        
        # Consistency score (prefer moderate, consistent commit sizes)
        if len(sizes) > 1:
            size_stdev = statistics.stdev(sizes)
            # Penalize very large standard deviations
            size_consistency = max(0, 100 - (size_stdev / max(average_size, 1)) * 50)
        else:
            size_consistency = 50
        
        return {
            "average_size": average_size,
            "size_consistency": size_consistency
        }
    
    def _analyze_security_vulnerabilities(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze code for potential security vulnerabilities"""
        
        vulnerabilities = {
            "sql_injection": 0,
            "xss": 0,
            "hardcoded_secrets": 0,
            "unsafe_functions": 0,
            "total_issues": 0,
            "security_score": 100,
            "files_with_issues": set(),
            "detailed_findings": []
        }
        
        for file_info in contents:
            content = file_info.get("content", "")
            filename = file_info.get("name", "")
            
            if not content:
                continue
            
            file_issues = 0
            
            # Check each vulnerability category
            for vuln_type, patterns in self.security_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        vulnerabilities[vuln_type] += len(matches)
                        vulnerabilities["files_with_issues"].add(filename)
                        file_issues += len(matches)
                        
                        # Add detailed findings
                        for match in matches:
                            vulnerabilities["detailed_findings"].append({
                                "file": filename,
                                "type": vuln_type,
                                "pattern": pattern,
                                "match": match[:100]  # Truncate long matches
                            })
        
        # Calculate total issues and security score
        vulnerabilities["total_issues"] = sum([
            vulnerabilities["sql_injection"],
            vulnerabilities["xss"],
            vulnerabilities["hardcoded_secrets"],
            vulnerabilities["unsafe_functions"]
        ])
        
        # Security score (100 - penalty for issues)
        total_files = len(contents)
        if total_files > 0:
            issue_ratio = vulnerabilities["total_issues"] / total_files
            vulnerabilities["security_score"] = max(0, 100 - (issue_ratio * 50))
        
        # Convert set to list for JSON serialization
        vulnerabilities["files_with_issues"] = list(vulnerabilities["files_with_issues"])
        
        return vulnerabilities
    
    def _calculate_comprehensive_acid_scores(self, repo_data: Dict[str, Any], repo_stats: Dict[str, Any], 
                                      code_analysis: Dict[str, Any], commit_analysis: Dict[str, Any],
                                      security_analysis: Dict[str, Any], complexity_analysis: Dict[str, Any] = None) -> Dict[str, float]:
        """
        Calculate comprehensive ACID scores based on detailed code analysis
        
        ACID Principles for Code Quality:
        - Atomicity: Code modularity, single responsibility, clear boundaries
        - Consistency: Code standards, formatting, naming conventions  
        - Isolation: Dependencies management, architecture separation
        - Durability: Testing, documentation, maintainability
        """
        
        if complexity_analysis is None:
            complexity_analysis = {}
        
        # ==================== ATOMICITY: Modularity and Single Responsibility ====================
        atomicity_score = 0.0
        atomicity_penalties = {}
        weights = self.acid_criteria['atomicity']
        
        # 1. Modularity Assessment (30% weight) - STRICT THRESHOLDS
        modularity_score = 0.0
        
        # Function density (functions per 1000 lines of code) - STRICTER
        total_lines = max(code_analysis.get("code_lines", 1), 1)
        function_count = code_analysis.get("function_count", 0)
        function_density = (function_count / total_lines) * 1000
        
        # Apply strict thresholds from quality_thresholds
        optimal_min = self.quality_thresholds['function_density']['optimal_min']
        optimal_max = self.quality_thresholds['function_density']['optimal_max']
        minimum = self.quality_thresholds['function_density']['minimum']
        excessive = self.quality_thresholds['function_density']['excessive']
        
        if optimal_min <= function_density <= optimal_max:  # Optimal range (5-15)
            modularity_score += 30
        elif minimum <= function_density < optimal_min or optimal_max < function_density <= excessive:  # Acceptable
            modularity_score += 15
        elif function_density > excessive:  # Excessive functions - PENALTY
            modularity_score += 5
            penalty = (function_density - excessive) * 0.5
            atomicity_penalties['excessive_functions'] = min(penalty, 10)
            logger.warning(f"Excessive function density: {function_density:.1f} (threshold: {excessive})")
        elif function_density > 0:  # Some functions
            modularity_score += 10
        
        # Class organization - STRICTER
        class_count = code_analysis.get("class_count", 0)
        if class_count > 0:
            class_density = (class_count / total_lines) * 1000
            if 1 <= class_density <= 5:  # Good class organization
                modularity_score += 20
            elif class_density > 5:  # Too many classes - PENALTY
                modularity_score += 5
                penalty = (class_density - 5) * 0.3
                atomicity_penalties['excessive_classes'] = min(penalty, 5)
            elif class_density > 0:
                modularity_score += 10
        
        # File organization - STRICTER
        file_count = code_analysis.get("total_files", 1)
        if 3 <= file_count <= 50:  # Well-organized projects
            modularity_score += 25
        elif 51 <= file_count <= 200:  # Large but manageable
            modularity_score += 15
        elif file_count > 200:  # Too many files - PENALTY
            modularity_score += 5
            penalty = (file_count - 200) * 0.02
            atomicity_penalties['excessive_files'] = min(penalty, 10)
        elif file_count > 0:
            modularity_score += 5
        
        # Framework usage indicates good architecture
        framework_usage = code_analysis.get("framework_usage", {})
        if len(framework_usage) > 0:
            modularity_score += 15
        
        modularity_score = min(modularity_score, 100)
        atomicity_score += modularity_score * weights['modularity_weight']
        
        # 2. Single Responsibility Assessment (25% weight) - STRICT THRESHOLDS
        single_responsibility_score = 0.0
        
        # Function complexity analysis - STRICTER with PENALTIES
        if complexity_analysis.get("function_complexity"):
            func_complexities = [f.get("cyclomatic_complexity", 1) for f in complexity_analysis["function_complexity"]]
            if func_complexities:
                avg_func_complexity = statistics.mean(func_complexities)
                excellent_threshold = self.complexity_thresholds['cyclomatic']['excellent']
                good_threshold = self.complexity_thresholds['cyclomatic']['good']
                acceptable_threshold = self.complexity_thresholds['cyclomatic']['acceptable']
                poor_threshold = self.complexity_thresholds['cyclomatic']['poor']
                
                if avg_func_complexity <= excellent_threshold:  # Excellent (<=5)
                    single_responsibility_score += 40
                elif avg_func_complexity <= good_threshold:  # Good (<=8)
                    single_responsibility_score += 30
                elif avg_func_complexity <= acceptable_threshold:  # Acceptable (<=12)
                    single_responsibility_score += 20
                elif avg_func_complexity <= poor_threshold:  # Poor (<=20)
                    single_responsibility_score += 10
                    penalty = (avg_func_complexity - acceptable_threshold) * 0.5
                    atomicity_penalties['high_function_complexity'] = min(penalty, 5)
                else:  # Critical - SEVERE PENALTY
                    single_responsibility_score += 5
                    penalty = (avg_func_complexity - acceptable_threshold) * 1.0
                    atomicity_penalties['critical_function_complexity'] = min(penalty, 15)
                    logger.warning(f"Critical function complexity: {avg_func_complexity:.1f}")
        
        # Class complexity analysis - STRICTER with PENALTIES
        if complexity_analysis.get("class_complexity"):
            class_complexities = [c.get("method_count", 0) for c in complexity_analysis["class_complexity"]]
            if class_complexities:
                avg_class_methods = statistics.mean(class_complexities)
                excellent_threshold = self.quality_thresholds['class_size']['excellent']
                good_threshold = self.quality_thresholds['class_size']['good']
                acceptable_threshold = self.quality_thresholds['class_size']['acceptable']
                
                if avg_class_methods <= excellent_threshold:  # Excellent (<=10)
                    single_responsibility_score += 30
                elif avg_class_methods <= good_threshold:  # Good (<=15)
                    single_responsibility_score += 20
                elif avg_class_methods <= acceptable_threshold:  # Acceptable (<=25)
                    single_responsibility_score += 10
                else:  # Poor - PENALTY
                    single_responsibility_score += 5
                    penalty = (avg_class_methods - acceptable_threshold) * 0.3
                    atomicity_penalties['large_classes'] = min(penalty, 10)
                    logger.warning(f"Large classes detected: avg {avg_class_methods:.1f} methods")
        
        # Language diversity (moderate is good for SRP)
        lang_count = len(code_analysis.get("language_breakdown", {}))
        if 1 <= lang_count <= 3:  # Focused technology stack
            single_responsibility_score += 30
        elif lang_count <= 5:
            single_responsibility_score += 15
        
        single_responsibility_score = min(single_responsibility_score, 100)
        atomicity_score += single_responsibility_score * weights['single_responsibility_weight']
        
        # 3. Function Size Assessment (20% weight) - STRICT THRESHOLDS
        function_size_score = 0.0
        
        if complexity_analysis.get("function_complexity"):
            func_sizes = [f.get("lines_of_code", 0) for f in complexity_analysis["function_complexity"]]
            if func_sizes:
                avg_func_size = statistics.mean(func_sizes)
                excellent_threshold = self.quality_thresholds['function_size']['excellent']
                good_threshold = self.quality_thresholds['function_size']['good']
                acceptable_threshold = self.quality_thresholds['function_size']['acceptable']
                poor_threshold = self.quality_thresholds['function_size']['poor']
                
                if avg_func_size <= excellent_threshold:  # Excellent (<=15)
                    function_size_score += 50
                elif avg_func_size <= good_threshold:  # Good (<=30)
                    function_size_score += 35
                elif avg_func_size <= acceptable_threshold:  # Acceptable (<=50)
                    function_size_score += 20
                elif avg_func_size <= poor_threshold:  # Poor (<=100)
                    function_size_score += 10
                    penalty = (avg_func_size - acceptable_threshold) * 0.1
                    atomicity_penalties['large_functions'] = min(penalty, 5)
                else:  # Critical - SEVERE PENALTY
                    function_size_score += 5
                    penalty = (avg_func_size - acceptable_threshold) * 0.2
                    atomicity_penalties['very_large_functions'] = min(penalty, 15)
                    logger.warning(f"Very large functions detected: avg {avg_func_size:.1f} lines")
                
                # Reward consistent function sizes
                if len(func_sizes) > 1:
                    func_size_std = statistics.stdev(func_sizes)
                    if func_size_std <= 10:  # Consistent sizes
                        function_size_score += 25
                    elif func_size_std <= 25:
                        function_size_score += 15
        
        # Comment ratio indicates well-documented functions - STRICTER
        comment_ratio = code_analysis.get("comment_ratio", 0)
        optimal_min = self.quality_thresholds['comment_ratio']['optimal_min']
        optimal_max = self.quality_thresholds['comment_ratio']['optimal_max']
        minimum = self.quality_thresholds['comment_ratio']['minimum']
        
        if optimal_min <= comment_ratio <= optimal_max:  # Optimal (0.15-0.30)
            function_size_score += 25
        elif comment_ratio >= minimum:  # Minimum (>=0.10)
            function_size_score += 15
        elif comment_ratio > 0:
            function_size_score += 5
        
        function_size_score = min(function_size_score, 100)
        atomicity_score += function_size_score * weights['function_size_weight']
        
        # 4. Class Cohesion Assessment (25% weight) - STRICT THRESHOLDS
        class_cohesion_score = 0.0
        
        if complexity_analysis.get("class_complexity"):
            # Analyze class cohesion based on method distribution - STRICTER
            large_class_count = 0
            for class_info in complexity_analysis["class_complexity"]:
                method_count = class_info.get("method_count", 0)
                excellent_threshold = self.quality_thresholds['class_size']['excellent']
                good_threshold = self.quality_thresholds['class_size']['good']
                acceptable_threshold = self.quality_thresholds['class_size']['acceptable']
                poor_threshold = self.quality_thresholds['class_size']['poor']
                
                if 3 <= method_count <= excellent_threshold:  # Excellent (3-10)
                    class_cohesion_score += 20
                elif method_count <= good_threshold:  # Good (<=15)
                    class_cohesion_score += 15
                elif method_count <= acceptable_threshold:  # Acceptable (<=25)
                    class_cohesion_score += 10
                elif method_count <= poor_threshold:  # Poor (<=50)
                    class_cohesion_score += 5
                    large_class_count += 1
                elif method_count > 0:
                    class_cohesion_score += 2
                    large_class_count += 1
            
            # Apply penalty for large classes
            if large_class_count > 0:
                penalty = large_class_count * 2.0
                atomicity_penalties['large_class_count'] = min(penalty, 10)
                logger.warning(f"Large classes detected: {large_class_count} classes exceed thresholds")
        
        # Test file organization indicates good separation
        test_files = code_analysis.get("test_file_count", 0)
        if test_files > 0:
            class_cohesion_score += 30
        
        # Configuration separation
        config_files = code_analysis.get("config_file_count", 0)
        if config_files > 0:
            class_cohesion_score += 20
        
        # File type diversity indicates good separation of concerns
        file_types = len(code_analysis.get("file_type_breakdown", {}))
        if file_types >= 3:
            class_cohesion_score += 30
        
        class_cohesion_score = min(class_cohesion_score, 100)
        atomicity_score += class_cohesion_score * weights['class_cohesion_weight']
        
        # Apply atomicity penalties
        total_atomicity_penalty = sum(atomicity_penalties.values())
        atomicity_score = max(0, atomicity_score - total_atomicity_penalty)
        
        # ==================== CONSISTENCY: Standards and Conventions ====================
        consistency_score = 0.0
        consistency_penalties = {}
        weights = self.acid_criteria['consistency']
        
        # 1. Naming Conventions (25% weight)
        naming_score = 0.0
        
        # Analyze naming patterns from complexity analysis
        if complexity_analysis.get("language_specific_metrics"):
            lang_metrics = complexity_analysis["language_specific_metrics"]
            if "naming_conventions" in lang_metrics:
                naming_consistency = lang_metrics["naming_conventions"].get("consistency_score", 0)
                naming_score += naming_consistency * 0.5
        
        # Function and class naming consistency
        if complexity_analysis.get("function_complexity"):
            func_names = [f.get("name", "") for f in complexity_analysis["function_complexity"]]
            naming_score += self._analyze_naming_consistency(func_names) * 0.3
        
        if complexity_analysis.get("class_complexity"):
            class_names = [c.get("name", "") for c in complexity_analysis["class_complexity"]]
            naming_score += self._analyze_naming_consistency(class_names) * 0.2
        
        naming_score = min(naming_score, 100)
        consistency_score += naming_score * weights['naming_conventions_weight']
        
        # 2. Code Style (25% weight) - STRICT REQUIREMENTS
        code_style_score = 0.0
        
        # Comment consistency - STRICTER (minimum 10% required)
        comment_ratio = code_analysis.get("comment_ratio", 0)
        minimum_comment = self.quality_thresholds['comment_ratio']['minimum']
        optimal_min = self.quality_thresholds['comment_ratio']['optimal_min']
        optimal_max = self.quality_thresholds['comment_ratio']['optimal_max']
        
        if optimal_min <= comment_ratio <= optimal_max:  # Optimal (0.15-0.30)
            code_style_score += 40
        elif comment_ratio >= minimum_comment:  # Meets minimum (>=0.10)
            code_style_score += 25
        elif comment_ratio >= 0.05:
            code_style_score += 10
            # Penalty for insufficient comments
            penalty = (minimum_comment - comment_ratio) * 20
            consistency_penalties['low_comment_ratio'] = min(penalty, 5)
            logger.warning(f"Low comment ratio: {comment_ratio:.2%} (minimum: {minimum_comment:.2%})")
        
        # Code complexity consistency
        if complexity_analysis.get("cyclomatic_complexity", 0) <= 15:  # Manageable complexity
            code_style_score += 30
        elif complexity_analysis.get("cyclomatic_complexity", 0) <= 25:
            code_style_score += 15
        
        # Modern language features usage
        if complexity_analysis.get("language_specific_metrics"):
            modern_features = complexity_analysis["language_specific_metrics"].get("modern_features", [])
            if len(modern_features) >= 3:  # Uses modern practices
                code_style_score += 30
            elif len(modern_features) > 0:
                code_style_score += 15
        
        code_style_score = min(code_style_score, 100)
        consistency_score += code_style_score * weights['code_style_weight']
        
        # 3. Documentation (25% weight) - STRICT REQUIREMENTS
        documentation_score = 0.0
        
        # Repository documentation - REQUIRED
        has_readme = repo_stats.get("has_readme", False)
        if has_readme:
            documentation_score += 25
        else:
            # Severe penalty for missing README
            penalty = self.penalty_multipliers['missing_essentials']['no_readme']
            consistency_penalties['no_readme'] = penalty
            logger.warning("Missing README - applying penalty")
        
        if repo_data.get("description") and len(repo_data["description"]) > 50:
            documentation_score += 20
        
        # Code documentation - STRICTER (minimum 10% required)
        doc_coverage = code_analysis.get("documentation_coverage", 0)
        minimum_doc = self.quality_thresholds['comment_ratio']['minimum']
        
        if doc_coverage >= minimum_doc:  # Meets minimum (>=0.10)
            documentation_score += doc_coverage * 0.35
        else:
            # Penalty for insufficient documentation
            documentation_score += doc_coverage * 0.15
            penalty = self.penalty_multipliers['missing_essentials']['no_documentation'] * 0.5
            consistency_penalties['insufficient_documentation'] = penalty
            logger.warning(f"Insufficient documentation: {doc_coverage:.2%} (minimum: {minimum_doc:.2%})")
        
        # Topics and metadata
        topics_count = len(repo_data.get("topics", []))
        if topics_count >= 3:
            documentation_score += 20
        elif topics_count > 0:
            documentation_score += 10
        
        documentation_score = min(documentation_score, 100)
        consistency_score += documentation_score * weights['documentation_weight']
        
        # 4. Commit Patterns (25% weight)
        commit_patterns_score = 0.0
        
        # Commit message quality
        commit_msg_quality = commit_analysis.get("commit_message_quality", 0)
        commit_patterns_score += commit_msg_quality * 0.4
        
        # Development consistency
        dev_consistency = commit_analysis.get("development_consistency", 0)
        commit_patterns_score += dev_consistency * 0.3
        
        # Recent activity
        recent_activity = commit_analysis.get("recent_activity", 0)
        commit_patterns_score += recent_activity * 0.3
        
        commit_patterns_score = min(commit_patterns_score, 100)
        consistency_score += commit_patterns_score * weights['commit_patterns_weight']
        
        # Apply consistency penalties
        total_consistency_penalty = sum(consistency_penalties.values())
        consistency_score = max(0, consistency_score - total_consistency_penalty)
        
        # ==================== ISOLATION: Architecture and Dependencies ====================
        isolation_score = 0.0
        isolation_penalties = {}
        weights = self.acid_criteria['isolation']
        
        # 1. Dependency Management (30% weight) - STRICT REQUIREMENTS
        dependency_score = 0.0
        
        # Configuration files indicate proper dependency management
        config_files = code_analysis.get("config_file_count", 0)
        if config_files > 0:
            dependency_score += 40
        
        # Language diversity management
        lang_count = len(code_analysis.get("language_breakdown", {}))
        if 1 <= lang_count <= 3:  # Focused stack
            dependency_score += 30
        elif lang_count <= 5:
            dependency_score += 15
        
        # Framework usage indicates structured dependencies
        framework_count = len(code_analysis.get("framework_usage", {}))
        if 1 <= framework_count <= 3:  # Reasonable framework usage
            dependency_score += 30
        elif framework_count > 0:
            dependency_score += 15
        
        # CI/CD presence - REQUIRED for good dependency management
        has_ci_cd = repo_stats.get("has_ci", False)
        if not has_ci_cd:
            penalty = self.penalty_multipliers['missing_essentials']['no_ci_cd'] * 0.5
            isolation_penalties['no_ci_cd'] = penalty
            logger.warning("Missing CI/CD configuration - applying penalty")
        
        dependency_score = min(dependency_score, 100)
        isolation_score += dependency_score * weights['dependency_management_weight']
        
        # 2. Architecture Separation (30% weight)
        architecture_score = 0.0
        
        # File type separation
        file_types = code_analysis.get("file_type_breakdown", {})
        source_files = file_types.get("source", 0)
        config_files = file_types.get("config", 0)
        doc_files = file_types.get("documentation", 0)
        
        if source_files > 0 and config_files > 0:
            architecture_score += 30
        if doc_files > 0:
            architecture_score += 20
        
        # Test separation
        test_files = code_analysis.get("test_file_count", 0)
        total_files = code_analysis.get("total_files", 1)
        test_ratio = test_files / total_files
        
        if 0.1 <= test_ratio <= 0.4:  # Good test isolation
            architecture_score += 30
        elif test_ratio > 0:
            architecture_score += 15
        
        # Complexity distribution indicates good separation
        if complexity_analysis.get("nesting_depth", 0) <= 4:  # Not deeply nested
            architecture_score += 20
        
        architecture_score = min(architecture_score, 100)
        isolation_score += architecture_score * weights['architecture_separation_weight']
        
        # 3. Coupling Assessment (20% weight) - STRICT THRESHOLDS
        coupling_score = 0.0
        
        # Low complexity indicates low coupling - STRICTER
        avg_complexity = complexity_analysis.get("cyclomatic_complexity", 0)
        good_threshold = self.complexity_thresholds['cyclomatic']['good']
        acceptable_threshold = self.complexity_thresholds['cyclomatic']['acceptable']
        poor_threshold = self.complexity_thresholds['cyclomatic']['poor']
        
        if avg_complexity <= good_threshold:  # <=8
            coupling_score += 40
        elif avg_complexity <= acceptable_threshold:  # <=12
            coupling_score += 25
        elif avg_complexity <= poor_threshold:  # <=20
            coupling_score += 10
        
        # Function parameter analysis - STRICTER with PENALTIES
        if complexity_analysis.get("function_complexity"):
            param_counts = []
            excessive_param_count = 0
            for func in complexity_analysis["function_complexity"]:
                if "parameter_count" in func:
                    param_count = func["parameter_count"]
                    param_counts.append(param_count)
                    # Track functions with excessive parameters
                    if param_count > self.quality_thresholds['parameters']['acceptable']:
                        excessive_param_count += 1
            
            if param_counts:
                avg_params = statistics.mean(param_counts)
                excellent_threshold = self.quality_thresholds['parameters']['excellent']
                good_threshold = self.quality_thresholds['parameters']['good']
                acceptable_threshold = self.quality_thresholds['parameters']['acceptable']
                
                if avg_params <= excellent_threshold:  # <=3
                    coupling_score += 30
                elif avg_params <= good_threshold:  # <=5
                    coupling_score += 20
                elif avg_params <= acceptable_threshold:  # <=7
                    coupling_score += 10
                else:  # Poor - PENALTY
                    coupling_score += 5
                    penalty = (avg_params - acceptable_threshold) * 2.0
                    isolation_penalties['excessive_parameters'] = min(penalty, 10)
                    logger.warning(f"Excessive parameters: avg {avg_params:.1f} (threshold: {acceptable_threshold})")
                
                # Additional penalty for multiple functions with excessive parameters
                if excessive_param_count > 0:
                    penalty = excessive_param_count * 0.5
                    isolation_penalties['excessive_param_functions'] = min(penalty, 5)
        
        # Import/dependency analysis
        total_lines = max(code_analysis.get("code_lines", 1), 1)
        if total_lines < 5000:  # Smaller codebases have lower coupling risk
            coupling_score += 30
        elif total_lines < 20000:
            coupling_score += 15
        
        coupling_score = min(coupling_score, 100)
        isolation_score += coupling_score * weights['coupling_weight']
        
        # 4. Security (20% weight)
        security_score = security_analysis.get("security_score", 100)
        isolation_score += security_score * weights['security_weight']
        
        # Apply isolation penalties
        total_isolation_penalty = sum(isolation_penalties.values())
        isolation_score = max(0, isolation_score - total_isolation_penalty)
        
        # ==================== DURABILITY: Long-term Maintainability ====================
        durability_score = 0.0
        durability_penalties = {}
        weights = self.acid_criteria['durability']
        
        # 1. Test Coverage (30% weight) - STRICT REQUIREMENTS
        test_coverage_score = 0.0
        
        # Test file presence and ratio - STRICTER with SEVERE PENALTIES
        test_files = code_analysis.get("test_file_count", 0)
        total_files = code_analysis.get("total_files", 1)
        
        if test_files > 0:
            test_ratio = test_files / total_files
            excellent_threshold = self.quality_thresholds['test_coverage']['excellent']
            good_threshold = self.quality_thresholds['test_coverage']['good']
            minimum_threshold = self.quality_thresholds['test_coverage']['minimum']
            required_threshold = self.quality_thresholds['test_coverage']['required']
            
            if test_ratio >= excellent_threshold:  # Excellent (>=0.30)
                test_coverage_score += 50
            elif test_ratio >= good_threshold:  # Good (>=0.20)
                test_coverage_score += 35
            elif test_ratio >= minimum_threshold:  # Minimum (>=0.10)
                test_coverage_score += 20
            elif test_ratio >= required_threshold:  # Required (>=0.05)
                test_coverage_score += 10
            else:  # Below required - PENALTY
                test_coverage_score += 5
                penalty = self.penalty_multipliers['missing_essentials']['no_tests'] * 0.3
                durability_penalties['insufficient_tests'] = penalty
                logger.warning(f"Insufficient test coverage: {test_ratio:.2%}")
        else:
            # SEVERE PENALTY for missing tests (40 points)
            penalty = self.penalty_multipliers['missing_essentials']['no_tests']
            durability_penalties['no_tests'] = penalty
            logger.warning("No tests found - applying severe penalty")
        
        # CI/CD indicators
        if repo_stats.get("has_ci"):
            test_coverage_score += 30
        
        # Framework testing support
        framework_usage = code_analysis.get("framework_usage", {})
        testing_frameworks = ["Jest", "PyTest", "JUnit", "RSpec", "Mocha"]
        has_testing_framework = any(fw in framework_usage for fw in testing_frameworks)
        if has_testing_framework:
            test_coverage_score += 20
        
        test_coverage_score = min(test_coverage_score, 100)
        durability_score += test_coverage_score * weights['test_coverage_weight']
        
        # 2. Documentation (25% weight)
        doc_durability_score = 0.0
        
        # Repository documentation
        if repo_stats.get("has_readme"):
            doc_durability_score += 30
        if repo_stats.get("has_license"):
            doc_durability_score += 20
        
        # Code documentation
        doc_coverage = code_analysis.get("documentation_coverage", 0)
        doc_durability_score += doc_coverage * 0.3
        
        # API documentation indicators
        if complexity_analysis.get("language_specific_metrics"):
            lang_metrics = complexity_analysis["language_specific_metrics"]
            if "best_practices" in lang_metrics:
                doc_durability_score += len(lang_metrics["best_practices"]) * 5
        
        doc_durability_score = min(doc_durability_score, 100)
        durability_score += doc_durability_score * weights['documentation_weight']
        
        # 3. Maintainability (25% weight) - STRICT THRESHOLDS
        maintainability_score = 0.0
        
        # Maintainability index from complexity analysis - STRICTER
        mi = complexity_analysis.get("maintainability_index", 50)
        excellent_threshold = self.complexity_thresholds['maintainability']['excellent']
        good_threshold = self.complexity_thresholds['maintainability']['good']
        acceptable_threshold = self.complexity_thresholds['maintainability']['acceptable']
        poor_threshold = self.complexity_thresholds['maintainability']['poor']
        
        if mi >= excellent_threshold:  # >=85
            maintainability_score += mi * 0.4
        elif mi >= good_threshold:  # >=75
            maintainability_score += mi * 0.35
        elif mi >= acceptable_threshold:  # >=65
            maintainability_score += mi * 0.3
        elif mi >= poor_threshold:  # >=50
            maintainability_score += mi * 0.2
            # Penalty for low maintainability
            deficit = acceptable_threshold - mi
            penalty = (deficit ** 1.3) * 0.1  # Exponential penalty
            durability_penalties['low_maintainability'] = min(penalty, 10)
            logger.warning(f"Low maintainability index: {mi:.1f} (threshold: {acceptable_threshold})")
        else:  # Critical - SEVERE EXPONENTIAL PENALTY
            maintainability_score += mi * 0.1
            deficit = acceptable_threshold - mi
            penalty = (deficit ** 1.5) * 0.15  # Severe exponential penalty
            durability_penalties['critical_maintainability'] = min(penalty, 20)
            logger.warning(f"Critical maintainability index: {mi:.1f}")
        
        # Code quality score
        quality_score = complexity_analysis.get("quality_score", 50)
        maintainability_score += quality_score * 0.3
        
        # Low complexity indicates good maintainability - STRICTER
        avg_complexity = complexity_analysis.get("cyclomatic_complexity", 0)
        acceptable_complexity = self.complexity_thresholds['cyclomatic']['acceptable']
        poor_complexity = self.complexity_thresholds['cyclomatic']['poor']
        
        if avg_complexity <= acceptable_complexity:  # <=12
            maintainability_score += 20
        elif avg_complexity <= poor_complexity:  # <=20
            maintainability_score += 10
        
        # Code smells penalty - STRICTER
        code_smells = complexity_analysis.get("code_smells", {})
        total_smells = sum(code_smells.values())
        smell_penalty = min(total_smells * 2.5, 35)  # Increased penalty
        maintainability_score -= smell_penalty
        if smell_penalty > 0:
            durability_penalties['code_smells'] = smell_penalty
        
        maintainability_score = max(0, min(maintainability_score, 100))
        durability_score += maintainability_score * weights['maintainability_weight']
        
        # 4. Version Control Practices (20% weight)
        version_control_score = 0.0
        
        # Commit frequency and consistency
        commit_frequency = commit_analysis.get("commit_frequency", 0)
        version_control_score += commit_frequency * 0.3
        
        # Contributor diversity
        contributor_diversity = commit_analysis.get("contributor_diversity", 0)
        version_control_score += contributor_diversity * 0.2
        
        # Recent activity
        recent_activity = commit_analysis.get("recent_activity", 0)
        version_control_score += recent_activity * 0.3
        
        # Repository maturity
        if repo_data.get("stargazers_count", 0) > 0:
            version_control_score += 10
        if repo_data.get("forks_count", 0) > 0:
            version_control_score += 10
        
        version_control_score = min(version_control_score, 100)
        durability_score += version_control_score * weights['version_control_weight']
        
        # Apply durability penalties
        total_durability_penalty = sum(durability_penalties.values())
        durability_score = max(0, durability_score - total_durability_penalty)
        
        # ==================== Final ACID Scores ====================
        
        # Normalize all scores to 0-100 range
        atomicity_final = min(100, max(0, atomicity_score))
        consistency_final = min(100, max(0, consistency_score))
        isolation_final = min(100, max(0, isolation_score))
        durability_final = min(100, max(0, durability_score))
        
        # Calculate overall ACID score with weighted average
        overall_acid = (atomicity_final * 0.25 + consistency_final * 0.25 + 
                       isolation_final * 0.25 + durability_final * 0.25)
        
        # Calculate total penalties applied
        total_penalties = {
            'atomicity': round(sum(atomicity_penalties.values()), 2),
            'consistency': round(sum(consistency_penalties.values()), 2),
            'isolation': round(sum(isolation_penalties.values()), 2),
            'durability': round(sum(durability_penalties.values()), 2)
        }
        
        return {
            "atomicity": round(atomicity_final, 1),
            "consistency": round(consistency_final, 1),
            "isolation": round(isolation_final, 1),
            "durability": round(durability_final, 1),
            "overall": round(overall_acid, 1),
            "penalties_applied": {
                "atomicity": atomicity_penalties,
                "consistency": consistency_penalties,
                "isolation": isolation_penalties,
                "durability": durability_penalties,
                "total_by_category": total_penalties,
                "grand_total": round(sum(total_penalties.values()), 2)
            },
            "detailed_breakdown": {
                "atomicity_components": {
                    "modularity": round(modularity_score, 1),
                    "single_responsibility": round(single_responsibility_score, 1),
                    "function_size": round(function_size_score, 1),
                    "class_cohesion": round(class_cohesion_score, 1)
                },
                "consistency_components": {
                    "naming_conventions": round(naming_score, 1),
                    "code_style": round(code_style_score, 1),
                    "documentation": round(documentation_score, 1),
                    "commit_patterns": round(commit_patterns_score, 1)
                },
                "isolation_components": {
                    "dependency_management": round(dependency_score, 1),
                    "architecture_separation": round(architecture_score, 1),
                    "coupling": round(coupling_score, 1),
                    "security": round(security_score, 1)
                },
                "durability_components": {
                    "test_coverage": round(test_coverage_score, 1),
                    "documentation": round(doc_durability_score, 1),
                    "maintainability": round(maintainability_score, 1),
                    "version_control": round(version_control_score, 1)
                }
            }
        }
    
    def _analyze_naming_consistency(self, names: List[str]) -> float:
        """Analyze naming consistency across function/class names"""
        
        if not names:
            return 0.0
        
        # Analyze naming patterns
        snake_case = sum(1 for name in names if re.match(r'^[a-z]+(_[a-z]+)*$', name))
        camel_case = sum(1 for name in names if re.match(r'^[a-z]+([A-Z][a-z]*)*$', name))
        pascal_case = sum(1 for name in names if re.match(r'^[A-Z][a-z]*([A-Z][a-z]*)*$', name))
        
        total_names = len(names)
        max_pattern = max(snake_case, camel_case, pascal_case)
        
        # Consistency score based on dominant pattern usage
        consistency = (max_pattern / total_names) * 100 if total_names > 0 else 0
        
        return consistency
    
    def _aggregate_complexity_metrics(self, complexity_by_language: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Aggregate complexity metrics across all files and languages"""
        
        aggregated = {
            "cyclomatic_complexity": 0,
            "cognitive_complexity": 0,
            "maintainability_index": 0,
            "nesting_depth": 0,
            "function_complexity": [],
            "class_complexity": [],
            "code_smells": {},
            "quality_score": 0,
            "language_specific_metrics": {},
            "halstead_metrics": {}
        }
        
        all_complexities = []
        all_maintainability = []
        all_quality_scores = []
        all_nesting_depths = []
        total_code_smells = defaultdict(int)
        
        # Aggregate metrics from all files
        for language, file_analyses in complexity_by_language.items():
            for file_analysis in file_analyses:
                all_complexities.append(file_analysis.get("cyclomatic_complexity", 0))
                all_maintainability.append(file_analysis.get("maintainability_index", 0))
                all_quality_scores.append(file_analysis.get("quality_score", 0))
                all_nesting_depths.append(file_analysis.get("nesting_depth", 0))
                
                # Aggregate function complexities
                func_complexities = file_analysis.get("function_complexity", [])
                aggregated["function_complexity"].extend(func_complexities)
                
                # Aggregate class complexities
                class_complexities = file_analysis.get("class_complexity", [])
                aggregated["class_complexity"].extend(class_complexities)
                
                # Aggregate code smells
                file_smells = file_analysis.get("code_smells", {})
                for smell_type, count in file_smells.items():
                    total_code_smells[smell_type] += count
                
                # Aggregate language-specific metrics
                lang_metrics = file_analysis.get("language_specific_metrics", {})
                if language not in aggregated["language_specific_metrics"]:
                    aggregated["language_specific_metrics"][language] = lang_metrics
        
        # Calculate overall metrics
        if all_complexities:
            aggregated["cyclomatic_complexity"] = statistics.mean(all_complexities)
        
        if all_maintainability:
            aggregated["maintainability_index"] = statistics.mean(all_maintainability)
        
        if all_quality_scores:
            aggregated["quality_score"] = statistics.mean(all_quality_scores)
        
        if all_nesting_depths:
            aggregated["nesting_depth"] = max(all_nesting_depths)
        
        aggregated["code_smells"] = dict(total_code_smells)
        
        # Calculate aggregated Halstead metrics
        if complexity_by_language:
            aggregated["halstead_metrics"] = self._aggregate_halstead_metrics(complexity_by_language)
        
        return aggregated
    
    def _aggregate_halstead_metrics(self, complexity_by_language: Dict[str, List[Dict[str, Any]]]) -> Dict[str, float]:
        """Aggregate Halstead metrics across all files"""
        
        total_vocabulary = 0
        total_length = 0
        total_volume = 0
        total_difficulty = 0
        total_effort = 0
        file_count = 0
        
        for language, file_analyses in complexity_by_language.items():
            for file_analysis in file_analyses:
                halstead = file_analysis.get("halstead_metrics", {})
                if halstead:
                    total_vocabulary += halstead.get("vocabulary", 0)
                    total_length += halstead.get("length", 0)
                    total_volume += halstead.get("volume", 0)
                    total_difficulty += halstead.get("difficulty", 0)
                    total_effort += halstead.get("effort", 0)
                    file_count += 1
        
        if file_count > 0:
            return {
                "vocabulary": total_vocabulary / file_count,
                "length": total_length / file_count,
                "volume": total_volume / file_count,
                "difficulty": total_difficulty / file_count,
                "effort": total_effort / file_count
            }
        
        return {}
    
    def _calculate_enhanced_quality_metrics(self, repo_data: Dict[str, Any], repo_stats: Dict[str, Any],
                                          code_analysis: Dict[str, Any], commit_analysis: Dict[str, Any],
                                          security_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Calculate enhanced quality metrics"""
        
        # READABILITY
        readability = 0.0
        readability += code_analysis.get("comment_ratio", 0) * 150  # Good comments
        readability += code_analysis.get("documentation_coverage", 0) * 0.3
        readability += min(commit_analysis.get("commit_message_quality", 0) * 0.4, 30)
        
        # Function/class organization
        total_lines = max(code_analysis.get("code_lines", 1), 1)
        function_density = (code_analysis.get("function_count", 0) / total_lines) * 1000
        if 5 <= function_density <= 20:  # Good function density
            readability += 20
        
        readability = min(readability, 100)
        
        # MAINTAINABILITY
        maintainability = 0.0
        maintainability += min(code_analysis.get("test_file_count", 0) * 15, 40)  # Tests
        maintainability += code_analysis.get("documentation_coverage", 0) * 0.25
        maintainability += commit_analysis.get("development_consistency", 0) * 0.2
        maintainability += commit_analysis.get("recent_activity", 0) * 0.15
        
        # Complexity penalty
        avg_complexity = self._get_average_complexity(code_analysis)
        maintainability += max(0, 20 - avg_complexity)
        
        maintainability = min(maintainability, 100)
        
        # SECURITY
        security = security_analysis.get("security_score", 100)
        
        # TEST COVERAGE (estimated)
        test_coverage = 0.0
        test_files = code_analysis.get("test_file_count", 0)
        total_files = code_analysis.get("total_files", 1)
        
        if test_files > 0:
            test_ratio = test_files / total_files
            test_coverage = min(test_ratio * 200, 80)  # Max 80 from ratio
            
            # Bonus for good test organization
            if test_ratio >= 0.2:
                test_coverage += 20
        
        test_coverage = min(test_coverage, 100)
        
        # DOCUMENTATION
        documentation = code_analysis.get("documentation_coverage", 0)
        
        return {
            "readability": round(readability, 1),
            "maintainability": round(maintainability, 1),
            "security": round(security, 1),
            "test_coverage": round(test_coverage, 1),
            "documentation": round(documentation, 1)
        }
    
    def _calculate_complexity_metrics(self, code_analysis: Dict[str, Any], repo_stats: Dict[str, Any]) -> Dict[str, float]:
        """Calculate complexity metrics"""
        
        # Cyclomatic complexity
        cyclomatic_complexity = self._get_average_complexity(code_analysis)
        
        # Structural complexity
        total_files = code_analysis.get("total_files", 1)
        total_lines = code_analysis.get("total_lines", 1)
        
        structural_complexity = min(math.log10(max(total_files, 1)) * 20, 50)
        structural_complexity += min(math.log10(max(total_lines, 1)) * 15, 50)
        
        # Language complexity
        language_count = len(code_analysis.get("language_breakdown", {}))
        language_complexity = min(language_count * 15, 75)
        
        # Dependency complexity (estimated from config files)
        config_files = code_analysis.get("config_file_count", 0)
        dependency_complexity = min(config_files * 20, 60)
        
        return {
            "cyclomatic_complexity": round(cyclomatic_complexity, 1),
            "structural_complexity": round(structural_complexity, 1),
            "language_complexity": round(language_complexity, 1),
            "dependency_complexity": round(dependency_complexity, 1),
            "overall_complexity": round((cyclomatic_complexity + structural_complexity + 
                                       language_complexity + dependency_complexity) / 4, 1)
        }
    
    def _assess_technology_usage(self, repo_data: Dict[str, Any], code_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess technology usage and proficiency"""
        
        languages = code_analysis.get("language_breakdown", {})
        total_lines = sum(languages.values()) if languages else 1
        
        # Calculate language proficiency based on usage
        language_proficiency = {}
        for language, lines in languages.items():
            percentage = (lines / total_lines) * 100
            
            # Proficiency estimation based on lines and complexity
            if percentage >= 50:
                proficiency = "Expert"
            elif percentage >= 20:
                proficiency = "Advanced"
            elif percentage >= 5:
                proficiency = "Intermediate"
            else:
                proficiency = "Beginner"
            
            language_proficiency[language] = {
                "lines": lines,
                "percentage": round(percentage, 1),
                "proficiency": proficiency
            }
        
        # Identify primary technologies
        primary_language = max(languages.keys(), key=lambda k: languages[k]) if languages else "Unknown"
        
        # Technology stack assessment
        tech_stack = self._identify_tech_stack(repo_data, code_analysis)
        
        return {
            "primary_language": primary_language,
            "language_proficiency": language_proficiency,
            "technology_stack": tech_stack,
            "language_diversity_score": min(len(languages) * 20, 100),
            "total_languages": len(languages)
        }
    
    def _identify_tech_stack(self, repo_data: Dict[str, Any], code_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify technology stack from repository analysis"""
        
        tech_stack = []
        languages = code_analysis.get("language_breakdown", {})
        
        # Add programming languages
        for language, lines in languages.items():
            tech_stack.append({
                "name": language,
                "category": "Programming Language",
                "usage_lines": lines,
                "confidence": "High"
            })
        
        # Identify frameworks and tools from file patterns
        file_breakdown = code_analysis.get("file_type_breakdown", {})
        
        if file_breakdown.get("config", 0) > 0:
            tech_stack.append({
                "name": "Configuration Management",
                "category": "DevOps",
                "usage_lines": 0,
                "confidence": "Medium"
            })
        
        # Add more technology detection based on file patterns, dependencies, etc.
        
        return tech_stack
    
    def _generate_recommendations(self, acid_scores: Dict[str, float], quality_metrics: Dict[str, float],
                                complexity_metrics: Dict[str, float], technology_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate improvement recommendations"""
        
        recommendations = []
        
        # ACID score recommendations
        if acid_scores["atomicity"] < 70:
            recommendations.append({
                "category": "Code Structure",
                "priority": "High",
                "title": "Improve Code Modularity",
                "description": "Break down large functions and classes into smaller, more focused components.",
                "impact": "Atomicity"
            })
        
        if acid_scores["consistency"] < 70:
            recommendations.append({
                "category": "Code Standards",
                "priority": "Medium",
                "title": "Establish Coding Standards",
                "description": "Implement consistent naming conventions, formatting, and documentation practices.",
                "impact": "Consistency"
            })
        
        if acid_scores["isolation"] < 70:
            recommendations.append({
                "category": "Architecture",
                "priority": "High",
                "title": "Improve Code Isolation",
                "description": "Better separate concerns and reduce coupling between components.",
                "impact": "Isolation"
            })
        
        if acid_scores["durability"] < 70:
            recommendations.append({
                "category": "Maintainability",
                "priority": "High",
                "title": "Enhance Long-term Maintainability",
                "description": "Add comprehensive tests, documentation, and establish maintenance practices.",
                "impact": "Durability"
            })
        
        # Quality metric recommendations
        if quality_metrics["test_coverage"] < 60:
            recommendations.append({
                "category": "Testing",
                "priority": "High",
                "title": "Increase Test Coverage",
                "description": "Add unit tests, integration tests, and establish testing practices.",
                "impact": "Quality"
            })
        
        if quality_metrics["documentation"] < 60:
            recommendations.append({
                "category": "Documentation",
                "priority": "Medium",
                "title": "Improve Documentation",
                "description": "Add comprehensive README, code comments, and API documentation.",
                "impact": "Maintainability"
            })
        
        if quality_metrics["security"] < 80:
            recommendations.append({
                "category": "Security",
                "priority": "High",
                "title": "Address Security Issues",
                "description": "Review and fix potential security vulnerabilities in the codebase.",
                "impact": "Security"
            })
        
        # Complexity recommendations
        if complexity_metrics["overall_complexity"] > 70:
            recommendations.append({
                "category": "Complexity",
                "priority": "Medium",
                "title": "Reduce Code Complexity",
                "description": "Simplify complex functions and reduce cyclomatic complexity.",
                "impact": "Maintainability"
            })
        
        return recommendations
    
    def _calculate_overall_score(self, acid_scores: Dict[str, float], quality_metrics: Dict[str, float],
                               complexity_metrics: Dict[str, float]) -> float:
        """Calculate overall repository score"""
        
        # Weighted average of different aspects
        acid_weight = 0.4
        quality_weight = 0.4
        complexity_weight = 0.2
        
        acid_avg = acid_scores["overall"]
        quality_avg = statistics.mean(quality_metrics.values())
        
        # Complexity penalty (higher complexity reduces score)
        complexity_penalty = complexity_metrics["overall_complexity"] * 0.3
        
        overall = (acid_avg * acid_weight + 
                  quality_avg * quality_weight - 
                  complexity_penalty * complexity_weight)
        
        return round(max(0, min(overall, 100)), 1)
    
    def _get_average_complexity(self, code_analysis: Dict[str, Any]) -> float:
        """Get average complexity across all languages"""
        complexity_data = code_analysis.get("complexity_indicators", {})
        
        if not complexity_data:
            return 0.0
        
        complexities = []
        for lang_data in complexity_data.values():
            if isinstance(lang_data, dict):
                complexities.append(lang_data.get("average", 0))
            else:
                complexities.append(lang_data)
        
        return statistics.mean(complexities) if complexities else 0.0
    
    def calculate_user_scores(self, repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall user scores from multiple repositories (legacy method)"""
        # Filter repositories to only include those marked for evaluation
        evaluated_repos = [repo for repo in repositories if repo.get('evaluated_for_scoring', True)]
        
        # Import here to avoid circular imports
        from app.services.profile_generator import ProfileGenerator
        
        profile_generator = ProfileGenerator()
        profile = profile_generator.generate_developer_profile(evaluated_repos)
        
        # Return legacy format for backward compatibility
        overall_scores = profile.get("overall_scores", {})
        return {
            "overall_score": overall_scores.get("overall_score", 0),
            "acid_scores": overall_scores.get("acid_scores", {}),
            "quality_metrics": overall_scores.get("quality_metrics", {}),
            "technology_summary": {lang["language"]: lang["lines"] 
                                 for lang in profile.get("repository_analysis", {}).get("primary_languages", [])},
            "total_repositories": len(repositories),  # Total repos including display-only
            "evaluated_repositories": len(evaluated_repos),  # Only evaluated repos
            "full_profile": profile  # Include full profile for enhanced features
        }
    
    def generate_comprehensive_profile(self, repositories: List[Dict[str, Any]], 
                                     user_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Calculate overall user scores from multiple repositories"""
        
        # Filter repositories to only include those marked for evaluation
        evaluated_repos = [repo for repo in repositories if repo.get('evaluated_for_scoring', True)]
        
        if not evaluated_repos:
            return {
                "overall_score": 0,
                "acid_scores": {"atomicity": 0, "consistency": 0, "isolation": 0, "durability": 0, "overall": 0},
                "quality_metrics": {"readability": 0, "maintainability": 0, "security": 0, "test_coverage": 0, "documentation": 0},
                "technology_summary": {},
                "total_repositories": len(repositories),
                "evaluated_repositories": 0
            }
        
        # Aggregate ACID scores
        acid_totals = {"atomicity": 0, "consistency": 0, "isolation": 0, "durability": 0}
        quality_totals = {"readability": 0, "maintainability": 0, "security": 0, "test_coverage": 0, "documentation": 0}
        
        total_lines = 0
        language_totals = defaultdict(int)
        
        for repo in evaluated_repos:
            acid_scores = repo.get("acid_scores", {})
            quality_metrics = repo.get("quality_metrics", {})
            
            # Weight by repository size/importance
            repo_lines = sum(repo.get("languages", {}).values())
            weight = max(1, repo_lines)  # Minimum weight of 1
            total_lines += weight
            
            # Aggregate scores
            for key in acid_totals:
                acid_totals[key] += acid_scores.get(key, 0) * weight
            
            for key in quality_totals:
                quality_totals[key] += quality_metrics.get(key, 0) * weight
            
            # Aggregate languages
            for lang, lines in repo.get("languages", {}).items():
                language_totals[lang] += lines
        
        # Calculate weighted averages
        if total_lines > 0:
            for key in acid_totals:
                acid_totals[key] /= total_lines
            for key in quality_totals:
                quality_totals[key] /= total_lines
        
        # Calculate overall score
        acid_overall = statistics.mean(acid_totals.values())
        quality_overall = statistics.mean(quality_totals.values())
        overall_score = (acid_overall + quality_overall) / 2
        
        acid_totals["overall"] = round(acid_overall, 1)
        
        # Round all scores
        for key in acid_totals:
            acid_totals[key] = round(acid_totals[key], 1)
        for key in quality_totals:
            quality_totals[key] = round(quality_totals[key], 1)
        
        return {
            "overall_score": round(overall_score, 1),
            "acid_scores": acid_totals,
            "quality_metrics": quality_totals,
            "technology_summary": dict(language_totals),
            "total_repositories": len(repositories),
            "evaluated_repositories": len(evaluated_repos),
            "total_lines_of_code": sum(language_totals.values())
        }
    
    def generate_comprehensive_profile(self, repositories: List[Dict[str, Any]], 
                                     user_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate comprehensive developer profile (new method)"""
        from app.services.profile_generator import ProfileGenerator
        
        profile_generator = ProfileGenerator()
        return profile_generator.generate_developer_profile(repositories, user_data)
    
    # Helper methods for enhanced analysis
    
    def _identify_project_type(self, file_paths: List[str], repo_data: Dict[str, Any]) -> str:
        """Identify the type of project based on file structure and metadata"""
        
        # Check for common project indicators
        indicators = {
            "web_frontend": ["package.json", "index.html", "src/components", "public/", "webpack.config.js"],
            "web_backend": ["app.py", "server.js", "main.go", "pom.xml", "requirements.txt"],
            "mobile_app": ["android/", "ios/", "lib/main.dart", "App.js", "pubspec.yaml"],
            "desktop_app": ["main.cpp", "MainWindow.xaml", "setup.py", "Cargo.toml"],
            "library": ["setup.py", "package.json", "Cargo.toml", "pom.xml", "__init__.py"],
            "data_science": ["notebook.ipynb", "requirements.txt", "data/", "models/"],
            "game": ["Assets/", "scenes/", "main.cpp", "game.py"],
            "cli_tool": ["main.py", "main.go", "main.rs", "cli.py"],
            "documentation": ["docs/", "README.md", ".md files"]
        }
        
        file_paths_str = " ".join(file_paths).lower()
        
        for project_type, patterns in indicators.items():
            matches = sum(1 for pattern in patterns if pattern.lower() in file_paths_str)
            if matches >= 2:
                return project_type
        
        # Fallback to language-based detection
        languages = repo_data.get("languages", {})
        if languages:
            primary_lang = max(languages.keys(), key=lambda k: languages[k])
            
            lang_to_type = {
                "JavaScript": "web_frontend",
                "TypeScript": "web_frontend", 
                "Python": "web_backend",
                "Java": "web_backend",
                "Go": "web_backend",
                "Swift": "mobile_app",
                "Kotlin": "mobile_app",
                "C++": "desktop_app",
                "C#": "desktop_app"
            }
            
            return lang_to_type.get(primary_lang, "general")
        
        return "general"
    
    def _identify_architecture_patterns(self, file_paths: List[str]) -> List[str]:
        """Identify architecture patterns from file structure"""
        
        patterns = []
        file_paths_str = " ".join(file_paths).lower()
        
        # MVC pattern
        if all(pattern in file_paths_str for pattern in ["models/", "views/", "controllers/"]):
            patterns.append("MVC")
        
        # Microservices
        if "services/" in file_paths_str and file_paths_str.count("service") > 2:
            patterns.append("Microservices")
        
        # Layered architecture
        if all(layer in file_paths_str for layer in ["controllers/", "services/", "repositories/"]):
            patterns.append("Layered")
        
        # Component-based
        if "components/" in file_paths_str:
            patterns.append("Component-based")
        
        # Domain-driven design
        if "domain/" in file_paths_str or "entities/" in file_paths_str:
            patterns.append("Domain-driven")
        
        return patterns
    
    def _calculate_organization_score(self, directories: Dict[str, int], file_paths: List[str]) -> float:
        """Calculate file organization quality score"""
        
        score = 0.0
        
        # Check for reasonable directory structure
        if len(directories) > 0:
            score += 20
        
        # Penalize too deep nesting
        max_depth = max(len(path.split('/')) for path in file_paths) if file_paths else 0
        if max_depth <= 4:
            score += 20
        elif max_depth <= 6:
            score += 10
        
        # Reward balanced file distribution
        if directories:
            files_per_dir = list(directories.values())
            if files_per_dir:
                avg_files = statistics.mean(files_per_dir)
                if 3 <= avg_files <= 15:  # Good balance
                    score += 20
        
        # Check for common organizational patterns
        common_dirs = ["src/", "lib/", "test/", "docs/", "config/"]
        present_dirs = sum(1 for dir_name in common_dirs if any(dir_name in path for path in file_paths))
        score += min(present_dirs * 8, 40)
        
        return min(score, 100)
    
    def _analyze_naming_conventions(self, file_paths: List[str]) -> Dict[str, Any]:
        """Analyze naming conventions used in the project"""
        
        conventions = {
            "snake_case": 0,
            "camelCase": 0,
            "PascalCase": 0,
            "kebab-case": 0,
            "consistency_score": 0
        }
        
        for path in file_paths:
            filename = path.split('/')[-1]
            name_without_ext = filename.split('.')[0] if '.' in filename else filename
            
            if re.match(r'^[a-z]+(_[a-z]+)*$', name_without_ext):
                conventions["snake_case"] += 1
            elif re.match(r'^[a-z]+([A-Z][a-z]*)*$', name_without_ext):
                conventions["camelCase"] += 1
            elif re.match(r'^[A-Z][a-z]*([A-Z][a-z]*)*$', name_without_ext):
                conventions["PascalCase"] += 1
            elif re.match(r'^[a-z]+(-[a-z]+)*$', name_without_ext):
                conventions["kebab-case"] += 1
        
        # Calculate consistency score
        total_files = len(file_paths)
        if total_files > 0:
            max_convention = max(conventions["snake_case"], conventions["camelCase"], 
                               conventions["PascalCase"], conventions["kebab-case"])
            conventions["consistency_score"] = (max_convention / total_files) * 100
        
        return conventions
    
    def _analyze_file_distribution(self, file_paths: List[str]) -> Dict[str, Any]:
        """Analyze distribution of files across directories"""
        
        distribution = {
            "files_per_directory": {},
            "depth_distribution": defaultdict(int),
            "file_type_distribution": defaultdict(int)
        }
        
        for path in file_paths:
            # Directory distribution
            directory = '/'.join(path.split('/')[:-1]) if '/' in path else "root"
            if directory not in distribution["files_per_directory"]:
                distribution["files_per_directory"][directory] = 0
            distribution["files_per_directory"][directory] += 1
            
            # Depth distribution
            depth = len(path.split('/')) - 1
            distribution["depth_distribution"][depth] += 1
            
            # File type distribution
            extension = path.split('.')[-1] if '.' in path else "no_extension"
            distribution["file_type_distribution"][extension] += 1
        
        return distribution
    
    def _detect_frameworks_comprehensive(self, content: str, language: str, filename: str) -> Dict[str, float]:
        """Detect frameworks and libraries with confidence scoring"""
        
        frameworks = {}
        
        if language == "JavaScript" or language == "TypeScript":
            # React
            if re.search(r'import.*react|from\s+["\']react["\']|React\.|jsx', content, re.IGNORECASE):
                frameworks["React"] = 0.9
            
            # Vue
            if re.search(r'import.*vue|from\s+["\']vue["\']|Vue\.|\.vue', content, re.IGNORECASE):
                frameworks["Vue.js"] = 0.9
            
            # Angular
            if re.search(r'@angular|import.*@angular|@Component|@Injectable', content, re.IGNORECASE):
                frameworks["Angular"] = 0.9
            
            # Express
            if re.search(r'express\(\)|require\(["\']express["\']|app\.get\(|app\.post\(', content, re.IGNORECASE):
                frameworks["Express.js"] = 0.8
            
            # Node.js
            if re.search(r'require\(|module\.exports|process\.|__dirname', content):
                frameworks["Node.js"] = 0.7
        
        elif language == "Python":
            # Django
            if re.search(r'from django|import django|models\.Model|HttpResponse', content, re.IGNORECASE):
                frameworks["Django"] = 0.9
            
            # Flask
            if re.search(r'from flask|import flask|Flask\(__name__\)|@app\.route', content, re.IGNORECASE):
                frameworks["Flask"] = 0.9
            
            # FastAPI
            if re.search(r'from fastapi|import fastapi|FastAPI\(\)|@app\.(get|post)', content, re.IGNORECASE):
                frameworks["FastAPI"] = 0.9
            
            # Pandas
            if re.search(r'import pandas|pd\.|DataFrame|read_csv', content, re.IGNORECASE):
                frameworks["Pandas"] = 0.8
            
            # NumPy
            if re.search(r'import numpy|np\.|array\(|ndarray', content, re.IGNORECASE):
                frameworks["NumPy"] = 0.8
        
        elif language == "Java":
            # Spring
            if re.search(r'@SpringBootApplication|@RestController|@Service|springframework', content):
                frameworks["Spring"] = 0.9
            
            # Android
            if re.search(r'android\.|Activity|Fragment|onCreate', content):
                frameworks["Android"] = 0.9
        
        return frameworks
    
    def _detect_design_patterns(self, content: str, language: str) -> List[str]:
        """Detect common design patterns in code"""
        
        patterns = []
        
        # Singleton pattern
        if re.search(r'class.*Singleton|private.*constructor|getInstance\(\)', content, re.IGNORECASE):
            patterns.append("Singleton")
        
        # Factory pattern
        if re.search(r'class.*Factory|createInstance|factory.*method', content, re.IGNORECASE):
            patterns.append("Factory")
        
        # Observer pattern
        if re.search(r'class.*Observer|addEventListener|subscribe|notify', content, re.IGNORECASE):
            patterns.append("Observer")
        
        # Strategy pattern
        if re.search(r'class.*Strategy|interface.*Strategy', content, re.IGNORECASE):
            patterns.append("Strategy")
        
        # Decorator pattern
        if language == "Python" and re.search(r'@\w+|def.*decorator', content):
            patterns.append("Decorator")
        
        return patterns
    
    def _detect_code_smells(self, content: str, language: str) -> Dict[str, int]:
        """Detect common code smells"""
        
        smells = {}
        
        # Long methods (more than 50 lines)
        if language in ["Python", "JavaScript", "Java"]:
            method_pattern = r'def\s+\w+|function\s+\w+|public\s+\w+\s+\w+\s*\('
            methods = re.findall(method_pattern, content)
            long_methods = 0
            
            for match in re.finditer(method_pattern, content):
                method_start = match.start()
                # Count lines until next method or end
                remaining_content = content[method_start:]
                method_lines = len(remaining_content.split('\n')[:50])  # Check first 50 lines
                if method_lines >= 50:
                    long_methods += 1
            
            if long_methods > 0:
                smells["long_methods"] = long_methods
        
        # Duplicate code (simple heuristic)
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        duplicate_lines = len(lines) - len(set(lines))
        if duplicate_lines > 10:
            smells["duplicate_code"] = duplicate_lines
        
        # Magic numbers
        magic_numbers = len(re.findall(r'\b\d{2,}\b', content))
        if magic_numbers > 5:
            smells["magic_numbers"] = magic_numbers
        
        # Long parameter lists
        long_param_lists = len(re.findall(r'\([^)]{50,}\)', content))
        if long_param_lists > 0:
            smells["long_parameter_lists"] = long_param_lists
        
        return smells
    
    def _calculate_maintainability_index(self, analysis: Dict[str, Any]) -> float:
        """Calculate maintainability index based on various metrics"""
        
        # Base score
        score = 100.0
        
        # Penalize high complexity
        avg_complexity = self._get_average_complexity(analysis)
        score -= min(avg_complexity * 2, 30)
        
        # Reward good comment ratio
        comment_ratio = analysis.get("comment_ratio", 0)
        if comment_ratio > 0.1:
            score += min(comment_ratio * 50, 20)
        
        # Penalize code smells
        code_smells = analysis.get("code_smells", {})
        total_smells = sum(code_smells.values())
        score -= min(total_smells * 2, 25)
        
        # Reward test files
        test_files = analysis.get("test_file_count", 0)
        total_files = analysis.get("total_files", 1)
        test_ratio = test_files / total_files
        score += min(test_ratio * 30, 15)
        
        return max(0, min(score, 100))
    
    def _identify_technical_debt(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Identify technical debt indicators"""
        
        debt_indicators = {
            "high_complexity_files": 0,
            "low_test_coverage": False,
            "code_smells_count": 0,
            "outdated_dependencies": 0,
            "documentation_gaps": False,
            "debt_score": 0
        }
        
        # High complexity files
        complexity_data = analysis.get("complexity_indicators", {})
        for lang_data in complexity_data.values():
            if isinstance(lang_data, dict) and lang_data.get("average", 0) > 15:
                debt_indicators["high_complexity_files"] += 1
        
        # Low test coverage
        test_files = analysis.get("test_file_count", 0)
        total_files = analysis.get("total_files", 1)
        if test_files / total_files < 0.2:
            debt_indicators["low_test_coverage"] = True
        
        # Code smells
        code_smells = analysis.get("code_smells", {})
        debt_indicators["code_smells_count"] = sum(code_smells.values())
        
        # Documentation gaps
        comment_ratio = analysis.get("comment_ratio", 0)
        if comment_ratio < 0.1:
            debt_indicators["documentation_gaps"] = True
        
        # Calculate overall debt score
        debt_score = 0
        debt_score += debt_indicators["high_complexity_files"] * 10
        debt_score += 20 if debt_indicators["low_test_coverage"] else 0
        debt_score += min(debt_indicators["code_smells_count"] * 2, 30)
        debt_score += 15 if debt_indicators["documentation_gaps"] else 0
        
        debt_indicators["debt_score"] = min(debt_score, 100)
        
        return debt_indicators
    
    def _analyze_language_features(self, content: str, language: str) -> Dict[str, Any]:
        """Analyze language-specific features and modern practices"""
        
        features = {"complexity": 0, "modern_features": [], "best_practices": []}
        
        if language == "Python":
            # Modern Python features
            if re.search(r'async\s+def|await\s+', content):
                features["modern_features"].append("async/await")
            if re.search(r'f["\'][^"\']*{[^}]+}', content):
                features["modern_features"].append("f-strings")
            if re.search(r':\s*List\[|:\s*Dict\[|from typing import', content):
                features["modern_features"].append("type_hints")
            
            # Best practices
            if re.search(r'if __name__ == ["\']__main__["\']:', content):
                features["best_practices"].append("main_guard")
        
        elif language == "JavaScript":
            # Modern JS features
            if re.search(r'=>', content):
                features["modern_features"].append("arrow_functions")
            if re.search(r'const\s+|let\s+', content):
                features["modern_features"].append("es6_variables")
            if re.search(r'async\s+function|await\s+', content):
                features["modern_features"].append("async/await")
        
        # Calculate complexity
        features["complexity"] = self._analyze_code_complexity(content, language)
        
        return features
    
    def _get_framework_category(self, framework: str) -> str:
        """Get category for a detected framework"""
        
        categories = {
            "React": "Frontend Framework",
            "Vue.js": "Frontend Framework", 
            "Angular": "Frontend Framework",
            "Express.js": "Backend Framework",
            "Django": "Backend Framework",
            "Flask": "Backend Framework",
            "FastAPI": "Backend Framework",
            "Spring": "Backend Framework",
            "Node.js": "Runtime Environment",
            "Pandas": "Data Science Library",
            "NumPy": "Scientific Computing",
            "Android": "Mobile Framework"
        }
        
        return categories.get(framework, "Library")
    
    def _build_technology_stack(self, primary_languages: Dict[str, Any], frameworks: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build comprehensive technology stack"""
        
        stack = []
        
        # Add languages
        for language, info in primary_languages.items():
            stack.append({
                "name": language,
                "type": "Programming Language",
                "usage_percentage": info["percentage"],
                "proficiency": "Primary"
            })
        
        # Add frameworks
        for framework, info in frameworks.items():
            stack.append({
                "name": framework,
                "type": info["category"],
                "confidence": info["confidence"],
                "proficiency": "Experienced" if info["confidence"] > 0.8 else "Familiar"
            })
        
        return stack
    
    def _assess_language_proficiency(self, language_stats: Dict[str, Any]) -> Dict[str, str]:
        """Assess proficiency level for each language"""
        
        proficiency = {}
        
        for language, stats in language_stats.items():
            lines = stats["lines"]
            files = stats["files"]
            avg_complexity = stats["complexity"] / max(files, 1)
            
            # Proficiency based on usage and complexity
            if lines > 5000 and files > 10 and avg_complexity > 5:
                proficiency[language] = "Expert"
            elif lines > 2000 and files > 5:
                proficiency[language] = "Advanced"
            elif lines > 500 and files > 2:
                proficiency[language] = "Intermediate"
            else:
                proficiency[language] = "Beginner"
        
        return proficiency
    
    def _detect_modern_practices(self, contents: List[Dict[str, Any]]) -> Dict[str, bool]:
        """Detect modern development practices"""
        
        practices = {
            "version_control": False,
            "dependency_management": False,
            "testing": False,
            "ci_cd": False,
            "containerization": False,
            "linting": False,
            "type_checking": False
        }
        
        all_content = " ".join([file_info.get("content", "") for file_info in contents])
        all_filenames = " ".join([file_info.get("name", "") for file_info in contents])
        
        # Check for various practices
        if ".git" in all_filenames or "git" in all_content.lower():
            practices["version_control"] = True
        
        if any(dep_file in all_filenames for dep_file in ["package.json", "requirements.txt", "pom.xml", "Cargo.toml"]):
            practices["dependency_management"] = True
        
        if any(test_indicator in all_filenames.lower() for test_indicator in ["test", "spec", "__test__"]):
            practices["testing"] = True
        
        if any(ci_file in all_filenames for ci_file in [".github/workflows", ".gitlab-ci.yml", "Jenkinsfile"]):
            practices["ci_cd"] = True
        
        if "Dockerfile" in all_filenames or "docker-compose" in all_filenames:
            practices["containerization"] = True
        
        if any(lint_file in all_filenames for lint_file in [".eslintrc", ".pylintrc", "tslint.json"]):
            practices["linting"] = True
        
        if "typescript" in all_content.lower() or ".ts" in all_filenames:
            practices["type_checking"] = True
        
        return practices
    
    def _calculate_cyclomatic_complexity(self, content: str, language: str) -> float:
        """Calculate cyclomatic complexity for a file"""
        
        complexity = 1  # Base complexity
        
        # Decision points that increase complexity
        decision_patterns = {
            "Python": [r'\bif\b', r'\belif\b', r'\bwhile\b', r'\bfor\b', r'\btry\b', r'\bexcept\b', r'\band\b', r'\bor\b'],
            "JavaScript": [r'\bif\b', r'\belse\s+if\b', r'\bwhile\b', r'\bfor\b', r'\btry\b', r'\bcatch\b', r'&&', r'\|\|', r'\?'],
            "Java": [r'\bif\b', r'\belse\s+if\b', r'\bwhile\b', r'\bfor\b', r'\btry\b', r'\bcatch\b', r'&&', r'\|\|', r'\?', r'\bcase\b'],
            "TypeScript": [r'\bif\b', r'\belse\s+if\b', r'\bwhile\b', r'\bfor\b', r'\btry\b', r'\bcatch\b', r'&&', r'\|\|', r'\?']
        }
        
        patterns = decision_patterns.get(language, decision_patterns["JavaScript"])
        
        for pattern in patterns:
            matches = len(re.findall(pattern, content, re.IGNORECASE))
            complexity += matches
        
        return complexity
    
    def _calculate_cognitive_complexity(self, content: str, language: str) -> float:
        """Calculate cognitive complexity (how hard code is to understand)"""
        
        complexity = 0
        nesting_level = 0
        
        lines = content.split('\n')
        
        for line in lines:
            stripped = line.strip()
            
            # Increase nesting for control structures
            if re.search(r'\b(if|while|for|try|def|function|class)\b', stripped):
                nesting_level += 1
                complexity += nesting_level  # Nested structures are harder to understand
            
            # Decrease nesting for closing braces/dedentation
            if stripped in ['}', 'end'] or (language == "Python" and len(line) - len(line.lstrip()) < nesting_level * 4):
                nesting_level = max(0, nesting_level - 1)
            
            # Additional complexity for logical operators
            complexity += len(re.findall(r'&&|\|\||and\s+|or\s+', stripped))
        
        return complexity
    
    def _calculate_halstead_metrics(self, content: str, language: str) -> Dict[str, float]:
        """Calculate Halstead complexity metrics"""
        
        # Simple implementation - count operators and operands
        operators = set()
        operands = set()
        
        # Common operators across languages
        operator_patterns = [r'\+', r'-', r'\*', r'/', r'=', r'==', r'!=', r'<', r'>', r'<=', r'>=', r'&&', r'\|\|']
        
        for pattern in operator_patterns:
            matches = re.findall(pattern, content)
            operators.update(matches)
        
        # Simple operand detection (variables, numbers, strings)
        operand_matches = re.findall(r'\b[a-zA-Z_]\w*\b|\b\d+\b|["\'][^"\']*["\']', content)
        operands.update(operand_matches)
        
        n1 = len(operators)  # Number of distinct operators
        n2 = len(operands)   # Number of distinct operands
        N1 = sum(len(re.findall(pattern, content)) for pattern in operator_patterns)  # Total operators
        N2 = len(operand_matches)  # Total operands
        
        # Halstead metrics
        vocabulary = n1 + n2
        length = N1 + N2
        volume = length * math.log2(vocabulary) if vocabulary > 0 else 0
        difficulty = (n1 / 2) * (N2 / n2) if n2 > 0 else 0
        effort = difficulty * volume
        
        return {
            "vocabulary": vocabulary,
            "length": length,
            "volume": volume,
            "difficulty": difficulty,
            "effort": effort
        }
    
    def _calculate_file_maintainability(self, content: str, language: str) -> float:
        """Calculate maintainability score for a single file"""
        
        score = 100.0
        
        # Penalize high complexity
        complexity = self._calculate_cyclomatic_complexity(content, language)
        score -= min(complexity * 2, 40)
        
        # Penalize long files
        lines = len([line for line in content.split('\n') if line.strip()])
        if lines > 500:
            score -= min((lines - 500) * 0.1, 20)
        
        # Reward comments
        comment_lines = len([line for line in content.split('\n') 
                           if line.strip() and self._is_comment_line(line.strip(), language)])
        comment_ratio = comment_lines / max(lines, 1)
        score += min(comment_ratio * 30, 15)
        
        # Penalize code smells
        smells = self._detect_code_smells(content, language)
        total_smells = sum(smells.values())
        score -= min(total_smells * 3, 25)
        
        return max(0, min(score, 100))
    
    def _calculate_complexity_distribution(self, complexities: List[float]) -> Dict[str, int]:
        """Calculate distribution of complexity scores"""
        
        distribution = {"low": 0, "medium": 0, "high": 0, "very_high": 0}
        
        for complexity in complexities:
            if complexity <= 5:
                distribution["low"] += 1
            elif complexity <= 10:
                distribution["medium"] += 1
            elif complexity <= 20:
                distribution["high"] += 1
            else:
                distribution["very_high"] += 1
        
        return distribution
    
    def _is_non_code_file(self, filename: str) -> bool:
        """Check if file is not a code file"""
        
        non_code_extensions = ['.md', '.txt', '.json', '.xml', '.yml', '.yaml', '.ini', '.cfg', '.conf']
        return any(filename.lower().endswith(ext) for ext in non_code_extensions)
    
    def _is_code_file(self, filename: str, language: str) -> bool:
        """Check if file is a code file"""
        
        code_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt']
        return any(filename.lower().endswith(ext) for ext in code_extensions) or language != "Unknown"
    
    def _assess_doc_quality(self, content: str, doc_type: str) -> float:
        """Assess quality of documentation content"""
        
        score = 0.0
        
        # Basic length check
        if len(content) > 100:
            score += 20
        if len(content) > 500:
            score += 20
        
        # Structure indicators
        if doc_type == "readme":
            if re.search(r'#.*installation|#.*setup', content, re.IGNORECASE):
                score += 15
            if re.search(r'#.*usage|#.*example', content, re.IGNORECASE):
                score += 15
            if re.search(r'#.*license', content, re.IGNORECASE):
                score += 10
            if re.search(r'#.*contributing', content, re.IGNORECASE):
                score += 10
        
        # Code examples
        if re.search(r'```|`[^`]+`', content):
            score += 10
        
        return min(score, 100)
    
    def _has_adequate_docstrings(self, content: str, language: str) -> bool:
        """Check if code has adequate documentation strings"""
        
        if language == "Python":
            # Check for docstrings in functions and classes
            functions = len(re.findall(r'def\s+\w+', content))
            classes = len(re.findall(r'class\s+\w+', content))
            docstrings = len(re.findall(r'""".*?"""', content, re.DOTALL))
            
            total_definitions = functions + classes
            return docstrings >= (total_definitions * 0.5) if total_definitions > 0 else False
        
        elif language in ["JavaScript", "TypeScript"]:
            # Check for JSDoc comments
            functions = len(re.findall(r'function\s+\w+|=>\s*{', content))
            jsdoc = len(re.findall(r'/\*\*.*?\*/', content, re.DOTALL))
            
            return jsdoc >= (functions * 0.3) if functions > 0 else False
        
        return False
    
    def _calculate_documentation_coverage_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall documentation coverage score"""
        
        score = 0.0
        
        # Documentation files score
        doc_types = analysis.get("documentation_types", {})
        score += sum(20 if present else 0 for present in doc_types.values())
        
        # Inline documentation score
        inline_docs = analysis.get("inline_documentation", {})
        if inline_docs:
            comment_ratio = inline_docs.get("comment_ratio", 0)
            doc_ratio = inline_docs.get("documentation_ratio", 0)
            
            score += min(comment_ratio * 100, 20)
            score += min(doc_ratio * 30, 20)
        
        return min(score, 100)
    
    def _identify_missing_documentation(self, analysis: Dict[str, Any], repo_data: Dict[str, Any]) -> List[str]:
        """Identify missing documentation types"""
        
        missing = []
        doc_types = analysis.get("documentation_types", {})
        
        if not doc_types.get("readme"):
            missing.append("README file")
        if not doc_types.get("license"):
            missing.append("LICENSE file")
        if not doc_types.get("contributing"):
            missing.append("CONTRIBUTING guidelines")
        
        # Check for API documentation if it's a library
        if repo_data.get("topics") and any("library" in topic.lower() for topic in repo_data.get("topics", [])):
            if not doc_types.get("api_docs"):
                missing.append("API documentation")
        
        return missing
    
    def _analyze_project_structure_practices(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze project structure best practices"""
        
        practices = {
            "has_src_directory": False,
            "has_test_directory": False,
            "has_docs_directory": False,
            "has_config_files": False,
            "separation_of_concerns": False,
            "score": 0
        }
        
        file_paths = [file_info.get("path", "") for file_info in contents]
        all_paths = " ".join(file_paths).lower()
        
        if "src/" in all_paths or "lib/" in all_paths:
            practices["has_src_directory"] = True
            practices["score"] += 20
        
        if "test/" in all_paths or "__test__/" in all_paths:
            practices["has_test_directory"] = True
            practices["score"] += 20
        
        if "docs/" in all_paths or "documentation/" in all_paths:
            practices["has_docs_directory"] = True
            practices["score"] += 15
        
        config_files = ["package.json", "requirements.txt", "pom.xml", "Cargo.toml"]
        if any(config_file in all_paths for config_file in config_files):
            practices["has_config_files"] = True
            practices["score"] += 15
        
        # Check separation of concerns
        if practices["has_src_directory"] and practices["has_test_directory"]:
            practices["separation_of_concerns"] = True
            practices["score"] += 30
        
        return practices
    
    def _analyze_code_organization_practices(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze code organization practices"""
        
        practices = {
            "modular_structure": False,
            "consistent_naming": False,
            "appropriate_file_sizes": False,
            "score": 0
        }
        
        file_sizes = []
        for file_info in contents:
            content = file_info.get("content", "")
            if content and self._is_code_file(file_info.get("name", ""), file_info.get("language", "")):
                lines = len([line for line in content.split('\n') if line.strip()])
                file_sizes.append(lines)
        
        # Check file sizes
        if file_sizes:
            avg_size = statistics.mean(file_sizes)
            max_size = max(file_sizes)
            
            if avg_size <= 200 and max_size <= 500:
                practices["appropriate_file_sizes"] = True
                practices["score"] += 30
        
        # Check modular structure (multiple files)
        code_files = len([f for f in contents if self._is_code_file(f.get("name", ""), f.get("language", ""))])
        if code_files >= 3:
            practices["modular_structure"] = True
            practices["score"] += 35
        
        # Check naming consistency (simplified)
        file_names = [file_info.get("name", "") for file_info in contents]
        naming_analysis = self._analyze_naming_conventions([f for f in file_names if f])
        if naming_analysis.get("consistency_score", 0) > 70:
            practices["consistent_naming"] = True
            practices["score"] += 35
        
        return practices
    
    def _analyze_testing_practices(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze testing practices"""
        
        practices = {
            "has_tests": False,
            "test_coverage_estimate": 0,
            "test_organization": False,
            "score": 0
        }
        
        test_files = 0
        code_files = 0
        
        for file_info in contents:
            file_name = file_info.get("name", "")
            file_path = file_info.get("path", "")
            
            if self._is_test_file(file_name, file_path):
                test_files += 1
            elif self._is_code_file(file_name, file_info.get("language", "")):
                code_files += 1
        
        if test_files > 0:
            practices["has_tests"] = True
            practices["score"] += 40
            
            # Estimate test coverage
            if code_files > 0:
                coverage_estimate = min((test_files / code_files) * 100, 100)
                practices["test_coverage_estimate"] = coverage_estimate
                practices["score"] += min(coverage_estimate * 0.4, 40)
            
            # Check test organization
            test_paths = [f.get("path", "") for f in contents if self._is_test_file(f.get("name", ""), f.get("path", ""))]
            if any("test/" in path or "__test__/" in path for path in test_paths):
                practices["test_organization"] = True
                practices["score"] += 20
        
        return practices
    
    def _analyze_ci_cd_practices(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze CI/CD practices"""
        
        practices = {
            "has_ci_config": False,
            "ci_platform": None,
            "automated_testing": False,
            "score": 0
        }
        
        file_names = [file_info.get("name", "") for file_info in contents]
        file_paths = [file_info.get("path", "") for file_info in contents]
        
        # Check for CI/CD configuration files
        ci_indicators = {
            "GitHub Actions": [".github/workflows/", "workflow.yml", "action.yml"],
            "GitLab CI": [".gitlab-ci.yml"],
            "Travis CI": [".travis.yml"],
            "CircleCI": [".circleci/config.yml"],
            "Jenkins": ["Jenkinsfile"]
        }
        
        for platform, indicators in ci_indicators.items():
            if any(indicator in " ".join(file_paths + file_names) for indicator in indicators):
                practices["has_ci_config"] = True
                practices["ci_platform"] = platform
                practices["score"] += 50
                break
        
        # Check for automated testing in CI
        if practices["has_ci_config"]:
            # Look for test commands in CI files
            ci_files = [f for f in contents if any(indicator in f.get("path", "") + f.get("name", "") 
                                                 for indicators in ci_indicators.values() 
                                                 for indicator in indicators)]
            
            for ci_file in ci_files:
                content = ci_file.get("content", "")
                if re.search(r'npm test|pytest|mvn test|go test|cargo test', content, re.IGNORECASE):
                    practices["automated_testing"] = True
                    practices["score"] += 30
                    break
        
        return practices
    
    def _analyze_security_practices(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze security practices"""
        
        practices = {
            "has_security_config": False,
            "dependency_scanning": False,
            "secrets_management": False,
            "security_score": 100
        }
        
        file_names = [file_info.get("name", "") for file_info in contents]
        all_content = " ".join([file_info.get("content", "") for file_info in contents])
        
        # Check for security configuration
        security_files = [".gitignore", "security.md", ".env.example"]
        if any(sec_file in file_names for sec_file in security_files):
            practices["has_security_config"] = True
        
        # Check for dependency scanning
        if any(dep_file in file_names for dep_file in ["package-lock.json", "requirements.txt", "Pipfile.lock"]):
            practices["dependency_scanning"] = True
        
        # Check secrets management (no hardcoded secrets)
        secret_patterns = [r'password\s*=\s*["\'][^"\']+["\']', r'api_key\s*=\s*["\'][^"\']+["\']']
        has_secrets = any(re.search(pattern, all_content, re.IGNORECASE) for pattern in secret_patterns)
        
        if not has_secrets:
            practices["secrets_management"] = True
        else:
            practices["security_score"] -= 30
        
        return practices
    
    def _analyze_documentation_practices(self, contents: List[Dict[str, Any]], repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze documentation practices"""
        
        practices = {
            "has_readme": False,
            "has_api_docs": False,
            "inline_documentation": False,
            "documentation_quality": 0,
            "score": 0
        }
        
        file_names = [file_info.get("name", "").lower() for file_info in contents]
        
        # Check for README
        if any("readme" in name for name in file_names):
            practices["has_readme"] = True
            practices["score"] += 30
        
        # Check for API documentation
        if any("api" in name or "docs" in name for name in file_names):
            practices["has_api_docs"] = True
            practices["score"] += 20
        
        # Check inline documentation
        code_files_with_docs = 0
        total_code_files = 0
        
        for file_info in contents:
            if self._is_code_file(file_info.get("name", ""), file_info.get("language", "")):
                total_code_files += 1
                if self._has_adequate_docstrings(file_info.get("content", ""), file_info.get("language", "")):
                    code_files_with_docs += 1
        
        if total_code_files > 0 and code_files_with_docs / total_code_files > 0.5:
            practices["inline_documentation"] = True
            practices["score"] += 30
        
        # Calculate documentation quality
        practices["documentation_quality"] = practices["score"] / 80 * 100 if practices["score"] > 0 else 0
        
        return practices
    
    def _analyze_version_control_practices(self, commit_history: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze version control practices"""
        
        practices = {
            "regular_commits": False,
            "good_commit_messages": False,
            "branching_strategy": False,
            "score": 0
        }
        
        commits = commit_history.get("commits", [])
        
        if len(commits) >= 10:
            practices["regular_commits"] = True
            practices["score"] += 30
        
        # Check commit message quality
        if commits:
            good_messages = 0
            for commit in commits:
                message = commit.get("message", "")
                if len(message) > 20 and not any(bad_word in message.lower() 
                                               for bad_word in ["wip", "temp", "fix", "update"]):
                    good_messages += 1
            
            if good_messages / len(commits) > 0.5:
                practices["good_commit_messages"] = True
                practices["score"] += 40
        
        # Simple branching strategy check (if we have merge commits)
        merge_commits = [c for c in commits if "merge" in c.get("message", "").lower()]
        if len(merge_commits) > 0:
            practices["branching_strategy"] = True
            practices["score"] += 30
        
        return practices
    
    def _calculate_best_practices_score(self, analysis: Dict[str, Any]) -> float:
        """Calculate overall best practices score"""
        
        scores = []
        
        for category, practices in analysis.items():
            if isinstance(practices, dict) and "score" in practices:
                scores.append(practices["score"])
        
        return statistics.mean(scores) if scores else 0