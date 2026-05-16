<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { API_CONFIG } from '$lib/config';
	import { apiFetch } from '$lib/api';
	import {
		coerceBiometrics,
		getLatestSubmissionBiometrics,
		getPatientBiometrics,
		savePatientBiometrics
	} from '$lib/biometrics';

	interface Video {
		id: string;
		filename: string;
		videoUrl: string;
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
			const response = await apiFetch(endpoint);
			if (!response.ok) throw new Error('Failed to load patient data');
			const data = await response.json();
			if (data.error) throw new Error(data.error);

			console.log('Backend response for patient videos:', data);

			const extractFilename = (url: string) => {
				if (!url) return 'video.mp4';
				const parts = url.split('/');
				return parts[parts.length - 1] || 'video.mp4';
			};

			const formatUploadDate = (dateString: string) => {
				if (!dateString) return new Date().toISOString().split('T')[0];
				return dateString.split('T')[0];
			};

			const mappedVideos = data.videos.map((v: any) => {
				const exercise = v.exercise_type || v.exerciseType || v.exercise || v.biometrics?.exercise_type || v.metadata?.exercise_type || 'General';
				const filename = extractFilename(v.video_url);
				const videoUrl = `/files/videos/${filename}`;
				return {
					id: String(v.submission_id || ''),
					filename,
					videoUrl,
					exercise,
					date: formatUploadDate(v.uploaded_at),
					duration: v.duration || '00:00',
					thumbnail: undefined as string | undefined
				};
			});

			const storedBiometrics = getPatientBiometrics(patientId!);
			const fallbackBiometrics = getLatestSubmissionBiometrics(data.videos);
			const biometrics = storedBiometrics || fallbackBiometrics || coerceBiometrics();

			if (!storedBiometrics && fallbackBiometrics && patientId) {
				savePatientBiometrics(patientId, fallbackBiometrics);
			}

			patientData = {
				name: data.patient?.name || patientName,
				age: Number(biometrics.age) || 0,
				gender: biometrics.gender || 'Unknown',
				height: Number(biometrics.height) || 0,
				weight: Number(biometrics.weight) || 0,
				videos: mappedVideos
			};
		} catch (err) {
			console.error('Error loading patient data:', err);
			error = `${err}`;
			patientData = null;
		} finally {
			isLoading = false;
		}
	}

	function handleEditBiometrics() {
		if (patientId) {
			goto(`/mobile/biometric-information?patientId=${patientId}&mode=edit&source=patient-detail`);
		}
	}

	function handleVideoClick(video: Video) {
		try {
			if (!video.videoUrl || video.videoUrl.trim() === '') {
				error = 'Video URL not available';
				return;
			}
			const videoUrl = `${API_CONFIG.BASE_URL}${video.videoUrl}`;
			try { new URL(videoUrl); } catch { error = 'Invalid video URL format'; return; }
			window.open(videoUrl, '_blank');
		} catch (err) {
			error = `Error opening video: ${err instanceof Error ? err.message : 'Unknown error'}`;
		}
	}

	function formatDate(dateString: string): string {
		try {
			const date = new Date(dateString);
			return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
		} catch {
			return dateString;
		}
	}

	let filteredVideos = $derived(() => {
		if (!patientData) return [];
		return patientData.videos.filter((video) => {
			const matchesSearch =
				searchQuery === '' ||
				video.exercise.toLowerCase().includes(searchQuery.toLowerCase()) ||
				video.filename.toLowerCase().includes(searchQuery.toLowerCase());
			const matchesExercise = selectedExercise === 'all' || video.exercise === selectedExercise;
			return matchesSearch && matchesExercise;
		});
	});
</script>

<svelte:head>
	<title>{patientName || 'Patient Detail'} — Gait Analysis</title>
</svelte:head>

<div class="page">
	<a href="/mobile/patients" class="back-link">
		<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
			<path d="M10 12L6 8l4-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
		</svg>
		Back to Patients
	</a>

	{#if isLoading}
		<div class="state-box">
			<div class="spinner"></div>
			<p>Loading patient data…</p>
		</div>
	{/if}

	{#if error && !isLoading}
		<div class="state-box">
			<svg width="48" height="48" viewBox="0 0 48 48" fill="none">
				<circle cx="24" cy="24" r="24" fill="#FFEBEE"/>
				<path d="M24 16v8M24 28v2" stroke="#e53935" stroke-width="2" stroke-linecap="round"/>
			</svg>
			<p class="error-text">{error}</p>
			<button class="btn-retry" onclick={loadPatientData}>Retry</button>
		</div>
	{/if}

	{#if !isLoading && !error && patientData}
		<!-- Page title row -->
		<div class="page-title-row">
			<div class="patient-avatar-large">
				<svg width="48" height="48" viewBox="0 0 48 48" fill="none">
					<circle cx="24" cy="24" r="24" fill="#E3F2FD"/>
					<path d="M24 14c-3.3 0-6 2.7-6 6s2.7 6 6 6 6-2.7 6-6-2.7-6-6-6zM24 27c-4.95 0-9 2.025-9 4.5V33h18v-1.5c0-2.475-4.05-4.5-9-4.5z" fill="#64B5F6"/>
				</svg>
			</div>
			<div>
				<h1 class="patient-name-title">{patientData.name}</h1>
				<p class="videos-count-sub">{patientData.videos.length} video{patientData.videos.length !== 1 ? 's' : ''} recorded</p>
			</div>
			<button class="btn-edit" onclick={handleEditBiometrics}>
				<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
					<path d="M11.5 2a1.5 1.5 0 0 1 2.12 2.12L5.5 12.25l-2.75.5.5-2.75L11.5 2z" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
				</svg>
				Edit Info
			</button>
		</div>

		<!-- Info + Videos layout -->
		<div class="detail-layout">
			<!-- Left: patient info card -->
			<div class="info-col">
				<div class="info-card">
					<h2 class="card-heading">Biometric Information</h2>
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
					<div class="total-badge">
						<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
							<rect x="1.5" y="2" width="13" height="10" rx="2" stroke="currentColor" stroke-width="1.3"/>
							<path d="M5 7l3 2 3-2" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"/>
						</svg>
						Total Videos: <strong>{patientData.videos.length}</strong>
					</div>
				</div>
			</div>

			<!-- Right: videos -->
			<div class="videos-col">
				<div class="videos-controls">
					<div class="search-box">
						<svg width="16" height="16" viewBox="0 0 16 16" fill="none" class="search-icon">
							<path d="M7 13A6 6 0 1 0 7 1a6 6 0 0 0 0 12zM15 15l-3.3-3.3" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
						</svg>
						<input
							type="text"
							bind:value={searchQuery}
							placeholder="Search videos…"
							class="search-input"
						/>
					</div>
					<select bind:value={selectedExercise} class="filter-select">
						{#each exerciseTypes as type}
							<option value={type.value}>{type.label}</option>
						{/each}
					</select>
				</div>

				{#if filteredVideos().length === 0}
					<div class="videos-empty">
						<svg width="48" height="48" viewBox="0 0 48 48" fill="none">
							<circle cx="24" cy="24" r="24" fill="#E3F2FD"/>
							<path d="M18 16l12 8-12 8V16z" fill="#90caf9"/>
						</svg>
						<p>{searchQuery || selectedExercise !== 'all' ? 'No videos match your filters' : 'No videos for this patient yet'}</p>
					</div>
				{:else}
					<div class="results-count">{filteredVideos().length} video{filteredVideos().length !== 1 ? 's' : ''}</div>
					<div class="video-grid">
						{#each filteredVideos() as video}
							<button class="video-card" onclick={() => handleVideoClick(video)}>
								<div class="video-thumbnail">
									{#if video.thumbnail}
										<img src={video.thumbnail} alt={video.filename} />
									{:else}
										<div class="thumbnail-placeholder">
											<svg width="40" height="40" viewBox="0 0 40 40" fill="none">
												<circle cx="20" cy="20" r="20" fill="white" opacity="0.25"/>
												<path d="M15 12l12 8-12 8V12z" fill="white"/>
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
			</div>
		</div>
	{/if}
</div>

<style>
	.page {
		padding: 32px 48px;
		max-width: 1200px;
	}

	.back-link {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 14px;
		font-weight: 500;
		color: #555;
		text-decoration: none;
		margin-bottom: 24px;
		transition: color 0.15s;
	}

	.back-link:hover {
		color: #1565c0;
	}

	/* Loading / Error states */
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

	/* Page title row */
	.page-title-row {
		display: flex;
		align-items: center;
		gap: 14px;
		margin-bottom: 28px;
	}

	.patient-avatar-large {
		flex-shrink: 0;
	}

	.patient-name-title {
		margin: 0 0 3px;
		font-size: 26px;
		font-weight: 700;
		color: #1a1a1a;
	}

	.videos-count-sub {
		margin: 0;
		font-size: 13px;
		color: #777;
	}

	.btn-edit {
		margin-left: auto;
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 9px 16px;
		background: #90caf9;
		color: #1a1a1a;
		border: none;
		border-radius: 8px;
		font-size: 13px;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.18s;
		flex-shrink: 0;
	}

	.btn-edit:hover {
		background: #64b5f6;
	}

	/* Detail layout: info left, videos right */
	.detail-layout {
		display: grid;
		grid-template-columns: 260px 1fr;
		gap: 24px;
		align-items: start;
	}

	/* Info card */
	.info-col {
		position: sticky;
		top: 24px;
	}

	.info-card {
		background: #ffffff;
		border: 1px solid #e8eaed;
		border-radius: 14px;
		padding: 22px;
	}

	.card-heading {
		font-size: 14px;
		font-weight: 600;
		color: #1a1a1a;
		margin: 0 0 16px;
		text-transform: uppercase;
		letter-spacing: 0.4px;
	}

	.info-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 16px;
		margin-bottom: 18px;
	}

	.info-item {
		display: flex;
		flex-direction: column;
		gap: 3px;
	}

	.info-label {
		font-size: 11px;
		color: #888;
		text-transform: uppercase;
		letter-spacing: 0.5px;
	}

	.info-value {
		font-size: 15px;
		color: #1a1a1a;
		font-weight: 600;
	}

	.total-badge {
		display: flex;
		align-items: center;
		gap: 7px;
		padding: 10px 14px;
		background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
		border-radius: 8px;
		font-size: 13px;
		color: #1565c0;
	}

	.total-badge strong {
		font-weight: 700;
	}

	/* Videos column */
	.videos-col {
		min-width: 0;
	}

	.videos-controls {
		display: flex;
		gap: 10px;
		margin-bottom: 16px;
		flex-wrap: wrap;
	}

	.search-box {
		position: relative;
		display: flex;
		align-items: center;
		flex: 1;
		min-width: 160px;
	}

	.search-icon {
		position: absolute;
		left: 12px;
		color: #999;
		pointer-events: none;
	}

	.search-input {
		width: 100%;
		padding: 10px 12px 10px 38px;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		font-size: 13px;
		color: #333;
		background: #ffffff;
		outline: none;
		transition: border-color 0.18s, box-shadow 0.18s;
	}

	.search-input:focus {
		border-color: #90caf9;
		box-shadow: 0 0 0 3px rgba(144, 202, 249, 0.2);
	}

	.search-input::placeholder {
		color: #aaa;
	}

	.filter-select {
		padding: 10px 12px;
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		font-size: 13px;
		color: #333;
		background: #ffffff;
		cursor: pointer;
		outline: none;
		transition: border-color 0.18s;
	}

	.filter-select:focus {
		border-color: #90caf9;
	}

	.videos-empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 12px;
		padding: 48px 20px;
		text-align: center;
		color: #888;
		font-size: 14px;
		background: #ffffff;
		border: 1px solid #e8eaed;
		border-radius: 14px;
	}

	.results-count {
		font-size: 13px;
		color: #888;
		margin-bottom: 14px;
	}

	/* Video grid */
	.video-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
		gap: 14px;
	}

	.video-card {
		background: #ffffff;
		border: 1px solid #e8eaed;
		border-radius: 12px;
		overflow: hidden;
		cursor: pointer;
		transition: box-shadow 0.18s;
		padding: 0;
		text-align: left;
		width: 100%;
	}

	.video-card:hover {
		box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
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
		bottom: 6px;
		right: 6px;
		background: rgba(0, 0, 0, 0.65);
		color: white;
		padding: 2px 6px;
		border-radius: 4px;
		font-size: 11px;
		font-weight: 600;
	}

	.video-info {
		padding: 10px 12px 12px;
	}

	.exercise-badge {
		display: inline-block;
		font-size: 11px;
		font-weight: 600;
		color: #1565c0;
		background: #e3f2fd;
		padding: 3px 7px;
		border-radius: 4px;
		margin-bottom: 6px;
	}

	.video-date {
		margin: 0;
		font-size: 11px;
		color: #aaa;
	}

	/* Responsive */
	@media (max-width: 900px) {
		.detail-layout {
			grid-template-columns: 1fr;
		}

		.info-col {
			position: static;
		}
	}

	@media (max-width: 768px) {
		.page {
			padding: 20px 16px 32px;
		}

		.patient-name-title {
			font-size: 20px;
		}

		.page-title-row {
			flex-wrap: wrap;
		}

		.btn-edit {
			margin-left: 0;
		}

		.video-grid {
			grid-template-columns: repeat(2, 1fr);
		}
	}
</style>
