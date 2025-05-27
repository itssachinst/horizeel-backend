#!/usr/bin/env python3
"""
Test script to verify uploadFlag functionality
"""

import sys
import os
import json

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from app.database import get_db
from app.models import User
from app.schemas import UserResponse
from app.crud import get_users, get_user_by_id

def test_upload_flag():
    """
    Test that uploadFlag is properly included in user responses
    """
    print("🧪 Testing uploadFlag functionality...")
    
    try:
        # Get a database session
        db = next(get_db())
        
        # Get all users
        users = get_users(db, limit=5)
        
        if not users:
            print("❌ No users found in database")
            return False
        
        print(f"✅ Found {len(users)} users")
        
        # Test each user
        for user in users:
            print(f"\n👤 Testing user: {user.username} (ID: {user.user_id})")
            
            # Check if uploadFlag attribute exists
            if hasattr(user, 'uploadFlag'):
                print(f"   ✅ uploadFlag attribute exists: {user.uploadFlag}")
            else:
                print(f"   ❌ uploadFlag attribute missing")
                return False
            
            # Test UserResponse schema
            try:
                user_response = UserResponse.model_validate(user)
                print(f"   ✅ UserResponse schema works")
                print(f"   📄 uploadFlag in response: {user_response.uploadFlag}")
                
                # Convert to dict to see full structure
                user_dict = user_response.model_dump()
                if 'uploadFlag' in user_dict:
                    print(f"   ✅ uploadFlag in serialized response: {user_dict['uploadFlag']}")
                else:
                    print(f"   ❌ uploadFlag missing from serialized response")
                    return False
                    
            except Exception as e:
                print(f"   ❌ UserResponse schema failed: {e}")
                return False
        
        print(f"\n🎉 All tests passed! uploadFlag is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        db.close()

def test_upload_flag_update():
    """
    Test updating uploadFlag for a user
    """
    print("\n🧪 Testing uploadFlag update functionality...")
    
    try:
        # Get a database session
        db = next(get_db())
        
        # Get the first user
        user = db.query(User).first()
        
        if not user:
            print("❌ No users found in database")
            return False
        
        print(f"👤 Testing with user: {user.username}")
        print(f"   Current uploadFlag: {user.uploadFlag}")
        
        # Toggle the uploadFlag
        original_value = user.uploadFlag
        new_value = not original_value
        
        user.uploadFlag = new_value
        db.commit()
        db.refresh(user)
        
        print(f"   Updated uploadFlag to: {user.uploadFlag}")
        
        if user.uploadFlag == new_value:
            print("   ✅ uploadFlag update successful")
            
            # Restore original value
            user.uploadFlag = original_value
            db.commit()
            print(f"   🔄 Restored original value: {original_value}")
            
            return True
        else:
            print("   ❌ uploadFlag update failed")
            return False
            
    except Exception as e:
        print(f"❌ Update test failed with error: {e}")
        return False
    finally:
        db.close()

def main():
    """
    Main function to run all tests
    """
    print("🚀 Starting uploadFlag tests...\n")
    
    # Test basic functionality
    test1_passed = test_upload_flag()
    
    # Test update functionality
    test2_passed = test_upload_flag_update()
    
    print(f"\n📊 Test Results:")
    print(f"   Basic functionality: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"   Update functionality: {'✅ PASSED' if test2_passed else '❌ FAILED'}")
    
    if test1_passed and test2_passed:
        print(f"\n🎉 All tests passed! uploadFlag implementation is working correctly.")
        return 0
    else:
        print(f"\n❌ Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 