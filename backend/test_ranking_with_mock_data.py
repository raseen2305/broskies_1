#!/usr/bin/env python3
"""
Test script for unified ranking system with mock data.
This script creates random test data and validates all ranking functionality.
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Import our services