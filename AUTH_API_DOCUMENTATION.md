# Authentication API Documentation

This document describes the authentication system and related endpoints in the backend.

## Base URL
All endpoints are prefixed with `/api`

## Authentication Overview
The system uses JWT (JSON Web Tokens) for authentication. Tokens are short-lived (30 minutes by default) and must be included in the `Authorization` header for protected endpoints.

### Token Format
- **Header**: `Authorization: Bearer <token>`
- **Token Type**: JWT
- **Algorithm**: HS256
- **Expiration**: 30 minutes
- **Token Payload**:
  ```json
  {
    "sub": "user-uuid-string",
    "exp": "timestamp"
  }
  ```

## Endpoints

### Login
- **URL**: `/users/login`
- **Method**: `POST`
- **Auth required**: No
- **Request Body**: Form Data
  ```
  username: string (email)
  password: string
  ```
- **Success Response**: 
  - **Code**: 200 OK
  - **Content**:
    ```json
    {
      "access_token": "string",
      "token_type": "bearer",
      "user_id": "string (uuid)"
    }
    ```
- **Error Response**:
  - **Code**: 401 UNAUTHORIZED
  - **Content**: `{"detail": "Incorrect email or password"}`

### Token Endpoint (OAuth2)
- **URL**: `/token`
- **Method**: `POST`
- **Auth required**: No
- **Request Body**: Form Data
  ```
  username: string (email)
  password: string
  grant_type: password
  ```
- **Success Response**: 
  - **Code**: 200 OK
  - **Content**:
    ```json
    {
      "access_token": "string",
      "token_type": "bearer"
    }
    ```
- **Error Response**:
  - **Code**: 401 UNAUTHORIZED
  - **Content**: `{"detail": "Incorrect username or password"}`

## Security Notes
1. Tokens are short-lived (30 minutes) for security
2. Passwords are hashed using bcrypt
3. All protected endpoints require the `Authorization` header
4. Invalid or expired tokens will return 401 Unauthorized
5. The system supports both form-based and JSON-based authentication

## Error Handling
- **401 Unauthorized**: Invalid or expired token
- **403 Forbidden**: Valid token but insufficient permissions
- **400 Bad Request**: Invalid request format
- **500 Internal Server Error**: Server-side error

## Best Practices
1. Always store tokens securely (e.g., in memory or secure storage)
2. Implement token refresh mechanism on the client side
3. Include the `Authorization` header in all protected requests
4. Handle token expiration gracefully
5. Use HTTPS in production environments 