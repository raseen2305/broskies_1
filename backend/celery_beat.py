#!/usr/bin/env python3
"""
Celery beat scheduler startup script for GitHub Repository Evaluator
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv()

from app.celery_app import celery_app

if __name__ == '__main__':
    # Start the Celery beat scheduler
    celery_app.start(['celery', 'beat', '--loglevel=info'])