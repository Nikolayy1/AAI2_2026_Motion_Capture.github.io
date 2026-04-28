<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { blurFacesInVideo } from '$lib/videoFaceBlurring';
	import { UPLOAD_ENDPOINT } from '$lib/config';

	// Video state
	let videoUrl = $state<string>('');
	let videoFile = $state<File | null>(null);
	let videoDuration = $state<string>('00:00');
	let videoElement = $state<HTMLVideoElement | null>(null);

	// Biometric data
	let biometricData = $state<any>(null);

	// Upload data
	let uploadData = $state<any>(null);

	// UI state
	let showConfirmDialog = $state(false);
	let isUploading = $state(false);
	let uploadProgress = $state(0);
	let uploadStatus = $state('');
	let isProcessing = $state(false);

	onMount(() => {
		// Load biometric data from session storage
		const savedBiometric = sessionStorage.getItem('biometricData');
		if (savedBiometric) {
			biometricData = JSON.parse(savedBiometric);
		}

		// Load upload data (video, patient, exercise, faceBlur)
		const savedUpload = sessionStorage.getItem('uploadData');
		if (savedUpload) {
			uploadData = JSON.parse(savedUpload);

			// Get video URL from upload data
			if (uploadData.blurredVideoUrl) {
				videoUrl = uploadData.blurredVideoUrl;
			} else if (uploadData.videoUrl) {
				videoUrl = uploadData.videoUrl;
			}
		}

		// Load video file from global variable
		videoFile = (window as any).__uploadFile || null;
		const blurredFile = (window as any).__blurredFile || null;

		// Use blurred file if face blur is enabled and available
		if (uploadData?.faceBlur && blurredFile) {
			videoFile = blurredFile;
		}

		// If no data found, redirect back to upload
		if (!biometricData || !uploadData || !videoFile) {
			goto('/mobile/upload');
		}
	});

	function handleLoadedMetadata(event: Event) {
		const video = event.target as HTMLVideoElement;
		const duration = video.duration;
		const minutes = Math.floor(duration / 60);
		const seconds = Math.floor(duration % 60);
		videoDuration = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
	}

	function handleEdit() {
		goto('/mobile/biometric-information');
	}

	function handleBack() {
		goto('/mobile/biometric-information');
	}

	function handleSubmitClick() {
		showConfirmDialog = true;
	}

	function handleCancelSubmit() {
		showConfirmDialog = false;
	}

	async function handleConfirmSubmit() {
		showConfirmDialog = false;
		isUploading = true;
		uploadStatus = 'Preparing upload...';
		uploadProgress = 0;

		try {
			let fileToUpload = videoFile;
			let baseProgress = 0;

			// Process face blurring if enabled
			if (uploadData.faceBlur && videoFile) {
				isProcessing = true;
				uploadStatus = 'Processing face blurring...';

				const blurredFile = await blurFacesInVideo(
					videoFile,
					(progress: number) => {
						// Face blurring takes 0-50% of total progress
						uploadProgress = Math.floor(progress * 0.5);
					}
				);

				fileToUpload = blurredFile;
				isProcessing = false;
				baseProgress = 50; // Start upload progress at 50% if face blur was used
			}

			// Upload to backend using XMLHttpRequest for progress tracking
			uploadStatus = 'Uploading video...';
			uploadProgress = baseProgress;

			await uploadWithProgress(fileToUpload as File, baseProgress);

			uploadProgress = 100;
			uploadStatus = 'Upload complete!';

			// Clear session storage
			sessionStorage.removeItem('biometricData');
			sessionStorage.removeItem('uploadData');

			// Clear global file variables
			delete (window as any).__uploadFile;
			delete (window as any).__blurredFile;

			// Navigate to video library
			setTimeout(() => {
				goto('/mobile/video-library');
			}, 1000);

		} catch (error) {
			console.error('Upload error:', error);
			uploadStatus = `Upload failed: ${error}`;
			isUploading = false;
		}
	}

	function uploadWithProgress(file: File, baseProgress: number): Promise<void> {
		return new Promise((resolve, reject) => {
			const formData = new FormData();
			formData.append('video', file);
			formData.append('patient_id', biometricData.patientId.toString());

			// Add biometric data
			formData.append('gender', biometricData.gender);
			formData.append('age', biometricData.age);
			formData.append('height', biometricData.height);
			formData.append('weight', biometricData.weight);
			if (biometricData.notes) {
				formData.append('notes', biometricData.notes);
			}

			const xhr = new XMLHttpRequest();

			// Track upload progress (50-100% of total progress)
			xhr.upload.addEventListener('progress', (e) => {
				if (e.lengthComputable) {
					const uploadPercent = (e.loaded / e.total) * 100;
					// Map upload progress from baseProgress to 100%
					const remainingProgress = 100 - baseProgress;
					uploadProgress = Math.floor(baseProgress + (uploadPercent * remainingProgress / 100));
				}
			});

			xhr.addEventListener('load', () => {
				if (xhr.status >= 200 && xhr.status < 300) {
					resolve();
				} else {
					reject(new Error(`Upload failed: ${xhr.statusText || 'Server error'}`));
				}
			});

			xhr.addEventListener('error', () => {
				reject(new Error('Upload failed: Network error. Please check if the backend server is running.'));
			});

			xhr.addEventListener('abort', () => {
				reject(new Error('Upload cancelled'));
			});

			xhr.open('POST', UPLOAD_ENDPOINT);
			xhr.send(formData);
		});
	}

	function getGenderLabel(value: string): string {
		const labels: Record<string, string> = {
			'female': 'Female',
			'male': 'Male',
			'other': 'Other',
			'prefer-not-to-say': 'Prefer not to say'
		};
		return labels[value] || value;
	}
</script>

<div class="container">
	<header>
		<button class="back-button" onclick={handleBack} aria-label="Go back">
			<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
				<path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
			</svg>
		</button>
		<h1>Recording overview</h1>
	</header>

	{#if biometricData}
		<!-- Video Preview Section -->
		<section class="video-section">
			<h2>Video preview</h2>
			<div class="video-container">
				{#if videoUrl}
					<video
						bind:this={videoElement}
						src={videoUrl}
						controls
						onloadedmetadata={handleLoadedMetadata}
					>
						<track kind="captions" />
					</video>
					<div class="video-duration">{videoDuration}</div>
				{:else}
					<div class="video-placeholder">
						<div class="play-icon">
							<svg width="48" height="48" viewBox="0 0 48 48" fill="none">
								<circle cx="24" cy="24" r="24" fill="#64B5F6" opacity="0.2"/>
								<path d="M19 15l14 9-14 9V15z" fill="#64B5F6"/>
							</svg>
						</div>
					</div>
				{/if}
			</div>
		</section>

		<!-- Biometric Information Summary -->
		<section class="info-section">
			<h2>Biometric Informations</h2>
			<div class="info-grid">
				<div class="info-item">
					<span class="info-label">Full Name</span>
					<span class="info-value">{biometricData.fullName}</span>
				</div>
				<div class="info-item">
					<span class="info-label">Gender</span>
					<span class="info-value">{getGenderLabel(biometricData.gender)}</span>
				</div>
				<div class="info-item">
					<span class="info-label">Age</span>
					<span class="info-value">{biometricData.age}</span>
				</div>
				<div class="info-item">
					<span class="info-label">Height</span>
					<span class="info-value">{biometricData.height} cm</span>
				</div>
				<div class="info-item">
					<span class="info-label">Weight</span>
					<span class="info-value">{biometricData.weight} kg</span>
				</div>
				<div class="info-item">
					<span class="info-label">Notes</span>
					<span class="info-value">{biometricData.notes || 'None'}</span>
				</div>
			</div>
		</section>

		<!-- Submit Section -->
		<section class="submit-section">
			<p class="submit-question">Ready to submit this recording to the database?</p>
			<div class="button-group">
				<button class="edit-button" onclick={handleEdit}>Edit</button>
				<button class="submit-button" onclick={handleSubmitClick} disabled={isUploading}>
					{isUploading ? 'Uploading...' : 'Submit Recording'}
				</button>
			</div>
		</section>

		<!-- Upload Progress -->
		{#if isUploading}
			<div class="upload-overlay">
				<div class="upload-modal">
					<h3>{isProcessing ? 'Processing Video' : 'Uploading'}</h3>
					<div class="progress-bar">
						<div class="progress-fill" style="width: {uploadProgress}%"></div>
					</div>
					<p class="upload-status">{uploadStatus}</p>
					<p class="upload-percentage">{uploadProgress}%</p>
				</div>
			</div>
		{/if}

		<!-- Confirmation Dialog -->
		{#if showConfirmDialog}
			<div class="dialog-overlay" onclick={handleCancelSubmit}>
				<div class="dialog" onclick={(e) => e.stopPropagation()}>
					<h3>Confirm Submission</h3>
					<p>Are you ready to submit this recording to the database?</p>
					<div class="dialog-buttons">
						<button class="cancel-button" onclick={handleCancelSubmit}>Cancel</button>
						<button class="confirm-button" onclick={handleConfirmSubmit}>Submit</button>
					</div>
				</div>
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
	}

	section {
		margin-bottom: 24px;
	}

	section h2 {
		font-size: 16px;
		font-weight: 600;
		color: #333;
		margin-bottom: 12px;
	}

	/* Video Section */
	.video-section {
		background-color: #ffffff;
		border-radius: 12px;
		padding: 16px;
	}

	.video-container {
		position: relative;
		width: 100%;
		aspect-ratio: 16 / 9;
		background-color: #E0E0E0;
		border-radius: 8px;
		overflow: hidden;
	}

	video {
		width: 100%;
		height: 100%;
		object-fit: cover;
	}

	.video-placeholder {
		width: 100%;
		height: 100%;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.play-icon {
		cursor: pointer;
	}

	.video-duration {
		position: absolute;
		bottom: 8px;
		right: 8px;
		background-color: rgba(0, 0, 0, 0.7);
		color: white;
		padding: 4px 8px;
		border-radius: 4px;
		font-size: 12px;
	}

	/* Info Section */
	.info-section {
		background-color: #ffffff;
		border-radius: 12px;
		padding: 16px;
	}

	.info-grid {
		display: grid;
		gap: 16px;
	}

	.info-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding-bottom: 16px;
		border-bottom: 1px solid #F0F0F0;
	}

	.info-item:last-child {
		border-bottom: none;
		padding-bottom: 0;
	}

	.info-label {
		font-size: 14px;
		color: #666;
	}

	.info-value {
		font-size: 14px;
		color: #333;
		font-weight: 500;
		text-align: right;
	}

	/* Submit Section */
	.submit-section {
		background-color: #ffffff;
		border-radius: 12px;
		padding: 16px;
	}

	.submit-question {
		font-size: 14px;
		color: #333;
		margin-bottom: 16px;
		text-align: center;
	}

	.button-group {
		display: flex;
		gap: 12px;
	}

	.edit-button {
		flex: 1;
		padding: 12px;
		background-color: #ffffff;
		color: #64B5F6;
		border: 2px solid #64B5F6;
		border-radius: 8px;
		font-size: 16px;
		font-weight: 600;
		cursor: pointer;
		transition: all 0.2s;
	}

	.edit-button:hover {
		background-color: #F5F8FA;
	}

	.submit-button {
		flex: 2;
		padding: 12px;
		background: linear-gradient(135deg, #64B5F6 0%, #42A5F5 100%);
		color: white;
		border: none;
		border-radius: 8px;
		font-size: 16px;
		font-weight: 600;
		cursor: pointer;
		transition: opacity 0.2s;
	}

	.submit-button:hover:not(:disabled) {
		opacity: 0.9;
	}

	.submit-button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	/* Upload Overlay */
	.upload-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.upload-modal {
		background-color: white;
		border-radius: 12px;
		padding: 32px;
		max-width: 320px;
		width: 90%;
		text-align: center;
	}

	.upload-modal h3 {
		font-size: 18px;
		font-weight: 600;
		color: #333;
		margin-bottom: 24px;
	}

	.progress-bar {
		width: 100%;
		height: 8px;
		background-color: #E0E0E0;
		border-radius: 4px;
		overflow: hidden;
		margin-bottom: 16px;
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #64B5F6 0%, #42A5F5 100%);
		transition: width 0.3s ease;
	}

	.upload-status {
		font-size: 14px;
		color: #666;
		margin-bottom: 8px;
	}

	.upload-percentage {
		font-size: 24px;
		font-weight: 600;
		color: #64B5F6;
	}

	/* Confirmation Dialog */
	.dialog-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
	}

	.dialog {
		background-color: white;
		border-radius: 12px;
		padding: 24px;
		max-width: 320px;
		width: 90%;
	}

	.dialog h3 {
		font-size: 18px;
		font-weight: 600;
		color: #333;
		margin-bottom: 12px;
	}

	.dialog p {
		font-size: 14px;
		color: #666;
		margin-bottom: 24px;
		line-height: 1.5;
	}

	.dialog-buttons {
		display: flex;
		gap: 12px;
	}

	.cancel-button,
	.confirm-button {
		flex: 1;
		padding: 12px;
		border: none;
		border-radius: 8px;
		font-size: 16px;
		font-weight: 600;
		cursor: pointer;
		transition: opacity 0.2s;
	}

	.cancel-button {
		background-color: #E0E0E0;
		color: #333;
	}

	.confirm-button {
		background: linear-gradient(135deg, #64B5F6 0%, #42A5F5 100%);
		color: white;
	}

	.cancel-button:hover,
	.confirm-button:hover {
		opacity: 0.9;
	}
</style>
