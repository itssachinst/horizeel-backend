# Watch History Functionality

This document describes the watch history tracking functionality implemented in the backend.

## Table Structure

The `watched_videos` table tracks user viewing history and engagement metrics for videos. It contains the following fields:

| Field             | Type      | Description                                           |
|-------------------|-----------|-------------------------------------------------------|
| id                | UUID      | Primary key                                           |
| user_id           | UUID      | Foreign key to users table                            |
| video_id          | UUID      | Foreign key to videos table                           |
| like_flag         | Boolean   | Whether the user liked the video                      |
| dislike_flag      | Boolean   | Whether the user disliked the video                   |
| saved_flag        | Boolean   | Whether the user saved the video                      |
| shared_flag       | Boolean   | Whether the user shared the video                     |
| watch_time        | Float     | Time in seconds the user watched the video            |
| watch_percentage  | Float     | Percentage of the video watched (0-100)               |
| completed         | Boolean   | Whether the user watched the video to completion      |
| last_position     | Float     | Last position in the video in seconds                 |
| first_watched_at  | Timestamp | When the user first watched the video                 |
| last_watched_at   | Timestamp | When the user last watched the video                  |
| watch_count       | Integer   | Number of times the user watched this video           |
| device_type       | String    | Type of device used (mobile, desktop, tablet, etc.)   |

## API Endpoints

### Update Watch History

```
POST /videos/watch-history
```

Updates a user's watch history for a video. If no record exists for this user-video pair, a new one is created.

**Request Body:**
```json
{
  "video_id": "uuid-string",
  "watch_time": 120.5,
  "watch_percentage": 45.0,
  "completed": false,
  "last_position": 120.5,
  "like_flag": true,
  "dislike_flag": false,
  "saved_flag": true,
  "shared_flag": false,
  "device_type": "mobile"
}
```

**Response:**
```json
{
  "id": "uuid-string",
  "video_id": "uuid-string",
  "user_id": "uuid-string",
  "watch_time": 120.5,
  "watch_percentage": 45.0,
  "completed": false,
  "last_position": 120.5,
  "like_flag": true,
  "dislike_flag": false,
  "saved_flag": true,
  "shared_flag": false,
  "watch_count": 3,
  "first_watched_at": "2023-04-01T12:00:00Z",
  "last_watched_at": "2023-04-01T12:02:00Z",
  "device_type": "mobile"
}
```

### Get Watch History

```
GET /videos/watch-history?limit=50&skip=0
```

Gets a user's watch history. Returns the most recently watched videos first.

**Query Parameters:**
- `limit` (optional): Maximum number of records to return. Default is 50.
- `skip` (optional): Number of records to skip. Default is 0.

**Response:**
```json
[
  {
    "id": "uuid-string",
    "video_id": "uuid-string",
    "user_id": "uuid-string",
    "watch_time": 120.5,
    "watch_percentage": 45.0,
    "completed": false,
    "last_position": 120.5,
    "like_flag": true,
    "dislike_flag": false,
    "saved_flag": true,
    "shared_flag": false,
    "watch_count": 3,
    "first_watched_at": "2023-04-01T12:00:00Z",
    "last_watched_at": "2023-04-01T12:02:00Z",
    "device_type": "mobile"
  },
  // More watch history records...
]
```

### Get Video Watch Stats

```
GET /videos/{video_id}/watch-stats
```

Get a user's watch statistics for a specific video.

**Path Parameters:**
- `video_id`: UUID of the video

**Response:**
```json
{
  "id": "uuid-string",
  "video_id": "uuid-string",
  "user_id": "uuid-string",
  "watch_time": 120.5,
  "watch_percentage": 45.0,
  "completed": false,
  "last_position": 120.5,
  "like_flag": true,
  "dislike_flag": false,
  "saved_flag": true,
  "shared_flag": false,
  "watch_count": 3,
  "first_watched_at": "2023-04-01T12:00:00Z",
  "last_watched_at": "2023-04-01T12:02:00Z",
  "device_type": "mobile"
}
```

### Delete Watch History

```
DELETE /videos/watch-history/{video_id}
```

Delete a user's watch history for a specific video.

**Path Parameters:**
- `video_id`: UUID of the video

**Response:**
```json
{
  "message": "Watch history for video with ID {video_id} deleted successfully"
}
```

## Usage in Frontend

To track user watch history, the frontend should:

1. Update the watch history whenever a user watches a video
2. Track engagement metrics like likes, dislikes, saves, and shares
3. Send regular updates to the backend with the current watch position
4. Send a final update when the user finishes watching the video

Example of sending watch history updates from the frontend:

```javascript
// Example function to update watch history (call this at regular intervals)
async function updateWatchHistory(video, watchTime, isCompleted) {
  const watchData = {
    video_id: video.video_id,
    watch_time: watchTime,
    watch_percentage: (watchTime / video.duration) * 100,
    completed: isCompleted,
    last_position: watchTime,
    like_flag: video.isLiked,
    dislike_flag: video.isDisliked,
    saved_flag: video.isSaved,
    shared_flag: video.isShared,
    device_type: isMobile ? 'mobile' : 'desktop'
  };

  try {
    const response = await fetch('/api/videos/watch-history', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(watchData)
    });
    
    if (!response.ok) {
      console.error('Failed to update watch history');
    }
  } catch (error) {
    console.error('Error updating watch history:', error);
  }
}
```

## Setting Up the Database

To create the `watched_videos` table in the database, run:

```
python create_watched_videos_table.py
```

To check the table and insert test data:

```
python check_watched_videos_table.py
```

## Analytics Possibilities

With this watch history data, you can:

1. Track user engagement patterns
2. Identify which videos are most frequently rewatched
3. Analyze drop-off points in videos
4. Generate personalized recommendations
5. Create watch history UIs for users to resume videos
6. Calculate average completion rates for videos
7. Identify which devices are most commonly used for watching 