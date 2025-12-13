import asyncio
import httpx
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MLEvaluationService:
    """Service for integrating with ML models for repository evaluation"""
    
    def __init__(self):
        self.ml_endpoint = None
        self.ml_available = False
        self.last_health_check = None
        self.health_check_interval = 300  # 5 minutes in seconds
    
    async def check_ml_availability(self, ml_endpoint_url: str = None) -> bool:
        """
        Check if ML model is available for evaluation
        
        Args:
            ml_endpoint_url: Optional ML endpoint URL to check
            
        Returns:
            True if ML model is available, False otherwise
        """
        
        if ml_endpoint_url:
            self.ml_endpoint = ml_endpoint_url
        
        if not self.ml_endpoint:
            logger.info("No ML endpoint configured, using ACID scoring only")
            return False
        
        # Check if we need to perform health check
        now = datetime.utcnow()
        if (self.last_health_check and 
            (now - self.last_health_check).seconds < self.health_check_interval and 
            self.ml_available):
            return self.ml_available
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.ml_endpoint}/health")
                
                if response.status_code == 200:
                    self.ml_available = True
                    self.last_health_check = now
                    logger.info(f"ML endpoint is available at {self.ml_endpoint}")
                    return True
                else:
                    self.ml_available = False
                    logger.warning(f"ML endpoint returned status {response.status_code}")
                    return False
                    
        except Exception as e:
            self.ml_available = False
            logger.info(f"ML endpoint not available: {e}. Will use ACID scoring.")
            return False
    
    async def evaluate_repository_hybrid(self, 
                                       github_url: str, 
                                       username: str,
                                       repo_data: Dict[str, Any],
                                       ml_endpoint_url: str = None) -> Dict[str, Any]:
        """
        Evaluate repository using hybrid approach: ML model if available, ACID scoring as fallback
        
        Args:
            github_url: GitHub repository or profile URL
            username: GitHub username
            repo_data: Repository metadata
            ml_endpoint_url: Optional ML endpoint URL
            
        Returns:
            Comprehensive evaluation results with ML insights if available
        """
        
        evaluation_result = {
            "evaluation_method": "unknown",
            "ml_available": False,
            "acid_scores": {},
            "ml_insights": {},
            "hybrid_score": 0,
            "evaluation_timestamp": datetime.utcnow().isoformat(),
            "github_url": github_url,
            "username": username
        }
        
        # Check ML availability
        ml_available = await self.check_ml_availability(ml_endpoint_url)
        evaluation_result["ml_available"] = ml_available
        
        if ml_available:
            try:
                # Try ML evaluation first
                logger.info(f"Using ML evaluation for {username}")
                ml_result = await self._evaluate_with_ml_model(github_url, username, repo_data)
                
                # Get ACID scores as backup/comparison
                acid_result = await self._evaluate_with_acid_scoring(repo_data)
                
                evaluation_result.update({
                    "evaluation_method": "hybrid_ml_primary",
                    "ml_insights": ml_result,
                    "acid_scores": acid_result,
                    "hybrid_score": self._calculate_hybrid_score(ml_result, acid_result),
                    "confidence": ml_result.get("confidence", 0.8)
                })
                
                logger.info(f"ML evaluation completed for {username} with confidence {ml_result.get('confidence', 'unknown')}")
                
            except Exception as e:
                logger.error(f"ML evaluation failed for {username}: {e}. Falling back to ACID scoring.")
                # Fallback to ACID scoring
                acid_result = await self._evaluate_with_acid_scoring(repo_data)
                evaluation_result.update({
                    "evaluation_method": "acid_fallback",
                    "acid_scores": acid_result,
                    "hybrid_score": acid_result.get("overall_score", 0),
                    "ml_error": str(e)
                })
        else:
            # Use ACID scoring only
            logger.info(f"Using ACID scoring only for {username}")
            acid_result = await self._evaluate_with_acid_scoring(repo_data)
            evaluation_result.update({
                "evaluation_method": "acid_only",
                "acid_scores": acid_result,
                "hybrid_score": acid_result.get("overall_score", 0)
            })
        
        return evaluation_result
    
    async def _evaluate_with_ml_model(self, 
                                     github_url: str, 
                                     username: str,
                                     repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send repository data to ML model for evaluation
        
        Args:
            github_url: GitHub URL
            username: GitHub username  
            repo_data: Repository metadata
            
        Returns:
            ML evaluation results
        """
        
        if not self.ml_endpoint:
            raise Exception("ML endpoint not configured")
        
        # Prepare payload for ML model
        payload = {
            "github_url": github_url,
            "username": username,
            "repository_data": repo_data,
            "analysis_type": "comprehensive",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:  # 2 minutes timeout for ML processing
                response = await client.post(
                    f"{self.ml_endpoint}/evaluate",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    ml_result = response.json()
                    
                    # Validate ML response structure
                    required_fields = ["ml_scores", "confidence", "insights"]
                    if all(field in ml_result for field in required_fields):
                        return ml_result
                    else:
                        logger.warning(f"ML response missing required fields: {ml_result}")
                        raise Exception("Invalid ML response structure")
                        
                else:
                    error_msg = f"ML model returned status {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    raise Exception(error_msg)
                    
        except httpx.TimeoutException:
            raise Exception("ML model evaluation timed out")
        except Exception as e:
            logger.error(f"ML model evaluation failed: {e}")
            raise e
    
    async def _evaluate_with_acid_scoring(self, repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate repository using existing ACID scoring system
        
        Args:
            repo_data: Repository metadata and analysis data
            
        Returns:
            ACID evaluation results
        """
        
        try:
            from app.services.evaluation_engine import EvaluationEngine
            
            evaluation_engine = EvaluationEngine()
            
            # Use existing ACID evaluation
            # Note: This is a simplified version - in practice you'd need full repo content
            acid_result = evaluation_engine._calculate_acid_scores(repo_data, {})
            quality_metrics = evaluation_engine._calculate_quality_metrics(repo_data, {})
            
            # Calculate overall score
            overall_score = (acid_result["overall"] + 
                           sum(quality_metrics.values()) / len(quality_metrics)) / 2
            
            return {
                "acid_scores": acid_result,
                "quality_metrics": quality_metrics,
                "overall_score": round(overall_score, 1),
                "evaluation_method": "acid_scoring"
            }
            
        except Exception as e:
            logger.error(f"ACID scoring failed: {e}")
            # Return basic fallback scores
            return {
                "acid_scores": {
                    "atomicity": 50,
                    "consistency": 50,
                    "isolation": 50,
                    "durability": 50,
                    "overall": 50
                },
                "quality_metrics": {
                    "readability": 50,
                    "maintainability": 50,
                    "security": 50,
                    "test_coverage": 50,
                    "documentation": 50
                },
                "overall_score": 50,
                "evaluation_method": "fallback_default"
            }
    
    def _calculate_hybrid_score(self, ml_result: Dict[str, Any], acid_result: Dict[str, Any]) -> float:
        """
        Calculate hybrid score combining ML and ACID results
        
        Args:
            ml_result: ML evaluation results
            acid_result: ACID evaluation results
            
        Returns:
            Combined hybrid score
        """
        
        try:
            # Get ML score
            ml_score = ml_result.get("ml_scores", {}).get("overall_score", 0)
            ml_confidence = ml_result.get("confidence", 0.5)
            
            # Get ACID score
            acid_score = acid_result.get("overall_score", 0)
            
            # Weight based on ML confidence
            # High confidence ML: 70% ML + 30% ACID
            # Low confidence ML: 30% ML + 70% ACID
            ml_weight = 0.3 + (ml_confidence * 0.4)  # 0.3 to 0.7
            acid_weight = 1 - ml_weight
            
            hybrid_score = (ml_score * ml_weight) + (acid_score * acid_weight)
            
            return round(hybrid_score, 1)
            
        except Exception as e:
            logger.error(f"Hybrid score calculation failed: {e}")
            # Fallback to ACID score
            return acid_result.get("overall_score", 50)
    
    async def get_ml_model_info(self) -> Dict[str, Any]:
        """
        Get information about the ML model if available
        
        Returns:
            ML model information and status
        """
        
        info = {
            "ml_endpoint": self.ml_endpoint,
            "available": self.ml_available,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "health_check_interval": self.health_check_interval
        }
        
        if self.ml_available and self.ml_endpoint:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{self.ml_endpoint}/info")
                    if response.status_code == 200:
                        ml_info = response.json()
                        info.update({"ml_model_info": ml_info})
            except Exception as e:
                info["ml_info_error"] = str(e)
        
        return info
    
    def set_ml_endpoint(self, endpoint_url: str) -> None:
        """
        Set the ML endpoint URL (e.g., from ngrok)
        
        Args:
            endpoint_url: The ML model endpoint URL
        """
        self.ml_endpoint = endpoint_url
        self.ml_available = False  # Reset availability, will be checked on next request
        self.last_health_check = None
        logger.info(f"ML endpoint set to: {endpoint_url}")

# Global ML service instance
ml_service = MLEvaluationService()