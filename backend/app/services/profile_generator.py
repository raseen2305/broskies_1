"""
Profile Generator Service

This service generates comprehensive developer profiles by analyzing GitHub repositories,
calculating scores, and providing personalized recommendations.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)

class ProfileGenerator:
    """Generate comprehensive developer profiles from repository analysis"""
    
    def __init__(self):
        self.skill_weights = {
            'primary_language': 0.3,
            'tech_diversity': 0.2,
            'project_complexity': 0.25,
            'activity_level': 0.15,
            'collaboration': 0.1
        }
    
    def generate_developer_profile(self, repositories: List[Dict[str, Any]], 
                                 user_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate a comprehensive developer profile from repository analysis
        
        Args:
            repositories: List of repository data with analysis
            user_data: Additional user information (optional)
            
        Returns:
            Comprehensive developer profile with scores, skills, and recommendations
        """
        
        if not repositories:
            return self._empty_profile()
        
        # Analyze repositories
        repo_analysis = self._analyze_repositories(repositories)
        
        # Calculate skill assessments
        skill_assessment = self._assess_skills(repositories, repo_analysis)
        
        # Generate technology roadmap
        tech_roadmap = self._generate_tech_roadmap(skill_assessment, repo_analysis)
        
        # Calculate overall scores
        overall_scores = self._calculate_overall_scores(repositories, repo_analysis, skill_assessment)
        
        # Generate insights and recommendations
        insights = self._generate_insights(repo_analysis, skill_assessment, overall_scores)
        
        # Compile comprehensive profile
        profile = {
            "profile_id": f"profile_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.utcnow().isoformat(),
            "user_data": user_data or {},
            "repository_analysis": repo_analysis,
            "skill_assessment": skill_assessment,
            "technology_roadmap": tech_roadmap,
            "overall_scores": overall_scores,
            "insights": insights,
            "profile_completeness": self._calculate_profile_completeness(repo_analysis, skill_assessment),
            "next_steps": self._suggest_next_steps(skill_assessment, overall_scores)
        }
        
        return profile
    
    def _analyze_repositories(self, repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze repository collection for patterns and metrics"""
        
        analysis = {
            "total_repositories": len(repositories),
            "active_repositories": 0,
            "primary_languages": [],
            "technology_usage": defaultdict(int),
            "project_types": defaultdict(int),
            "collaboration_metrics": {
                "total_stars": 0,
                "total_forks": 0,
                "total_watchers": 0,
                "avg_stars_per_repo": 0,
                "most_starred_repo": None
            },
            "activity_metrics": {
                "recent_activity_count": 0,
                "total_commits": 0,
                "avg_repo_age_days": 0,
                "last_activity": None
            },
            "quality_indicators": {
                "repos_with_readme": 0,
                "repos_with_license": 0,
                "repos_with_tests": 0,
                "repos_with_ci": 0,
                "avg_repo_size": 0
            }
        }
        
        # Language statistics
        language_stats = defaultdict(lambda: {"repos": 0, "total_size": 0, "stars": 0})
        
        # Recent activity cutoff (6 months)
        recent_cutoff = datetime.now() - timedelta(days=180)
        
        total_size = 0
        total_age_days = 0
        most_starred = {"stars": 0, "repo": None}
        
        for repo in repositories:
            # Basic metrics
            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            watchers = repo.get("watchers_count", 0)
            size = repo.get("size", 0)
            
            analysis["collaboration_metrics"]["total_stars"] += stars
            analysis["collaboration_metrics"]["total_forks"] += forks
            analysis["collaboration_metrics"]["total_watchers"] += watchers
            
            total_size += size
            
            # Track most starred repository
            if stars > most_starred["stars"]:
                most_starred = {"stars": stars, "repo": repo.get("name", "Unknown")}
            
            # Language analysis
            primary_lang = repo.get("language")
            if primary_lang:
                language_stats[primary_lang]["repos"] += 1
                language_stats[primary_lang]["total_size"] += size
                language_stats[primary_lang]["stars"] += stars
            
            # Activity analysis
            try:
                updated_at = datetime.fromisoformat(repo.get("updated_at", "").replace('Z', '+00:00'))
                created_at = datetime.fromisoformat(repo.get("created_at", "").replace('Z', '+00:00'))
                
                # Check if recently active
                if updated_at.replace(tzinfo=None) > recent_cutoff:
                    analysis["activity_metrics"]["recent_activity_count"] += 1
                
                # Calculate repository age
                repo_age = (datetime.now() - created_at.replace(tzinfo=None)).days
                total_age_days += repo_age
                
                # Track latest activity
                if (analysis["activity_metrics"]["last_activity"] is None or 
                    updated_at > datetime.fromisoformat(analysis["activity_metrics"]["last_activity"])):
                    analysis["activity_metrics"]["last_activity"] = updated_at.isoformat()
                    
            except (ValueError, TypeError):
                pass
            
            # Quality indicators
            if repo.get("has_readme"):
                analysis["quality_indicators"]["repos_with_readme"] += 1
            if repo.get("has_license"):
                analysis["quality_indicators"]["repos_with_license"] += 1
            if repo.get("has_tests"):
                analysis["quality_indicators"]["repos_with_tests"] += 1
            
            # Project type classification
            topics = repo.get("topics", [])
            if any(topic in ["web", "website", "frontend", "react", "vue", "angular"] for topic in topics):
                analysis["project_types"]["web_development"] += 1
            elif any(topic in ["api", "backend", "server", "microservice"] for topic in topics):
                analysis["project_types"]["backend_development"] += 1
            elif any(topic in ["mobile", "android", "ios", "react-native", "flutter"] for topic in topics):
                analysis["project_types"]["mobile_development"] += 1
            elif any(topic in ["data", "ml", "ai", "machine-learning", "data-science"] for topic in topics):
                analysis["project_types"]["data_science"] += 1
            else:
                analysis["project_types"]["general"] += 1
        
        # Calculate averages and derived metrics
        total_repos = len(repositories)
        if total_repos > 0:
            analysis["collaboration_metrics"]["avg_stars_per_repo"] = analysis["collaboration_metrics"]["total_stars"] / total_repos
            analysis["collaboration_metrics"]["most_starred_repo"] = most_starred["repo"]
            analysis["quality_indicators"]["avg_repo_size"] = total_size / total_repos
            analysis["activity_metrics"]["avg_repo_age_days"] = total_age_days / total_repos
        
        # Process language statistics
        sorted_languages = sorted(language_stats.items(), key=lambda x: x[1]["repos"], reverse=True)
        for lang, stats in sorted_languages[:10]:  # Top 10 languages
            analysis["primary_languages"].append({
                "language": lang,
                "repositories": stats["repos"],
                "total_size": stats["total_size"],
                "stars": stats["stars"],
                "percentage": round((stats["repos"] / total_repos) * 100, 1) if total_repos > 0 else 0
            })
        
        return analysis
    
    def _assess_skills(self, repositories: List[Dict[str, Any]], 
                      repo_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Assess developer skills based on repository analysis"""
        
        skills = {
            "programming_languages": {},
            "frameworks_and_tools": {},
            "development_practices": {},
            "domain_expertise": {},
            "skill_level_summary": {
                "beginner_indicators": 0,
                "intermediate_indicators": 0,
                "advanced_indicators": 0,
                "expert_indicators": 0
            }
        }
        
        total_repos = len(repositories)
        
        # Programming Language Proficiency
        for lang_data in repo_analysis["primary_languages"]:
            lang = lang_data["language"]
            repo_count = lang_data["repositories"]
            percentage = lang_data["percentage"]
            
            # Determine proficiency level
            if percentage >= 40 and repo_count >= 5:
                proficiency = "Expert"
                skills["skill_level_summary"]["expert_indicators"] += 1
            elif percentage >= 20 and repo_count >= 3:
                proficiency = "Advanced"
                skills["skill_level_summary"]["advanced_indicators"] += 1
            elif percentage >= 10 and repo_count >= 2:
                proficiency = "Intermediate"
                skills["skill_level_summary"]["intermediate_indicators"] += 1
            else:
                proficiency = "Beginner"
                skills["skill_level_summary"]["beginner_indicators"] += 1
            
            skills["programming_languages"][lang] = {
                "proficiency": proficiency,
                "repositories": repo_count,
                "usage_percentage": percentage,
                "total_stars": lang_data["stars"],
                "confidence_score": min(100, (repo_count * 20) + (percentage * 2))
            }
        
        # Development Practices Assessment
        quality_metrics = repo_analysis["quality_indicators"]
        
        practices = {
            "documentation": (quality_metrics["repos_with_readme"] / total_repos) * 100 if total_repos > 0 else 0,
            "licensing": (quality_metrics["repos_with_license"] / total_repos) * 100 if total_repos > 0 else 0,
            "testing": (quality_metrics["repos_with_tests"] / total_repos) * 100 if total_repos > 0 else 0,
            "version_control": 100,  # Using GitHub implies version control
            "collaboration": min(100, repo_analysis["collaboration_metrics"]["total_forks"] * 10)
        }
        
        skills["development_practices"] = practices
        
        # Domain Expertise
        project_types = repo_analysis["project_types"]
        total_projects = sum(project_types.values())
        
        if total_projects > 0:
            for domain, count in project_types.items():
                percentage = (count / total_projects) * 100
                if percentage >= 30:
                    expertise_level = "Specialized"
                elif percentage >= 15:
                    expertise_level = "Experienced"
                else:
                    expertise_level = "Familiar"
                
                skills["domain_expertise"][domain] = {
                    "level": expertise_level,
                    "projects": count,
                    "percentage": round(percentage, 1)
                }
        
        return skills
    
    def _generate_tech_roadmap(self, skill_assessment: Dict[str, Any], 
                              repo_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized technology learning roadmap"""
        
        roadmap = {
            "current_level": "Intermediate",  # Will be calculated
            "recommended_paths": [],
            "skill_gaps": [],
            "next_milestones": [],
            "learning_priorities": {
                "high": [],
                "medium": [],
                "low": []
            }
        }
        
        # Determine current overall level
        skill_summary = skill_assessment["skill_level_summary"]
        if skill_summary["expert_indicators"] >= 2:
            roadmap["current_level"] = "Expert"
        elif skill_summary["advanced_indicators"] >= 2:
            roadmap["current_level"] = "Advanced"
        elif skill_summary["intermediate_indicators"] >= 1:
            roadmap["current_level"] = "Intermediate"
        else:
            roadmap["current_level"] = "Beginner"
        
        # Identify primary technology stack
        primary_languages = [lang["language"] for lang in repo_analysis["primary_languages"][:3]]
        
        # Generate recommendations based on current skills
        if primary_languages:
            primary_lang = primary_languages[0].lower()
            
            # Language-specific roadmaps
            if primary_lang in ["javascript", "typescript"]:
                roadmap["recommended_paths"].extend([
                    {
                        "path": "Full-Stack JavaScript Developer",
                        "description": "Master both frontend and backend JavaScript development",
                        "technologies": ["React/Vue", "Node.js", "Express", "MongoDB/PostgreSQL"],
                        "timeline": "3-6 months"
                    },
                    {
                        "path": "Frontend Specialist",
                        "description": "Become an expert in modern frontend development",
                        "technologies": ["Advanced React", "TypeScript", "Next.js", "Testing"],
                        "timeline": "2-4 months"
                    }
                ])
            
            elif primary_lang == "python":
                roadmap["recommended_paths"].extend([
                    {
                        "path": "Python Web Developer",
                        "description": "Build scalable web applications with Python",
                        "technologies": ["Django/FastAPI", "PostgreSQL", "Docker", "AWS"],
                        "timeline": "3-5 months"
                    },
                    {
                        "path": "Data Science Track",
                        "description": "Leverage Python for data analysis and machine learning",
                        "technologies": ["Pandas", "Scikit-learn", "TensorFlow", "Jupyter"],
                        "timeline": "4-8 months"
                    }
                ])
        
        # Identify skill gaps
        practices = skill_assessment["development_practices"]
        
        if practices["testing"] < 50:
            roadmap["skill_gaps"].append({
                "area": "Testing",
                "current_score": practices["testing"],
                "recommendation": "Implement unit and integration tests in your projects",
                "priority": "High"
            })
        
        if practices["documentation"] < 70:
            roadmap["skill_gaps"].append({
                "area": "Documentation",
                "current_score": practices["documentation"],
                "recommendation": "Add comprehensive README files and code comments",
                "priority": "Medium"
            })
        
        # Generate next milestones
        current_level = roadmap["current_level"]
        
        if current_level == "Beginner":
            roadmap["next_milestones"] = [
                "Complete 3 projects in your primary language",
                "Learn version control (Git) best practices",
                "Build your first web application",
                "Deploy a project to production"
            ]
        elif current_level == "Intermediate":
            roadmap["next_milestones"] = [
                "Master a web framework",
                "Learn database design and optimization",
                "Implement comprehensive testing",
                "Contribute to open source projects"
            ]
        elif current_level == "Advanced":
            roadmap["next_milestones"] = [
                "Design and build a microservices architecture",
                "Master cloud deployment and DevOps",
                "Lead a team project",
                "Mentor junior developers"
            ]
        else:  # Expert
            roadmap["next_milestones"] = [
                "Architect large-scale systems",
                "Contribute to technology standards",
                "Speak at conferences or write technical articles",
                "Build and lead engineering teams"
            ]
        
        return roadmap
    
    def _calculate_overall_scores(self, repositories: List[Dict[str, Any]], 
                                 repo_analysis: Dict[str, Any], 
                                 skill_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comprehensive scoring metrics"""
        
        scores = {
            "overall_score": 0,
            "category_scores": {
                "technical_skills": 0,
                "project_quality": 0,
                "collaboration": 0,
                "activity_level": 0,
                "innovation": 0
            },
            "acid_scores": {
                "atomicity": 0,
                "consistency": 0,
                "isolation": 0,
                "durability": 0,
                "overall": 0
            },
            "quality_metrics": {
                "readability": 0,
                "maintainability": 0,
                "security": 0,
                "test_coverage": 0,
                "documentation": 0
            }
        }
        
        # Technical Skills Score (0-100)
        lang_diversity = len(skill_assessment["programming_languages"])
        primary_lang_strength = 0
        
        if skill_assessment["programming_languages"]:
            # Get strongest language proficiency
            proficiencies = {"Expert": 100, "Advanced": 80, "Intermediate": 60, "Beginner": 40}
            primary_lang_strength = max(
                proficiencies.get(lang_data["proficiency"], 40) 
                for lang_data in skill_assessment["programming_languages"].values()
            )
        
        scores["category_scores"]["technical_skills"] = min(100, 
            (primary_lang_strength * 0.7) + (min(lang_diversity * 15, 30))
        )
        
        # Project Quality Score
        quality_indicators = repo_analysis["quality_indicators"]
        total_repos = repo_analysis["total_repositories"]
        
        if total_repos > 0:
            readme_score = (quality_indicators["repos_with_readme"] / total_repos) * 30
            license_score = (quality_indicators["repos_with_license"] / total_repos) * 20
            test_score = (quality_indicators["repos_with_tests"] / total_repos) * 30
            size_score = min(20, quality_indicators["avg_repo_size"] / 1000)  # Normalize repo size
            
            scores["category_scores"]["project_quality"] = readme_score + license_score + test_score + size_score
        
        # Collaboration Score
        collab_metrics = repo_analysis["collaboration_metrics"]
        stars_score = min(40, collab_metrics["total_stars"] * 2)
        forks_score = min(30, collab_metrics["total_forks"] * 5)
        watchers_score = min(30, collab_metrics["total_watchers"] * 3)
        
        scores["category_scores"]["collaboration"] = stars_score + forks_score + watchers_score
        
        # Activity Level Score
        activity_metrics = repo_analysis["activity_metrics"]
        recent_activity_score = min(50, activity_metrics["recent_activity_count"] * 10)
        repo_count_score = min(30, total_repos * 3)
        avg_age_score = max(0, 20 - (activity_metrics["avg_repo_age_days"] / 365) * 5)  # Newer is better
        
        scores["category_scores"]["activity_level"] = recent_activity_score + repo_count_score + avg_age_score
        
        # Innovation Score (based on project diversity and uniqueness)
        project_types = len(repo_analysis["project_types"])
        innovation_score = min(100, project_types * 20 + collab_metrics["total_stars"])
        scores["category_scores"]["innovation"] = innovation_score
        
        # Calculate Overall Score
        category_weights = {
            "technical_skills": 0.3,
            "project_quality": 0.25,
            "collaboration": 0.2,
            "activity_level": 0.15,
            "innovation": 0.1
        }
        
        weighted_score = sum(
            scores["category_scores"][category] * weight 
            for category, weight in category_weights.items()
        )
        
        scores["overall_score"] = round(min(100, weighted_score), 1)
        
        # ACID Scores (simplified calculation)
        scores["acid_scores"] = {
            "atomicity": round(scores["category_scores"]["technical_skills"] * 0.8, 1),
            "consistency": round(scores["category_scores"]["project_quality"] * 0.9, 1),
            "isolation": round((scores["category_scores"]["technical_skills"] + scores["category_scores"]["innovation"]) / 2, 1),
            "durability": round((scores["category_scores"]["project_quality"] + scores["category_scores"]["activity_level"]) / 2, 1)
        }
        scores["acid_scores"]["overall"] = round(statistics.mean(scores["acid_scores"].values()), 1)
        
        # Quality Metrics
        practices = skill_assessment["development_practices"]
        scores["quality_metrics"] = {
            "readability": round(practices["documentation"], 1),
            "maintainability": round((practices["documentation"] + practices["testing"]) / 2, 1),
            "security": round(practices["licensing"], 1),  # License indicates security awareness
            "test_coverage": round(practices["testing"], 1),
            "documentation": round(practices["documentation"], 1)
        }
        
        return scores
    
    def _generate_insights(self, repo_analysis: Dict[str, Any], 
                          skill_assessment: Dict[str, Any], 
                          overall_scores: Dict[str, Any]) -> Dict[str, Any]:
        """Generate actionable insights and recommendations"""
        
        insights = {
            "strengths": [],
            "areas_for_improvement": [],
            "career_recommendations": [],
            "technical_recommendations": [],
            "market_insights": []
        }
        
        # Identify strengths
        category_scores = overall_scores["category_scores"]
        
        if category_scores["technical_skills"] >= 80:
            insights["strengths"].append("Strong technical foundation across multiple programming languages")
        
        if category_scores["collaboration"] >= 70:
            insights["strengths"].append("Active in open source community with good project visibility")
        
        if category_scores["project_quality"] >= 75:
            insights["strengths"].append("Maintains high code quality standards with good documentation practices")
        
        # Areas for improvement
        if category_scores["project_quality"] < 60:
            insights["areas_for_improvement"].append({
                "area": "Code Quality",
                "suggestion": "Add README files, licenses, and tests to your repositories",
                "impact": "Improves professional credibility and code maintainability"
            })
        
        if category_scores["collaboration"] < 40:
            insights["areas_for_improvement"].append({
                "area": "Community Engagement",
                "suggestion": "Contribute to open source projects and share your work publicly",
                "impact": "Increases visibility and networking opportunities"
            })
        
        # Career recommendations based on skills
        primary_languages = repo_analysis["primary_languages"]
        if primary_languages:
            primary_lang = primary_languages[0]["language"].lower()
            
            if primary_lang in ["javascript", "typescript"]:
                insights["career_recommendations"].extend([
                    "Consider specializing in full-stack development",
                    "Explore modern frameworks like React, Vue, or Angular",
                    "Learn cloud deployment and DevOps practices"
                ])
            elif primary_lang == "python":
                insights["career_recommendations"].extend([
                    "Explore data science and machine learning opportunities",
                    "Consider backend development with Django or FastAPI",
                    "Look into automation and scripting roles"
                ])
        
        # Market insights
        insights["market_insights"] = [
            "Full-stack developers are in high demand across all industries",
            "Cloud computing skills can increase salary potential by 20-30%",
            "AI/ML expertise is one of the fastest-growing tech fields",
            "DevOps and automation skills are increasingly valuable"
        ]
        
        return insights
    
    def _calculate_profile_completeness(self, repo_analysis: Dict[str, Any], 
                                      skill_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate how complete the developer profile is"""
        
        completeness = {
            "overall_percentage": 0,
            "missing_elements": [],
            "suggestions": []
        }
        
        score = 0
        max_score = 100
        
        # Repository presence (20 points)
        if repo_analysis["total_repositories"] > 0:
            score += 20
        else:
            completeness["missing_elements"].append("No repositories found")
        
        # Language diversity (15 points)
        lang_count = len(skill_assessment["programming_languages"])
        score += min(15, lang_count * 5)
        
        if lang_count < 2:
            completeness["missing_elements"].append("Limited programming language diversity")
        
        # Documentation (20 points)
        if repo_analysis["quality_indicators"]["repos_with_readme"] > 0:
            score += 20
        else:
            completeness["missing_elements"].append("No documented repositories")
            completeness["suggestions"].append("Add README files to your repositories")
        
        # Testing (15 points)
        if repo_analysis["quality_indicators"]["repos_with_tests"] > 0:
            score += 15
        else:
            completeness["missing_elements"].append("No evidence of testing practices")
            completeness["suggestions"].append("Add tests to demonstrate code quality")
        
        # Collaboration (15 points)
        if repo_analysis["collaboration_metrics"]["total_stars"] > 0:
            score += 15
        else:
            completeness["missing_elements"].append("Limited community engagement")
            completeness["suggestions"].append("Share your projects and engage with the community")
        
        # Recent activity (15 points)
        if repo_analysis["activity_metrics"]["recent_activity_count"] > 0:
            score += 15
        else:
            completeness["missing_elements"].append("No recent development activity")
            completeness["suggestions"].append("Stay active with regular commits and updates")
        
        completeness["overall_percentage"] = round(score, 1)
        
        return completeness
    
    def _suggest_next_steps(self, skill_assessment: Dict[str, Any], 
                           overall_scores: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest concrete next steps for career development"""
        
        next_steps = []
        overall_score = overall_scores["overall_score"]
        
        # Beginner level (0-40)
        if overall_score < 40:
            next_steps.extend([
                {
                    "step": "Build Your Foundation",
                    "description": "Complete 3-5 projects in your primary programming language",
                    "timeline": "1-2 months",
                    "priority": "High"
                },
                {
                    "step": "Learn Version Control",
                    "description": "Master Git and GitHub workflows",
                    "timeline": "2 weeks",
                    "priority": "High"
                },
                {
                    "step": "Document Your Work",
                    "description": "Add README files and comments to all projects",
                    "timeline": "Ongoing",
                    "priority": "Medium"
                }
            ])
        
        # Intermediate level (40-70)
        elif overall_score < 70:
            next_steps.extend([
                {
                    "step": "Master a Framework",
                    "description": "Become proficient in a popular framework for your language",
                    "timeline": "2-3 months",
                    "priority": "High"
                },
                {
                    "step": "Add Testing",
                    "description": "Implement unit and integration tests in your projects",
                    "timeline": "1 month",
                    "priority": "High"
                },
                {
                    "step": "Deploy to Production",
                    "description": "Learn cloud deployment and DevOps basics",
                    "timeline": "1-2 months",
                    "priority": "Medium"
                }
            ])
        
        # Advanced level (70-85)
        elif overall_score < 85:
            next_steps.extend([
                {
                    "step": "System Design",
                    "description": "Learn to design scalable, distributed systems",
                    "timeline": "3-4 months",
                    "priority": "High"
                },
                {
                    "step": "Open Source Contribution",
                    "description": "Contribute to popular open source projects",
                    "timeline": "Ongoing",
                    "priority": "Medium"
                },
                {
                    "step": "Mentorship",
                    "description": "Start mentoring junior developers",
                    "timeline": "Ongoing",
                    "priority": "Low"
                }
            ])
        
        # Expert level (85+)
        else:
            next_steps.extend([
                {
                    "step": "Technical Leadership",
                    "description": "Lead architecture decisions and technical strategy",
                    "timeline": "Ongoing",
                    "priority": "High"
                },
                {
                    "step": "Knowledge Sharing",
                    "description": "Write technical articles or speak at conferences",
                    "timeline": "3-6 months",
                    "priority": "Medium"
                },
                {
                    "step": "Innovation",
                    "description": "Create new tools or contribute to emerging technologies",
                    "timeline": "6-12 months",
                    "priority": "Medium"
                }
            ])
        
        return next_steps
    
    def _empty_profile(self) -> Dict[str, Any]:
        """Return empty profile structure when no repositories are available"""
        return {
            "profile_id": f"empty_profile_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.utcnow().isoformat(),
            "user_data": {},
            "repository_analysis": {
                "total_repositories": 0,
                "primary_languages": [],
                "collaboration_metrics": {"total_stars": 0, "total_forks": 0},
                "activity_metrics": {"recent_activity_count": 0}
            },
            "skill_assessment": {
                "programming_languages": {},
                "development_practices": {},
                "skill_level_summary": {"beginner_indicators": 0, "intermediate_indicators": 0, 
                                      "advanced_indicators": 0, "expert_indicators": 0}
            },
            "technology_roadmap": {
                "current_level": "Beginner",
                "recommended_paths": [],
                "skill_gaps": [],
                "next_milestones": ["Create your first repository", "Learn a programming language", 
                                  "Build your first project", "Deploy to GitHub"]
            },
            "overall_scores": {
                "overall_score": 0,
                "category_scores": {"technical_skills": 0, "project_quality": 0, "collaboration": 0, 
                                  "activity_level": 0, "innovation": 0},
                "acid_scores": {"atomicity": 0, "consistency": 0, "isolation": 0, "durability": 0, "overall": 0},
                "quality_metrics": {"readability": 0, "maintainability": 0, "security": 0, 
                                  "test_coverage": 0, "documentation": 0}
            },
            "insights": {
                "strengths": [],
                "areas_for_improvement": [{"area": "Getting Started", "suggestion": "Create your first repository", 
                                         "impact": "Begin building your developer profile"}],
                "career_recommendations": ["Choose a programming language to focus on", 
                                         "Complete online tutorials and courses", "Build small projects to practice"],
                "market_insights": ["Programming skills are in high demand", 
                                  "Start with popular languages like Python or JavaScript"]
            },
            "profile_completeness": {"overall_percentage": 0, "missing_elements": ["No repositories"], 
                                   "suggestions": ["Create your first repository"]},
            "next_steps": [{"step": "Get Started", "description": "Create your first GitHub repository", 
                          "timeline": "1 day", "priority": "High"}]
        }