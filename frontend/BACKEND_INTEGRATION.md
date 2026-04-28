# Backend Integration Guide

This guide explains how to connect the frontend with your backend server for video uploads.

## Configuration

### Update API Endpoint

Edit the file: `src/lib/config.ts`

```typescript
export const API_CONFIG = {
  UPLOAD_ENDPOINT: 'http://127.0.0.1:8000/upload-video',
};
```

**Examples:**
- Upload video: `http://127.0.0.1:8000/upload-video`
- List patients: `http://127.0.0.1:8000/patients`
- List videos: `http://127.0.0.1:8000/videos`

## Backend API Requirements

### Upload Endpoint Specification

**Endpoint:** `POST /upload-video`

**Request Format:**
- Content-Type: `multipart/form-data`
- Field name: `video`
- File type: MP4 video file

**Example Request (using FormData):**
```javascript
const formData = new FormData();
formData.append('video', videoFile);
```

### Required Backend Response

**Success Response (Status 200-299):**
```json
{
  "success": true,
  "message": "Video uploaded successfully",
  "videoId": "unique-video-id",
  "url": "http://127.0.0.1:8000/download-video/unique-video-id"
}
```

**Error Response (Status 400+):**
```json
{
  "success": false,
  "error": "Error message here"
}
```

### Backend CORS Configuration

Make sure your backend allows requests from your frontend domain:

**Node.js/Express Example:**
```javascript
app.use(cors({
  origin: 'http://localhost:5173', // Your SvelteKit dev server
  methods: ['POST', 'GET'],
  allowedHeaders: ['Content-Type']
}));
```

**Python/Flask Example:**
```python
from flask_cors import CORS
CORS(app, origins=['http://localhost:5173'])
```

## Testing the Integration

1. **Start your backend server** (make sure it's running)
2. **Start the frontend:** `npm run dev`
3. **Navigate to:** `http://localhost:5173/web/upload`
4. **Select an MP4 file** and click "Upload video"
5. **Check the browser console** for any errors

### Common Issues

**Network Error:**
- Backend server is not running
- Wrong URL in `config.ts`
- CORS not configured properly

**Upload Failed:**
- Backend endpoint path is incorrect
- Backend not accepting `multipart/form-data`
- Backend field name mismatch (should be `video`)

## Frontend Features

✅ **File validation** - Only accepts MP4 files
✅ **Face blurring** - Automatic privacy protection using TensorFlow.js and FFmpeg
✅ **Upload progress** - Real-time progress bar (0-100%)
✅ **Processing stages** - Shows face detection and video encoding progress
✅ **Success feedback** - Green success message
✅ **Error handling** - Red error messages with details
✅ **Loading state** - Button disabled during upload

## What the Frontend Sends

When a user uploads a video, the frontend sends:

```
POST YOUR_ENDPOINT
Content-Type: multipart/form-data

------WebKitFormBoundary...
Content-Disposition: form-data; name="video"; filename="example.mp4"
Content-Type: video/mp4

[binary video data]
------WebKitFormBoundary...--
```

## Backend Developer Checklist

- [ ] Create POST endpoint for video uploads
- [ ] Accept `multipart/form-data` requests
- [ ] Handle file field named `video`
- [ ] Validate file is MP4 format
- [ ] Store video file (filesystem/cloud storage)
- [ ] Return JSON response with success/error
- [ ] Configure CORS to allow frontend domain
- [ ] Test with actual video file from frontend

## Next Steps

Once basic upload works, you might want to add:
- User authentication (send JWT token in headers)
- File size limits
- Video metadata extraction
- Thumbnail generation
- Database entry creation
- Queue system for processing
