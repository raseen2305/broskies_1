#!/usr/bin/env python3
import asyncio
from app.db_connection import diagnose_connection_issues

async def main():
    result = await diagnose_connection_issues()
    print('Connection attempts:')
    for attempt in result['connection_attempts']:
        print(f"  {attempt['name']}: {attempt.get('error', 'Success')}")
    
    print('\nRecommendations:')
    for rec in result['recommendations']:
        print(f"  - {rec}")

if __name__ == "__main__":
    asyncio.run(main())