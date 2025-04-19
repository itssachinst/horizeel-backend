#!/bin/bash
# EC2 Fix Script for 307 Redirect Issue
# Run this script in your FastAPI application directory on EC2

echo "=== EC2 HTTPS Redirect Fix Script ==="
echo "This script will fix the 307 Temporary Redirect issue in your EC2 instance."

# Create proper .env file
echo "Creating .env file..."
cat > .env << EOF
# EC2 Configuration - Set by fix script
ENABLE_HTTPS_REDIRECT=false

# API Configuration
LOG_LEVEL=INFO

# Add other needed environment variables here
EOF

echo ".env file created with HTTPS redirects disabled."

# Create systemd service definition
echo "Creating systemd service definition..."
SERVICE_FILE=/tmp/fastapi_app.service
CURRENT_DIR=$(pwd)
cat > $SERVICE_FILE << EOF
[Unit]
Description=FastAPI Application Service
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=$CURRENT_DIR
Environment="ENABLE_HTTPS_REDIRECT=false"
ExecStart=$(which python3) -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

echo "Service file created at $SERVICE_FILE"

# Instructions for installation
echo "==========================================="
echo "To install the service, run:"
echo "sudo cp $SERVICE_FILE /etc/systemd/system/fastapi_app.service"
echo "sudo systemctl daemon-reload"
echo "sudo systemctl enable fastapi_app"
echo "sudo systemctl start fastapi_app"
echo "==========================================="

# Offer to run the app directly
echo "Would you like to run the application directly now? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Starting FastAPI application with HTTPS redirects disabled..."
    export ENABLE_HTTPS_REDIRECT=false
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    echo "Not running the application. You can start it manually or use the systemd service."
fi 