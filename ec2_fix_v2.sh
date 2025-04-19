#!/bin/bash
# EC2 Fix V2 - Complete solution for 307 Redirect issues
# This script directly modifies the code to ensure redirects never happen

echo "=== EC2 HTTPS Redirect Fix v2 ==="
echo "This script applies a direct fix to the code to prevent all redirects."

# 1. Create a backup of main.py before modifying it
MAIN_PY_PATH="app/main.py"
BACKUP_PATH="app/main.py.bak.$(date +%s)"

if [ -f "$MAIN_PY_PATH" ]; then
    echo "Creating backup of main.py to $BACKUP_PATH"
    cp "$MAIN_PY_PATH" "$BACKUP_PATH"
else
    echo "Error: Cannot find $MAIN_PY_PATH. Make sure you're running this script from the project root."
    exit 1
fi

# 2. Directly modify the middleware to completely disable redirects
echo "Modifying the redirect middleware in main.py..."

# Find the middleware function and replace it
awk '
/^@app.middleware\("http"\)/{
    print $0;
    getline;
    print $0;
    print "    # IMPORTANT: Skip all redirects for EC2 deployment";
    print "    # This was added by the ec2_fix_v2.sh script";
    print "    return await call_next(request)";
    print "";
    print "    # The code below is bypassed to fix 307 redirects";
    in_middleware = 1;
    next;
}
in_middleware && /^def / {
    in_middleware = 0;
}
{print $0}' "$BACKUP_PATH" > "$MAIN_PY_PATH"

echo "Modified main.py to bypass redirects completely."

# 3. Create/update .env file as an additional precaution
echo "Updating .env file..."
cat > .env << EOF
# EC2 Configuration - Created by ec2_fix_v2.sh
# CRITICAL: This setting disables HTTPS redirects
ENABLE_HTTPS_REDIRECT=false

# API Configuration
LOG_LEVEL=INFO
EOF

echo ".env file updated."

# 4. Create a script to run the app with the environment variable directly set
echo "Creating startup script..."
cat > start_app.sh << EOF
#!/bin/bash
# Start the FastAPI app with HTTPS redirects disabled
export ENABLE_HTTPS_REDIRECT=false
echo "Starting app with ENABLE_HTTPS_REDIRECT=\$ENABLE_HTTPS_REDIRECT"
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
EOF

chmod +x start_app.sh
echo "Created executable startup script: start_app.sh"

# 5. Instructions
echo "==========================================="
echo "Fix applied! To start the application:"
echo "./start_app.sh"
echo "==========================================="
echo "This fix directly modifies the code to bypass redirects completely."
echo "The 307 redirect issue should now be resolved."

# 6. Offer to run
echo "Would you like to start the application now? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    export ENABLE_HTTPS_REDIRECT=false
    echo "Starting app with ENABLE_HTTPS_REDIRECT=$ENABLE_HTTPS_REDIRECT"
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    echo "You can start the app later using: ./start_app.sh"
fi 