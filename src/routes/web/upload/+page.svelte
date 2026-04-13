<script lang="ts">
	import { API_CONFIG } from "$lib/config";
	import { blurFacesInVideo } from "$lib/videoFaceBlurring";

	let src: string | null = $state(null);
	let fileName: string = $state("");
	let selectedFile: File | null = $state(null);
	let blurredVideoFile: File | null = $state(null);
	let blurredVideoUrl: string | null = $state(null);
	let currentTime: number = $state(0);
	let isUploading: boolean = $state(false);
	let isBlurringFaces: boolean = $state(false);
	let blurFaces: boolean = $state(true);
	let blurProgress: number = $state(0);
	let uploadProgress: number = $state(0);
	let uploadSuccess: boolean = $state(false);
	let uploadError: string | null = $state(null);
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

	// Upload always goes through this gate so blur can run first when enabled.
	async function handleUpload(event: Event) {
		event.preventDefault();

		if (!selectedFile) {
			alert("Please choose an MP4 video first.");
			return;
		}

		const fileToUpload = await prepareVideoForUpload(selectedFile);

		if (fileToUpload) {
			uploadVideo(fileToUpload);
		}
	}

	async function handleGenerateBlurredPreview() {
		if (!selectedFile) {
			alert("Please choose an MP4 video first.");
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

		const formData = new FormData();
		formData.append("video", file);

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

<div class="page">
	<header class="topbar">
		<div class="brand">
			<img src="/logo.png" alt="Biomechanics4All logo" class="logo" />
			<span class="brand-text">
				<span class="dark">Biomechanics</span><span class="accent"
					>4All</span
				>
			</span>
		</div>
	</header>

	<main class="content">
		<div class="card">
			<h1>Upload Video</h1>
			<p class="subtitle">Select an MP4 video file to continue.</p>

			<form onsubmit={handleUpload}>
				<div class="field">
					<label for="video-upload">Video file</label>

					<label for="video-upload" class="upload-box">
						{#if fileName}
							<span>{fileName}</span>
						{:else}
							<span>Choose an MP4 video</span>
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

				{#if previewSrc}
					<div class="preview-wrapper">
						<p class="preview-label">
							{blurFaces && blurredVideoUrl
								? "Blurred preview"
								: "Preview"}
						</p>
						<!-- svelte-ignore a11y_media_has_caption -->
						<video
							src={previewSrc}
							bind:currentTime
							controls
							preload="metadata"
						></video>
						<p class="time-text">
							Current time: {currentTime.toFixed(1)}s
						</p>
					</div>
				{/if}

				<label class="toggle-row">
					<input
						type="checkbox"
						bind:checked={blurFaces}
						disabled={isUploading || isBlurringFaces}
					/>
					<span>Blur faces before upload</span>
				</label>

				{#if selectedFile && blurFaces}
					<button
						type="button"
						class="secondary-btn"
						disabled={isUploading || isBlurringFaces}
						onclick={handleGenerateBlurredPreview}
					>
						{#if isBlurringFaces}
							Making blurred preview...
						{:else if blurredVideoUrl}
							Regenerate blurred preview
						{:else}
							Preview blurred video
						{/if}
					</button>
				{/if}

				{#if blurredVideoUrl && blurredVideoFile}
					<a
						class="secondary-btn download-btn"
						href={blurredVideoUrl}
						download={blurredVideoFile.name}
					>
						Download blurred video
					</a>
				{/if}

				{#if isBlurringFaces}
					<div class="progress-wrapper">
						<p class="progress-label">
							Making blurred preview... {blurProgress}%
						</p>
						<div class="progress-bar">
							<div
								class="progress-fill"
								style="width: {blurProgress}%"
							></div>
						</div>
					</div>
				{/if}

				{#if isUploading}
					<div class="progress-wrapper">
						<p class="progress-label">
							Uploading... {uploadProgress}%
						</p>
						<div class="progress-bar">
							<div
								class="progress-fill"
								style="width: {uploadProgress}%"
							></div>
						</div>
					</div>
				{/if}

				{#if uploadSuccess}
					<div class="success-message">
						✓ Video uploaded successfully!
					</div>
				{/if}

				{#if uploadError}
					<div class="error-message">
						✗ {uploadError}
					</div>
				{/if}

				<button
					type="submit"
					class="primary-btn"
					disabled={isUploading || isBlurringFaces}
				>
					{#if isBlurringFaces}
						Making preview...
					{:else if isUploading}
						Uploading...
					{:else}
						Upload video
					{/if}
				</button>

				<div class="divider"></div>
			</form>
		</div>
	</main>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: Arial, sans-serif;
		background: linear-gradient(90deg, #f7fbff 0%, #ffffff 100%);
		color: #222;
	}

	:global(*) {
		box-sizing: border-box;
	}

	.page {
		min-height: 100vh;
	}

	.topbar {
		height: 72px;
		background: #eef5fb;
		display: flex;
		align-items: center;
		padding: 0 28px;
		border-bottom: 1px solid rgba(0, 0, 0, 0.04);
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.logo {
		height: 80px;
		width: auto;
		object-fit: contain;
	}

	.brand-text {
		font-size: 22px;
		font-weight: 700;
		line-height: 1;
	}

	.dark {
		color: #17345d;
	}

	.accent {
		color: #2db4bf;
	}

	.content {
		min-height: calc(100vh - 72px);
		display: flex;
		justify-content: center;
		align-items: center;
		padding: 40px 20px;
	}

	.card {
		width: 100%;
		max-width: 425px;
		background: #f8f8f8;
		border-radius: 22px;
		padding: 28px 34px 34px;
		box-shadow: 0 4px 14px rgba(0, 0, 0, 0.16);
	}

	h1 {
		margin: 0 0 12px;
		text-align: center;
		font-size: 28px;
		font-weight: 700;
	}

	.subtitle {
		margin: 0 0 26px;
		text-align: center;
		font-size: 15px;
		color: #444;
	}

	form {
		display: flex;
		flex-direction: column;
	}

	.field {
		display: flex;
		flex-direction: column;
		margin-bottom: 18px;
	}

	label {
		font-size: 15px;
		font-weight: 600;
		margin-bottom: 8px;
		color: #303030;
	}

	.upload-box {
		width: 100%;
		min-height: 44px;
		padding: 12px 18px;
		border: 1px solid #cfcfcf;
		border-radius: 4px;
		background: #f7f7f7;
		font-size: 14px;
		color: #a0a0a0;
		display: flex;
		align-items: center;
		cursor: pointer;
		box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.03);
	}

	.upload-box:hover {
		border-color: #8ab2df;
		background: white;
	}

	.hidden-input {
		display: none;
	}

	.preview-wrapper {
		margin-bottom: 18px;
	}

	.preview-label {
		margin: 0 0 8px;
		font-size: 15px;
		font-weight: 600;
		color: #303030;
	}

	video {
		width: 100%;
		display: block;
		border-radius: 8px;
		background: black;
		border: 1px solid #cfcfcf;
	}

	.time-text {
		margin: 8px 0 0;
		font-size: 13px;
		color: #666;
	}

	.toggle-row {
		display: flex;
		align-items: center;
		gap: 10px;
		margin: 0 0 12px;
		cursor: pointer;
	}

	.toggle-row input {
		width: 18px;
		height: 18px;
		margin: 0;
		accent-color: #2db4bf;
	}

	.toggle-row span {
		font-size: 14px;
		color: #303030;
	}

	.primary-btn,
	.secondary-btn {
		width: 100%;
		height: 46px;
		border-radius: 4px;
		font-size: 16px;
		font-weight: 700;
		cursor: pointer;
		text-align: center;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-top: 8px;
		border: none;
		background: #97bbe8;
		color: #1f1f1f;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12);
	}

	.primary-btn:hover:not(:disabled) {
		background: #89aedc;
	}

	.secondary-btn {
		height: 42px;
		margin: 0 0 10px;
		background: white;
		border: 1px solid #97bbe8;
		box-shadow: none;
		color: #17345d;
	}

	.secondary-btn:hover:not(:disabled) {
		background: #eef5fb;
	}

	.download-btn {
		text-decoration: none;
		margin: 0 0 10px;
	}

	.primary-btn:disabled,
	.secondary-btn:disabled {
		background: #c5d5ea;
		cursor: not-allowed;
		opacity: 0.7;
	}

	.progress-wrapper {
		margin: 18px 0;
	}

	.progress-label {
		margin: 0 0 8px;
		font-size: 14px;
		font-weight: 600;
		color: #303030;
		text-align: center;
	}

	.progress-bar {
		width: 100%;
		height: 24px;
		background: #e5e5e5;
		border-radius: 12px;
		overflow: hidden;
		box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
	}

	.progress-fill {
		height: 100%;
		background: linear-gradient(90deg, #6fa3d8 0%, #97bbe8 100%);
		transition: width 0.3s ease;
		display: flex;
		align-items: center;
		justify-content: flex-end;
		padding-right: 8px;
	}

	.success-message {
		margin: 18px 0;
		padding: 12px 16px;
		background: #d4edda;
		border: 1px solid #c3e6cb;
		border-radius: 6px;
		color: #155724;
		font-size: 15px;
		font-weight: 600;
		text-align: center;
	}

	.error-message {
		margin: 18px 0;
		padding: 12px 16px;
		background: #f8d7da;
		border: 1px solid #f5c6cb;
		border-radius: 6px;
		color: #721c24;
		font-size: 14px;
		text-align: center;
		word-break: break-word;
	}

	.divider {
		margin: 18px 0;
		display: flex;
		align-items: center;
		gap: 12px;
	}

	@media (max-width: 520px) {
		.topbar {
			padding: 0 16px;
		}

		.brand-text {
			font-size: 18px;
		}

		.logo {
			height: 130px;
			width: auto;
			object-fit: contain;
		}

		.card {
			padding: 24px 20px 26px;
		}
	}
</style>
