#!/usr/bin/env python3
"""
Start the backend with proper environment loading
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set the GitHub token explicitly (ensure consistency)
os.environ['GITHUB_TOKEN'] = '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'

# Verify environment variables are loaded
print("Environment variables loaded:")
print(f"EXTERNAL_USERS_DB_URL: {'✅ Set' if os.getenv('EXTERNAL_USERS_DB_URL') else '❌ Not set'}")
print(f"RASEEN_TEMP_USER_DB_URL: {'✅ Set' if os.getenv('RASEEN_TEMP_USER_DB_URL') else '❌ Not set'}")
print(f"GITHUB_TOKEN: {'✅ Set' if os.getenv('GITHUB_TOKEN') else '❌ Not set'}")

# Now start the main application
if __name__ == "__main__":
    import main