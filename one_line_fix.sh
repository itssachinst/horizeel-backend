#!/bin/bash
# One-line fix for EC2 redirect issues
sed -i.bak '/@app.middleware("http")/,/async def redirect_to_https/ s/async def redirect_to_https/async def redirect_to_https\n    return await call_next(request)  # Added by one_line_fix.sh\n    # Original code bypassed/' app/main.py && echo "Fix applied! Redirects disabled. Backup saved as app/main.py.bak" 