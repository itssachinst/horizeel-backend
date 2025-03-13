"""
Script to restart the FastAPI server.
"""

import os
import sys
import subprocess

def restart_server():
    """Restart the FastAPI server."""
    print("Restarting the FastAPI server...")
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Change to the parent directory
    os.chdir(os.path.dirname(current_dir))
    
    # Start the server
    try:
        subprocess.run(["python", "-m", "uvicorn", "backend.app.main:app", "--reload"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
    except KeyboardInterrupt:
        print("Server stopped by user.")

if __name__ == "__main__":
    restart_server() 