# Quick Fix for 307 Redirect Issues on EC2

If you're experiencing 307 Temporary Redirect issues on your EC2 instance, use one of these solutions:

## Option 1: One-Command Fix (Recommended)

Run this single command in your project directory:

```bash
sed -i.bak '/@app.middleware("http")/,/async def redirect_to_https/ s/async def redirect_to_https/async def redirect_to_https\n    return await call_next(request)  # EC2 fix\n    # Original code bypassed/' app/main.py && echo "Fix applied! Redirects disabled."
```

This directly modifies the code to bypass all redirects. A backup of your original file is saved as `app/main.py.bak`.

## Option 2: Run with Environment Variable

If you prefer not to modify the code, run with the environment variable:

```bash
# Create script
cat > run_app.sh << 'EOF'
#!/bin/bash
export ENABLE_HTTPS_REDIRECT=false
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
EOF

# Make executable
chmod +x run_app.sh

# Run it
./run_app.sh
```

## Option 3: Set Up as System Service

For a permanent solution:

```bash
# Create service file
sudo tee /etc/systemd/system/fastapi_app.service > /dev/null << EOF
[Unit]
Description=FastAPI Application
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=$(pwd)
Environment="ENABLE_HTTPS_REDIRECT=false"
ExecStart=$(which python3) -m uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable fastapi_app
sudo systemctl start fastapi_app

# Check status
sudo systemctl status fastapi_app
```

## Verifying the Fix

Test your API endpoint directly:

```bash
curl http://localhost:8000/api/videos?skip=0&limit=20
```

If successful, you'll get a proper JSON response instead of a 307 redirect.

## Troubleshooting

If you still have issues:

1. Make sure the service is running:
   ```bash
   sudo systemctl status fastapi_app
   ```

2. Check the logs:
   ```bash
   sudo journalctl -u fastapi_app -n 50
   ```

3. Verify the environment variable is set:
   ```bash
   sudo systemctl show fastapi_app | grep Environment
   ``` 