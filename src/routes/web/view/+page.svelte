<script lang="ts">
	import { onMount } from "svelte";
	import { API_CONFIG } from "$lib/config";
	import OpenSimViewer from "$lib/OpenSimViewer.svelte";

	let srcOriginal = $state<string | null>(null);
	let srcModel = $state<string | null>(null);
	let currentTime = $state<number>(0);
	let loading = $state<boolean>(true);
	let error = $state<string | null>(null);
	let isDownloading = $state<boolean>(false);
	let downloadProgress = $state<number>(0);
	let downloadSuccess = $state<boolean>(false);
	let downloadError = $state<string | null>(null);

	// OpenSim data
	let opensimModel = $state<any>(null);
	let opensimAnimation = $state<any>(null);
	let analysisResults = $state<any>(null);
	let activeTab = $state<'videos' | 'opensim'>('opensim'); // Start with OpenSim tab for testing
	let useWhamResult = $state<boolean>(true); // Enable WHAM result mode

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

	async function loadOpenSimData() {


		try {
			const animationResponse = await fetch(API_CONFIG.OPENSIM_ANIMATION_ENDPOINT);
			if (animationResponse.ok) {
				opensimAnimation = await animationResponse.json();
				}
			} catch (animationError) {
				console.warn('OpenSim animation endpoint unavailable:', animationError);
			}
			try {
				const modelResponse = await fetch(API_CONFIG.OPENSIM_MODEL_ENDPOINT);
				if (modelResponse.ok) {
					opensimModel = await modelResponse.json();
				}
			} catch (modelError) {
				console.warn('OpenSim model endpoint unavailable:', modelError);
			}
	}

	onMount(async () => {
		// await loadVideos();
		await loadOpenSimData();
	});

</script>

<svelte:head>
	<title>View Videos</title>
</svelte:head>

<div class="view-page">
	<h1>Motion Capture Analysis</h1>

	<!-- Tab Navigation -->
	<div class="tab-navigation">
		<button
			class="tab-button {activeTab === 'videos' ? 'active' : ''}"
			onclick={() => activeTab = 'videos'}
		>
			Video Comparison
		</button>
		<button
			class="tab-button {activeTab === 'opensim' ? 'active' : ''}"
			onclick={() => activeTab = 'opensim'}
		>
			OpenSim Model
		</button>
	</div>

	{#if activeTab === 'videos'}
		{#if loading}
			<p>Loading videos from the server...</p>
		{:else if error}
			<p class="error">{error}</p>
		{:else}
			<div class="video-grid">
				{#if srcOriginal}
					<div class="video-card">
						<h2>Original Video</h2>
						<!-- svelte-ignore a11y_media_has_caption -->
						<video src={srcOriginal} bind:currentTime controls preload="metadata"></video>
						<p>Time: {currentTime.toFixed(1)}s</p>
					</div>
				{/if}

				{#if srcModel}
					<div class="video-card">
						<h2>Processed Video</h2>
						<!-- svelte-ignore a11y_media_has_caption -->
						<video src={srcModel} bind:currentTime controls preload="metadata"></video>
						<p>Time: {currentTime.toFixed(1)}s</p>
					</div>
				{/if}
			</div>

			{#if !srcOriginal && !srcModel}
				<p>No videos are available right now.</p>
			{/if}
		{/if}
	{:else if activeTab === 'opensim'}
		<div class="opensim-section">
			<div class="opensim-content">
				<div class="viewer-container">
					<h2>3D Musculoskeletal Model</h2>
					<OpenSimViewer animationData={opensimAnimation} analysisResults={analysisResults}/>
				</div>

				{#if analysisResults}
					<div class="analysis-panel">
						<h3>Analysis Results</h3>
						<div class="analysis-grid">
							{#if analysisResults.jointForces}
								<div class="analysis-card">
									<h4>Joint Forces</h4>
									<div class="force-data">
										{#each Object.entries(analysisResults.jointForces) as [joint, force]}
											<div class="force-item">
												<span class="joint-name">{joint}:</span>
												<span class="force-value">{typeof force === 'number' ? force.toFixed(2) : force} N</span>
											</div>
										{/each}
									</div>
								</div>
							{/if}

							{#if analysisResults.muscleActivations}
								<div class="analysis-card">
									<h4>Muscle Activations</h4>
									<div class="activation-data">
										{#each Object.entries(analysisResults.muscleActivations) as [muscle, activation]}
											<div class="activation-item">
												<span class="muscle-name">{muscle}:</span>
												<div class="activation-bar">
													<div
														class="activation-fill"
														style="width: {Math.min(100, (activation as number) * 100)}%"
													></div>
												</div>
												<span class="activation-value">{typeof activation === 'number' ? (activation * 100).toFixed(1) : activation}%</span>
											</div>
										{/each}
									</div>
								</div>
							{/if}
						</div>
					</div>
				{:else}
					<div class="no-data">
						<p>No OpenSim analysis data available. Please process a video first.</p>
					</div>
				{/if}
			</div>
		</div>
	{/if}
</div>

<style>
	.view-page {
		padding: 1rem;
	}

	.tab-navigation {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1.5rem;
		border-bottom: 1px solid #ddd;
	}

	.tab-button {
		padding: 0.75rem 1.5rem;
		border: none;
		background: none;
		border-bottom: 2px solid transparent;
		cursor: pointer;
		font-size: 1rem;
		font-weight: 500;
		color: #666;
		transition: all 0.2s ease;
	}

	.tab-button:hover {
		color: #333;
		background: #f5f5f5;
	}

	.tab-button.active {
		color: #2563eb;
		border-bottom-color: #2563eb;
		background: #eff6ff;
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

	.opensim-section {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.opensim-content {
		display: grid;
		grid-template-columns: 2fr 1fr;
		gap: 1.5rem;
		align-items: start;
	}

	.viewer-container {
		border: 1px solid #ddd;
		border-radius: 0.75rem;
		padding: 1rem;
		background: #fff;
	}

	.viewer-container h2 {
		margin-top: 0;
		margin-bottom: 1rem;
		font-size: 1.2rem;
	}

	.test-controls {
		margin-bottom: 1rem;
		padding: 0.5rem;
		background: #f8f9fa;
		border-radius: 0.5rem;
		border: 1px solid #e9ecef;
	}

	.test-controls label {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.9rem;
		font-weight: 500;
		color: #495057;
		cursor: pointer;
	}

	.test-controls input[type="checkbox"] {
		width: 16px;
		height: 16px;
		cursor: pointer;
	}

	.analysis-panel {
		border: 1px solid #ddd;
		border-radius: 0.75rem;
		padding: 1rem;
		background: #fff;
		max-height: 600px;
		overflow-y: auto;
	}

	.analysis-panel h3 {
		margin-top: 0;
		margin-bottom: 1rem;
		font-size: 1.1rem;
	}

	.analysis-grid {
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.analysis-card {
		border: 1px solid #eee;
		border-radius: 0.5rem;
		padding: 1rem;
		background: #fafafa;
	}

	.analysis-card h4 {
		margin: 0 0 0.75rem 0;
		font-size: 1rem;
		color: #333;
	}

	.force-data, .activation-data {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.force-item, .activation-item {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0.25rem 0;
		font-size: 0.9rem;
	}

	.joint-name, .muscle-name {
		font-weight: 500;
		color: #555;
		min-width: 120px;
	}

	.force-value, .activation-value {
		font-weight: 600;
		color: #2563eb;
	}

	.activation-bar {
		flex: 1;
		height: 8px;
		background: #e5e7eb;
		border-radius: 4px;
		margin: 0 0.5rem;
		overflow: hidden;
	}

	.activation-fill {
		height: 100%;
		background: linear-gradient(90deg, #10b981, #f59e0b, #ef4444);
		transition: width 0.3s ease;
	}

	.no-data {
		grid-column: 1 / -1;
		text-align: center;
		padding: 2rem;
		color: #666;
		font-style: italic;
	}

	@media (max-width: 1200px) {
		.opensim-content {
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 900px) {
		.video-grid {
			grid-template-columns: 1fr;
		}

		.tab-navigation {
			flex-direction: column;
		}

		.tab-button {
			text-align: left;
			border-bottom: none;
			border-left: 2px solid transparent;
		}

		.tab-button.active {
			border-bottom: none;
			border-left-color: #2563eb;
		}
	}
</style>