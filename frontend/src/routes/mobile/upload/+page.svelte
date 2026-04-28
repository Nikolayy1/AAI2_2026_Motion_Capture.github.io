<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { API_CONFIG, PATIENTS_LIST_ENDPOINT } from "$lib/config";
	import { blurFacesInVideo } from "$lib/videoFaceBlurring";

	interface Patient {
		id: number;
		name: string;
	}

	let src: string | null = $state(null);
	let fileName: string = $state("");
	let selectedFile: File | null = $state(null);
	let blurredVideoFile: File | null = $state(null);
	let blurredVideoUrl: string | null = $state(null);
	let currentTime: number = $state(0);
	let isUploading: boolean = $state(false);
	let isBlurringFaces: boolean = $state(false);
	let blurFaces: boolean = $state(false);
	let blurProgress: number = $state(0);
	let uploadProgress: number = $state(0);
	let uploadSuccess: boolean = $state(false);
	let uploadError: string | null = $state(null);
	let selectedPatientId: number | null = $state(null);
	let selectedPatientName: string = $state("");
	let selectedExercise: string = $state("");
	let showPatientDropdown: boolean = $state(false);
	let showExerciseDropdown: boolean = $state(false);
	let isLoadingPatients: boolean = $state(true);

	// Patient list loaded from backend
	let patients: Patient[] = $state([]);

	// Load patients from backend on mount
	onMount(async () => {
		await loadPatients();
	});

	async function loadPatients() {
		isLoadingPatients = true;
		try {
			const response = await fetch(PATIENTS_LIST_ENDPOINT);
			if (!response.ok) throw new Error('Failed to load patients');
			const data = await response.json();

			// Map backend response to Patient interface
			patients = data.map((p: any) => ({
				id: p.id,
				name: p.name || 'Unknown Patient'
			}));
		} catch (error) {
			console.error('Error loading patients:', error);
			uploadError = 'Failed to load patients. Please check if the backend server is running.';
			patients = [];
		} finally {
			isLoadingPatients = false;
		}
	}

	// Exercise options
	const exercises = [
		"Sit-to-Stand",
		"Balance Test",
		"Walk Test",
		"Gait Analysis",
		"Range of Motion"
	];

	// Show the processed preview when blur is enabled and already generated.
	let previewSrc: string | null = $derived(
		blurFaces && blurredVideoUrl ? blurredVideoUrl : src,
	);

	function handleFileChange(e: Event) {
		const input = e.currentTarget as HTMLInputElement;
		const file = input.files?.[0];

		if (!file) return;

		if (file.type !== "video/mp4") {
			alert("Please select an MP4 video file.");
			input.value = "";
			return;
		}

		if (src) {
			URL.revokeObjectURL(src);
		}

		clearBlurredPreview();
		selectedFile = file;
		fileName = file.name;
		src = URL.createObjectURL(file);
		uploadSuccess = false;
		uploadError = null;
	}

	function selectPatient(patient: Patient) {
		selectedPatientId = patient.id;
		selectedPatientName = patient.name;
		showPatientDropdown = false;
	}

	function createNewPatient() {
		showPatientDropdown = false;
		goto('/mobile/create-patient');
	}

	function selectExercise(exercise: string) {
		selectedExercise = exercise;
		showExerciseDropdown = false;
	}

	// Continue to biometric information page instead of uploading directly
	async function handleContinue(event: Event) {
		event.preventDefault();

		if (!selectedFile) {
			alert("Please select a video first.");
			return;
		}

		if (!selectedPatientId) {
			alert("Please select a patient.");
			return;
		}

		if (!selectedExercise) {
			alert("Please select an exercise.");
			return;
		}

		// Save upload data to session storage
		const uploadData = {
			patientId: selectedPatientId,
			patientName: selectedPatientName,
			exercise: selectedExercise,
			faceBlur: blurFaces,
			fileName: selectedFile.name,
			fileSize: selectedFile.size,
			fileType: selectedFile.type,
			videoUrl: src,
			blurredVideoUrl: blurredVideoUrl
		};
		sessionStorage.setItem('uploadData', JSON.stringify(uploadData));

		// Store the file in a global variable for access across pages
		// This is necessary because File objects cannot be serialized to sessionStorage
		(window as any).__uploadFile = selectedFile;
		(window as any).__blurredFile = blurredVideoFile;

		// Navigate to biometric information page using SvelteKit navigation
		goto(`/mobile/biometric-information?patientId=${encodeURIComponent(selectedPatientId)}&patientName=${encodeURIComponent(selectedPatientName)}`);
	}

	async function handleGenerateBlurredPreview() {
		if (!selectedFile) {
			alert("Please choose a video first.");
			return;
		}

		await generateBlurredPreview(selectedFile);
	}

	// Reuse the cached blurred file when it already exists to avoid reprocessing.
	async function prepareVideoForUpload(file: File) {
		if (!blurFaces) {
			return file;
		}

		if (blurredVideoFile) {
			return blurredVideoFile;
		}

		return generateBlurredPreview(file);
	}

	// Build a frontend-only processed copy for preview, download, and upload.
	async function generateBlurredPreview(file: File) {
		isBlurringFaces = true;
		blurProgress = 0;
		uploadSuccess = false;
		uploadError = null;

		try {
			const blurredFile = await blurFacesInVideo(file, (progress) => {
				blurProgress = progress;
			});
			const blurredUrl = URL.createObjectURL(blurredFile);

			clearBlurredPreview();
			blurredVideoFile = blurredFile;
			blurredVideoUrl = blurredUrl;
			currentTime = 0;

			return blurredFile;
		} catch (error) {
			uploadError =
				error instanceof Error
					? `Face blurring failed: ${error.message}`
					: "Face blurring failed.";
			return null;
		} finally {
			isBlurringFaces = false;
		}
	}

	// Revoke the old object URL whenever a new processed preview replaces it.
	function clearBlurredPreview() {
		if (blurredVideoUrl) {
			URL.revokeObjectURL(blurredVideoUrl);
		}

		blurredVideoFile = null;
		blurredVideoUrl = null;
		blurProgress = 0;
	}

	// Keep the backend upload path isolated from the preview/processing logic.
	function uploadVideo(file: File) {
		isUploading = true;
		uploadProgress = 0;
		uploadSuccess = false;
		uploadError = null;

		if (!selectedPatientId) {
			uploadError = "No patient selected";
			isUploading = false;
			return;
		}

		const formData = new FormData();
		formData.append("video", file);
		formData.append("patient_id", selectedPatientId.toString());

		const xhr = new XMLHttpRequest();

		// Track upload progress
		xhr.upload.addEventListener("progress", (e) => {
			if (e.lengthComputable) {
				uploadProgress = Math.round((e.loaded / e.total) * 100);
			}
		});

		xhr.addEventListener("load", () => {
			isUploading = false;

			if (xhr.status >= 200 && xhr.status < 300) {
				uploadSuccess = true;
				uploadProgress = 100;

				try {
					const response = JSON.parse(xhr.responseText);
					console.log("Upload successful:", response);
				} catch (e) {
					console.log("Upload successful");
				}
			} else {
				uploadError = `Upload failed: ${xhr.statusText || "Server error"}`;
				uploadProgress = 0;
			}
		});

		// Handle errors
		xhr.addEventListener("error", () => {
			isUploading = false;
			uploadError =
				"Upload failed: Network error. Please check if the backend server is running.";
			uploadProgress = 0;
		});

		xhr.addEventListener("abort", () => {
			isUploading = false;
			uploadError = "Upload cancelled";
			uploadProgress = 0;
		});

		// Send the request
		xhr.open("POST", API_CONFIG.UPLOAD_ENDPOINT);
		xhr.send(formData);
	}
</script>

<svelte:head>
	<title>Upload Video</title>
</svelte:head>

<div class="screen">
	<header class="topbar">
		<a href="/mobile/dashboard" class="back-btn" aria-label="Go back">
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" xmlns="http://www.w3.org/2000/svg">
				<polyline points="15 18 9 12 15 6"></polyline>
			</svg>
		</a>
		<h1>Upload Video</h1>
	</header>

	<main class="content">
		<h2 class="page-title">Select a video from your device</h2>

		<form onsubmit={handleContinue}>
			<!-- File Upload Area -->
			<div class="upload-area">
				<label for="video-upload" class="upload-dropzone">
					<svg class="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" xmlns="http://www.w3.org/2000/svg">
						<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
						<polyline points="14 2 14 8 20 8"></polyline>
						<line x1="12" y1="12" x2="12" y2="18"></line>
						<line x1="9" y1="15" x2="15" y2="15"></line>
					</svg>
					<button type="button" class="select-btn" onclick={() => document.getElementById('video-upload')?.click()}>
						Select from device
					</button>
					{#if fileName}
						<p class="file-name">{fileName}</p>
					{/if}
				</label>
				<input
					id="video-upload"
					class="hidden-input"
					type="file"
					accept=".mp4,video/mp4"
					onchange={handleFileChange}
				/>
			</div>

			<!-- Patient Dropdown -->
			<div class="field">
				<label for="patient">Patient</label>
				<div class="dropdown-wrapper">
					<button
						type="button"
						class="dropdown-trigger"
						onclick={() => showPatientDropdown = !showPatientDropdown}
						disabled={isLoadingPatients}
					>
						<span class={selectedPatientName ? "" : "placeholder"}>
							{isLoadingPatients ? "Loading patients..." : (selectedPatientName || "Select Patient")}
						</span>
						<svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<polyline points="6 9 12 15 18 9"></polyline>
						</svg>
					</button>
					{#if showPatientDropdown}
						<div class="dropdown-menu">
							<button type="button" class="dropdown-item create-new" onclick={createNewPatient}>
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
									<line x1="12" y1="5" x2="12" y2="19"></line>
									<line x1="5" y1="12" x2="19" y2="12"></line>
								</svg>
								Create New Patient
							</button>
							<div class="dropdown-divider"></div>
							{#each patients as patient}
								<button type="button" class="dropdown-item" onclick={() => selectPatient(patient)}>
									{patient.name}
								</button>
							{/each}
						</div>
					{/if}
				</div>
			</div>

			<!-- Exercise Dropdown -->
			<div class="field">
				<label for="exercise">Recorded Exercise</label>
				<div class="dropdown-wrapper">
					<button
						type="button"
						class="dropdown-trigger"
						onclick={() => showExerciseDropdown = !showExerciseDropdown}
					>
						<span class={selectedExercise ? "" : "placeholder"}>
							{selectedExercise || "Select Exercise"}
						</span>
						<svg class="chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<polyline points="6 9 12 15 18 9"></polyline>
						</svg>
					</button>
					{#if showExerciseDropdown}
						<div class="dropdown-menu">
							{#each exercises as exercise}
								<button type="button" class="dropdown-item" onclick={() => selectExercise(exercise)}>
									{exercise}
								</button>
							{/each}
						</div>
					{/if}
				</div>
			</div>

			<!-- Face Blurring Options -->
			{#if selectedFile}
				<label class="toggle-row">
					<input
						type="checkbox"
						bind:checked={blurFaces}
						disabled={isUploading || isBlurringFaces}
					/>
					<span>Enable face blurring</span>
				</label>

				{#if blurFaces}
					<button
						type="button"
						class="preview-blur-btn"
						disabled={isUploading || isBlurringFaces}
						onclick={handleGenerateBlurredPreview}
					>
						{#if isBlurringFaces}
							Processing...
						{:else if blurredVideoUrl}
							Regenerate Preview
						{:else}
							Preview Blurred Video
						{/if}
					</button>
				{/if}
			{/if}

			<!-- Video Preview -->
			{#if previewSrc}
				<div class="preview-wrapper">
					<p class="preview-label">
						{blurFaces && blurredVideoUrl ? "Blurred Preview" : "Video Preview"}
					</p>
					<!-- svelte-ignore a11y_media_has_caption -->
					<video
						src={previewSrc}
						bind:currentTime
						controls
						preload="metadata"
					></video>
				</div>
			{/if}

			<!-- Progress Bars -->
			{#if isBlurringFaces}
				<div class="progress-wrapper">
					<p class="progress-label">Processing face blur... {blurProgress}%</p>
					<div class="progress-bar">
						<div class="progress-fill" style="width: {blurProgress}%"></div>
					</div>
				</div>
			{/if}

			{#if isUploading}
				<div class="progress-wrapper">
					<p class="progress-label">Uploading... {uploadProgress}%</p>
					<div class="progress-bar">
						<div class="progress-fill" style="width: {uploadProgress}%"></div>
					</div>
				</div>
			{/if}

			<!-- Success/Error Messages -->
			{#if uploadSuccess}
				<div class="success-message">✓ Video uploaded successfully!</div>
			{/if}

			{#if uploadError}
				<div class="error-message">✗ {uploadError}</div>
			{/if}

			<!-- Continue Button -->
			<button
				type="submit"
				class="upload-btn"
				disabled={isBlurringFaces || !selectedFile || !selectedPatientId || !selectedExercise || isLoadingPatients}
			>
				{#if isBlurringFaces}
					Processing...
				{:else if isLoadingPatients}
					Loading...
				{:else}
					Continue
				{/if}
			</button>
		</form>
	</main>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
		background: #ffffff;
		color: #000000;
	}

	:global(*) {
		box-sizing: border-box;
	}

	.screen {
		min-height: 100vh;
		max-width: 430px;
		min-width: 360px;
		margin: 0 auto;
		background: #ffffff;
		position: relative;
	}

	.topbar {
		height: 84px;
		background: #ffffff;
		border-bottom: 1px solid #e0e0e0;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
	}

	.back-btn {
		position: absolute;
		left: 18px;
		top: 50%;
		transform: translateY(-50%);
		background: transparent;
		border: none;
		cursor: pointer;
		color: #000000;
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		text-decoration: none;
	}

	.back-btn svg {
		width: 28px;
		height: 28px;
	}

	.topbar h1 {
		margin: 0;
		font-size: 24px;
		font-weight: 600;
		color: #000000;
	}

	.content {
		padding: 24px 24px 40px;
	}

	.page-title {
		margin: 0 0 24px;
		font-size: 20px;
		font-weight: 600;
		color: #000000;
		text-align: center;
	}

	form {
		display: flex;
		flex-direction: column;
		gap: 20px;
	}

	.upload-area {
		margin-bottom: 8px;
	}

	.upload-dropzone {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 180px;
		padding: 32px 24px;
		border: 2px dashed #B0BEC5;
		border-radius: 12px;
		background: #F5F8FA;
		cursor: pointer;
		transition: all 0.2s;
	}

	.upload-dropzone:hover {
		border-color: #64B5F6;
		background: #E3F2FD;
	}

	.file-icon {
		width: 64px;
		height: 64px;
		color: #90A4AE;
		margin-bottom: 20px;
	}

	.select-btn {
		padding: 12px 32px;
		background: #90CAF9;
		border: none;
		border-radius: 8px;
		color: #000000;
		font-size: 16px;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.2s;
	}

	.select-btn:hover {
		background: #64B5F6;
	}

	.file-name {
		margin: 12px 0 0;
		font-size: 14px;
		color: #666666;
		text-align: center;
		word-break: break-all;
	}

	.hidden-input {
		display: none;
	}

	.field {
		display: flex;
		flex-direction: column;
		gap: 12px;
		position: relative;
	}

	label {
		font-size: 18px;
		font-weight: 600;
		color: #000000;
	}

	.dropdown-wrapper {
		position: relative;
	}

	.dropdown-trigger {
		width: 100%;
		padding: 16px 20px;
		border: 1px solid #d0d0d0;
		border-radius: 12px;
		background: #ffffff;
		font-size: 16px;
		color: #000000;
		display: flex;
		align-items: center;
		justify-content: space-between;
		cursor: pointer;
		transition: border-color 0.2s;
		text-align: left;
	}

	.dropdown-trigger:hover {
		border-color: #1976D2;
	}

	.dropdown-trigger .placeholder {
		color: #999999;
	}

	.chevron {
		width: 20px;
		height: 20px;
		color: #666666;
		flex-shrink: 0;
	}

	.dropdown-menu {
		position: absolute;
		top: calc(100% + 4px);
		left: 0;
		right: 0;
		background: #ffffff;
		border: 1px solid #d0d0d0;
		border-radius: 12px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
		z-index: 10;
		max-height: 240px;
		overflow-y: auto;
	}

	.dropdown-item {
		width: 100%;
		padding: 14px 20px;
		border: none;
		background: transparent;
		color: #000000;
		font-size: 16px;
		text-align: left;
		cursor: pointer;
		transition: background 0.2s;
		display: flex;
		align-items: center;
		gap: 8px;
	}

	.dropdown-item:hover {
		background: #f0f0f0;
	}

	.dropdown-item.create-new {
		color: #1976D2;
		font-weight: 600;
	}

	.dropdown-item.create-new svg {
		width: 18px;
		height: 18px;
	}

	.dropdown-divider {
		height: 1px;
		background: #e0e0e0;
		margin: 4px 0;
	}

	.toggle-row {
		display: flex;
		align-items: center;
		gap: 12px;
		cursor: pointer;
		margin: -8px 0;
	}

	.toggle-row input {
		width: 20px;
		height: 20px;
		margin: 0;
		accent-color: #1976D2;
		cursor: pointer;
	}

	.toggle-row span {
		font-size: 16px;
		color: #000000;
	}

	.preview-blur-btn {
		width: 100%;
		padding: 14px;
		background: #E3F2FD;
		border: 1px solid #90CAF9;
		border-radius: 12px;
		color: #1976D2;
		font-size: 16px;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.2s;
	}

	.preview-blur-btn:hover:not(:disabled) {
		background: #BBDEFB;
	}

	.preview-blur-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.preview-wrapper {
		margin: 8px 0;
	}

	.preview-label {
		margin: 0 0 12px;
		font-size: 16px;
		font-weight: 600;
		color: #000000;
	}

	video {
		width: 100%;
		border-radius: 12px;
		background: black;
		border: 1px solid #d0d0d0;
	}

	.progress-wrapper {
		margin: 8px 0;
	}

	.progress-label {
		margin: 0 0 8px;
		font-size: 14px;
		font-weight: 600;
		color: #000000;
		text-align: center;
	}

	.progress-bar {
		width: 100%;
		height: 24px;
		background: #e5e5e5;
		border-radius: 12px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: #64B5F6;
		transition: width 0.3s ease;
	}

	.success-message {
		padding: 14px 16px;
		background: #d4edda;
		border: 1px solid #c3e6cb;
		border-radius: 8px;
		color: #155724;
		font-size: 15px;
		font-weight: 600;
		text-align: center;
	}

	.error-message {
		padding: 14px 16px;
		background: #f8d7da;
		border: 1px solid #f5c6cb;
		border-radius: 8px;
		color: #721c24;
		font-size: 14px;
		text-align: center;
		word-break: break-word;
	}

	.upload-btn {
		width: 100%;
		padding: 18px;
		border: none;
		border-radius: 12px;
		background: #90CAF9;
		color: #000000;
		font-size: 18px;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.2s;
	}

	.upload-btn:hover:not(:disabled) {
		background: #64B5F6;
	}

	.upload-btn:disabled {
		background: #E0E0E0;
		cursor: not-allowed;
	}
</style>
