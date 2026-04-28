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

// Export individual endpoints for convenience
export const BASE_URL = API_CONFIG.BASE_URL;
export const UPLOAD_ENDPOINT = API_CONFIG.UPLOAD_ENDPOINT;
export const DOWNLOAD_ENDPOINT = API_CONFIG.DOWNLOAD_ENDPOINT;
export const VIDEO_LIST_ENDPOINT = API_CONFIG.VIDEO_LIST_ENDPOINT;
export const CREATE_PATIENT_ENDPOINT = API_CONFIG.CREATE_PATIENT_ENDPOINT;
export const UPDATE_PATIENT_ENDPOINT = API_CONFIG.UPDATE_PATIENT_ENDPOINT;
export const PATIENTS_LIST_ENDPOINT = API_CONFIG.PATIENTS_LIST_ENDPOINT;
export const PATIENT_DETAIL_ENDPOINT = API_CONFIG.PATIENT_DETAIL_ENDPOINT;
export const PATIENT_VIDEOS_ENDPOINT = API_CONFIG.PATIENT_VIDEOS_ENDPOINT;	
