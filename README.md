# API Backend

## Development Setup

### Environment Configuration

To avoid the HTTPS redirect issues in development, create a `.env` file in the root directory (copy from `.env.example`):

```
# Set this to false in development to avoid HTTPS redirects
ENABLE_HTTPS_REDIRECT=false
```

### Running the Application

1. Install dependencies:
```
pip install -r requirements.txt
```

2. Run database migrations:
```
alembic upgrade head
```

3. Start the development server:
```
uvicorn app.main:app --reload
```

## API Endpoints

The API will be available at `http://localhost:8000/api/`

- Health Check: `GET /api/health`
- API Documentation: `GET /api/docs`

## Troubleshooting

### 307 Temporary Redirect

If you're experiencing 307 Temporary Redirect responses:

1. Ensure `ENABLE_HTTPS_REDIRECT=false` is set in your `.env` file
2. Restart the application
3. For API clients, make sure your requests don't include browser user-agent strings (which may trigger HTTPS redirects)

#### Explanation of the Fix

The 307 redirects were happening because:
- The HTTPS redirect middleware was enabled by default
- It was redirecting all requests, even API clients
- It wasn't properly handling paths with or without trailing slashes

Our solution:
1. Made the middleware skip redirects for API clients (non-browser requests)
2. Added proper handling for both `/api/health` and `/api/health/` paths
3. Improved the logic to skip redirects for localhost and already-HTTPS connections
4. Added runtime environment variable checking for easier testing

### 401 Unauthorized

For authenticated endpoints like `/api/users/me`:

1. Get a token using the `/api/auth/login` endpoint
2. Include the token in your requests with the Authorization header:
   `Authorization: Bearer YOUR_TOKEN_HERE` 