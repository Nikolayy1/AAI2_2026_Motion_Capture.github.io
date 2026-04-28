<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { PATIENTS_LIST_ENDPOINT } from '$lib/config';

	interface Patient {
		id: number;
		name: string;
		lastVisit: string;
		videoCount: number;
	}

	let patients = $state<Patient[]>([]);
	let isLoading = $state(true);
	let error = $state('');
	let searchQuery = $state('');

	onMount(async () => {
		await loadPatients();
	});

	async function loadPatients() {
		isLoading = true;
		error = '';

		try {
			const response = await fetch(PATIENTS_LIST_ENDPOINT);
			if (!response.ok) throw new Error('Failed to load patients');
			const data = await response.json();

			// Map backend response to frontend Patient interface
			patients = data.map((p: any) => ({
				id: p.id,
				name: p.name || '',
				lastVisit: p.lastVisit || '',
				videoCount: p.videoCount || 0
			}));
		} catch (err) {
			console.error('Error loading patients:', err);
			error = `${err}`;
			patients = [];
		} finally {
			isLoading = false;
		}
	}

	function handlePatientClick(patient: Patient) {
		goto(`/mobile/patient-detail?id=${patient.id}&name=${encodeURIComponent(patient.name)}`);
	}

	function handleBack() {
		goto('/mobile/dashboard');
	}

	function formatDate(dateString: string): string {
		try {
			const date = new Date(dateString);
			const today = new Date();
			const yesterday = new Date(today);
			yesterday.setDate(yesterday.getDate() - 1);

			// Check if today
			if (date.toDateString() === today.toDateString()) {
				return 'Today';
			}
			// Check if yesterday
			if (date.toDateString() === yesterday.toDateString()) {
				return 'Yesterday';
			}
			// Otherwise format as date
			return date.toLocaleDateString('en-US', {
				month: 'short',
				day: 'numeric',
				year: 'numeric'
			});
		} catch {
			return dateString;
		}
	}

	// Filter patients based on search query
	let filteredPatients = $derived(() => {
		if (searchQuery === '') return patients;
		return patients.filter(patient =>
			patient.name.toLowerCase().includes(searchQuery.toLowerCase())
		);
	});
</script>

<div class="container">
	<header>
		<button class="back-button" onclick={handleBack} aria-label="Go back">
			<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
				<path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
			</svg>
		</button>
		<h1>Patients</h1>
	</header>

	<!-- Search Bar -->
	<div class="search-box">
		<svg width="20" height="20" viewBox="0 0 20 20" fill="none" class="search-icon">
			<path d="M9 17A8 8 0 1 0 9 1a8 8 0 0 0 0 16zM18 18l-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
		</svg>
		<input
			type="text"
			bind:value={searchQuery}
			placeholder="Search patients..."
			class="search-input"
		/>
	</div>

	<!-- Loading State -->
	{#if isLoading}
		<div class="loading">
			<div class="spinner"></div>
			<p>Loading patients...</p>
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
			<button class="retry-button" onclick={loadPatients}>Retry</button>
		</div>
	{/if}

	<!-- Patient List -->
	{#if !isLoading && !error}
		{#if filteredPatients().length === 0}
			<div class="empty-state">
				<svg width="64" height="64" viewBox="0 0 64 64" fill="none">
					<circle cx="32" cy="32" r="32" fill="#E3F2FD"/>
					<path d="M32 20c-4.4 0-8 3.6-8 8s3.6 8 8 8 8-3.6 8-8-3.6-8-8-8zM32 38c-6.6 0-12 2.7-12 6v2h24v-2c0-3.3-5.4-6-12-6z" fill="#64B5F6"/>
				</svg>
				<h2>No Patients Found</h2>
				<p>{searchQuery ? 'Try adjusting your search' : 'No patients in the system yet'}</p>
			</div>
		{:else}
			<div class="patient-list">
				{#each filteredPatients() as patient}
					<button class="patient-card" onclick={() => handlePatientClick(patient)}>
						<div class="patient-avatar">
							<svg width="32" height="32" viewBox="0 0 32 32" fill="none">
								<circle cx="16" cy="16" r="16" fill="#E3F2FD"/>
								<path d="M16 10c-2.2 0-4 1.8-4 4s1.8 4 4 4 4-1.8 4-4-1.8-4-4-4zM16 19c-3.3 0-6 1.35-6 3v1h12v-1c0-1.65-2.7-3-6-3z" fill="#64B5F6"/>
							</svg>
						</div>
						<div class="patient-info">
							<h3 class="patient-name">{patient.name}</h3>
							<div class="patient-meta">
								<span class="last-visit">
									<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
										<circle cx="7" cy="7" r="6" stroke="currentColor" stroke-width="1.5"/>
										<path d="M7 4v3l2 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
									</svg>
									Last visit: {formatDate(patient.lastVisit)}
								</span>
								<span class="video-count">
									<svg width="14" height="14" viewBox="0 0 14 14" fill="none">
										<path d="M2 4a1 1 0 0 1 1-1h8a1 1 0 0 1 1 1v6a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V4z" stroke="currentColor" stroke-width="1.5"/>
										<path d="M5.5 7L8 5.5v3L5.5 7z" fill="currentColor"/>
									</svg>
									{patient.videoCount} {patient.videoCount === 1 ? 'video' : 'videos'}
								</span>
							</div>
						</div>
						<svg width="20" height="20" viewBox="0 0 20 20" fill="none" class="chevron">
							<path d="M7.5 5l5 5-5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
						</svg>
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
	}

	/* Search Box */
	.search-box {
		position: relative;
		display: flex;
		align-items: center;
		margin-bottom: 24px;
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
	}

	/* Patient List */
	.patient-list {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}

	.patient-card {
		width: 100%;
		background-color: #ffffff;
		border: none;
		border-radius: 12px;
		padding: 16px;
		display: flex;
		align-items: center;
		gap: 12px;
		cursor: pointer;
		transition: transform 0.2s, box-shadow 0.2s;
		text-align: left;
	}

	.patient-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
	}

	.patient-avatar {
		flex-shrink: 0;
	}

	.patient-info {
		flex: 1;
		min-width: 0;
	}

	.patient-name {
		font-size: 16px;
		font-weight: 600;
		color: #333;
		margin: 0 0 8px 0;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.patient-meta {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.last-visit,
	.video-count {
		font-size: 12px;
		color: #666;
		display: flex;
		align-items: center;
		gap: 4px;
	}

	.last-visit svg,
	.video-count svg {
		flex-shrink: 0;
	}

	.chevron {
		flex-shrink: 0;
		color: #999;
	}
</style>
