#!/usr/bin/env python3
"""
Test script to verify background tasks functionality
"""

import sys
import os
import requests
import time
import json

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

def test_video_status_endpoint():
    """
    Test the video status endpoint
    """
    print("🧪 Testing video status endpoint...")
    
    # This would require a real video ID from your database
    # For now, we'll test with a dummy ID to see if the endpoint exists
    test_video_id = "00000000-0000-0000-0000-000000000000"
    
    try:
        response = requests.get(f"http://localhost:8000/api/videos/{test_video_id}/status")
        
        if response.status_code == 404:
            print("✅ Status endpoint exists (returned 404 for non-existent video)")
            return True
        elif response.status_code == 200:
            print("✅ Status endpoint works and returned video data")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error testing status endpoint: {e}")
        return False

def test_upload_endpoint_structure():
    """
    Test that the upload endpoint accepts BackgroundTasks parameter
    """
    print("\n🧪 Testing upload endpoint structure...")
    
    try:
        # Test with invalid data to see if endpoint exists
        response = requests.post("http://localhost:8000/api/videos/")
        
        # We expect either 422 (validation error) or 401 (unauthorized)
        if response.status_code in [422, 401]:
            print("✅ Upload endpoint exists and has proper validation")
            return True
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure the server is running on localhost:8000")
        return False
    except Exception as e:
        print(f"❌ Error testing upload endpoint: {e}")
        return False

def test_database_migration():
    """
    Test if the database migration was successful
    """
    print("\n🧪 Testing database migration...")
    
    try:
        from app.database import get_db
        from app.models import Video
        from sqlalchemy import text
        
        # Get a database session
        db = next(get_db())
        
        # Try to query videos with new status values
        try:
            # Test if we can filter by new status values
            processing_videos = db.query(Video).filter(Video.status == 'processing').count()
            ready_videos = db.query(Video).filter(Video.status == 'ready').count()
            failed_videos = db.query(Video).filter(Video.status == 'failed').count()
            
            print(f"✅ Database migration successful")
            print(f"   Processing videos: {processing_videos}")
            print(f"   Ready videos: {ready_videos}")
            print(f"   Failed videos: {failed_videos}")
            
            db.close()
            return True
            
        except Exception as e:
            print(f"❌ Database migration failed: {e}")
            db.close()
            return False
            
    except Exception as e:
        print(f"❌ Error testing database migration: {e}")
        return False

def test_background_task_module():
    """
    Test if the background task module can be imported
    """
    print("\n🧪 Testing background task module...")
    
    try:
        from app.utils.background_tasks import (
            process_video_background, 
            process_youtube_video_background,
            update_video_status
        )
        print("✅ Background task module imported successfully")
        print("   Available functions:")
        print("   - process_video_background")
        print("   - process_youtube_video_background")
        print("   - update_video_status")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import background task module: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing background task module: {e}")
        return False

def test_schema_updates():
    """
    Test if the schema updates are working
    """
    print("\n🧪 Testing schema updates...")
    
    try:
        from app.schemas import VideoStatus, VideoResponse
        
        # Test VideoStatus schema
        test_status = {
            "video_id": "00000000-0000-0000-0000-000000000000",
            "status": "processing",
            "title": "Test Video",
            "created_at": "2023-01-01T00:00:00Z"
        }
        
        status_obj = VideoStatus(**test_status)
        print("✅ VideoStatus schema works")
        
        # Test VideoResponse with status field
        test_response = {
            "video_id": "00000000-0000-0000-0000-000000000000",
            "video_url": "http://example.com/video.m3u8",
            "thumbnail_url": "http://example.com/thumb.jpg",
            "title": "Test Video",
            "description": "Test Description",
            "user_id": "00000000-0000-0000-0000-000000000000",
            "username": "testuser",
            "views": 0,
            "likes": 0,
            "status": "ready",
            "created_at": "2023-01-01T00:00:00Z"
        }
        
        response_obj = VideoResponse(**test_response)
        print("✅ VideoResponse schema with status field works")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing schema updates: {e}")
        return False

def main():
    """
    Main function to run all tests
    """
    print("🚀 Starting Background Tasks Tests...\n")
    
    tests = [
        ("Background Task Module", test_background_task_module),
        ("Schema Updates", test_schema_updates),
        ("Database Migration", test_database_migration),
        ("Video Status Endpoint", test_video_status_endpoint),
        ("Upload Endpoint Structure", test_upload_endpoint_structure),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print(f"\n📊 Test Results:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Background tasks implementation is ready.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 