# User API Documentation

This document describes the API endpoints for user management in the backend.

## Base URL
All endpoints are prefixed with `/api/users`

## Authentication
Most endpoints require authentication using a JWT token. The token should be included in the `Authorization` header as `Bearer <token>`. See [AUTH_API_DOCUMENTATION.md](AUTH_API_DOCUMENTATION.md) for detailed authentication information.

## Endpoints

### Register a New User
- **URL**: `/register`
- **Method**: `POST`
- **Auth required**: No
- **Request Body**:
  ```json
  {
    "username": "string",
    "email": "user@example.com",
    "password": "string"
  }
  ```
- **Success Response**: 
  - **Code**: 201 CREATED
  - **Content**:
    ```json
    {
      "user_id": "string (uuid)",
      "username": "string",
      "email": "user@example.com",
      "profile_picture": "string (url) or null",
      "cover_image": "string (url) or null",
      "created_at": "datetime"
    }
    ```
- **Error Responses**:
  - **Code**: 400 BAD REQUEST
  - **Content**: `{"detail": "Email already registered"}` or `{"detail": "Username already taken"}`

### User Login
- **URL**: `/login`
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

### Get Current User's Profile
- **URL**: `/me`
- **Method**: `GET`
- **Auth required**: Yes (token)
- **Headers**:
  - `Authorization: Bearer <token>`
- **Success Response**: 
  - **Code**: 200 OK
  - **Content**:
    ```json
    {
      "user_id": "string (uuid)",
      "username": "string",
      "email": "user@example.com",
      "profile_picture": "string (url) or null",
      "cover_image": "string (url) or null", 
      "created_at": "datetime"
    }
    ```
- **Error Response**:
  - **Code**: 401 UNAUTHORIZED
  - **Content**: `{"detail": "Could not validate credentials"}`

### Get All Users
- **URL**: `/`
- **Method**: `GET`
- **Auth required**: No
- **Query Parameters**:
  - `skip`: integer (default 0) - Number of records to skip
  - `limit`: integer (default 100) - Maximum number of records to return
- **Success Response**: 
  - **Code**: 200 OK
  - **Content**:
    ```json
    [
      {
        "user_id": "string (uuid)",
        "username": "string",
        "email": "user@example.com",
        "profile_picture": "string (url) or null",
        "cover_image": "string (url) or null",
        "created_at": "datetime"
      },
      ...
    ]
    ```

### Get User by ID
- **URL**: `/{user_id}`
- **Method**: `GET`
- **Auth required**: No
- **URL Parameters**:
  - `user_id`: string (uuid) - The ID of the user to retrieve
- **Success Response**: 
  - **Code**: 200 OK
  - **Content**:
    ```json
    {
      "user_id": "string (uuid)",
      "username": "string",
      "email": "user@example.com",
      "profile_picture": "string (url) or null",
      "cover_image": "string (url) or null",
      "created_at": "datetime"
    }
    ```
- **Error Response**:
  - **Code**: 404 NOT FOUND
  - **Content**: `{"detail": "User not found"}`

### Update User
- **URL**: `/{user_id}`
- **Method**: `PUT`
- **Auth required**: Yes (token, and must be the same user)
- **Headers**:
  - `Authorization: Bearer <token>`
- **URL Parameters**:
  - `user_id`: string (uuid) - The ID of the user to update
- **Request Body**:
  ```json
  {
    "username": "string or null",
    "email": "user@example.com or null",
    "password": "string or null",
    "profile_picture": "string (url) or null",
    "cover_image": "string (url) or null"
  }
  ```
  *Note: Only include fields you want to update*
- **Success Response**: 
  - **Code**: 200 OK
  - **Content**:
    ```json
    {
      "user_id": "string (uuid)",
      "username": "string",
      "email": "user@example.com",
      "profile_picture": "string (url) or null",
      "cover_image": "string (url) or null",
      "created_at": "datetime"
    }
    ```
- **Error Responses**:
  - **Code**: 401 UNAUTHORIZED - If not authenticated
  - **Code**: 403 FORBIDDEN - If trying to update another user's profile
  - **Code**: 404 NOT FOUND - If user doesn't exist

### Delete User
- **URL**: `/{user_id}`
- **Method**: `DELETE`
- **Auth required**: Yes (token, and must be the same user)
- **Headers**:
  - `Authorization: Bearer <token>`
- **URL Parameters**:
  - `user_id`: string (uuid) - The ID of the user to delete
- **Success Response**: 
  - **Code**: 204 NO CONTENT
- **Error Responses**:
  - **Code**: 401 UNAUTHORIZED - If not authenticated
  - **Code**: 403 FORBIDDEN - If trying to delete another user's account
  - **Code**: 404 NOT FOUND - If user doesn't exist 