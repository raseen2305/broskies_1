import re
import json
from typing import Dict, List, Any, Set, Tuple
from collections import defaultdict, Counter
import logging

logger = logging.getLogger(__name__)

class TechnologyDetector:
    """
    Advanced technology stack detection and analysis service
    """
    
    def __init__(self):
        self.framework_patterns = self._initialize_framework_patterns()
        self.library_patterns = self._initialize_library_patterns()
        self.tool_patterns = self._initialize_tool_patterns()
        self.language_extensions = self._initialize_language_extensions()
        self.dependency_files = self._initialize_dependency_files()
    
    def analyze_technology_stack(self, contents: List[Dict[str, Any]], 
                               repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive technology stack analysis
        """
        
        analysis = {
            "languages": self._analyze_languages(contents, repo_data),
            "frameworks": self._detect_frameworks(contents),
            "libraries": self._detect_libraries(contents),
            "tools": self._detect_tools(contents),
            "databases": self._detect_databases(contents),
            "cloud_services": self._detect_cloud_services(contents),
            "development_tools": self._detect_development_tools(contents),
            "architecture_patterns": self._detect_architecture_patterns(contents),
            "technology_trends": self._analyze_technology_trends(contents),
            "skill_level_assessment": {}
        }
        
        # Calculate skill levels
        analysis["skill_level_assessment"] = self._assess_skill_levels(analysis)
        
        # Generate technology recommendations
        analysis["recommendations"] = self._generate_tech_recommendations(analysis)
        
        return analysis
    
    def _initialize_framework_patterns(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize framework detection patterns"""
        return {
            "web_frameworks": {
                "React": [
                    r'import.*react', r'from\s+["\']react["\']', r'React\.', r'jsx?$',
                    r'useState|useEffect|useContext', r'<.*/>.*</.*>'
                ],
                "Vue": [
                    r'import.*vue', r'from\s+["\']vue["\']', r'Vue\.', r'\.vue$',
                    r'v-if|v-for|v-model', r'<template>|<script>|<style>'
                ],
                "Angular": [
                    r'@angular', r'import.*@angular', r'@Component|@Injectable',
                    r'ngOnInit|ngOnDestroy', r'\.component\.ts$|\.service\.ts$'
                ],
                "Django": [
                    r'from django', r'import django', r'django\.', r'models\.Model',
                    r'HttpResponse|render', r'urls\.py|views\.py|models\.py'
                ],
                "Flask": [
                    r'from flask', r'import flask', r'Flask\(__name__\)',
                    r'@app\.route', r'render_template'
                ],
                "Express": [
                    r'express\(\)', r'require\(["\']express["\']', r'app\.get|app\.post',
                    r'app\.listen', r'middleware'
                ],
                "Spring": [
                    r'@SpringBootApplication', r'@RestController', r'@Service',
                    r'springframework', r'@Autowired'
                ],
                "Laravel": [
                    r'use Illuminate', r'Eloquent', r'Artisan', r'Blade',
                    r'Route::', r'composer\.json.*laravel'
                ],
                "Ruby on Rails": [
                    r'Rails\.application', r'ActiveRecord', r'ActionController',
                    r'Gemfile.*rails', r'config/routes\.rb'
                ]
            },
            "mobile_frameworks": {
                "React Native": [
                    r'react-native', r'import.*react-native', r'StyleSheet\.create',
                    r'View|Text|ScrollView', r'Platform\.OS'
                ],
                "Flutter": [
                    r'import.*flutter', r'StatelessWidget|StatefulWidget',
                    r'pubspec\.yaml', r'dart$', r'MaterialApp'
                ],
                "Xamarin": [
                    r'Xamarin', r'using Xamarin', r'\.xaml$', r'DependencyService'
                ],
                "Ionic": [
                    r'@ionic', r'ionic-angular', r'ion-', r'ionic\.config\.json'
                ]
            },
            "backend_frameworks": {
                "Node.js": [
                    r'require\(', r'module\.exports', r'process\.', r'__dirname',
                    r'package\.json', r'npm|yarn'
                ],
                "ASP.NET": [
                    r'using System', r'namespace.*Controllers', r'\.csproj$',
                    r'IActionResult', r'[HttpGet]|[HttpPost]'
                ],
                "FastAPI": [
                    r'from fastapi', r'FastAPI\(\)', r'@app\.(get|post|put|delete)',
                    r'Pydantic', r'uvicorn'
                ],
                "Gin": [
                    r'gin-gonic/gin', r'gin\.Default\(\)', r'c\.JSON',
                    r'router\.GET|router\.POST'
                ]
            }
        }
    
    def _initialize_library_patterns(self) -> Dict[str, List[str]]:
        """Initialize library detection patterns"""
        return {
            "data_science": [
                r'pandas|numpy|scipy|matplotlib|seaborn|sklearn|tensorflow|pytorch',
                r'jupyter|ipython|anaconda', r'import (pandas|numpy|scipy) as',
                r'from sklearn', r'import tensorflow as tf'
            ],
            "testing": [
                r'jest|mocha|chai|jasmine|pytest|unittest|rspec|minitest',
                r'describe\(|it\(|test\(|expect\(', r'@Test|@Before|@After',
                r'assert|should|expect'
            ],
            "database": [
                r'mongoose|sequelize|typeorm|prisma|sqlalchemy|hibernate',
                r'mysql|postgresql|mongodb|redis|sqlite', r'knex|bookshelf'
            ],
            "ui_libraries": [
                r'bootstrap|tailwind|material-ui|ant-design|semantic-ui',
                r'styled-components|emotion|sass|less', r'jquery|lodash|underscore'
            ],
            "state_management": [
                r'redux|mobx|vuex|ngrx|recoil|zustand', r'useReducer|createStore',
                r'@reduxjs/toolkit'
            ],
            "build_tools": [
                r'webpack|rollup|parcel|vite|gulp|grunt', r'babel|typescript',
                r'eslint|prettier|husky'
            ]
        }
    
    def _initialize_tool_patterns(self) -> Dict[str, List[str]]:
        """Initialize development tools patterns"""
        return {
            "version_control": [r'\.git', r'\.gitignore', r'\.gitmodules'],
            "containerization": [r'Dockerfile', r'docker-compose', r'\.dockerignore'],
            "ci_cd": [
                r'\.github/workflows', r'\.travis\.yml', r'\.circleci',
                r'jenkins|gitlab-ci|azure-pipelines'
            ],
            "package_managers": [
                r'package\.json|yarn\.lock', r'requirements\.txt|Pipfile',
                r'pom\.xml|build\.gradle', r'Cargo\.toml|composer\.json'
            ],
            "linting": [r'\.eslintrc|\.pylintrc|\.rubocop', r'tslint|jshint'],
            "testing_tools": [r'jest\.config|pytest\.ini|phpunit\.xml']
        }
    
    def _initialize_language_extensions(self) -> Dict[str, List[str]]:
        """Initialize language file extensions"""
        return {
            "JavaScript": [".js", ".jsx", ".mjs"],
            "TypeScript": [".ts", ".tsx"],
            "Python": [".py", ".pyw", ".pyi"],
            "Java": [".java"],
            "C++": [".cpp", ".cc", ".cxx", ".c++", ".hpp", ".h"],
            "C#": [".cs"],
            "Go": [".go"],
            "Rust": [".rs"],
            "Ruby": [".rb"],
            "PHP": [".php"],
            "Swift": [".swift"],
            "Kotlin": [".kt", ".kts"],
            "Scala": [".scala"],
            "R": [".r", ".R"],
            "MATLAB": [".m"],
            "Shell": [".sh", ".bash", ".zsh"],
            "PowerShell": [".ps1"],
            "HTML": [".html", ".htm"],
            "CSS": [".css", ".scss", ".sass", ".less"],
            "SQL": [".sql"],
            "Dart": [".dart"],
            "Lua": [".lua"],
            "Perl": [".pl", ".pm"]
        }
    
    def _initialize_dependency_files(self) -> Dict[str, str]:
        """Initialize dependency file mappings"""
        return {
            "package.json": "Node.js/JavaScript",
            "requirements.txt": "Python",
            "Pipfile": "Python",
            "setup.py": "Python",
            "pom.xml": "Java/Maven",
            "build.gradle": "Java/Gradle",
            "Cargo.toml": "Rust",
            "composer.json": "PHP",
            "Gemfile": "Ruby",
            "go.mod": "Go",
            "pubspec.yaml": "Dart/Flutter",
            "project.clj": "Clojure",
            "mix.exs": "Elixir"
        }
    
    def _analyze_languages(self, contents: List[Dict[str, Any]], 
                          repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze programming languages used"""
        
        language_stats = defaultdict(lambda: {
            "files": 0,
            "lines": 0,
            "bytes": 0,
            "percentage": 0.0,
            "proficiency_indicators": [],
            "frameworks_used": [],
            "complexity_score": 0.0
        })
        
        total_lines = 0
        total_bytes = 0
        
        # Analyze from file contents
        for file_info in contents:
            filename = file_info.get("name", "")
            content = file_info.get("content", "")
            language = file_info.get("language", self._detect_language_from_extension(filename))
            
            if not content or language == "Unknown":
                continue
            
            lines = len(content.split('\n'))
            bytes_count = len(content.encode('utf-8'))
            
            language_stats[language]["files"] += 1
            language_stats[language]["lines"] += lines
            language_stats[language]["bytes"] += bytes_count
            
            total_lines += lines
            total_bytes += bytes_count
            
            # Analyze language-specific features
            features = self._analyze_language_features(content, language)
            language_stats[language]["proficiency_indicators"].extend(features)
            
            # Detect frameworks for this language
            frameworks = self._detect_language_frameworks(content, language)
            language_stats[language]["frameworks_used"].extend(frameworks)
        
        # Use GitHub API language data if available
        github_languages = repo_data.get("languages", {})
        for lang, bytes_count in github_languages.items():
            if lang not in language_stats:
                language_stats[lang] = {
                    "files": 0, "lines": 0, "bytes": bytes_count,
                    "percentage": 0.0, "proficiency_indicators": [],
                    "frameworks_used": [], "complexity_score": 0.0
                }
            else:
                language_stats[lang]["bytes"] = max(language_stats[lang]["bytes"], bytes_count)
            
            total_bytes = max(total_bytes, sum(github_languages.values()))
        
        # Calculate percentages and proficiency
        for language, stats in language_stats.items():
            if total_bytes > 0:
                stats["percentage"] = (stats["bytes"] / total_bytes) * 100
            
            # Assess proficiency based on usage and features
            stats["proficiency_level"] = self._assess_language_proficiency(stats)
            stats["complexity_score"] = self._calculate_language_complexity(stats)
            
            # Remove duplicates
            stats["proficiency_indicators"] = list(set(stats["proficiency_indicators"]))
            stats["frameworks_used"] = list(set(stats["frameworks_used"]))
        
        # Sort by usage
        sorted_languages = dict(sorted(language_stats.items(), 
                                     key=lambda x: x[1]["percentage"], reverse=True))
        
        return {
            "languages": sorted_languages,
            "primary_language": max(sorted_languages.keys(), 
                                  key=lambda k: sorted_languages[k]["percentage"]) if sorted_languages else "Unknown",
            "language_count": len(sorted_languages),
            "total_lines": total_lines,
            "total_bytes": total_bytes,
            "language_diversity_score": self._calculate_diversity_score(sorted_languages)
        }    

    def _detect_frameworks(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detect frameworks used in the project"""
        
        detected_frameworks = defaultdict(lambda: {
            "confidence": 0.0,
            "evidence": [],
            "category": "",
            "files": []
        })
        
        all_content = ""
        for file_info in contents:
            content = file_info.get("content", "")
            filename = file_info.get("name", "")
            all_content += content + "\n"
            
            # Check each framework category
            for category, frameworks in self.framework_patterns.items():
                for framework, patterns in frameworks.items():
                    confidence = 0
                    evidence = []
                    
                    for pattern in patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
                        if matches:
                            confidence += len(matches) * 10
                            evidence.extend(matches[:3])  # Limit evidence
                    
                    if confidence > 0:
                        detected_frameworks[framework]["confidence"] += confidence
                        detected_frameworks[framework]["evidence"].extend(evidence)
                        detected_frameworks[framework]["category"] = category
                        detected_frameworks[framework]["files"].append(filename)
        
        # Filter and normalize
        filtered_frameworks = {}
        for framework, data in detected_frameworks.items():
            if data["confidence"] >= 20:  # Minimum confidence threshold
                data["confidence"] = min(data["confidence"], 100)  # Cap at 100
                data["evidence"] = list(set(data["evidence"][:5]))  # Unique, limited evidence
                data["files"] = list(set(data["files"][:10]))  # Unique, limited files
                filtered_frameworks[framework] = data
        
        return filtered_frameworks
    
    def _detect_libraries(self, contents: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Detect libraries and dependencies"""
        
        detected_libraries = defaultdict(set)
        
        for file_info in contents:
            content = file_info.get("content", "")
            filename = file_info.get("name", "")
            
            # Check dependency files
            if filename in self.dependency_files:
                libs = self._parse_dependency_file(content, filename)
                for category, lib_list in libs.items():
                    detected_libraries[category].update(lib_list)
            
            # Check import statements and usage patterns
            for category, patterns in self.library_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        detected_libraries[category].add(pattern.split('|')[0])  # First alternative
        
        # Convert sets to sorted lists
        return {category: sorted(list(libs)) for category, libs in detected_libraries.items()}
    
    def _detect_tools(self, contents: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Detect development tools and configurations"""
        
        detected_tools = defaultdict(set)
        
        for file_info in contents:
            filename = file_info.get("name", "")
            filepath = file_info.get("path", "")
            content = file_info.get("content", "")
            
            for tool_category, patterns in self.tool_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, filepath + "/" + filename, re.IGNORECASE):
                        detected_tools[tool_category].add(pattern)
                    elif re.search(pattern, content, re.IGNORECASE):
                        detected_tools[tool_category].add(pattern)
        
        return {category: sorted(list(tools)) for category, tools in detected_tools.items()}
    
    def _detect_databases(self, contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect database technologies"""
        
        database_patterns = {
            "MongoDB": [r'mongodb|mongoose|mongo', r'db\.collection', r'ObjectId'],
            "PostgreSQL": [r'postgresql|postgres|psycopg2', r'SELECT.*FROM', r'pg_'],
            "MySQL": [r'mysql|pymysql', r'SELECT.*FROM.*WHERE', r'mysql_'],
            "SQLite": [r'sqlite3?', r'\.db$|\.sqlite$'],
            "Redis": [r'redis', r'HSET|HGET|LPUSH', r'redis-py'],
            "Elasticsearch": [r'elasticsearch', r'es\.search', r'@elastic'],
            "Firebase": [r'firebase', r'firestore', r'firebase-admin'],
            "DynamoDB": [r'dynamodb', r'boto3.*dynamodb', r'aws-sdk.*dynamodb']
        }
        
        detected_dbs = []
        
        for db_name, patterns in database_patterns.items():
            confidence = 0
            evidence = []
            
            for file_info in contents:
                content = file_info.get("content", "")
                filename = file_info.get("name", "")
                
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        confidence += len(matches) * 5
                        evidence.extend(matches[:2])
            
            if confidence >= 10:
                detected_dbs.append({
                    "name": db_name,
                    "confidence": min(confidence, 100),
                    "evidence": list(set(evidence))[:3],
                    "type": self._get_database_type(db_name)
                })
        
        return sorted(detected_dbs, key=lambda x: x["confidence"], reverse=True)
    
    def _detect_cloud_services(self, contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect cloud services and platforms"""
        
        cloud_patterns = {
            "AWS": [r'aws-sdk|boto3|amazonaws', r'lambda_function|handler', r's3|ec2|rds'],
            "Google Cloud": [r'google-cloud|gcp', r'@google-cloud', r'googleapis'],
            "Azure": [r'azure|@azure', r'microsoft\.azure', r'azurewebsites'],
            "Heroku": [r'heroku', r'Procfile', r'heroku-postbuild'],
            "Vercel": [r'vercel', r'now\.json', r'@vercel'],
            "Netlify": [r'netlify', r'_redirects|netlify\.toml'],
            "Docker": [r'Dockerfile|docker-compose', r'FROM.*:|RUN.*apt-get'],
            "Kubernetes": [r'kubectl|kubernetes', r'apiVersion.*v1', r'kind:.*Pod|Service']
        }
        
        detected_services = []
        
        for service_name, patterns in cloud_patterns.items():
            confidence = 0
            evidence = []
            
            for file_info in contents:
                content = file_info.get("content", "")
                filename = file_info.get("name", "")
                
                for pattern in patterns:
                    if re.search(pattern, content + filename, re.IGNORECASE):
                        confidence += 15
                        evidence.append(pattern)
            
            if confidence >= 15:
                detected_services.append({
                    "name": service_name,
                    "confidence": min(confidence, 100),
                    "evidence": list(set(evidence))[:3],
                    "category": self._get_cloud_category(service_name)
                })
        
        return sorted(detected_services, key=lambda x: x["confidence"], reverse=True)
    
    def _detect_development_tools(self, contents: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Detect development and build tools"""
        
        dev_tools = {
            "bundlers": ["webpack", "rollup", "parcel", "vite", "esbuild"],
            "transpilers": ["babel", "typescript", "coffeescript"],
            "linters": ["eslint", "pylint", "rubocop", "golint", "tslint"],
            "formatters": ["prettier", "black", "gofmt", "rustfmt"],
            "test_runners": ["jest", "mocha", "pytest", "rspec", "go test"],
            "task_runners": ["gulp", "grunt", "npm scripts", "make"],
            "monitors": ["nodemon", "watchdog", "fswatch"]
        }
        
        detected_tools = defaultdict(list)
        
        for file_info in contents:
            content = file_info.get("content", "")
            filename = file_info.get("name", "")
            
            for category, tools in dev_tools.items():
                for tool in tools:
                    if (tool.lower() in content.lower() or 
                        tool.lower() in filename.lower()):
                        detected_tools[category].append(tool)
        
        # Remove duplicates and sort
        return {category: sorted(list(set(tools))) 
                for category, tools in detected_tools.items() if tools}
    
    def _detect_architecture_patterns(self, contents: List[Dict[str, Any]]) -> List[str]:
        """Detect architectural patterns and design patterns"""
        
        patterns = {
            "MVC": [r'models?/', r'views?/', r'controllers?/', r'Model|View|Controller'],
            "MVP": [r'presenters?/', r'Presenter'],
            "MVVM": [r'viewmodels?/', r'ViewModel'],
            "Microservices": [r'docker-compose.*services', r'api/v\d+', r'service\.'],
            "REST API": [r'@app\.route|@RestController', r'GET|POST|PUT|DELETE.*/', r'api/'],
            "GraphQL": [r'graphql', r'query|mutation|subscription', r'@Query|@Mutation'],
            "Event-Driven": [r'event|Event', r'publish|subscribe', r'EventEmitter'],
            "Layered": [r'layers?/', r'business|service|data.*layer'],
            "Repository Pattern": [r'repository|Repository', r'interface.*Repository'],
            "Factory Pattern": [r'factory|Factory', r'create.*\(\)'],
            "Observer Pattern": [r'observer|Observer', r'notify|update'],
            "Singleton": [r'singleton|Singleton', r'getInstance']
        }
        
        detected_patterns = []
        all_content = ""
        all_filenames = []
        
        for file_info in contents:
            all_content += file_info.get("content", "") + "\n"
            all_filenames.append(file_info.get("path", "") + "/" + file_info.get("name", ""))
        
        all_text = all_content + " ".join(all_filenames)
        
        for pattern_name, indicators in patterns.items():
            confidence = 0
            for indicator in indicators:
                matches = len(re.findall(indicator, all_text, re.IGNORECASE))
                confidence += matches
            
            if confidence >= 2:  # At least 2 indicators
                detected_patterns.append(pattern_name)
        
        return detected_patterns
    
    def _analyze_technology_trends(self, contents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze technology trends and modernity"""
        
        modern_indicators = {
            "modern_js": [r'const |let ', r'=>', r'async/await', r'import.*from'],
            "modern_python": [r'f".*{.*}"', r'async def', r'type.*:', r'dataclass'],
            "modern_java": [r'var ', r'lambda', r'Stream\.', r'Optional\.'],
            "modern_css": [r'grid|flexbox', r'css.*variables', r'@media'],
            "modern_practices": [r'\.test\.|\.spec\.', r'README\.md', r'\.gitignore']
        }
        
        trend_scores = {}
        total_files = len(contents)
        
        for trend, patterns in modern_indicators.items():
            score = 0
            for file_info in contents:
                content = file_info.get("content", "")
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        score += 1
                        break  # Count each file only once per trend
            
            trend_scores[trend] = (score / max(total_files, 1)) * 100
        
        return {
            "trend_scores": trend_scores,
            "modernity_score": sum(trend_scores.values()) / len(trend_scores) if trend_scores else 0,
            "is_modern": sum(trend_scores.values()) / len(trend_scores) > 30 if trend_scores else False
        }    
 
    def _assess_skill_levels(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess skill levels based on technology usage"""
        
        skill_assessment = {}
        languages = analysis.get("languages", {}).get("languages", {})
        
        for language, stats in languages.items():
            skill_level = "Beginner"
            skill_score = 0
            
            # Base score from usage percentage
            percentage = stats.get("percentage", 0)
            if percentage >= 50:
                skill_score += 40
            elif percentage >= 20:
                skill_score += 25
            elif percentage >= 5:
                skill_score += 15
            else:
                skill_score += 5
            
            # Bonus for advanced features
            features = stats.get("proficiency_indicators", [])
            skill_score += min(len(features) * 5, 30)
            
            # Bonus for frameworks
            frameworks = stats.get("frameworks_used", [])
            skill_score += min(len(frameworks) * 10, 30)
            
            # Determine skill level
            if skill_score >= 80:
                skill_level = "Expert"
            elif skill_score >= 60:
                skill_level = "Advanced"
            elif skill_score >= 40:
                skill_level = "Intermediate"
            elif skill_score >= 20:
                skill_level = "Beginner"
            else:
                skill_level = "Novice"
            
            skill_assessment[language] = {
                "level": skill_level,
                "score": skill_score,
                "evidence": {
                    "usage_percentage": percentage,
                    "advanced_features": len(features),
                    "frameworks_known": len(frameworks)
                }
            }
        
        return skill_assessment
    
    def _generate_tech_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate technology learning recommendations"""
        
        recommendations = []
        languages = analysis.get("languages", {}).get("languages", {})
        primary_lang = analysis.get("languages", {}).get("primary_language", "")
        
        # Language-specific recommendations
        if primary_lang == "JavaScript":
            if "React" not in str(analysis.get("frameworks", {})):
                recommendations.append({
                    "category": "Frontend Framework",
                    "technology": "React",
                    "priority": "High",
                    "reason": "Most popular JavaScript frontend framework",
                    "learning_path": ["JSX", "Components", "Hooks", "State Management"]
                })
        
        elif primary_lang == "Python":
            if "Django" not in str(analysis.get("frameworks", {})) and "Flask" not in str(analysis.get("frameworks", {})):
                recommendations.append({
                    "category": "Web Framework",
                    "technology": "Django or Flask",
                    "priority": "High",
                    "reason": "Essential for Python web development",
                    "learning_path": ["Routing", "Templates", "ORM", "Authentication"]
                })
        
        # General recommendations based on missing technologies
        detected_dbs = [db["name"] for db in analysis.get("databases", [])]
        if not detected_dbs:
            recommendations.append({
                "category": "Database",
                "technology": "PostgreSQL or MongoDB",
                "priority": "Medium",
                "reason": "Database knowledge is essential for most applications",
                "learning_path": ["Basic queries", "Schema design", "Indexing", "Optimization"]
            })
        
        # Cloud recommendations
        cloud_services = [service["name"] for service in analysis.get("cloud_services", [])]
        if not cloud_services:
            recommendations.append({
                "category": "Cloud Platform",
                "technology": "AWS or Google Cloud",
                "priority": "Medium",
                "reason": "Cloud skills are increasingly important",
                "learning_path": ["Basic services", "Deployment", "Scaling", "Monitoring"]
            })
        
        # Testing recommendations
        dev_tools = analysis.get("development_tools", {})
        if "test_runners" not in dev_tools:
            recommendations.append({
                "category": "Testing",
                "technology": f"Testing framework for {primary_lang}",
                "priority": "High",
                "reason": "Testing is crucial for code quality",
                "learning_path": ["Unit tests", "Integration tests", "Mocking", "TDD"]
            })
        
        return recommendations
    
    # Helper methods
    def _detect_language_from_extension(self, filename: str) -> str:
        """Detect language from file extension"""
        if '.' not in filename:
            return "Unknown"
        
        extension = "." + filename.split('.')[-1].lower()
        
        for language, extensions in self.language_extensions.items():
            if extension in extensions:
                return language
        
        return "Unknown"
    
    def _analyze_language_features(self, content: str, language: str) -> List[str]:
        """Analyze advanced language features used"""
        
        features = []
        
        if language == "Python":
            if re.search(r'async def|await ', content):
                features.append("Async/Await")
            if re.search(r'f".*{.*}"', content):
                features.append("F-strings")
            if re.search(r'@\w+', content):
                features.append("Decorators")
            if re.search(r'\[.*for.*in.*\]', content):
                features.append("List Comprehensions")
            if re.search(r'with\s+\w+.*:', content):
                features.append("Context Managers")
        
        elif language == "JavaScript":
            if re.search(r'=>', content):
                features.append("Arrow Functions")
            if re.search(r'async\s+function|await\s+', content):
                features.append("Async/Await")
            if re.search(r'const\s*{[^}]+}\s*=', content):
                features.append("Destructuring")
            if re.search(r'`[^`]*\$\{[^}]+\}[^`]*`', content):
                features.append("Template Literals")
            if re.search(r'\.map\(|\.filter\(|\.reduce\(', content):
                features.append("Array Methods")
        
        elif language == "Java":
            if re.search(r'->', content):
                features.append("Lambda Expressions")
            if re.search(r'Stream\.<|\.stream\(\)', content):
                features.append("Streams API")
            if re.search(r'Optional\.<|Optional\.of', content):
                features.append("Optional")
            if re.search(r'@\w+', content):
                features.append("Annotations")
        
        return features
    
    def _detect_language_frameworks(self, content: str, language: str) -> List[str]:
        """Detect frameworks specific to a language"""
        
        frameworks = []
        
        if language == "JavaScript":
            if re.search(r'react|React', content, re.IGNORECASE):
                frameworks.append("React")
            if re.search(r'vue|Vue', content, re.IGNORECASE):
                frameworks.append("Vue")
            if re.search(r'angular|@angular', content, re.IGNORECASE):
                frameworks.append("Angular")
            if re.search(r'express|Express', content, re.IGNORECASE):
                frameworks.append("Express")
        
        elif language == "Python":
            if re.search(r'django|Django', content, re.IGNORECASE):
                frameworks.append("Django")
            if re.search(r'flask|Flask', content, re.IGNORECASE):
                frameworks.append("Flask")
            if re.search(r'fastapi|FastAPI', content, re.IGNORECASE):
                frameworks.append("FastAPI")
        
        return frameworks
    
    def _assess_language_proficiency(self, stats: Dict[str, Any]) -> str:
        """Assess proficiency level for a language"""
        
        percentage = stats.get("percentage", 0)
        features = len(stats.get("proficiency_indicators", []))
        frameworks = len(stats.get("frameworks_used", []))
        
        score = 0
        if percentage >= 50:
            score += 40
        elif percentage >= 20:
            score += 25
        elif percentage >= 5:
            score += 15
        
        score += min(features * 10, 30)
        score += min(frameworks * 15, 30)
        
        if score >= 80:
            return "Expert"
        elif score >= 60:
            return "Advanced"
        elif score >= 40:
            return "Intermediate"
        elif score >= 20:
            return "Beginner"
        else:
            return "Novice"
    
    def _calculate_language_complexity(self, stats: Dict[str, Any]) -> float:
        """Calculate complexity score for language usage"""
        
        base_score = stats.get("percentage", 0) * 0.5
        feature_bonus = len(stats.get("proficiency_indicators", [])) * 5
        framework_bonus = len(stats.get("frameworks_used", [])) * 10
        
        return min(base_score + feature_bonus + framework_bonus, 100)
    
    def _calculate_diversity_score(self, languages: Dict[str, Any]) -> float:
        """Calculate language diversity score"""
        
        if not languages:
            return 0.0
        
        # Shannon entropy for diversity
        total = sum(lang["percentage"] for lang in languages.values())
        if total == 0:
            return 0.0
        
        entropy = 0
        for lang_stats in languages.values():
            p = lang_stats["percentage"] / total
            if p > 0:
                entropy -= p * (p ** 0.5)  # Modified entropy
        
        # Normalize to 0-100 scale
        max_entropy = len(languages) ** 0.5 if len(languages) > 1 else 1
        return min((entropy / max_entropy) * 100, 100)
    
    def _parse_dependency_file(self, content: str, filename: str) -> Dict[str, List[str]]:
        """Parse dependency files to extract libraries"""
        
        dependencies = defaultdict(list)
        
        if filename == "package.json":
            try:
                data = json.loads(content)
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})
                
                dependencies["runtime"].extend(deps.keys())
                dependencies["development"].extend(dev_deps.keys())
            except:
                pass
        
        elif filename == "requirements.txt":
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    pkg = line.split('==')[0].split('>=')[0].split('<=')[0]
                    dependencies["python"].append(pkg)
        
        elif filename == "pom.xml":
            # Simple XML parsing for Maven dependencies
            deps = re.findall(r'<artifactId>([^<]+)</artifactId>', content)
            dependencies["java"].extend(deps)
        
        return dependencies
    
    def _get_database_type(self, db_name: str) -> str:
        """Get database type category"""
        
        sql_dbs = ["PostgreSQL", "MySQL", "SQLite"]
        nosql_dbs = ["MongoDB", "Redis", "DynamoDB"]
        search_dbs = ["Elasticsearch"]
        
        if db_name in sql_dbs:
            return "SQL"
        elif db_name in nosql_dbs:
            return "NoSQL"
        elif db_name in search_dbs:
            return "Search Engine"
        else:
            return "Other"
    
    def _get_cloud_category(self, service_name: str) -> str:
        """Get cloud service category"""
        
        platforms = ["AWS", "Google Cloud", "Azure"]
        deployment = ["Heroku", "Vercel", "Netlify"]
        containers = ["Docker", "Kubernetes"]
        
        if service_name in platforms:
            return "Cloud Platform"
        elif service_name in deployment:
            return "Deployment Platform"
        elif service_name in containers:
            return "Containerization"
        else:
            return "Cloud Service"