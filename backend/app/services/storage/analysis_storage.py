"""
Analysis Storage Service
Handles storage of code analysis results and ACID scores
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

from app.models.repository import Evaluation, EvaluationCreate, ACIDScore, QualityMetrics

logger = logging.getLogger(__name__)


class AnalysisStorageService:
    """
    Service for analysis result storage operations
    
    Provides operations for storing and retrieving code analysis results
    """
    
    def __init__(self, database: AsyncIOMotorDatabase):
        """
        Initialize analysis storage service
        
        Args:
            database: MongoDB database instance
        """
        self.db = database
        self.collection = database.evaluations
    
    async def create_evaluation(
        self,
        evaluation_data: EvaluationCreate
    ) -> str:
        """
        Create a new evaluation record
        
        Args:
            evaluation_data: Evaluation creation data
            
        Returns:
            Created evaluation ID
        """
        doc = evaluation_data.model_dump(by_alias=True, exclude={'id'})
        doc['created_at'] = datetime.utcnow()
        
        result = await self.collection.insert_one(doc)
        logger.info(f"Created evaluation for repository: {evaluation_data.repo_id}")
        
        return str(result.inserted_id)
    
    async def get_evaluation_by_id(self, evaluation_id: str) -> Optional[Evaluation]:
        """
        Get evaluation by ID
        
        Args:
            evaluation_id: Evaluation ID
            
        Returns:
            Evaluation or None if not found
        """
        from bson import ObjectId
        
        try:
            doc = await self.collection.find_one({'_id': ObjectId(evaluation_id)})
        except Exception:
            doc = await self.collection.find_one({'_id': evaluation_id})
        
        if doc:
            doc['_id'] = str(doc['_id'])
            return Evaluation(**doc)
        
        return None
    
    async def get_evaluation_by_repo(
        self,
        repo_id: str
    ) -> Optional[Evaluation]:
        """
        Get evaluation for a repository
        
        Args:
            repo_id: Repository ID
            
        Returns:
            Evaluation or None if not found
        """
        doc = await self.collection.find_one({'repo_id': repo_id})
        
        if doc:
            doc['_id'] = str(doc['_id'])
            return Evaluation(**doc)
        
        return None
    
    async def get_user_evaluations(
        self,
        user_id: str
    ) -> List[Evaluation]:
        """
        Get all evaluations for a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of Evaluation objects
        """
        cursor = self.collection.find({'user_id': user_id}).sort('created_at', -1)
        
        evaluations = []
        async for doc in cursor:
            doc['_id'] = str(doc['_id'])
            evaluations.append(Evaluation(**doc))
        
        return evaluations
    
    async def update_acid_scores(
        self,
        repo_id: str,
        acid_scores: ACIDScore
    ) -> bool:
        """
        Update ACID scores for a repository
        
        Args:
            repo_id: Repository ID
            acid_scores: ACID scores object
            
        Returns:
            True if updated successfully
        """
        update_doc = {
            'acid_score': acid_scores.model_dump(),
            'updated_at': datetime.utcnow()
        }
        
        result = await self.collection.update_one(
            {'repo_id': repo_id},
            {
                '$set': update_doc,
                '$setOnInsert': {'created_at': datetime.utcnow()}
            },
            upsert=True
        )
        
        logger.info(f"Updated ACID scores for repository: {repo_id}")
        
        return result.modified_count > 0 or result.upserted_id is not None
    
    async def update_complexity_metrics(
        self,
        repo_id: str,
        complexity_score: float,
        file_count: int,
        total_lines: int
    ) -> bool:
        """
        Update complexity metrics for a repository
        
        Args:
            repo_id: Repository ID
            complexity_score: Overall complexity score
            file_count: Number of files analyzed
            total_lines: Total lines of code
            
        Returns:
            True if updated successfully
        """
        update_doc = {
            'complexity_score': complexity_score,
            'file_count': file_count,
            'total_lines': total_lines,
            'updated_at': datetime.utcnow()
        }
        
        result = await self.collection.update_one(
            {'repo_id': repo_id},
            {
                '$set': update_doc,
                '$setOnInsert': {'created_at': datetime.utcnow()}
            },
            upsert=True
        )
        
        return result.modified_count > 0 or result.upserted_id is not None
    
    async def update_quality_metrics(
        self,
        repo_id: str,
        quality_metrics: QualityMetrics
    ) -> bool:
        """
        Update quality metrics for a repository
        
        Args:
            repo_id: Repository ID
            quality_metrics: Quality metrics object
            
        Returns:
            True if updated successfully
        """
        update_doc = {
            'quality_metrics': quality_metrics.model_dump(),
            'updated_at': datetime.utcnow()
        }
        
        result = await self.collection.update_one(
            {'repo_id': repo_id},
            {
                '$set': update_doc,
                '$setOnInsert': {'created_at': datetime.utcnow()}
            },
            upsert=True
        )
        
        return result.modified_count > 0 or result.upserted_id is not None
    
    async def update_complete_evaluation(
        self,
        repo_id: str,
        user_id: str,
        acid_scores: ACIDScore,
        quality_metrics: QualityMetrics,
        complexity_score: float,
        best_practices_score: float,
        language_stats: Dict[str, int],
        file_count: int,
        total_lines: int
    ) -> str:
        """
        Update or create complete evaluation atomically
        
        Args:
            repo_id: Repository ID
            user_id: User ID
            acid_scores: ACID scores
            quality_metrics: Quality metrics
            complexity_score: Complexity score
            best_practices_score: Best practices score
            language_stats: Language statistics
            file_count: Number of files
            total_lines: Total lines of code
            
        Returns:
            Evaluation ID
        """
        doc = {
            'repo_id': repo_id,
            'user_id': user_id,
            'acid_score': acid_scores.model_dump(),
            'quality_metrics': quality_metrics.model_dump(),
            'complexity_score': complexity_score,
            'best_practices_score': best_practices_score,
            'language_stats': language_stats,
            'file_count': file_count,
            'total_lines': total_lines,
            'updated_at': datetime.utcnow()
        }
        
        result = await self.collection.update_one(
            {'repo_id': repo_id},
            {
                '$set': doc,
                '$setOnInsert': {'created_at': datetime.utcnow()}
            },
            upsert=True
        )
        
        logger.info(f"Updated complete evaluation for repository: {repo_id}")
        
        if result.upserted_id:
            return str(result.upserted_id)
        else:
            # Find the existing document
            existing = await self.collection.find_one({'repo_id': repo_id})
            return str(existing['_id']) if existing else repo_id
    
    async def delete_evaluation(self, evaluation_id: str) -> bool:
        """
        Delete evaluation
        
        Args:
            evaluation_id: Evaluation ID
            
        Returns:
            True if deleted successfully
        """
        from bson import ObjectId
        
        try:
            result = await self.collection.delete_one({'_id': ObjectId(evaluation_id)})
        except Exception:
            result = await self.collection.delete_one({'_id': evaluation_id})
        
        if result.deleted_count > 0:
            logger.info(f"Deleted evaluation: {evaluation_id}")
            return True
        
        return False
    
    async def delete_user_evaluations(self, user_id: str) -> int:
        """
        Delete all evaluations for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of evaluations deleted
        """
        result = await self.collection.delete_many({'user_id': user_id})
        
        logger.info(f"Deleted {result.deleted_count} evaluations for user {user_id}")
        
        return result.deleted_count
    
    async def get_average_acid_scores(
        self,
        user_id: str,
        category: Optional[str] = None
    ) -> Optional[ACIDScore]:
        """
        Calculate average ACID scores for a user's repositories
        
        Args:
            user_id: User ID
            category: Optional category filter (flagship/significant)
            
        Returns:
            Average ACID scores or None if no evaluations
        """
        # Build aggregation pipeline
        match_stage = {'user_id': user_id}
        
        if category:
            # Need to join with repositories collection to filter by category
            pipeline = [
                {'$match': match_stage},
                {
                    '$lookup': {
                        'from': 'repositories',
                        'localField': 'repo_id',
                        'foreignField': '_id',
                        'as': 'repo'
                    }
                },
                {'$unwind': '$repo'},
                {'$match': {'repo.category': category}},
                {
                    '$group': {
                        '_id': None,
                        'atomicity': {'$avg': '$acid_score.atomicity'},
                        'consistency': {'$avg': '$acid_score.consistency'},
                        'isolation': {'$avg': '$acid_score.isolation'},
                        'durability': {'$avg': '$acid_score.durability'},
                        'overall': {'$avg': '$acid_score.overall'}
                    }
                }
            ]
        else:
            pipeline = [
                {'$match': match_stage},
                {
                    '$group': {
                        '_id': None,
                        'atomicity': {'$avg': '$acid_score.atomicity'},
                        'consistency': {'$avg': '$acid_score.consistency'},
                        'isolation': {'$avg': '$acid_score.isolation'},
                        'durability': {'$avg': '$acid_score.durability'},
                        'overall': {'$avg': '$acid_score.overall'}
                    }
                }
            ]
        
        cursor = self.collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        
        if result:
            scores = result[0]
            return ACIDScore(
                atomicity=scores.get('atomicity', 0.0),
                consistency=scores.get('consistency', 0.0),
                isolation=scores.get('isolation', 0.0),
                durability=scores.get('durability', 0.0),
                overall=scores.get('overall', 0.0)
            )
        
        return None
    
    async def get_evaluation_statistics(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get evaluation statistics for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with statistics
        """
        evaluations = await self.get_user_evaluations(user_id)
        
        if not evaluations:
            return {
                'total_evaluations': 0,
                'average_acid_score': 0.0,
                'average_complexity': 0.0,
                'total_lines': 0,
                'total_files': 0
            }
        
        total_acid = sum(e.acid_score.overall for e in evaluations)
        total_complexity = sum(e.complexity_score for e in evaluations)
        total_lines = sum(e.total_lines for e in evaluations)
        total_files = sum(e.file_count for e in evaluations)
        
        return {
            'total_evaluations': len(evaluations),
            'average_acid_score': total_acid / len(evaluations),
            'average_complexity': total_complexity / len(evaluations),
            'total_lines': total_lines,
            'total_files': total_files
        }
    
    async def ensure_indexes(self) -> None:
        """
        Ensure required indexes exist for performance
        """
        try:
            # Unique index on repo_id
            await self.collection.create_index('repo_id', unique=True)
            
            # Index on user_id for user queries
            await self.collection.create_index('user_id')
            
            # Compound index for user + repo queries
            await self.collection.create_index(
                [('user_id', 1), ('repo_id', 1)],
                name='user_repo'
            )
            
            # Index on created_at for sorting
            await self.collection.create_index(
                [('created_at', -1)],
                name='created_at_desc'
            )
            
            logger.info("Evaluation indexes ensured")
            
        except Exception as e:
            logger.error(f"Error ensuring indexes: {e}")
