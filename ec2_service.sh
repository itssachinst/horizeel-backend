#!/bin/bash
# EC2 Service Setup Script
# Creates and enables a systemd service with HTTPS redirects disabled

echo "=== EC2 Service Setup ==="
echo "This script creates a systemd service that will properly run your FastAPI app on EC2."

# Get current directory and username
CURRENT_DIR=$(pwd)
CURRENT_USER=$(whoami)

# Create service file
SERVICE_FILE="/tmp/fastapi_app.service"
echo "Creating systemd service file..."
cat > "$SERVICE_FILE" << EOF
[Unit]
Description=FastAPI Application Service
After=network.target

[Service]
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
# This environment variable is CRITICAL
Environment="ENABLE_HTTPS_REDIRECT=false"
ExecStart=$(which python3) -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
# Ensure the service restarts if it fails
RestartSec=5
# Redirect stdout and stderr to syslog
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=fastapi_app

[Install]
WantedBy=multi-user.target
EOF

echo "Service file created at $SERVICE_FILE"

# Ask to install the service
echo "Do you want to install and start the service now? (requires sudo) (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Installing systemd service..."
    sudo cp "$SERVICE_FILE" /etc/systemd/system/fastapi_app.service
    
    echo "Reloading systemd daemon..."
    sudo systemctl daemon-reload
    
    echo "Enabling service to start on boot..."
    sudo systemctl enable fastapi_app
    
    echo "Starting service..."
    sudo systemctl start fastapi_app
    
    echo "Service status:"
    sudo systemctl status fastapi_app
    
    echo "==========================================="
    echo "Service installed and started!"
    echo "To check logs: sudo journalctl -u fastapi_app"
    echo "To restart: sudo systemctl restart fastapi_app"
    echo "To stop: sudo systemctl stop fastapi_app"
    echo "==========================================="
else
    echo "Service not installed. To install later, run:"
    echo "sudo cp $SERVICE_FILE /etc/systemd/system/fastapi_app.service"
    echo "sudo systemctl daemon-reload"
    echo "sudo systemctl enable fastapi_app"
    echo "sudo systemctl start fastapi_app"
fi 