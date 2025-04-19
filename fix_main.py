#!/usr/bin/env python3
"""
Direct Fix for main.py
This script directly modifies app/main.py to completely disable the redirect middleware
"""
import os
import sys
import re
import shutil
import time

def backup_file(file_path):
    """Create a backup of the file before modifying it"""
    if os.path.exists(file_path):
        backup_path = f"{file_path}.bak.{int(time.time())}"
        shutil.copy2(file_path, backup_path)
        print(f"Created backup at {backup_path}")
        return backup_path
    else:
        print(f"Error: File {file_path} not found")
        sys.exit(1)

def apply_fix():
    """Apply the fix to main.py"""
    main_py_path = "app/main.py"
    
    # Backup the file
    backup_file(main_py_path)
    
    # Read the file
    with open(main_py_path, 'r') as f:
        content = f.read()
    
    # Method 1: Completely disable the redirect middleware by adding a return at the beginning
    redirect_middleware_pattern = r'(@app\.middleware\("http"\)\n(?:async )?def redirect_to_https\(request: Request, call_next\):)'
    if re.search(redirect_middleware_pattern, content):
        modified_content = re.sub(
            redirect_middleware_pattern,
            r'\1\n    # CRITICAL: This line added by fix_main.py to disable redirects completely\n    return await call_next(request)\n    # Original middleware code below is bypassed',
            content
        )
        
        # Write the modified content
        with open(main_py_path, 'w') as f:
            f.write(modified_content)
        
        print(f"Successfully modified {main_py_path} to disable redirects")
        print("The middleware now bypasses all redirect logic by immediately returning the response")
        return True
    else:
        print("Could not find the redirect middleware in the file. No changes made.")
        return False

def main():
    print("=== Direct Fix for FastAPI Redirect Issue ===")
    print("This script will modify app/main.py to completely disable HTTP redirects")
    
    # Check if we're in the right directory
    if not os.path.exists("app/main.py"):
        print("Error: app/main.py not found. Make sure you're running this script from the project root.")
        sys.exit(1)
    
    # Ask for confirmation
    response = input("This will modify your code directly. Continue? (y/n): ")
    if response.lower() not in ('y', 'yes'):
        print("Operation cancelled.")
        return
    
    # Apply the fix
    if apply_fix():
        print("\nFix successfully applied!")
        print("You should now be able to run the application without redirects.")
        print("To start the application: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
    else:
        print("\nFailed to apply fix. No changes were made.")

if __name__ == "__main__":
    main() 