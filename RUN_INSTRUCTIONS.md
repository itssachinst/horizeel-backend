# Running the API with Fixed Redirect Logic

Follow these steps to fix the 307 Temporary Redirect issues:

## IMPORTANT: Use the provided startup scripts

We've created special startup scripts that ensure the environment variables are set correctly:

### Option 1: Using Python script (recommended for all platforms)

```bash
# Run the Python script to start the server with proper environment variables
python start_server.py
```

### Option 2: Using platform-specific scripts

**Windows:**
```
start_api.bat
```

**Linux/Mac:**
```bash
chmod +x start_api.sh  # Make executable (one time)
./start_api.sh
```

### Option 3: Manual setup

If you prefer to start the server manually:

1. Create a `.env` file in the root directory with:
```
ENABLE_HTTPS_REDIRECT=false
```

2. Set the environment variable before starting the server:
   
   **Windows (PowerShell):**
   ```
   $env:ENABLE_HTTPS_REDIRECT = "false"
   uvicorn app.main:app --reload
   ```
   
   **Windows (Command Prompt):**
   ```
   set ENABLE_HTTPS_REDIRECT=false
   uvicorn app.main:app --reload
   ```
   
   **Linux/Mac:**
   ```bash
   export ENABLE_HTTPS_REDIRECT=false
   uvicorn app.main:app --reload
   ```

## Testing API endpoints

Test the API endpoints to confirm they no longer redirect:

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/videos?skip=0&limit=20
```

If using a browser, you might still get redirected (which is expected for browser requests).

## For mobile apps and other API clients

The updated middleware logic will:
1. Never redirect non-browser API clients
2. Explicitly allow access to the /api/videos endpoint without redirects
3. Skip redirects for localhost and development environments

## For production deployment

In production:
- Set `ENABLE_HTTPS_REDIRECT=true` in your production environment
- Ensure your load balancer/reverse proxy is correctly configured with HTTPS
- The API will redirect browser requests to HTTPS but allow API clients to connect over HTTP

## Troubleshooting

If you're still experiencing 307 redirects:

1. Check logs to see if your requests are being identified as browser requests
2. Try setting a custom User-Agent header that doesn't include "Mozilla"
3. Restart your server completely after making changes to environment variables
4. Verify that the middleware changes were applied correctly 