"""
Cron script for periodic ranking updates
Run this script hourly to keep rankings fresh

Usage:
    python backend/scripts/update_rankings_cron.py

Or add to crontab:
    0 * * * * cd /path/to/project && python backend/scripts/update_rankings_cron.py >> logs/ranking_updates.log 2>&1
"""

import asyncio
import sys
import os
from datetime import datetime
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Main function to run ranking updates"""
    try:
        logger.info("=" * 80)
        logger.info(f"🔄 Starting scheduled ranking update at {datetime.utcnow().isoformat()}")
        logger.info("=" * 80)
        
        # Import after path is set
        from backend.app.tasks.ranking_batch_update import batch_update_all_rankings
        
        # Run batch update
        result = await batch_update_all_rankings()
        
        if result.get("success"):
            logger.info("✅ Ranking update completed successfully")
            logger.info(f"   - Regions updated: {result.get('regions_updated', 0)}/{result.get('total_regions', 0)}")
            logger.info(f"   - Universities updated: {result.get('universities_updated', 0)}/{result.get('total_universities', 0)}")
            logger.info(f"   - Duration: {result.get('duration_seconds', 0):.2f}s")
            
            if result.get('errors'):
                logger.warning(f"   - Errors encountered: {len(result['errors'])}")
                for error in result['errors'][:5]:  # Show first 5 errors
                    logger.warning(f"     - {error['type']}: {error['identifier']} - {error['error']}")
        else:
            logger.error(f"❌ Ranking update failed: {result.get('error')}")
            sys.exit(1)
        
        logger.info("=" * 80)
        logger.info("🎉 Ranking update job completed")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Fatal error in ranking update job: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
