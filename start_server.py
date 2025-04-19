#!/usr/bin/env python
"""
Script to start the FastAPI server with proper environment variables.
This ensures that HTTPS redirects are disabled for development.
"""
import os
import subprocess
import sys

def main():
    # Set environment variables
    print("Setting environment variables for development...")
    os.environ["ENABLE_HTTPS_REDIRECT"] = "false"
    
    # Check if Python is in the path
    python_cmd = sys.executable
    
    # Build the uvicorn command
    cmd = [
        python_cmd,
        "-m",
        "uvicorn",
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000",
    ]
    
    print(f"Starting FastAPI server with HTTPS redirects disabled...")
    print(f"Command: {' '.join(cmd)}")
    
    # Run the command
    try:
        result = subprocess.run(cmd)
        return result.returncode
    except KeyboardInterrupt:
        print("\nServer shutdown by user")
        return 0
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 