# Setup Instructions for Backend Integration

## Quick Start

### 1. Update Backend URL

Edit the file: **`src/lib/config.ts`**

```typescript
export const API_CONFIG = {
  UPLOAD_ENDPOINT: 'http://localhost:3000/api/upload'  // ← Change this URL
};
```

**Replace with your backend URL:**
- Local dev: `http://localhost:3000/api/upload`
- Production: `https://api.yourdomain.com/upload`

### 2. Start Development Server

```bash
npm run dev
```

Navigate to: `http://localhost:5173/web/upload`

### 3. Test Upload

1. Select an MP4 video file
2. Click "Upload video"
3. Watch the upload progress bar

## What Your Backend Needs

Your backend developer needs to create an endpoint that:

1. **Accepts:** `POST` requests with `multipart/form-data`
2. **Field name:** `video`
3. **Returns:** JSON with success/error status

Example backend (Node.js/Express):

```javascript
app.post('/api/upload', upload.single('video'), (req, res) => {
  const file = req.file;

  // Save file, process, store in database, etc.

  res.json({
    success: true,
    message: 'Video uploaded successfully',
    videoId: 'some-unique-id'
  });
});
```

## Features Checklist

✅ MP4 file selection and validation
✅ Video preview with playback controls
✅ Real-time upload progress
✅ Success/error messages
✅ Configurable backend endpoint

## Files Changed/Created

**New Files:**
- `src/lib/config.ts` - API configuration
- `BACKEND_INTEGRATION.md` - Backend integration guide
- `SETUP_INSTRUCTIONS.md` - This file

**Modified Files:**
- `src/routes/web/upload/+page.svelte` - Upload page

## Testing

1. **Without backend:** You'll see a network error
2. **With backend:** Update config.ts and test full pipeline

## Need Help?

- Read `BACKEND_INTEGRATION.md` for backend requirements
- Check browser console for detailed error messages
