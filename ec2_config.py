#!/usr/bin/env python
"""
EC2 Instance Configuration Script for FastAPI Application
This script configures an EC2 instance to properly handle HTTPS redirects.
"""
import os
import sys
import subprocess
import argparse
import shutil
import time

def setup_environment_file():
    """Create a proper .env file specifically for EC2 environment"""
    env_content = """# EC2 Configuration - Created by setup script
ENABLE_HTTPS_REDIRECT=false

# API Configuration
LOG_LEVEL=INFO

# Uncomment and set these as needed
# DATABASE_URL=postgresql://user:password@localhost/dbname
"""
    
    # Backup existing .env if present
    if os.path.exists(".env"):
        backup_path = f".env.backup.{int(time.time())}"
        shutil.copy2(".env", backup_path)
        print(f"Backed up existing .env to {backup_path}")
    
    # Write new .env file
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("Created new .env file with HTTPS redirects disabled")
    return True

def create_systemd_service():
    """Create a systemd service for the FastAPI application"""
    service_content = """[Unit]
Description=FastAPI Application Service
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/path/to/your/app
Environment="ENABLE_HTTPS_REDIRECT=false"
ExecStart=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
"""

    # Get current working directory
    current_path = os.getcwd()
    
    # Replace placeholder with actual path
    service_content = service_content.replace("/path/to/your/app", current_path)
    
    service_path = "/tmp/fastapi_app.service"
    with open(service_path, "w") as f:
        f.write(service_content)
    
    print(f"Created systemd service file at {service_path}")
    print("To install the service, run:")
    print(f"sudo cp {service_path} /etc/systemd/system/")
    print("sudo systemctl daemon-reload")
    print("sudo systemctl enable fastapi_app")
    print("sudo systemctl start fastapi_app")
    
    return service_path

def modify_nginx_config():
    """Create a sample NGINX configuration for the FastAPI application"""
    nginx_config = """
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # For serving static files if needed
    location /static/ {
        alias /path/to/your/app/static/;
    }
}
"""
    
    config_path = "/tmp/fastapi_nginx.conf"
    with open(config_path, "w") as f:
        f.write(nginx_config)
    
    print(f"Created NGINX configuration at {config_path}")
    print("To use this configuration:")
    print(f"1. Edit {config_path} to update your domain and paths")
    print(f"2. sudo cp {config_path} /etc/nginx/conf.d/fastapi_app.conf")
    print("3. sudo systemctl restart nginx")
    
    return config_path

def run_server_directly():
    """Run the FastAPI server directly with proper environment variables"""
    # Set environment variables
    os.environ["ENABLE_HTTPS_REDIRECT"] = "false"
    
    # Check if Python is in the path
    python_cmd = sys.executable
    
    # Build the uvicorn command
    cmd = [
        python_cmd,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
    ]
    
    print(f"Starting FastAPI server on EC2 with HTTPS redirects disabled...")
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

def main():
    parser = argparse.ArgumentParser(description="EC2 Configuration Script for FastAPI Application")
    parser.add_argument("--setup", action="store_true", help="Set up the environment file")
    parser.add_argument("--service", action="store_true", help="Create systemd service")
    parser.add_argument("--nginx", action="store_true", help="Create NGINX configuration")
    parser.add_argument("--run", action="store_true", help="Run the server directly")
    
    args = parser.parse_args()
    
    if args.setup:
        setup_environment_file()
    
    if args.service:
        create_systemd_service()
    
    if args.nginx:
        modify_nginx_config()
    
    if args.run:
        return run_server_directly()
    
    if not (args.setup or args.service or args.nginx or args.run):
        print("No actions specified. Use --help to see available options.")
        parser.print_help()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 