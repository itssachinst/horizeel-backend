# Running the API with Fixed Redirect Logic

Follow these steps to fix the 307 Temporary Redirect issues:

## 1. Create or update .env file

Create a `.env` file in the root directory (where `main.py` is located) with:

```
ENABLE_HTTPS_REDIRECT=false
```

## 2. Restart the API server

```bash
# Stop any running instances
# Then start the server with:
uvicorn app.main:app --reload
```

## 3. Testing API endpoints

Test the API endpoints to confirm they no longer redirect:

```bash
curl http://localhost:8000/api/health
curl http://localhost:8000/api/videos?skip=0&limit=20
```

If using a browser, you might still get redirected (which is expected for browser requests).

## 4. For mobile apps and other API clients

For mobile apps and API clients:
- Make sure your client doesn't include browser-like User-Agent headers
- Use the `.env` settings to control the redirect behavior in development

## 5. For production deployment

In production:
- Set `ENABLE_HTTPS_REDIRECT=true` in your production environment
- Ensure your load balancer/reverse proxy is correctly configured with HTTPS
- The API will redirect browser requests to HTTPS but allow API clients to connect over HTTP 