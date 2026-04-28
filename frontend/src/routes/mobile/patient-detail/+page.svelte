<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { API_CONFIG } from '$lib/config';

	interface Video {
		id: string;
		filename: string;
		videoUrl: string;  // Full path like /files/videos/abc.mp4
		exercise: string;
		date: string;
		duration: string;
		thumbnail?: string;
	}

	interface PatientData {
		name: string;
		age: number;
		gender: string;
		height: number;
		weight: number;
		videos: Video[];
	}

	let patientId: number | null = $state(null);
	let patientName = $state('');
	let patientData = $state<PatientData | null>(null);
	let isLoading = $state(true);
	let error = $state('');
	let searchQuery = $state('');
	let selectedExercise = $state('all');

	const exerciseTypes = [
		{ value: 'all', label: 'All Exercises' },
		{ value: 'Sit-to-Stand', label: 'Sit-to-Stand' },
		{ value: 'Balance Test', label: 'Balance Test' },
		{ value: 'Walk Test', label: 'Walk Test' },
		{ value: 'Gait Analysis', label: 'Gait Analysis' },
		{ value: 'Range of Motion', label: 'Range of Motion' }
	];

	onMount(() => {
		const urlParams = new URLSearchParams(window.location.search);
		const patientIdParam = urlParams.get('id');
		patientName = urlParams.get('name') || '';

		if (!patientIdParam) {
			goto('/mobile/patients');
			return;
		}

		patientId = parseInt(patientIdParam);
		void loadPatientData();
	});

	async function loadPatientData() {
		isLoading = true;
		error = '';

		try {
			const endpoint = API_CONFIG.PATIENT_VIDEOS_ENDPOINT.replace(':id', patientId!.toString());
			const response = await fetch(endpoint);

			if (!response.ok) throw new Error('Failed to load patient data');

			const data = await response.json();

			if (data.error) {
				throw new Error(data.error);
			}

			// Debug: Log the response to see what fields are available
			console.log('Backend response for patient videos:', data);
			if (data.videos && data.videos.length > 0) {
				console.log('First video data:', data.videos[0]);
				console.log('All fields in first video:', Object.keys(data.videos[0]));
				console.log('First video JSON:', JSON.stringify(data.videos[0], null, 2));
			}

			// Extract filename from video_url path
			const extractFilename = (url: string) => {
				if (!url) return 'video.mp4';
				const parts = url.split('/');
				return parts[parts.length - 1] || 'video.mp4';
			};

			// Format upload date
			const formatUploadDate = (dateString: string) => {
				if (!dateString) return new Date().toISOString().split('T')[0];
				return dateString.split('T')[0]; // Extract just the date part from timestamp
			};

			// Map backend response to frontend PatientData interface
			const mappedVideos = data.videos.map((v: any) => {
				// Try multiple possible field names for exercise type
				const exercise = v.exercise_type || v.exerciseType || v.exercise ||
				                v.biometrics?.exercise_type || v.metadata?.exercise_type || 'General';

				console.log(`Video ${v.submission_id} exercise:`, exercise, 'Raw video data:', v);

				// Extract filename from video_url - backend returns full file paths
				const filename = extractFilename(v.video_url);
				// Construct proper relative URL for video playback
				const videoUrl = `/files/videos/${filename}`;

				console.log(`Video URL mapping: ${v.video_url} -> ${videoUrl}`);

				return {
					id: String(v.submission_id || ''),
					filename: filename,
					videoUrl: videoUrl,  // Use relative path like /files/videos/abc.mp4
					exercise: exercise,
					date: formatUploadDate(v.uploaded_at), // Use actual upload date
					duration: v.duration || '00:00', // Use duration from backend if available
					thumbnail: undefined as string | undefined
				};
			});

			// Get biometric data from patient object (not from videos)
			patientData = {
				name: data.patient?.name || patientName,
				age: data.patient?.age || 0,
				gender: data.patient?.gender || 'Unknown',
				height: data.patient?.height || 0,
				weight: data.patient?.weight || 0,
				videos: mappedVideos
			};

			// Thumbnail generation disabled due to CORS security restrictions
			// Videos will show placeholder icon instead
			// To enable: backend needs to serve videos with proper CORS headers
		} catch (err) {
			console.error('Error loading patient data:', err);
			error = `${err}`;
			patientData = null;
		} finally {
			isLoading = false;
		}
	}

	function handleBack() {
		goto('/mobile/patients');
	}

	function handleEditBiometrics() {
		if (patientId) {
			goto(`/mobile/biometric-information?patientId=${patientId}&mode=edit&source=patient-detail`);
		}
	}

	async function generateThumbnail(videoUrl: string): Promise<string | undefined> {
		return new Promise((resolve) => {
			try {
				const video = document.createElement('video');
				const fullUrl = `${API_CONFIG.BASE_URL}${videoUrl}`;

				console.log('Attempting to load video for thumbnail:', fullUrl);

				// IMPORTANT: Don't use crossOrigin to avoid CORS/tainted canvas issues
				// This only works if video is served from same origin
				video.muted = true;
				video.preload = 'metadata';
				video.autoplay = false;

				let hasResolved = false;
				const resolveOnce = (value: string | undefined) => {
					if (!hasResolved) {
						hasResolved = true;
						// Clean up
						video.src = '';
						video.load();
						resolve(value);
					}
				};

				video.onloadedmetadata = () => {
					console.log('Video metadata loaded:', {
						duration: video.duration,
						width: video.videoWidth,
						height: video.videoHeight
					});

					// Seek to 1 second or 25% of duration
					const seekTime = Math.min(1, video.duration > 0 ? video.duration * 0.25 : 1);

					// Add seeked listener before seeking
					video.onseeked = () => {
						try {
							console.log('Video seeked, capturing frame...');
							const canvas = document.createElement('canvas');
							canvas.width = video.videoWidth || 640;
							canvas.height = video.videoHeight || 360;

							const ctx = canvas.getContext('2d', { willReadFrequently: false });
							if (ctx && video.videoWidth > 0 && video.videoHeight > 0) {
								ctx.drawImage(video, 0, 0);

								// Try to get the data URL, handle CORS errors
								try {
									const thumbnailDataUrl = canvas.toDataURL('image/jpeg', 0.7);
									console.log('Thumbnail generated successfully');
									resolveOnce(thumbnailDataUrl);
								} catch (canvasErr: any) {
									console.error('Canvas toDataURL error (likely CORS):', canvasErr.message);
									// CORS issue - can't extract thumbnail
									resolveOnce(undefined);
								}
							} else {
								console.error('Canvas context not available or invalid video dimensions');
								resolveOnce(undefined);
							}
						} catch (err) {
							console.error('Error capturing video frame:', err);
							resolveOnce(undefined);
						}
					};

					video.currentTime = seekTime;
				};

				video.onerror = (e) => {
					console.error('Error loading video for thumbnail:', video.error);
					resolveOnce(undefined);
				};

				// Set source after all event listeners are attached
				video.src = fullUrl;
				video.load();

				// Timeout after 10 seconds
				setTimeout(() => {
					console.warn('Thumbnail generation timeout for:', fullUrl);
					resolveOnce(undefined);
				}, 10000);
			} catch (err) {
				console.error('Thumbnail generation error:', err);
				resolve(undefined);
			}
		});
	}

	function handleVideoClick(video: Video) {
		try {
			// Validate video URL exists
			if (!video.videoUrl || video.videoUrl.trim() === '') {
				error = 'Video URL not available';
				console.error('Missing video URL for video:', video);
				return;
			}

			// Open video in new tab using the backend's static file serving
			// video.videoUrl is like "/files/videos/abc123.mp4"
			const videoUrl = `${API_CONFIG.BASE_URL}${video.videoUrl}`;

			// Validate URL format before opening
			try {
				new URL(videoUrl);
			} catch (urlError) {
				error = 'Invalid video URL format';
				console.error('URL validation failed:', videoUrl, urlError);
				return;
			}

			window.open(videoUrl, '_blank');
		} catch (err) {
			error = `Error opening video: ${err instanceof Error ? err.message : 'Unknown error'}`;
			console.error('Video click error:', err, video);
		}
	}

	function formatDate(dateString: string): string {
		try {
			const date = new Date(dateString);
			return date.toLocaleDateString('en-US', {
				month: 'short',
				day: 'numeric',
				year: 'numeric'
			});
		} catch {
			return dateString;
		}
	}

	// Filter videos based on search and exercise type
	let filteredVideos = $derived(() => {
		if (!patientData) return [];

		return patientData.videos.filter(video => {
			const matchesSearch = searchQuery === '' ||
				video.exercise.toLowerCase().includes(searchQuery.toLowerCase()) ||
				video.filename.toLowerCase().includes(searchQuery.toLowerCase());

			const matchesExercise = selectedExercise === 'all' ||
				video.exercise === selectedExercise;

			return matchesSearch && matchesExercise;
		});
	});
</script>

<div class="container">
	<header>
		<button class="back-button" onclick={handleBack} aria-label="Go back">
			<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
				<path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
			</svg>
		</button>
		<h1>{patientName}</h1>
	</header>

	<!-- Loading State -->
	{#if isLoading}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading patient data...</p>
		</div>
	{/if}

	<!-- Error State -->
	{#if error && !isLoading}
		<div class="error-state">
			<svg width="48" height="48" viewBox="0 0 48 48" fill="none">
				<circle cx="24" cy="24" r="24" fill="#FFEBEE"/>
				<path d="M24 16v8M24 28v2" stroke="#f44336" stroke-width="2" stroke-linecap="round"/>
			</svg>
			<p class="error-message">{error}</p>
			<button class="retry-button" onclick={loadPatientData}>Retry</button>
		</div>
	{/if}

	<!-- Patient Data -->
	{#if !isLoading && !error && patientData}
		<!-- Patient Summary Card -->
		<div class="patient-summary">
			<div class="summary-header">
				<h2>Patient Information</h2>
				<button class="edit-button" onclick={handleEditBiometrics} aria-label="Edit biometric information">
					<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
						<path d="M14.166 2.5a2.357 2.357 0 0 1 3.334 3.334l-9.167 9.167-4.166.833.833-4.166L14.166 2.5z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
					</svg>
					Edit
				</button>
			</div>
			<div class="info-grid">
				<div class="info-item">
					<span class="info-label">Age</span>
					<span class="info-value">{patientData.age || 'Not set'}</span>
				</div>
				<div class="info-item">
					<span class="info-label">Gender</span>
					<span class="info-value">{patientData.gender || 'Not set'}</span>
				</div>
				<div class="info-item">
					<span class="info-label">Height</span>
					<span class="info-value">{patientData.height ? `${patientData.height} cm` : 'Not set'}</span>
				</div>
				<div class="info-item">
					<span class="info-label">Weight</span>
					<span class="info-value">{patientData.weight ? `${patientData.weight} kg` : 'Not set'}</span>
				</div>
			</div>
			<div class="video-count-badge">
				Total Videos: <strong>{patientData.videos.length}</strong>
			</div>
		</div>

		<!-- Controls -->
		<div class="controls">
			<div class="search-box">
				<svg width="20" height="20" viewBox="0 0 20 20" fill="none" class="search-icon">
					<path d="M9 17A8 8 0 1 0 9 1a8 8 0 0 0 0 16zM18 18l-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
				</svg>
				<input
					type="text"
					bind:value={searchQuery}
					placeholder="Search videos..."
					class="search-input"
				/>
			</div>

			<select bind:value={selectedExercise} class="filter-select">
				{#each exerciseTypes as type}
					<option value={type.value}>{type.label}</option>
				{/each}
			</select>
		</div>

		<!-- Videos Grid -->
		{#if filteredVideos().length === 0}
			<div class="empty-state">
				<svg width="64" height="64" viewBox="0 0 64 64" fill="none">
					<circle cx="32" cy="32" r="32" fill="#E3F2FD"/>
					<path d="M24 22l16 10-16 10V22z" fill="#64B5F6"/>
				</svg>
				<h3>No Videos Found</h3>
				<p>{searchQuery || selectedExercise !== 'all' ? 'Try adjusting your filters' : 'No videos for this patient yet'}</p>
			</div>
		{:else}
			<div class="video-grid">
				{#each filteredVideos() as video}
					<button class="video-card" onclick={() => handleVideoClick(video)}>
						<div class="video-thumbnail">
							{#if video.thumbnail}
								<img src={video.thumbnail} alt={video.filename} />
							{:else}
								<div class="thumbnail-placeholder">
									<svg width="48" height="48" viewBox="0 0 48 48" fill="none">
										<circle cx="24" cy="24" r="24" fill="white" opacity="0.3"/>
										<path d="M19 15l14 9-14 9V15z" fill="white"/>
									</svg>
								</div>
							{/if}
							<span class="duration-badge">{video.duration}</span>
						</div>
						<div class="video-info">
							<span class="exercise-badge">{video.exercise}</span>
							<p class="video-date">{formatDate(video.date)}</p>
						</div>
					</button>
				{/each}
			</div>
		{/if}
	{/if}
</div>

<style>
	.container {
		max-width: 430px;
		margin: 0 auto;
		padding: 20px;
		background-color: #F5F8FA;
		min-height: 100vh;
	}

	header {
		display: flex;
		align-items: center;
		gap: 12px;
		margin-bottom: 24px;
	}

	.back-button {
		background: none;
		border: none;
		padding: 4px;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		color: #333;
		transition: color 0.2s;
	}

	.back-button:hover {
		color: #64B5F6;
	}

	h1 {
		font-size: 20px;
		font-weight: 600;
		color: #333;
		margin: 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	/* Loading State */
	.loading {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 48px 20px;
	}

	.spinner {
		width: 40px;
		height: 40px;
		border: 4px solid #E0E0E0;
		border-top-color: #64B5F6;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: 16px;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.loading p {
		font-size: 14px;
		color: #666;
	}

	/* Error State */
	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 48px 20px;
	}

	.error-message {
		font-size: 14px;
		color: #f44336;
		margin: 16px 0;
		text-align: center;
	}

	.retry-button {
		padding: 10px 24px;
		background-color: #64B5F6;
		color: white;
		border: none;
		border-radius: 6px;
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
		transition: opacity 0.2s;
	}

	.retry-button:hover {
		opacity: 0.9;
	}

	/* Patient Summary */
	.patient-summary {
		background-color: #ffffff;
		border-radius: 12px;
		padding: 20px;
		margin-bottom: 24px;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
	}

	.summary-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 16px;
	}

	.patient-summary h2 {
		font-size: 16px;
		font-weight: 600;
		color: #333;
		margin: 0;
	}

	.edit-button {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 8px 16px;
		background-color: #64B5F6;
		color: white;
		border: none;
		border-radius: 6px;
		font-size: 14px;
		font-weight: 500;
		cursor: pointer;
		transition: background-color 0.2s;
	}

	.edit-button:hover {
		background-color: #42A5F5;
	}

	.edit-button:active {
		background-color: #1E88E5;
	}

	.edit-button svg {
		stroke: currentColor;
	}

	.info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 16px;
		margin-bottom: 16px;
	}

	.info-item {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.info-label {
		font-size: 12px;
		color: #666;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.info-value {
		font-size: 16px;
		color: #333;
		font-weight: 600;
	}

	.video-count-badge {
		padding: 12px;
		background: linear-gradient(135deg, #E3F2FD 0%, #BBDEFB 100%);
		border-radius: 8px;
		text-align: center;
		font-size: 14px;
		color: #1976D2;
	}

	.video-count-badge strong {
		font-weight: 700;
	}

	/* Controls */
	.controls {
		display: flex;
		flex-direction: column;
		gap: 12px;
		margin-bottom: 24px;
	}

	.search-box {
		position: relative;
		display: flex;
		align-items: center;
	}

	.search-icon {
		position: absolute;
		left: 12px;
		color: #999;
	}

	.search-input {
		width: 100%;
		padding: 12px 12px 12px 44px;
		border: 1px solid #E0E0E0;
		border-radius: 8px;
		font-size: 14px;
		color: #333;
		background-color: #ffffff;
		transition: border-color 0.2s;
		box-sizing: border-box;
	}

	.search-input:focus {
		outline: none;
		border-color: #64B5F6;
	}

	.search-input::placeholder {
		color: #999;
	}

	.filter-select {
		width: 100%;
		padding: 12px 16px;
		border: 1px solid #E0E0E0;
		border-radius: 8px;
		font-size: 14px;
		color: #333;
		background-color: #ffffff;
		cursor: pointer;
		transition: border-color 0.2s;
	}

	.filter-select:focus {
		outline: none;
		border-color: #64B5F6;
	}

	/* Empty State */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 48px 20px;
		text-align: center;
	}

	.empty-state h3 {
		font-size: 18px;
		font-weight: 600;
		color: #333;
		margin: 16px 0 8px 0;
	}

	.empty-state p {
		font-size: 14px;
		color: #666;
	}

	/* Video Grid */
	.video-grid {
		display: grid;
		grid-template-columns: repeat(2, 1fr);
		gap: 12px;
	}

	.video-card {
		background-color: #ffffff;
		border: none;
		border-radius: 12px;
		overflow: hidden;
		cursor: pointer;
		transition: transform 0.2s, box-shadow 0.2s;
		padding: 0;
	}

	.video-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}

	.video-thumbnail {
		position: relative;
		width: 100%;
		aspect-ratio: 16 / 9;
		background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		overflow: hidden;
	}

	.video-thumbnail img {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.thumbnail-placeholder {
		width: 100%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.duration-badge {
		position: absolute;
		bottom: 8px;
		right: 8px;
		background-color: rgba(0, 0, 0, 0.7);
		color: white;
		padding: 4px 8px;
		border-radius: 4px;
		font-size: 11px;
		font-weight: 600;
	}

	.video-info {
		padding: 12px;
		text-align: left;
	}

	.exercise-badge {
		display: inline-block;
		font-size: 12px;
		font-weight: 600;
		color: #64B5F6;
		background-color: #E3F2FD;
		padding: 4px 8px;
		border-radius: 4px;
		margin-bottom: 8px;
	}

	.video-date {
		font-size: 12px;
		color: #999;
		margin: 0;
	}
</style>
