<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { API_CONFIG } from '$lib/config';
	import { apiFetch } from '$lib/api';

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
			const response = await apiFetch(API_CONFIG.PATIENTS_LIST_ENDPOINT);
			if (!response.ok) throw new Error('Failed to load patients');
			const data = await response.json();

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

	function formatDate(dateString: string): string {
		try {
			const date = new Date(dateString);
			const today = new Date();
			const yesterday = new Date(today);
			yesterday.setDate(yesterday.getDate() - 1);

			if (date.toDateString() === today.toDateString()) return 'Today';
			if (date.toDateString() === yesterday.toDateString()) return 'Yesterday';

			return date.toLocaleDateString('en-US', {
				month: 'short',
				day: 'numeric',
				year: 'numeric'
			});
		} catch {
			return dateString;
		}
	}

	let filteredPatients = $derived(() => {
		if (searchQuery === '') return patients;
		return patients.filter((patient) =>
			patient.name.toLowerCase().includes(searchQuery.toLowerCase())
		);
	});
</script>

<svelte:head>
	<title>Patients — Gait Analysis</title>
</svelte:head>

<div class="page">
	<div class="page-header">
		<div class="header-text">
			<h1>Patients</h1>
			<p class="header-subtitle">Manage and view all patient records</p>
		</div>
		<a href="/mobile/create-patient" class="btn-add">
			<svg width="18" height="18" viewBox="0 0 18 18" fill="none">
				<path d="M9 3v12M3 9h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
			</svg>
			Add Patient
		</a>
	</div>

	<!-- Search Bar -->
	<div class="search-box">
		<svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="search-icon">
			<path d="M8 15A7 7 0 1 0 8 1a7 7 0 0 0 0 14zM17 17l-3.8-3.8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
		</svg>
		<input
			type="text"
			bind:value={searchQuery}
			placeholder="Search patients by name…"
			class="search-input"
		/>
	</div>

	<!-- Loading State -->
	{#if isLoading}
		<div class="state-box">
			<div class="spinner"></div>
			<p>Loading patients…</p>
		</div>
	{/if}

	<!-- Error State -->
	{#if error && !isLoading}
		<div class="state-box">
			<div class="error-icon">
				<svg width="40" height="40" viewBox="0 0 40 40" fill="none">
					<circle cx="20" cy="20" r="20" fill="#FFEBEE"/>
					<path d="M20 13v7M20 24v2" stroke="#e53935" stroke-width="2" stroke-linecap="round"/>
				</svg>
			</div>
			<p class="error-text">{error}</p>
			<button class="btn-retry" onclick={loadPatients}>Retry</button>
		</div>
	{/if}

	<!-- Patient List -->
	{#if !isLoading && !error}
		{#if filteredPatients().length === 0}
			<div class="state-box">
				<svg width="56" height="56" viewBox="0 0 56 56" fill="none">
					<circle cx="28" cy="28" r="28" fill="#E3F2FD"/>
					<path d="M28 18c-3.9 0-7 3.1-7 7s3.1 7 7 7 7-3.1 7-7-3.1-7-7-7zM28 33c-5.8 0-10.5 2.4-10.5 5.25V40h21v-1.75C38.5 35.4 33.8 33 28 33z" fill="#64B5F6"/>
				</svg>
				<h3>No Patients Found</h3>
				<p>{searchQuery ? 'Try a different search term' : 'No patients in the system yet'}</p>
				{#if !searchQuery}
					<a href="/mobile/create-patient" class="btn-add" style="margin-top: 8px; text-decoration: none;">
						Add First Patient
					</a>
				{/if}
			</div>
		{:else}
			<div class="results-count">{filteredPatients().length} patient{filteredPatients().length !== 1 ? 's' : ''}</div>
			<div class="patient-list">
				{#each filteredPatients() as patient}
					<button class="patient-card" onclick={() => handlePatientClick(patient)}>
						<div class="patient-avatar">
							<svg width="36" height="36" viewBox="0 0 36 36" fill="none">
								<circle cx="18" cy="18" r="18" fill="#E3F2FD"/>
								<path d="M18 11c-2.5 0-4.5 2-4.5 4.5S15.5 20 18 20s4.5-2 4.5-4.5S20.5 11 18 11zM18 22c-3.7 0-6.75 1.5-6.75 3.375V27h13.5v-1.625C24.75 23.5 21.7 22 18 22z" fill="#64B5F6"/>
							</svg>
						</div>
						<div class="patient-info">
							<h3 class="patient-name">{patient.name}</h3>
							<div class="patient-meta">
								<span class="meta-item">
									<svg width="13" height="13" viewBox="0 0 13 13" fill="none">
										<circle cx="6.5" cy="6.5" r="5.5" stroke="currentColor" stroke-width="1.3"/>
										<path d="M6.5 4v2.5l1.5 1.5" stroke="currentColor" stroke-width="1.3" stroke-linecap="round"/>
									</svg>
									{formatDate(patient.lastVisit)}
								</span>
								<span class="meta-sep">·</span>
								<span class="meta-item">
									<svg width="13" height="13" viewBox="0 0 13 13" fill="none">
										<rect x="1.5" y="2.5" width="10" height="8" rx="1.5" stroke="currentColor" stroke-width="1.3"/>
										<path d="M5 6.5L7.5 5v3L5 6.5z" fill="currentColor"/>
									</svg>
									{patient.videoCount} {patient.videoCount === 1 ? 'video' : 'videos'}
								</span>
							</div>
						</div>
						<svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="chevron">
							<path d="M6.5 4.5l5 4.5-5 4.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
						</svg>
					</button>
				{/each}
			</div>
		{/if}
	{/if}
</div>

<style>
	.page {
		padding: 40px 48px;
		max-width: 1000px;
	}

	/* Header */
	.page-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		gap: 16px;
		margin-bottom: 28px;
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

	.btn-add {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		padding: 10px 18px;
		background: #90caf9;
		color: #1a1a1a;
		border: none;
		border-radius: 8px;
		font-size: 14px;
		font-weight: 600;
		cursor: pointer;
		text-decoration: none;
		transition: background 0.18s;
		flex-shrink: 0;
		white-space: nowrap;
	}

	.btn-add:hover {
		background: #64b5f6;
	}

	/* Search */
	.search-box {
		position: relative;
		display: flex;
		align-items: center;
		margin-bottom: 20px;
		max-width: 480px;
	}

	.search-icon {
		position: absolute;
		left: 13px;
		color: #999;
		pointer-events: none;
	}

	.search-input {
		width: 100%;
		padding: 11px 14px 11px 42px;
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

	/* Results count */
	.results-count {
		font-size: 13px;
		color: #888;
		margin-bottom: 14px;
	}

	/* States */
	.state-box {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 64px 20px;
		text-align: center;
		color: #555;
	}

	.state-box p {
		margin: 10px 0 0;
		font-size: 14px;
		color: #777;
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
		to {
			transform: rotate(360deg);
		}
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

	/* Patient list */
	.patient-list {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.patient-card {
		width: 100%;
		background: #ffffff;
		border: 1px solid #e8eaed;
		border-radius: 12px;
		padding: 16px 18px;
		display: flex;
		align-items: center;
		gap: 14px;
		cursor: pointer;
		transition: box-shadow 0.18s, border-color 0.18s;
		text-align: left;
	}

	.patient-card:hover {
		box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
		border-color: #90caf9;
	}

	.patient-avatar {
		flex-shrink: 0;
	}

	.patient-info {
		flex: 1;
		min-width: 0;
	}

	.patient-name {
		font-size: 15px;
		font-weight: 600;
		color: #1a1a1a;
		margin: 0 0 6px;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}

	.patient-meta {
		display: flex;
		align-items: center;
		gap: 6px;
		flex-wrap: wrap;
	}

	.meta-item {
		font-size: 12px;
		color: #777;
		display: inline-flex;
		align-items: center;
		gap: 4px;
	}

	.meta-sep {
		font-size: 12px;
		color: #ccc;
	}

	.chevron {
		flex-shrink: 0;
		color: #bbb;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.page {
			padding: 20px 16px 32px;
		}

		.header-text h1 {
			font-size: 22px;
		}

		.btn-add {
			padding: 9px 14px;
			font-size: 13px;
		}

		.search-box {
			max-width: 100%;
		}
	}
</style>
