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

<<<<<<< HEAD:src/lib/config.ts
	// Base API URL for additional endpoints
	API_BASE: 'http://10.55.108.157:8000',

	// OpenSim specific endpoints
	OPENSIM_MODEL_ENDPOINT: 'http://10.55.108.157:8000/opensim/model',
	OPENSIM_ANALYSIS_ENDPOINT: 'http://10.55.108.157:8000/opensim/analysis',
	// OPENSIM_ANIMATION_ENDPOINT: 'http://10.55.108.157:8000/opensim/animation',
	OPENSIM_ANIMATION_ENDPOINT: '/opensim_animation.json',

	// Add other API endpoints here as needed
	// Example:
	// LOGIN_ENDPOINT: 'http://localhost:3000/api/login',
	// REGISTER_ENDPOINT: 'http://localhost:3000/api/register',
=======
	// LOGIN_ENDPOINT: 'http://127.0.0.1:8000/login',
	// REGISTER_ENDPOINT: 'http://127.0.0.1:8000/register',
>>>>>>> b46bbf967ed15c50be47d613bf231ec960488d87:frontend/src/lib/config.ts
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
