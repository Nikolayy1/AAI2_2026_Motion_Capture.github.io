<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { API_CONFIG } from '$lib/config';
	import { apiFetch } from '$lib/api';

	interface Video {
		filename: string;
		patient: string;
		exercise?: string;
		uploadDate?: string;
		duration?: string;
		thumbnail?: string;
		videoUrl?: string;
		keypointsUrl?: string;
		isAnnotated?: boolean;
		submissionId?: string;
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

	onMount(() => {
		void loadVideos();
	});

	async function loadVideos() {
		isLoading = true;
		error = '';
		try {
			const response = await apiFetch(API_CONFIG.VIDEO_LIST_ENDPOINT);
			if (!response.ok) throw new Error(`Failed to load videos: ${response.statusText}`);

			const data = await response.json();
			console.log('Backend response for all videos:', data);

			const rawVideoList = Array.isArray(data) ? data : data.videos || [];
			const videoList = rawVideoList.filter((v: any) => v.annotated_video_url);

			if (videoList.length > 0) console.log('First video data:', videoList[0]);

			videos = videoList.map((v: any) => {
				const exercise = v.exercise_type || v.exerciseType || v.exercise || v.biometrics?.exercise_type || v.metadata?.exercise_type || 'General';
				const filename = extractFilename(v.annotated_video_url) || v.filename || 'video_out.mp4';
				const videoUrl = v.annotated_video_url;
				const videoData = {
					filename,
					patient: v.patient_name || v.patient?.name || 'Unknown Patient',
					exercise,
					uploadDate: v.uploaded_at || v.upload_date || new Date().toISOString(),
					duration: v.duration || undefined,
					thumbnail: v.thumbnail || undefined,
					videoUrl,
					keypointsUrl: getKeypointsUrlFromVideoUrl(videoUrl),
					isAnnotated: true,
					submissionId: v.submission_id || undefined
				};
				console.log(`Video ${v.submission_id || filename} - Exercise: ${exercise}`);
				return videoData;
			});
		} catch (err) {
			console.error('Error loading videos:', err);
			error = `${err}`;
			videos = [];
		} finally {
			isLoading = false;
		}
	}

	function extractFilename(url: string): string {
		if (!url) return 'video.mp4';
		const parts = url.split('/');
		return parts[parts.length - 1] || 'video.mp4';
	}

	function handleUploadNew() {
		goto('/mobile/upload');
	}

	function getKeypointsUrlFromVideoUrl(videoUrl?: string) {
		if (!videoUrl) return undefined;
		return videoUrl.replace(/output\.mp4$/, 'keypoints_2d.csv');
	}

	function handleAnnotationButton(event: MouseEvent, video: Video) {
		event.stopPropagation();
		const videoUrl = video.videoUrl?.startsWith('http') ? video.videoUrl : `${API_CONFIG.BASE_URL}${video.videoUrl}`;
		const keypointsUrl = video.keypointsUrl?.startsWith('http') ? video.keypointsUrl : `${API_CONFIG.BASE_URL}${video.keypointsUrl}`;
		goto(`/web/annotation?submission_id=${video.submissionId}&video=${encodeURIComponent(videoUrl)}&keypoints=${encodeURIComponent(keypointsUrl)}`);
	}

	function handleVideoClick(video: Video) {
		if (!video.videoUrl) return;
		const videoUrl = video.videoUrl.startsWith('http') ? video.videoUrl : `${API_CONFIG.BASE_URL}${video.videoUrl}`;
		window.open(videoUrl, '_blank');
	}

	function formatDate(dateString?: string): string {
		if (!dateString) return 'N/A';
		try {
			const date = new Date(dateString);
			return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
		} catch {
			return dateString;
		}
	}

	let filteredVideos = $derived(() => {
		return videos.filter((video) => {
			const matchesSearch =
				searchQuery === '' ||
				video.patient.toLowerCase().includes(searchQuery.toLowerCase()) ||
				(video.exercise?.toLowerCase().includes(searchQuery.toLowerCase()) ?? false);
			const matchesExercise = selectedExercise === 'all' || video.exercise === selectedExercise;
			return matchesSearch && matchesExercise;
		});
	});
</script>

<svelte:head>
	<title>Video Library — Gait Analysis</title>
</svelte:head>

<div class="page">
	<!-- Header -->
	<div class="page-header">
		<div class="header-text">
			<h1>Video Library</h1>
			<p class="header-subtitle">Browse all annotated recordings</p>
		</div>
		<button class="btn-upload" onclick={handleUploadNew}>
			<svg width="18" height="18" viewBox="0 0 18 18" fill="none">
				<path d="M9 3v12M3 9h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
			</svg>
			Upload Recording
		</button>
	</div>

	<!-- Controls -->
	<div class="controls">
		<div class="search-box">
			<svg width="17" height="17" viewBox="0 0 17 17" fill="none" class="search-icon">
				<path d="M7.5 14A6.5 6.5 0 1 0 7.5 1a6.5 6.5 0 0 0 0 13zM16 16l-3.5-3.5" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>
			</svg>
			<input
				type="text"
				bind:value={searchQuery}
				placeholder="Search by patient or exercise…"
				class="search-input"
			/>
		</div>
		<select bind:value={selectedExercise} class="filter-select">
			{#each exerciseTypes as type}
				<option value={type.value}>{type.label}</option>
			{/each}
		</select>
	</div>

	<!-- Loading -->
	{#if isLoading}
		<div class="state-box">
			<div class="spinner"></div>
			<p>Loading videos…</p>
		</div>
	{/if}

	<!-- Error -->
	{#if error && !isLoading}
		<div class="state-box">
			<svg width="48" height="48" viewBox="0 0 48 48" fill="none">
				<circle cx="24" cy="24" r="24" fill="#FFEBEE"/>
				<path d="M24 16v8M24 28v2" stroke="#e53935" stroke-width="2" stroke-linecap="round"/>
			</svg>
			<p class="error-text">{error}</p>
			<button class="btn-retry" onclick={loadVideos}>Retry</button>
		</div>
	{/if}

	<!-- Videos -->
	{#if !isLoading && !error}
		{#if filteredVideos().length === 0}
			<div class="state-box">
				<svg width="64" height="64" viewBox="0 0 64 64" fill="none">
					<circle cx="32" cy="32" r="32" fill="#E3F2FD"/>
					<path d="M24 22l16 10-16 10V22z" fill="#90caf9"/>
				</svg>
				<h3>No Videos Found</h3>
				<p>{searchQuery || selectedExercise !== 'all' ? 'Try adjusting your filters' : 'Upload your first recording to get started'}</p>
				{#if !searchQuery && selectedExercise === 'all'}
					<button class="btn-upload" onclick={handleUploadNew} style="margin-top: 12px;">
						Upload Recording
					</button>
				{/if}
			</div>
		{:else}
			<div class="results-count">{filteredVideos().length} recording{filteredVideos().length !== 1 ? 's' : ''}</div>
			<div class="video-grid">
				{#each filteredVideos() as video}
					<div class="video-item">
						<button
							type="button"
							class="video-card"
							onclick={() => handleVideoClick(video)}
						>
							<div class="video-thumbnail">
								{#if video.thumbnail}
									<img src={video.thumbnail} alt={video.filename} />
								{:else}
									<div class="thumbnail-placeholder">
										<svg width="44" height="44" viewBox="0 0 44 44" fill="none">
											<circle cx="22" cy="22" r="22" fill="white" opacity="0.25"/>
											<path d="M17 14l14 8-14 8V14z" fill="white"/>
										</svg>
									</div>
								{/if}
								{#if video.duration}
									<span class="duration-badge">{video.duration}</span>
								{/if}
								<div class="play-overlay">
									<svg width="36" height="36" viewBox="0 0 36 36" fill="none">
										<circle cx="18" cy="18" r="18" fill="rgba(0,0,0,0.45)"/>
										<path d="M14 12l12 6-12 6V12z" fill="white"/>
									</svg>
								</div>
							</div>
							<div class="video-info">
								<p class="video-exercise">{video.exercise || 'General'}</p>
								<p class="video-patient">{video.patient}</p>
								<p class="video-date">{formatDate(video.uploadDate)}</p>
							</div>
						</button>
						<button
							type="button"
							class="annotation-button"
							onclick={(e) => handleAnnotationButton(e, video)}
						>
							<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
								<path d="M9.5 1.5a1.5 1.5 0 0 1 2.12 2.12L4.5 10.75l-2.75.5.5-2.75L9.5 1.5z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
							</svg>
							Annotate Keypoints
						</button>
					</div>
				{/each}
			</div>
		{/if}
	{/if}
</div>

<style>
	.page {
		padding: 40px 48px;
		max-width: 1200px;
	}

	/* Header */
	.page-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 16px;
		margin-bottom: 24px;
	}

	.header-text h1 {
		margin: 0 0 4px;
		font-size: 28px;
		font-weight: 700;
		color: #1a1a1a;
	}

	.header-subtitle {
		margin: 0;
		font-size: 14px;
		color: #666;
	}

	.btn-upload {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		padding: 10px 18px;
		background: #66bb6a;
		color: #ffffff;
		border: none;
		border-radius: 8px;
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.18s;
		flex-shrink: 0;
		white-space: nowrap;
	}

	.btn-upload:hover {
		background: #4caf50;
	}

	/* Controls */
	.controls {
		display: flex;
		gap: 12px;
		margin-bottom: 20px;
		flex-wrap: wrap;
	}

	.search-box {
		position: relative;
		display: flex;
		align-items: center;
		flex: 1;
		min-width: 200px;
	}

	.search-icon {
		position: absolute;
		left: 13px;
		color: #999;
		pointer-events: none;
	}

	.search-input {
		width: 100%;
		padding: 10px 14px 10px 40px;
		border: 1px solid #e0e0e0;
		border-radius: 9px;
		font-size: 14px;
		color: #333;
		background: #ffffff;
		transition: border-color 0.18s, box-shadow 0.18s;
		outline: none;
	}

	.search-input:focus {
		border-color: #90caf9;
		box-shadow: 0 0 0 3px rgba(144, 202, 249, 0.2);
	}

	.search-input::placeholder {
		color: #aaa;
	}

	.filter-select {
		padding: 10px 14px;
		border: 1px solid #e0e0e0;
		border-radius: 9px;
		font-size: 14px;
		color: #333;
		background: #ffffff;
		cursor: pointer;
		transition: border-color 0.18s;
		outline: none;
		min-width: 160px;
	}

	.filter-select:focus {
		border-color: #90caf9;
	}

	/* States */
	.state-box {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 64px 20px;
		text-align: center;
		color: #666;
	}

	.state-box p {
		margin: 10px 0 0;
		font-size: 14px;
		color: #888;
	}

	.state-box h3 {
		margin: 14px 0 6px;
		font-size: 17px;
		font-weight: 600;
		color: #333;
	}

	.spinner {
		width: 36px;
		height: 36px;
		border: 3.5px solid #e0e0e0;
		border-top-color: #90caf9;
		border-radius: 50%;
		animation: spin 0.85s linear infinite;
		margin-bottom: 12px;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.error-text {
		color: #e53935;
		font-size: 14px;
		margin: 12px 0 16px;
	}

	.btn-retry {
		padding: 9px 22px;
		background: #90caf9;
		color: #1a1a1a;
		border: none;
		border-radius: 7px;
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.18s;
	}

	.btn-retry:hover {
		background: #64b5f6;
	}

	/* Results count */
	.results-count {
		font-size: 13px;
		color: #888;
		margin-bottom: 16px;
	}

	/* Video grid */
	.video-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
		gap: 20px;
	}

	.video-item {
		display: flex;
		flex-direction: column;
		gap: 0;
	}

	.video-card {
		border: 1px solid #e8eaed;
		background: #ffffff;
		border-radius: 12px 12px 0 0;
		padding: 0;
		text-align: left;
		width: 100%;
		overflow: hidden;
		cursor: pointer;
		transition: box-shadow 0.18s;
		border-bottom: none;
	}

	.video-card:hover {
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
	}

	.video-card:hover .play-overlay {
		opacity: 1;
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

	.play-overlay {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		opacity: 0;
		transition: opacity 0.18s;
	}

	.duration-badge {
		position: absolute;
		bottom: 8px;
		right: 8px;
		background: rgba(0, 0, 0, 0.65);
		color: white;
		padding: 3px 7px;
		border-radius: 4px;
		font-size: 11px;
		font-weight: 600;
	}

	.video-info {
		padding: 12px 14px 14px;
	}

	.video-exercise {
		margin: 0 0 3px;
		font-size: 14px;
		font-weight: 600;
		color: #1a1a1a;
	}

	.video-patient {
		margin: 0 0 4px;
		font-size: 13px;
		color: #1565c0;
	}

	.video-date {
		margin: 0;
		font-size: 12px;
		color: #aaa;
	}

	.annotation-button {
		width: 100%;
		padding: 10px;
		background: #e3f2fd;
		border: 1px solid #e8eaed;
		border-top: 1px solid #bbdefb;
		border-radius: 0 0 12px 12px;
		color: #1565c0;
		font-size: 13px;
		font-weight: 600;
		cursor: pointer;
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 6px;
		transition: background 0.18s;
	}

	.annotation-button:hover {
		background: #bbdefb;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.page {
			padding: 20px 16px 32px;
		}

		.header-text h1 {
			font-size: 22px;
		}

		.controls {
			flex-direction: column;
		}

		.filter-select {
			min-width: 0;
			width: 100%;
		}

		.video-grid {
			grid-template-columns: 1fr;
		}
	}

	@media (min-width: 769px) and (max-width: 1100px) {
		.video-grid {
			grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
		}
	}
</style>
