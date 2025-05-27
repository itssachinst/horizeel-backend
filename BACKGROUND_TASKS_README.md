# FastAPI BackgroundTasks for Video Processing

This document describes the implementation of FastAPI's BackgroundTasks feature for asynchronous video processing.

## Overview

Video uploads are now handled asynchronously to improve user experience and API performance. When a video is uploaded, the API immediately returns a success response while video processing (conversion, compression, S3 upload) happens in the background.

## Architecture

### Components

1. **Background Task Module** (`app/utils/background_tasks.py`)
   - Contains background processing functions
   - Handles video conversion and S3 upload
   - Updates video status in database

2. **Updated Video Model** (`app/models.py`)
   - Extended status enum with processing states
   - Default status is now 'processing'

3. **Modified Upload Endpoints** (`app/routes/video.py`)
   - Immediate response after file acceptance
   - Background task registration
   - Status checking endpoint

4. **Database Migration** (`update_video_status_migration.py`)
   - Updates existing enum to include new states
   - Migrates existing videos to 'ready' status

## Video Processing States

| Status | Description |
|--------|-------------|
| `processing` | Video is being processed (default for new uploads) |
| `ready` | Video processing completed successfully |
| `failed` | Video processing failed |
| `published` | Video is published and visible (legacy) |
| `draft` | Video is in draft state |
| `private` | Video is private |

## API Endpoints

### Upload Video (Modified)
```http
POST /api/videos/
```

**Changes:**
- Immediately returns response with `status: "processing"`
- Video processing happens in background
- Files are saved to temporary location for processing

**Response:**
```json
{
  "video_id": "uuid",
  "title": "Video Title",
  "description": "Video Description",
  "status": "processing",
  "video_url": "processing",
  "thumbnail_url": "processing",
  "created_at": "2023-01-01T00:00:00Z",
  "user_id": "uuid",
  "username": "user123"
}
```

### Check Video Status (New)
```http
GET /api/videos/{video_id}/status
```

**Response:**
```json
{
  "video_id": "uuid",
  "status": "ready",
  "title": "Video Title",
  "created_at": "2023-01-01T00:00:00Z"
}
```

### Upload YouTube Video (Modified)
```http
POST /api/videos/youtube
```

**Changes:**
- Same background processing approach
- Immediate response with processing status

## Background Processing Flow

### Regular Video Upload

1. **File Reception**
   - API receives video and thumbnail files
   - Validates upload permissions (`uploadFlag`)
   - Creates database entry with `processing` status

2. **Background Task Registration**
   - Saves files to temporary location
   - Registers `process_video_background` task
   - Returns immediate response to client

3. **Background Processing**
   - Validates video files
   - Converts video to HLS format
   - Uploads to S3
   - Updates database with final URLs and `ready` status
   - Cleans up temporary files

### YouTube Video Processing

1. **Request Validation**
   - Validates YouTube URL and parameters
   - Creates database entry with `processing` status

2. **Background Task Registration**
   - Registers `process_youtube_video_background` task
   - Returns immediate response to client

3. **Background Processing**
   - Downloads video from YouTube
   - Clips video to specified duration
   - Converts to HLS format
   - Generates thumbnail
   - Uploads to S3
   - Updates database with final URLs and `ready` status

## Error Handling

### Processing Failures
- Background tasks catch all exceptions
- Failed videos get `failed` status
- Detailed error logging for debugging
- Temporary files are always cleaned up

### Database Consistency
- Separate database sessions for background tasks
- Proper transaction handling
- Rollback on errors

## Frontend Integration

### Polling Strategy
```javascript
async function checkVideoStatus(videoId) {
  const response = await fetch(`/api/videos/${videoId}/status`);
  const status = await response.json();
  
  switch(status.status) {
    case 'processing':
      // Show loading indicator
      // Poll again after delay
      setTimeout(() => checkVideoStatus(videoId), 2000);
      break;
    case 'ready':
      // Video is ready, redirect to video page
      window.location.href = `/videos/${videoId}`;
      break;
    case 'failed':
      // Show error message
      showError('Video processing failed');
      break;
  }
}
```

### Upload Flow
1. User uploads video
2. Show immediate success message
3. Redirect to processing page
4. Poll status endpoint every 2-3 seconds
5. Show progress indicator
6. Redirect to video when ready

## Performance Benefits

### Before (Synchronous)
- Upload blocked until processing complete
- High memory usage for large files
- Timeout issues for long processing
- Poor user experience

### After (Asynchronous)
- Immediate response (< 1 second)
- Lower memory footprint
- No timeout issues
- Better user experience
- Scalable processing

## Configuration

### File Size Limits
```python
# app/main.py
StarletteUploadFile.spool_max_size = 1024 * 1024 * 500  # 500MB
```

### Background Task Settings
- Automatic cleanup of temporary files
- Detailed logging for monitoring
- Database session management

## Migration Instructions

### 1. Run Database Migration
```bash
python update_video_status_migration.py
```

### 2. Update Frontend Code
- Implement status polling
- Update upload success handling
- Add processing indicators

### 3. Monitor Logs
- Check background task execution
- Monitor processing times
- Watch for failed uploads

## Monitoring and Debugging

### Log Messages
```
INFO: Video upload accepted for background processing: {video_id}
INFO: Starting background processing for video {video_id}
INFO: Video conversion completed: {video_url}
INFO: Background processing completed successfully for video {video_id}
ERROR: Background processing failed for video {video_id}: {error}
```

### Status Checking
```bash
# Check video status via API
curl -X GET "http://localhost:8000/api/videos/{video_id}/status"

# Check database directly
SELECT video_id, title, status, created_at FROM videos WHERE status = 'processing';
```

## Security Considerations

### Upload Permissions
- `uploadFlag` check before processing
- User authentication required
- File validation in background tasks

### Resource Management
- Temporary file cleanup
- Memory usage optimization
- Processing time limits (via FFmpeg timeouts)

## Future Enhancements

### Possible Improvements
1. **Progress Tracking**
   - Real-time processing progress
   - Estimated completion time

2. **Queue Management**
   - Priority queues for different user types
   - Rate limiting for processing

3. **Notification System**
   - Email/push notifications when ready
   - WebSocket updates for real-time status

4. **Retry Mechanism**
   - Automatic retry for failed processing
   - Exponential backoff

5. **Analytics**
   - Processing time metrics
   - Failure rate tracking
   - Resource usage monitoring

## Troubleshooting

### Common Issues

1. **Videos Stuck in Processing**
   - Check background task logs
   - Verify FFmpeg installation
   - Check S3 connectivity

2. **Failed Status**
   - Review error logs
   - Check file format compatibility
   - Verify S3 permissions

3. **Temporary File Cleanup**
   - Monitor disk space
   - Check cleanup logs
   - Manual cleanup if needed

### Recovery Procedures

1. **Reset Failed Videos**
   ```sql
   UPDATE videos SET status = 'processing' WHERE status = 'failed';
   ```

2. **Manual Processing**
   - Re-trigger background task
   - Process via admin interface
   - Direct S3 upload

This implementation provides a robust, scalable solution for video processing that significantly improves user experience while maintaining system performance. 