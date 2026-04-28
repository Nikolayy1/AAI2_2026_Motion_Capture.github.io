// API Configuration
// Update this file with your actual backend API endpoints

export const API_CONFIG = {
	// Base backend URL - change this if server IP changes
	BASE_URL: 'http://127.0.0.1:8000',

	// TODO: Replace with your actual backend URL
	UPLOAD_ENDPOINT: 'http://127.0.0.1:8000/upload-video',
	DOWNLOAD_ENDPOINT: 'http://127.0.0.1:8000/download-video',
	VIDEO_LIST_ENDPOINT: 'http://127.0.0.1:8000/videos',

	// Patient management endpoints
	CREATE_PATIENT_ENDPOINT: 'http://127.0.0.1:8000/patients',
	UPDATE_PATIENT_ENDPOINT: 'http://127.0.0.1:8000/patients/{patient_id}',
	PATIENTS_LIST_ENDPOINT: 'http://127.0.0.1:8000/patients',
	PATIENT_DETAIL_ENDPOINT: 'http://127.0.0.1:8000/patients/:id',
	PATIENT_VIDEOS_ENDPOINT: 'http://127.0.0.1:8000/patients/:id/videos',

	// LOGIN_ENDPOINT: 'http://127.0.0.1:8000/login',
	// REGISTER_ENDPOINT: 'http://127.0.0.1:8000/register',
};
