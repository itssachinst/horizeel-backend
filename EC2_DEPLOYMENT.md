# EC2 Deployment Guide

This guide provides instructions for deploying your FastAPI application to an EC2 instance while fixing the 307 Temporary Redirect issue.

## Quick Fix

For a quick fix to the 307 Temporary Redirect issue, run:

```bash
# Download the fix script
curl -o ec2_fix.sh https://raw.githubusercontent.com/yourusername/yourrepo/main/ec2_fix.sh

# Make it executable
chmod +x ec2_fix.sh

# Run the script
./ec2_fix.sh
```

## Manual Setup

If you prefer to set things up manually, follow these steps:

### 1. Environment Variables

Create a `.env` file with:

```
ENABLE_HTTPS_REDIRECT=false
```

### 2. Run as a Systemd Service

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/fastapi_app.service
```

Add the following content (update paths as needed):

```
[Unit]
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
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable fastapi_app
sudo systemctl start fastapi_app
```

## Using NGINX as a Reverse Proxy

If you want to use NGINX as a reverse proxy (recommended for production):

1. Install NGINX:
   ```bash
   sudo yum install nginx
   ```

2. Create a configuration file:
   ```bash
   sudo nano /etc/nginx/conf.d/fastapi_app.conf
   ```

3. Add the following content:
   ```
   server {
       listen 80;
       server_name your-domain-or-ip;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

4. Start NGINX:
   ```bash
   sudo systemctl enable nginx
   sudo systemctl start nginx
   ```

## Troubleshooting the 307 Redirect Issue

If you still face 307 redirect issues:

1. **Verify environment variable**: Make sure `ENABLE_HTTPS_REDIRECT=false` is properly set:
   ```bash
   # Check if it's set in the current environment
   echo $ENABLE_HTTPS_REDIRECT
   
   # Check if it's set in the systemd service
   sudo systemctl cat fastapi_app.service | grep Environment
   ```

2. **Check logs**: Look for redirect messages in your application logs:
   ```bash
   sudo journalctl -u fastapi_app.service
   ```

3. **Update the code**: You may need to modify your FastAPI application's middleware to handle EC2-specific headers:
   ```python
   # Add this to your middleware function
   # EC2 with load balancer often uses different header conventions
   is_ec2 = "ec2" in host or "amazonaws" in host
   if is_ec2:
       logger.info(f"EC2 environment detected, skipping HTTPS redirect for {path}")
       return await call_next(request)
   ```

4. **Force disable redirects**: As a last resort, you can modify the main.py file to completely disable the redirect logic.

## Security Considerations

When disabling HTTPS redirects:

1. If you're using a load balancer or CloudFront, ensure HTTPS is configured there
2. Consider setting up security groups to restrict access to your EC2 instance
3. For production deployments, use NGINX with proper SSL configuration 