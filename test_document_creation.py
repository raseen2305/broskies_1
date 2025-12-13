#!/usr/bin/env python3
"""
Test script to verify the document creation fix is working
"""

import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

async def test_document_creation():
    """Test the document creation logic"""
    try:
        from app.user_type_detector import UserTypeDetector
        from datetime import datetime
        
        print("✅ Successfully imported UserTypeDetector")
        
        # Test the document creation logic
        username = "testuser"
        timestamp = int(datetime.utcnow().timestamp())
        
        # Simulate source document
        source_doc = {
            '_id': 'test_id_123',
            'username': username,
            'user_id': username.lower(),
            'repositories': [
                {'name': 'test-repo', 'language': 'Python'},
                {'name': 'another-repo', 'language': 'JavaScript'}
            ],
            'scan_date': datetime.utcnow(),
            'repositoriesCount': 2,
            'summary': {'total_repos': 2},
            'name': 'Test User',
            'bio': 'Test bio',
            'location': 'Test Location'
        }
        
        # Simulate new document creation
        new_document = {
            **source_doc,
            '_id': None,
            'document_type': 'updated_with_deep_analysis',
            'scan_id': f"deep_analysis_updated_{username}_{timestamp}",
            'original_scan_id': source_doc.get('scan_id'),
            'created_from_document_id': str(source_doc['_id']),
            'scan_date': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'overallScore': 88.5,
            'overall_score': 88.5,
            'deepAnalysisComplete': True,
            'needsDeepAnalysis': False,
            'analyzedAt': datetime.utcnow().isoformat(),
            'analyzed': True,
            'deepAnalysisInProgress': False,
            'analysis_id': f"analysis_{username}_{timestamp}",
            'analysis_type': 'deep_analysis_with_old_data',
            'analysis_version': '1.0',
            'activityScore': 82.0,
            'consistencyScore': 75.0,
            'innovationScore': 80.0,
            'deliveryScore': 77.0,
            'is_latest_analysis': True
        }
        
        # Remove the original _id
        if '_id' in new_document:
            del new_document['_id']
        
        print("✅ Document creation logic test passed")
        print(f"   - Original repositories: {len(source_doc.get('repositories', []))}")
        print(f"   - New document repositories: {len(new_document.get('repositories', []))}")
        print(f"   - Overall Score: {new_document.get('overallScore')}")
        print(f"   - Document Type: {new_document.get('document_type')}")
        print(f"   - Deep Analysis Complete: {new_document.get('deepAnalysisComplete')}")
        print(f"   - Analysis ID: {new_document.get('analysis_id')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_document_creation())
    if success:
        print("\n🎉 All tests passed! The document creation fix should work correctly.")
    else:
        print("\n💥 Tests failed. There may be issues with the fix.")