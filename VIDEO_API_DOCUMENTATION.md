# Video API Documentation

This document describes the API endpoints for video management in the backend.

## Base URL
All endpoints are prefixed with `/api`

## Authentication
The upload endpoint requires authentication using a JWT token. The token should be included in the `Authorization` header as `Bearer <token>`.

## Endpoints

### Upload a Video
- **URL**: `/videos/`
- **Method**: `POST`
- **Auth required**: Yes
- **Request Body**: Multipart Form
  - `title`: string (required) - The title of the video
  - `description`: string (required) - The description of the video
  - `vfile`: file (required) - The video file to upload
  - `tfile`: file (required) - The thumbnail image for the video
- **Success Response**: 
  - **Code**: 201 CREATED
  - **Content**:
    ```json
    {
      "video_id": "string (uuid)",
      "title": "string",
      "description": "string",
      "video_url": "string (url)",
      "thumbnail_url": "string (url)",
      "created_at": "datetime",
      "views": 0,
      "likes": 0,
      "dislikes": 0,
      "user_id": "string (uuid)",
      "username": "string"
    }
    ```
- **Error Responses**:
  - **Code**: 401 UNAUTHORIZED - If not authenticated
  - **Code**: 400 BAD REQUEST - If required fields are missing

### Search Videos
- **URL**: `/videos/search/`
- **Method**: `GET`
- **Auth required**: No
- **Query Parameters**:
  - `query`: string (required) - The search term to look for in video titles and descriptions
- **Success Response**: 
  - **Code**: 200 OK
  - **Content**:
    ```json
    [
      {
        "video_id": "string (uuid)",
        "title": "string",
        "description": "string",
        "video_url": "string (url)",
        "thumbnail_url": "string (url)",
        "created_at": "datetime",
        "views": integer,
        "likes": integer,
        "dislikes": integer,
        "user_id": "string (uuid)",
        "username": "string"
      },
      ...
    ]
    ```

### Get Video by ID
- **URL**: `/videos/{video_id}`
- **Method**: `GET`
- **Auth required**: No
- **URL Parameters**:
  - `video_id`: string (uuid) - The ID of the video to retrieve
- **Success Response**: 
  - **Code**: 200 OK
  - **Content**:
    ```json
    {
      "video_id": "string (uuid)",
      "title": "string",
      "description": "string",
      "video_url": "string (url)",
      "thumbnail_url": "string (url)",
      "created_at": "datetime",
      "views": integer,
      "likes": integer,
      "dislikes": integer,
      "user_id": "string (uuid)",
      "username": "string"
    }
    ```
- **Error Response**:
  - **Code**: 404 NOT FOUND - If video doesn't exist

### List All Videos
- **URL**: `/videos/`
- **Method**: `GET`
- **Auth required**: No
- **Success Response**: 
  - **Code**: 200 OK
  - **Content**:
    ```json
    [
      {
        "video_id": "string (uuid)",
        "title": "string",
        "description": "string",
        "video_url": "string (url)",
        "thumbnail_url": "string (url)",
        "created_at": "datetime",
        "views": integer,
        "likes": integer,
        "dislikes": integer,
        "user_id": "string (uuid)",
        "username": "string"
      },
      ...
    ]
    ```

### Increment Video Views
- **URL**: `/videos/{video_id}/view`
- **Method**: `POST`
- **Auth required**: No
- **URL Parameters**:
  - `video_id`: string (uuid) - The ID of the video
- **Success Response**: 
  - **Code**: 200 OK
  - **Content**:
    ```json
    {
      "message": "View count incremented successfully",
      "views": integer
    }
    ```

### Increment Video Likes
- **URL**: `/videos/{video_id}/like`
- **Method**: `POST`
- **Auth required**: No
- **URL Parameters**:
  - `video_id`: string (uuid) - The ID of the video
- **Success Response**: 
  - **Code**: 200 OK
  - **Content**:
    ```json
    {
      "message": "View count incremented successfully",
      "likes": integer
    }
    ```

### Increment Video Dislikes
- **URL**: `/videos/{video_id}/dislike`
- **Method**: `POST`
- **Auth required**: No
- **URL Parameters**:
  - `video_id`: string (uuid) - The ID of the video
- **Success Response**: 
  - **Code**: 200 OK
  - **Content**:
    ```json
    {
      "message": "View count incremented successfully",
      "dislikes": integer
    }
    ```

### Increment Video Subscribers
- **URL**: `/videos/{video_id}/subscribe`
- **Method**: `POST`
- **Auth required**: No
- **URL Parameters**:
  - `video_id`: string (uuid) - The ID of the video
- **Success Response**: 
  - **Code**: 200 OK
  - **Content**:
    ```json
    {
      "message": "View count incremented successfully",
      "subscribers": integer
    }
    ``` 