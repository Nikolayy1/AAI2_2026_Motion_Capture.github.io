<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { VIDEO_LIST_ENDPOINT, DOWNLOAD_ENDPOINT } from '$lib/config';

	interface Video {
		filename: string;
		patient: string;
		exercise?: string;
		uploadDate?: string;
		duration?: string;
		thumbnail?: string;
	}

	let videos = $state<Video[]>([]);
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

	onMount(async () => {
		await loadVideos();
	});

	async function loadVideos() {
		isLoading = true;
		error = '';

		try {
			const response = await fetch(VIDEO_LIST_ENDPOINT);

			if (!response.ok) {
				throw new Error(`Failed to load videos: ${response.statusText}`);
			}

			const data = await response.json();
			videos = data.videos || [];
		} catch (err) {
			console.error('Error loading videos:', err);
			error = `${err}`;
			videos = [];
		} finally {
			isLoading = false;
		}
	}

	function handleBack() {
		goto('/mobile/dashboard');
	}

	function handleUploadNew() {
		goto('/mobile/upload');
	}

	function handleVideoClick(video: Video) {
		// Navigate to video detail page or play video
		const videoUrl = `${DOWNLOAD_ENDPOINT}/${video.filename}`;
		window.open(videoUrl, '_blank');
	}

	function formatDate(dateString?: string): string {
		if (!dateString) return 'N/A';
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
		return videos.filter(video => {
			const matchesSearch = searchQuery === '' ||
				video.patient.toLowerCase().includes(searchQuery.toLowerCase()) ||
				(video.exercise?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false);

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
		<h1>Video Library</h1>
	</header>

	<!-- Search and Filter -->
	<div class="controls">
		<div class="search-box">
			<svg width="20" height="20" viewBox="0 0 20 20" fill="none" class="search-icon">
				<path d="M9 17A8 8 0 1 0 9 1a8 8 0 0 0 0 16zM18 18l-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
			</svg>
			<input
				type="text"
				bind:value={searchQuery}
				placeholder="Search by patient or exercise..."
				class="search-input"
			/>
		</div>

		<select bind:value={selectedExercise} class="filter-select">
			{#each exerciseTypes as type}
				<option value={type.value}>{type.label}</option>
			{/each}
		</select>
	</div>

	<!-- Upload New Button -->
	<button class="upload-new-button" onclick={handleUploadNew}>
		<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
			<path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
		</svg>
		Upload New Recording
	</button>

	<!-- Loading State -->
	{#if isLoading}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading videos...</p>
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
			<button class="retry-button" onclick={loadVideos}>Retry</button>
		</div>
	{/if}

	<!-- Videos List -->
	{#if !isLoading && !error}
		{#if filteredVideos().length === 0}
			<div class="empty-state">
				<svg width="64" height="64" viewBox="0 0 64 64" fill="none">
					<circle cx="32" cy="32" r="32" fill="#E3F2FD"/>
					<path d="M24 22l16 10-16 10V22z" fill="#64B5F6"/>
				</svg>
				<h2>No Videos Found</h2>
				<p>{searchQuery || selectedExercise !== 'all' ? 'Try adjusting your filters' : 'Upload your first recording to get started'}</p>
				<button class="upload-button" onclick={handleUploadNew}>Upload Recording</button>
			</div>
		{:else}
			<div class="video-grid">
				{#each filteredVideos() as video}
					<div class="video-card" onclick={() => handleVideoClick(video)}>
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
							{#if video.duration}
								<span class="duration-badge">{video.duration}</span>
							{/if}
						</div>
						<div class="video-info">
							<h3 class="video-title">{video.patient}</h3>
							<p class="video-exercise">{video.exercise || 'General'}</p>
							<div class="video-meta">
								<span class="video-date">{formatDate(video.uploadDate)}</span>
							</div>
						</div>
					</div>
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
	}

	/* Controls */
	.controls {
		display: flex;
		flex-direction: column;
		gap: 12px;
		margin-bottom: 16px;
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

	/* Upload New Button */
	.upload-new-button {
		width: 100%;
		padding: 14px;
		background: linear-gradient(135deg, #66BB6A 0%, #4CAF50 100%);
		color: white;
		border: none;
		border-radius: 8px;
		font-size: 16px;
		font-weight: 600;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 8px;
		transition: opacity 0.2s;
		margin-bottom: 24px;
	}

	.upload-new-button:hover {
		opacity: 0.9;
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

	/* Empty State */
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 48px 20px;
		text-align: center;
	}

	.empty-state h2 {
		font-size: 18px;
		font-weight: 600;
		color: #333;
		margin: 16px 0 8px 0;
	}

	.empty-state p {
		font-size: 14px;
		color: #666;
		margin-bottom: 24px;
	}

	.upload-button {
		padding: 12px 24px;
		background: linear-gradient(135deg, #64B5F6 0%, #42A5F5 100%);
		color: white;
		border: none;
		border-radius: 8px;
		font-size: 16px;
		font-weight: 600;
		cursor: pointer;
		transition: opacity 0.2s;
	}

	.upload-button:hover {
		opacity: 0.9;
	}

	/* Video Grid */
	.video-grid {
		display: grid;
		gap: 16px;
	}

	.video-card {
		background-color: #ffffff;
		border-radius: 12px;
		overflow: hidden;
		cursor: pointer;
		transition: transform 0.2s, box-shadow 0.2s;
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
		font-size: 12px;
		font-weight: 600;
	}

	.video-info {
		padding: 16px;
	}

	.video-title {
		font-size: 16px;
		font-weight: 600;
		color: #333;
		margin: 0 0 4px 0;
	}

	.video-exercise {
		font-size: 14px;
		color: #64B5F6;
		margin: 0 0 8px 0;
	}

	.video-meta {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.video-date {
		font-size: 12px;
		color: #999;
	}
</style>
