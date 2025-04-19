#!/bin/bash
# Quick fix for EC2 instance to solve 307 Temporary Redirect issues
echo "ENABLE_HTTPS_REDIRECT=false" > .env
echo "Quick fix applied - Start your server and the redirects should be fixed!" 