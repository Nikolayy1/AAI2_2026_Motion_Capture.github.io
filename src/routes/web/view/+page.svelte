<script lang="ts">
	import { onMount } from "svelte";
	import { API_CONFIG } from "$lib/config";

	let srcOriginal: string | null = $state(null);
	let srcModel: string | null = $state(null);
	let currentTime: number = $state(0);
	let loading: boolean = $state(true);
	let error: string | null = $state(null);
	let isDownloading: boolean = $state(false);
	let downloadProgress: number = $state(0);
	let downloadSuccess: boolean = $state(false);
	let downloadError: string | null = $state(null);

	async function loadVideos() {
		loading = true;
		error = null;

		try {
			const response = await fetch(API_CONFIG.VIDEO_LIST_ENDPOINT);
			if (!response.ok) {
				throw new Error(`Server returned ${response.status}`);
			}

			const payload = await response.json();
			const videos = Array.isArray(payload)
				? payload
				: payload.videos ?? payload.items ?? [];

			const videoUrls = videos
				.map((video: any) =>
					typeof video === "string"
						? video
						: video.url ?? video.src ?? ""
				)
				.filter((url: string) => !!url)
				.slice(0, 2);

			if (videoUrls.length >= 1) {
				srcOriginal = videoUrls[0];
			}
			if (videoUrls.length >= 2) {
				srcModel = videoUrls[1];
			}

			if (videoUrls.length === 0) {
				error = "No video URLs were returned from the server.";
			}
		} catch (err) {
			error = err instanceof Error ? err.message : "Unable to load videos.";
		} finally {
			loading = false;
		}
	}

	onMount(loadVideos);

/**
	function downloadVideo(file: File) {
		isDownloading = true;
		downloadProgress = 0;
		downloadSuccess = false;
		downloadError = null;

		const formData = new FormData();
		formData.append("video", file);

		const xhr = new XMLHttpRequest();

		// Track download progress
		xhr.addEventListener("progress", (e) => {
			if (e.lengthComputable) {
				downloadProgress = Math.round((e.loaded / e.total) * 100);
			}
		});

		xhr.addEventListener("load", () => {
			isDownloading = false;

			if (xhr.status >= 200 && xhr.status < 300) {
				downloadSuccess = true;
				downloadProgress = 100;

				try {
					const response = JSON.parse(xhr.responseText);
					console.log("Download successful:", response);
				} catch (e) {
					console.log("Download successful");
				}
			} else {
				downloadError = `Download failed: ${xhr.statusText || "Server error"}`;
				downloadProgress = 0;
			}
		});

		// Handle errors
		xhr.addEventListener("error", () => {
			isDownloading = false;
			downloadError =
				"Download failed: Network error. Please check if the backend server is running.";
			downloadProgress = 0;
		});

		xhr.addEventListener("abort", () => {
			isDownloading = false;
			downloadError = "Download cancelled";
			downloadProgress = 0;
		});

		// Send the request
		xhr.open("GET", API_CONFIG.DOWNLOAD_ENDPOINT);
		xhr.send();
	}
	*/
</script>

<svelte:head>
	<title>View Videos</title>
</svelte:head>

<div class="view-page">
	<h1>Compare Original and Model output</h1>

	{#if loading}
		<p>Loading videos from the server...</p>
	{:else if error}
		<p class="error">{error}</p>
	{:else}
		<div class="video-grid">
			{#if srcOriginal}
				<div class="video-card">
					<h2>Video 1</h2>
					<!-- svelte-ignore a11y-media-has-caption -->
					<video src={srcOriginal} bind:currentTime controls preload="metadata" />
					<p>Time: {currentTime.toFixed(1)}s</p>
				</div>
			{/if}

			{#if srcModel}
				<div class="video-card">
					<h2>Video 2</h2>
					<!-- svelte-ignore a11y-media-has-caption -->
					<video src={srcModel} bind:currentTime controls preload="metadata" />
					<p>Time: {currentTime.toFixed(1)}s</p>
				</div>
			{/if}
		</div>

		{#if !srcOriginal && !srcModel}
			<p>No videos are available right now.</p>
		{/if}
	{/if}
</div>

<style>
	.view-page {
		padding: 1rem;
	}

	.video-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		align-items: start;
	}

	.video-card {
		border: 1px solid #ddd;
		border-radius: 0.75rem;
		padding: 1rem;
		background: #fff;
	}

	.video-card h2 {
		margin-top: 0;
		font-size: 1.1rem;
	}

	video {
		display: block;
		width: 100%;
		max-width: 100%;
		height: auto;
		border-radius: 0.5rem;
		margin: 0.5rem 0;
	}

	.error {
		color: #bf2d2d;
	}

	@media (max-width: 900px) {
		.video-grid {
			grid-template-columns: 1fr;
		}
	}
</style>