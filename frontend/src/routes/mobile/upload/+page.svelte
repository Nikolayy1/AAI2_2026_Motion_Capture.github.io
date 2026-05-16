<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { API_CONFIG } from '$lib/config';
	import { blurFacesInVideo } from '$lib/videoFaceBlurring';
	import { apiFetch } from '$lib/api';
	import { coerceBiometrics, getPatientBiometrics } from '$lib/biometrics';

	interface Patient {
		id: number;
		name: string;
	}

	let src: string | null = $state(null);
	let fileName: string = $state('');
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
	let selectedPatientName: string = $state('');
	let selectedExercise: string = $state('');
	let showPatientDropdown: boolean = $state(false);
	let showExerciseDropdown: boolean = $state(false);
	let isLoadingPatients: boolean = $state(true);

	let patients: Patient[] = $state([]);

	onMount(() => {
		void loadPatients();
	});

	async function loadPatients() {
		isLoadingPatients = true;
		try {
			const response = await apiFetch(API_CONFIG.PATIENTS_LIST_ENDPOINT);
			if (!response.ok) throw new Error('Failed to load patients');
			const data = await response.json();
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

	const exercises = ['Sit-to-Stand', 'Balance Test', 'Walk Test', 'Gait Analysis', 'Range of Motion'];

	let previewSrc: string | null = $derived(blurFaces && blurredVideoUrl ? blurredVideoUrl : src);

	function handleFileChange(e: Event) {
		const input = e.currentTarget as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;

		if (!file.type.startsWith('video/')) {
			alert('Please select a valid video file.');
			input.value = '';
			return;
		}

		if (src) URL.revokeObjectURL(src);
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

	async function handleContinue(event: Event) {
		event.preventDefault();
		if (!selectedFile) { alert('Please select a video first.'); return; }
		if (!selectedPatientId) { alert('Please select a patient.'); return; }
		if (!selectedExercise) { alert('Please select an exercise.'); return; }

		const uploadData = {
			patientId: selectedPatientId,
			patientName: selectedPatientName,
			exercise: selectedExercise,
			faceBlur: blurFaces,
			biometrics: coerceBiometrics(getPatientBiometrics(selectedPatientId)),
			fileName: selectedFile.name,
			fileSize: selectedFile.size,
			fileType: selectedFile.type,
			videoUrl: src,
			blurredVideoUrl
		};
		sessionStorage.setItem('uploadData', JSON.stringify(uploadData));
		(window as any).__uploadFile = selectedFile;
		(window as any).__blurredFile = blurredVideoFile;
		goto('/mobile/recording-overview');
	}

	async function handleGenerateBlurredPreview() {
		if (!selectedFile) { alert('Please choose a video first.'); return; }
		await generateBlurredPreview(selectedFile);
	}

	async function prepareVideoForUpload(file: File) {
		if (!blurFaces) return file;
		if (blurredVideoFile) return blurredVideoFile;
		return generateBlurredPreview(file);
	}

	async function generateBlurredPreview(file: File) {
		isBlurringFaces = true;
		blurProgress = 0;
		uploadSuccess = false;
		uploadError = null;
		try {
			const blurredFile = await blurFacesInVideo(file, (progress) => { blurProgress = progress; });
			const blurredUrl = URL.createObjectURL(blurredFile);
			clearBlurredPreview();
			blurredVideoFile = blurredFile;
			blurredVideoUrl = blurredUrl;
			currentTime = 0;
			return blurredFile;
		} catch (error) {
			uploadError = error instanceof Error ? `Face blurring failed: ${error.message}` : 'Face blurring failed.';
			return null;
		} finally {
			isBlurringFaces = false;
		}
	}

	function clearBlurredPreview() {
		if (blurredVideoUrl) URL.revokeObjectURL(blurredVideoUrl);
		blurredVideoFile = null;
		blurredVideoUrl = null;
		blurProgress = 0;
	}

	function uploadVideo(file: File) {
		isUploading = true;
		uploadProgress = 0;
		uploadSuccess = false;
		uploadError = null;
		if (!selectedPatientId) { uploadError = 'No patient selected'; isUploading = false; return; }
		const formData = new FormData();
		formData.append('video', file);
		formData.append('patient_id', selectedPatientId.toString());
		const xhr = new XMLHttpRequest();
		xhr.upload.addEventListener('progress', (e) => {
			if (e.lengthComputable) uploadProgress = Math.round((e.loaded / e.total) * 100);
		});
		xhr.addEventListener('load', () => {
			isUploading = false;
			if (xhr.status >= 200 && xhr.status < 300) {
				uploadSuccess = true;
				uploadProgress = 100;
			} else {
				uploadError = `Upload failed: ${xhr.statusText || 'Server error'}`;
				uploadProgress = 0;
			}
		});
		xhr.addEventListener('error', () => {
			isUploading = false;
			uploadError = 'Upload failed: Network error. Please check if the backend server is running.';
			uploadProgress = 0;
		});
		xhr.addEventListener('abort', () => { isUploading = false; uploadError = 'Upload cancelled'; uploadProgress = 0; });
		xhr.open('POST', API_CONFIG.UPLOAD_ENDPOINT);
		xhr.send(formData);
	}
</script>

<svelte:head>
	<title>Upload Video — Gait Analysis</title>
</svelte:head>

<div class="page">
	<a href="/mobile/dashboard" class="back-link">
		<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
			<path d="M10 12L6 8l4-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
		</svg>
		Back to Dashboard
	</a>

	<div class="page-header">
		<h1>Upload Video</h1>
		<p class="page-subtitle">Select a recording and patient details to submit for analysis</p>
	</div>

	<form onsubmit={handleContinue} class="upload-layout">
		<!-- Left column: form fields -->
		<div class="form-col">
			<!-- File Upload Area -->
			<div class="section">
				<h2 class="section-title">Recording</h2>
				<label for="video-upload" class="upload-dropzone" class:has-file={!!fileName}>
					<svg class="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
						<polyline points="14 2 14 8 20 8"></polyline>
						<line x1="12" y1="12" x2="12" y2="18"></line>
						<line x1="9" y1="15" x2="15" y2="15"></line>
					</svg>
					{#if fileName}
						<p class="file-name-selected">{fileName}</p>
						<span class="change-file">Click to change file</span>
					{:else}
						<button
							type="button"
							class="select-btn"
							onclick={() => document.getElementById('video-upload')?.click()}
						>
							Select video from device
						</button>
						<p class="upload-hint">MP4, MOV, AVI supported</p>
					{/if}
				</label>
				<input id="video-upload" class="hidden-input" type="file" accept="video/*" onchange={handleFileChange} />
			</div>

			<!-- Patient -->
			<div class="section">
				<h2 class="section-title">Patient</h2>
				<div class="dropdown-wrapper">
					<button
						type="button"
						class="dropdown-trigger"
						onclick={() => (showPatientDropdown = !showPatientDropdown)}
						disabled={isLoadingPatients}
					>
						<span class={selectedPatientName ? '' : 'placeholder'}>
							{isLoadingPatients ? 'Loading patients…' : selectedPatientName || 'Select patient'}
						</span>
						<svg class="chevron-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
							<polyline points="6 9 12 15 18 9"></polyline>
						</svg>
					</button>
					{#if showPatientDropdown}
						<div class="dropdown-menu">
							<button type="button" class="dropdown-item create-new" onclick={createNewPatient}>
								<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="dropdown-icon">
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

			<!-- Exercise -->
			<div class="section">
				<h2 class="section-title">Recorded Exercise</h2>
				<div class="dropdown-wrapper">
					<button
						type="button"
						class="dropdown-trigger"
						onclick={() => (showExerciseDropdown = !showExerciseDropdown)}
					>
						<span class={selectedExercise ? '' : 'placeholder'}>
							{selectedExercise || 'Select exercise type'}
						</span>
						<svg class="chevron-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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

			<!-- Face Blurring -->
			{#if selectedFile}
				<div class="section">
					<h2 class="section-title">Privacy</h2>
					<label class="toggle-row">
						<input type="checkbox" bind:checked={blurFaces} disabled={isUploading || isBlurringFaces} />
						<span class="toggle-label">Enable face blurring</span>
					</label>
					{#if blurFaces}
						<button
							type="button"
							class="btn-blur-preview"
							disabled={isUploading || isBlurringFaces}
							onclick={handleGenerateBlurredPreview}
						>
							{#if isBlurringFaces}
								Processing…
							{:else if blurredVideoUrl}
								Regenerate Preview
							{:else}
								Preview Blurred Video
							{/if}
						</button>
					{/if}
				</div>
			{/if}

			<!-- Progress & Messages -->
			{#if isBlurringFaces}
				<div class="progress-block">
					<div class="progress-label-row">
						<span>Processing face blur</span>
						<span>{blurProgress}%</span>
					</div>
					<div class="progress-bar"><div class="progress-fill" style="width:{blurProgress}%"></div></div>
				</div>
			{/if}

			{#if isUploading}
				<div class="progress-block">
					<div class="progress-label-row">
						<span>Uploading</span>
						<span>{uploadProgress}%</span>
					</div>
					<div class="progress-bar"><div class="progress-fill" style="width:{uploadProgress}%"></div></div>
				</div>
			{/if}

			{#if uploadSuccess}
				<div class="msg-success">✓ Video uploaded successfully!</div>
			{/if}

			{#if uploadError}
				<div class="msg-error">✗ {uploadError}</div>
			{/if}

			<button
				type="submit"
				class="btn-continue"
				disabled={isBlurringFaces || !selectedFile || !selectedPatientId || !selectedExercise || isLoadingPatients}
			>
				{#if isBlurringFaces}
					Processing…
				{:else if isLoadingPatients}
					Loading…
				{:else}
					Continue →
				{/if}
			</button>
		</div>

		<!-- Right column: video preview -->
		<div class="preview-col">
			{#if previewSrc}
				<div class="preview-card">
					<h2 class="section-title">
						{blurFaces && blurredVideoUrl ? 'Blurred Preview' : 'Video Preview'}
					</h2>
					<!-- svelte-ignore a11y_media_has_caption -->
					<video src={previewSrc} bind:currentTime controls preload="metadata" class="preview-video"></video>
				</div>
			{:else}
				<div class="preview-placeholder">
					<svg width="64" height="64" viewBox="0 0 64 64" fill="none">
						<circle cx="32" cy="32" r="32" fill="#E3F2FD"/>
						<path d="M24 22l16 10-16 10V22z" fill="#90caf9"/>
					</svg>
					<p>Video preview will appear here after you select a file</p>
				</div>
			{/if}
		</div>
	</form>
</div>

<style>
	.page {
		padding: 32px 48px;
		max-width: 1100px;
	}

	.back-link {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 14px;
		font-weight: 500;
		color: #555;
		text-decoration: none;
		margin-bottom: 20px;
		transition: color 0.15s;
	}

	.back-link:hover {
		color: #1565c0;
	}

	.page-header {
		margin-bottom: 32px;
	}

	.page-header h1 {
		margin: 0 0 6px;
		font-size: 26px;
		font-weight: 700;
		color: #1a1a1a;
	}

	.page-subtitle {
		margin: 0;
		font-size: 14px;
		color: #666;
	}

	/* Two-column layout */
	.upload-layout {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 32px;
		align-items: start;
	}

	/* Sections */
	.section {
		margin-bottom: 24px;
	}

	.section-title {
		margin: 0 0 10px;
		font-size: 14px;
		font-weight: 600;
		color: #1a1a1a;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	/* Upload dropzone */
	.upload-dropzone {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		min-height: 150px;
		padding: 28px 20px;
		border: 2px dashed #c0cfe0;
		border-radius: 12px;
		background: #f8fbff;
		cursor: pointer;
		transition: border-color 0.18s, background 0.18s;
		text-align: center;
	}

	.upload-dropzone:hover,
	.upload-dropzone.has-file {
		border-color: #90caf9;
		background: #e8f4ff;
	}

	.file-icon {
		width: 44px;
		height: 44px;
		color: #90a4ae;
		margin-bottom: 14px;
	}

	.select-btn {
		padding: 10px 24px;
		background: #90caf9;
		border: none;
		border-radius: 8px;
		color: #1a1a1a;
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.18s;
		margin-bottom: 8px;
	}

	.select-btn:hover {
		background: #64b5f6;
	}

	.upload-hint {
		margin: 0;
		font-size: 12px;
		color: #aaa;
	}

	.file-name-selected {
		font-size: 14px;
		font-weight: 600;
		color: #1a1a1a;
		margin: 0 0 6px;
		word-break: break-all;
	}

	.change-file {
		font-size: 12px;
		color: #888;
	}

	.hidden-input {
		display: none;
	}

	/* Dropdowns */
	.dropdown-wrapper {
		position: relative;
	}

	.dropdown-trigger {
		width: 100%;
		padding: 12px 16px;
		border: 1px solid #d0d0d0;
		border-radius: 10px;
		background: #ffffff;
		font-size: 14px;
		color: #1a1a1a;
		display: flex;
		align-items: center;
		justify-content: space-between;
		cursor: pointer;
		transition: border-color 0.18s, box-shadow 0.18s;
		text-align: left;
	}

	.dropdown-trigger:hover:not(:disabled) {
		border-color: #90caf9;
	}

	.dropdown-trigger:focus {
		outline: none;
		border-color: #90caf9;
		box-shadow: 0 0 0 3px rgba(144, 202, 249, 0.2);
	}

	.dropdown-trigger:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.placeholder {
		color: #aaa;
	}

	.chevron-icon {
		width: 18px;
		height: 18px;
		color: #777;
		flex-shrink: 0;
	}

	.dropdown-menu {
		position: absolute;
		top: calc(100% + 4px);
		left: 0;
		right: 0;
		background: #ffffff;
		border: 1px solid #e0e0e0;
		border-radius: 10px;
		box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12);
		z-index: 20;
		max-height: 240px;
		overflow-y: auto;
	}

	.dropdown-item {
		width: 100%;
		padding: 12px 16px;
		border: none;
		background: transparent;
		color: #1a1a1a;
		font-size: 14px;
		text-align: left;
		cursor: pointer;
		display: flex;
		align-items: center;
		gap: 8px;
		transition: background 0.15s;
	}

	.dropdown-item:hover {
		background: #f5f5f5;
	}

	.dropdown-item.create-new {
		color: #1565c0;
		font-weight: 600;
	}

	.dropdown-icon {
		width: 16px;
		height: 16px;
	}

	.dropdown-divider {
		height: 1px;
		background: #e8e8e8;
		margin: 4px 0;
	}

	/* Toggle */
	.toggle-row {
		display: flex;
		align-items: center;
		gap: 10px;
		cursor: pointer;
		margin-bottom: 12px;
	}

	.toggle-row input {
		width: 18px;
		height: 18px;
		margin: 0;
		accent-color: #1565c0;
		cursor: pointer;
	}

	.toggle-label {
		font-size: 14px;
		color: #1a1a1a;
	}

	.btn-blur-preview {
		width: 100%;
		padding: 11px;
		background: #e3f2fd;
		border: 1px solid #90caf9;
		border-radius: 9px;
		color: #1565c0;
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.18s;
	}

	.btn-blur-preview:hover:not(:disabled) {
		background: #bbdefb;
	}

	.btn-blur-preview:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* Progress */
	.progress-block {
		margin-bottom: 16px;
	}

	.progress-label-row {
		display: flex;
		justify-content: space-between;
		font-size: 13px;
		color: #555;
		margin-bottom: 6px;
	}

	.progress-bar {
		width: 100%;
		height: 8px;
		background: #e0e0e0;
		border-radius: 4px;
		overflow: hidden;
	}

	.progress-fill {
		height: 100%;
		background: #64b5f6;
		transition: width 0.3s ease;
		border-radius: 4px;
	}

	/* Messages */
	.msg-success {
		padding: 12px 14px;
		background: #e8f5e9;
		border: 1px solid #c8e6c9;
		border-radius: 8px;
		color: #2e7d32;
		font-size: 14px;
		font-weight: 600;
		margin-bottom: 16px;
	}

	.msg-error {
		padding: 12px 14px;
		background: #ffebee;
		border: 1px solid #ffcdd2;
		border-radius: 8px;
		color: #c62828;
		font-size: 14px;
		margin-bottom: 16px;
		word-break: break-word;
	}

	/* Continue button */
	.btn-continue {
		width: 100%;
		padding: 14px;
		border: none;
		border-radius: 10px;
		background: #90caf9;
		color: #1a1a1a;
		font-size: 15px;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.18s;
	}

	.btn-continue:hover:not(:disabled) {
		background: #64b5f6;
	}

	.btn-continue:disabled {
		background: #e0e0e0;
		color: #aaa;
		cursor: not-allowed;
	}

	/* Preview column */
	.preview-col {
		position: sticky;
		top: 24px;
	}

	.preview-card {
		background: #ffffff;
		border: 1px solid #e8eaed;
		border-radius: 14px;
		padding: 20px;
	}

	.preview-video {
		width: 100%;
		border-radius: 10px;
		background: #000;
		border: 1px solid #e0e0e0;
		margin-top: 4px;
	}

	.preview-placeholder {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 48px 24px;
		background: #ffffff;
		border: 1px dashed #d0d0d0;
		border-radius: 14px;
		text-align: center;
		color: #999;
		gap: 16px;
		font-size: 14px;
		line-height: 1.5;
	}

	/* Responsive: single column on mobile */
	@media (max-width: 768px) {
		.page {
			padding: 20px 16px 40px;
		}

		.upload-layout {
			grid-template-columns: 1fr;
			gap: 0;
		}

		.preview-col {
			position: static;
			margin-top: 8px;
		}

		.page-header h1 {
			font-size: 22px;
		}
	}
</style>
