<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { apiFetch } from '$lib/api';
	import { API_CONFIG } from '$lib/config';
	import {
		coerceBiometrics,
		getLatestSubmissionBiometrics,
		getPatientBiometrics,
		savePatientBiometrics
	} from '$lib/biometrics';

	let fullName = $state('');
	let gender = $state('');
	let age = $state('');
	let height = $state('');
	let weight = $state('');
	let notes = $state('');
	let genderDropdownOpen = $state(false);
	let patientId: number | null = $state(null);

	let showErrors = $state(false);
	let mode = $state('create');
	let source = $state('upload');
	let showSuccess = $state(false);
	let isCreatingPatient = $state(false);

	const genderOptions = [
		{ value: 'female', label: 'Female' },
		{ value: 'male', label: 'Male' },
		{ value: 'other', label: 'Other' },
		{ value: 'prefer-not-to-say', label: 'Prefer not to say' }
	];

	onMount(() => {
		const urlParams = new URLSearchParams(window.location.search);
		const patientIdParam = urlParams.get('patientId');
		const patientNameParam = urlParams.get('patient') || urlParams.get('patientName');
		const modeParam = urlParams.get('mode');
		source = urlParams.get('source') || 'create-patient';

		if (modeParam === 'edit' || source === 'patient-detail') {
			mode = 'edit';
			if (patientIdParam) {
				patientId = parseInt(patientIdParam);
				loadPatientData(patientId);
			}
		} else {
			mode = 'create';
		}

		if (mode === 'create' && patientNameParam) {
			fullName = patientNameParam;
		}

		if (patientIdParam && !patientId) {
			patientId = parseInt(patientIdParam);
		}
	});

	async function loadPatientData(id: number) {
		try {
			const endpoint = API_CONFIG.PATIENT_VIDEOS_ENDPOINT.replace(':id', id.toString());
			const response = await apiFetch(endpoint);
			if (response.ok) {
				const data = await response.json();
				fullName = data.patient.name || '';
				const storedBiometrics = getPatientBiometrics(id);
				const fallbackBiometrics = getLatestSubmissionBiometrics(data.videos);
				const biometrics = storedBiometrics || fallbackBiometrics || coerceBiometrics();

				gender = biometrics.gender;
				age = biometrics.age;
				height = biometrics.height;
				weight = biometrics.weight;
				notes = biometrics.notes;
			}
		} catch (error) {
			console.error('Error loading patient data:', error);
		}
	}

	function selectGender(value: string) {
		gender = value;
		genderDropdownOpen = false;
	}

	async function handleSaveAndContinue() {
		showErrors = true;
		if (!fullName || !gender || !age || !height || !weight) return;

		const biometricData = { patientId, fullName, gender, age, height, weight, notes };

		if (mode === 'edit') {
			await updatePatient(biometricData);
		} else if (source === 'create-patient') {
			await createPatient(biometricData);
		}
	}

	async function createPatient(biometricData: any) {
		isCreatingPatient = true;
		try {
			const formData = new FormData();
			formData.append('name', biometricData.fullName);

			const response = await apiFetch(API_CONFIG.CREATE_PATIENT_ENDPOINT, {
				method: 'POST',
				body: formData
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({}));
				throw new Error(errorData.error || 'Failed to create patient');
			}

			const result = await response.json();
			savePatientBiometrics(result.patient_id, {
				age: biometricData.age,
				gender: biometricData.gender,
				height: biometricData.height,
				weight: biometricData.weight,
				notes: biometricData.notes || ''
			});
			console.log('Patient created:', result);

			showSuccess = true;
			sessionStorage.removeItem('newPatientName');

			setTimeout(() => {
				goto(`/mobile/patient-detail?id=${result.patient_id}&name=${encodeURIComponent(biometricData.fullName)}`);
			}, 2000);
		} catch (error) {
			console.error('Error creating patient:', error);
			alert(`Failed to create patient: ${error}`);
			isCreatingPatient = false;
		}
	}

	async function updatePatient(biometricData: any) {
		isCreatingPatient = true;
		try {
			if (!patientId) throw new Error('Patient ID is required');

			savePatientBiometrics(patientId, {
				age: biometricData.age,
				gender: biometricData.gender,
				height: biometricData.height,
				weight: biometricData.weight,
				notes: biometricData.notes || ''
			});

			showSuccess = true;
			setTimeout(() => {
				goto(`/mobile/patient-detail?id=${patientId}`);
			}, 1000);
		} catch (error) {
			console.error('Error updating patient:', error);
			alert(`Failed to update patient: ${error}`);
			isCreatingPatient = false;
		}
	}

	function handleBack() {
		if (source === 'patient-detail' && patientId) {
			goto(`/mobile/patient-detail?id=${patientId}`);
		} else if (source === 'create-patient') {
			goto('/mobile/create-patient');
		} else {
			goto('/mobile/upload');
		}
	}

	let buttonText = $derived(() => {
		if (isCreatingPatient) return mode === 'edit' ? 'Updating…' : 'Creating Patient…';
		return mode === 'edit' ? 'Save Changes' : 'Create Patient';
	});
</script>

<svelte:head>
	<title>{mode === 'edit' ? 'Edit Patient' : 'Patient Information'} — Gait Analysis</title>
</svelte:head>

<div class="page">
	<button class="back-link" onclick={handleBack}>
		<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
			<path d="M10 12L6 8l4-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
		</svg>
		{source === 'patient-detail' ? 'Back to Patient' : 'Back'}
	</button>

	<div class="page-header">
		<h1>{mode === 'edit' ? 'Edit Patient Information' : 'Patient Information'}</h1>
		<p class="page-subtitle">{mode === 'edit' ? "Update the patient's biometric details" : "Fill in the patient's details to complete their profile"}</p>
	</div>

	<form
		onsubmit={(e) => { e.preventDefault(); handleSaveAndContinue(); }}
		class="form-body"
	>
		<!-- Personal Details -->
		<div class="form-card">
			<h2 class="section-heading">
				<svg width="18" height="18" viewBox="0 0 18 18" fill="none">
					<circle cx="9" cy="6" r="3.5" stroke="currentColor" stroke-width="1.4"/>
					<path d="M2.5 16v-.75a5.25 5.25 0 0 1 5.25-5.25h2.5a5.25 5.25 0 0 1 5.25 5.25V16" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>
				</svg>
				Personal Details
			</h2>

			<div class="field-grid">
				<!-- Full Name — spans 2 cols -->
				<div class="field full-width">
					<label for="fullName">Full Name <span class="req">*</span></label>
					<input
						id="fullName"
						type="text"
						bind:value={fullName}
						placeholder="Enter patient's full name"
						class:invalid={showErrors && !fullName}
					/>
					{#if showErrors && !fullName}
						<span class="error-hint">Required field</span>
					{/if}
				</div>

				<!-- Gender -->
				<div class="field">
					<label>Gender <span class="req">*</span></label>
					<div class="dropdown" class:open={genderDropdownOpen}>
						<button
							type="button"
							class="dropdown-btn"
							class:placeholder={!gender}
							class:invalid={showErrors && !gender}
							onclick={() => (genderDropdownOpen = !genderDropdownOpen)}
						>
							<span>{gender ? genderOptions.find((o) => o.value === gender)?.label : 'Select gender'}</span>
							<svg width="18" height="18" viewBox="0 0 18 18" fill="none" class="chevron">
								<path d="M4.5 6.75l4.5 4.5 4.5-4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
							</svg>
						</button>
						{#if genderDropdownOpen}
							<div class="dropdown-menu">
								{#each genderOptions as option}
									<button
										type="button"
										class="dropdown-item"
										class:selected={gender === option.value}
										onclick={() => selectGender(option.value)}
									>
										{option.label}
										{#if gender === option.value}
											<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
												<path d="M13.5 4L6 11.5 2.5 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
											</svg>
										{/if}
									</button>
								{/each}
							</div>
						{/if}
					</div>
					{#if showErrors && !gender}
						<span class="error-hint">Required field</span>
					{/if}
				</div>

				<!-- Age -->
				<div class="field">
					<label for="age">Age <span class="req">*</span></label>
					<input
						id="age"
						type="number"
						bind:value={age}
						placeholder="Years"
						min="0"
						max="150"
						class:invalid={showErrors && !age}
					/>
					{#if showErrors && !age}
						<span class="error-hint">Required field</span>
					{/if}
				</div>
			</div>
		</div>

		<!-- Body Metrics -->
		<div class="form-card">
			<h2 class="section-heading">
				<svg width="18" height="18" viewBox="0 0 18 18" fill="none">
					<path d="M9 2v14M5 6l4-4 4 4M5 12l4 4 4-4" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
				</svg>
				Body Metrics
			</h2>

			<div class="field-grid">
				<!-- Height -->
				<div class="field">
					<label for="height">Height <span class="req">*</span></label>
					<div class="input-with-unit">
						<input
							id="height"
							type="number"
							bind:value={height}
							placeholder="0"
							min="0"
							step="0.1"
							class:invalid={showErrors && !height}
						/>
						<span class="unit">cm</span>
					</div>
					{#if showErrors && !height}
						<span class="error-hint">Required field</span>
					{/if}
				</div>

				<!-- Weight -->
				<div class="field">
					<label for="weight">Weight <span class="req">*</span></label>
					<div class="input-with-unit">
						<input
							id="weight"
							type="number"
							bind:value={weight}
							placeholder="0"
							min="0"
							step="0.1"
							class:invalid={showErrors && !weight}
						/>
						<span class="unit">kg</span>
					</div>
					{#if showErrors && !weight}
						<span class="error-hint">Required field</span>
					{/if}
				</div>

				<!-- Notes — spans 2 cols -->
				<div class="field full-width">
					<label for="notes">Notes <span class="optional">(optional)</span></label>
					<textarea
						id="notes"
						bind:value={notes}
						placeholder="Any additional notes about the patient…"
						rows="3"
					></textarea>
				</div>
			</div>
		</div>

		<!-- Actions -->
		<div class="form-actions">
			<button type="submit" class="btn-primary" disabled={isCreatingPatient}>
				{buttonText()}
			</button>
			<button type="button" class="btn-secondary" onclick={handleBack} disabled={isCreatingPatient}>
				Cancel
			</button>
		</div>
	</form>
</div>

<!-- Success Overlay -->
{#if showSuccess}
	<div class="success-overlay">
		<div class="success-modal">
			<div class="success-icon">
				<svg width="64" height="64" viewBox="0 0 64 64" fill="none">
					<circle cx="32" cy="32" r="32" fill="#4CAF50"/>
					<path d="M20 32l8 8 16-16" stroke="white" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
				</svg>
			</div>
			<h2 class="success-title">{mode === 'edit' ? 'Patient Updated!' : 'Patient Created!'}</h2>
			<p class="success-message">
				{mode === 'edit'
					? `${fullName}'s information has been successfully updated.`
					: `${fullName} has been successfully added to the system.`}
			</p>
		</div>
	</div>
{/if}

<style>
	.page {
		padding: 32px 48px;
		max-width: 860px;
	}

	/* Back link */
	.back-link {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 14px;
		font-weight: 500;
		color: #555;
		background: none;
		border: none;
		padding: 0;
		cursor: pointer;
		margin-bottom: 24px;
		transition: color 0.15s;
	}

	.back-link:hover {
		color: #1565c0;
	}

	/* Page header */
	.page-header {
		margin-bottom: 28px;
	}

	.page-header h1 {
		margin: 0 0 5px;
		font-size: 26px;
		font-weight: 700;
		color: #1a1a1a;
	}

	.page-subtitle {
		margin: 0;
		font-size: 14px;
		color: #666;
	}

	/* Form layout */
	.form-body {
		display: flex;
		flex-direction: column;
		gap: 20px;
	}

	/* Cards */
	.form-card {
		background: #ffffff;
		border: 1px solid #e8eaed;
		border-radius: 14px;
		padding: 28px 32px;
	}

	.section-heading {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 14px;
		font-weight: 600;
		color: #1a1a1a;
		text-transform: uppercase;
		letter-spacing: 0.5px;
		margin: 0 0 22px;
	}

	/* Two-column field grid */
	.field-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 18px 24px;
	}

	.field.full-width {
		grid-column: 1 / -1;
	}

	/* Individual field */
	.field {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}

	label {
		font-size: 13px;
		font-weight: 600;
		color: #333;
	}

	.req {
		color: #e53935;
	}

	.optional {
		font-weight: 400;
		color: #999;
		font-size: 12px;
	}

	input[type='text'],
	input[type='number'],
	textarea {
		width: 100%;
		padding: 11px 14px;
		border: 1px solid #d8dadd;
		border-radius: 9px;
		font-size: 14px;
		color: #1a1a1a;
		background: #fafafa;
		outline: none;
		transition: border-color 0.18s, box-shadow 0.18s, background 0.18s;
		font-family: inherit;
	}

	input::placeholder,
	textarea::placeholder {
		color: #bbb;
	}

	input:focus,
	textarea:focus {
		border-color: #90caf9;
		background: #ffffff;
		box-shadow: 0 0 0 3px rgba(144, 202, 249, 0.2);
	}

	input.invalid,
	.dropdown-btn.invalid {
		border-color: #e53935;
	}

	.error-hint {
		font-size: 12px;
		color: #e53935;
	}

	/* Input with unit suffix */
	.input-with-unit {
		position: relative;
		display: flex;
		align-items: center;
	}

	.input-with-unit input {
		padding-right: 44px;
	}

	.unit {
		position: absolute;
		right: 14px;
		font-size: 13px;
		color: #888;
		pointer-events: none;
		font-weight: 500;
	}

	/* Textarea */
	textarea {
		resize: vertical;
		min-height: 80px;
	}

	/* Dropdown */
	.dropdown {
		position: relative;
	}

	.dropdown-btn {
		width: 100%;
		padding: 11px 14px;
		border: 1px solid #d8dadd;
		border-radius: 9px;
		font-size: 14px;
		color: #1a1a1a;
		background: #fafafa;
		text-align: left;
		cursor: pointer;
		display: flex;
		justify-content: space-between;
		align-items: center;
		transition: border-color 0.18s, box-shadow 0.18s, background 0.18s;
		outline: none;
	}

	.dropdown-btn.placeholder {
		color: #bbb;
	}

	.dropdown-btn:hover,
	.dropdown-btn:focus {
		border-color: #90caf9;
		background: #ffffff;
	}

	.dropdown-btn:focus {
		box-shadow: 0 0 0 3px rgba(144, 202, 249, 0.2);
	}

	.chevron {
		color: #888;
		flex-shrink: 0;
		transition: transform 0.18s;
	}

	.dropdown.open .chevron {
		transform: rotate(180deg);
	}

	.dropdown-menu {
		position: absolute;
		top: calc(100% + 4px);
		left: 0;
		right: 0;
		background: #ffffff;
		border: 1px solid #e0e0e0;
		border-radius: 9px;
		box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1);
		z-index: 20;
		overflow: hidden;
	}

	.dropdown-item {
		width: 100%;
		padding: 11px 14px;
		border: none;
		background: none;
		text-align: left;
		cursor: pointer;
		font-size: 14px;
		color: #1a1a1a;
		display: flex;
		justify-content: space-between;
		align-items: center;
		transition: background 0.15s;
		font-family: inherit;
	}

	.dropdown-item:hover {
		background: #f5f8fa;
	}

	.dropdown-item.selected {
		color: #1565c0;
		font-weight: 600;
	}

	.dropdown-item.selected svg {
		color: #1565c0;
	}

	/* Actions */
	.form-actions {
		display: flex;
		gap: 12px;
	}

	.btn-primary {
		flex: 1;
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

	.btn-primary:hover:not(:disabled) {
		background: #64b5f6;
	}

	.btn-primary:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.btn-secondary {
		padding: 14px 28px;
		border: 1px solid #e0e0e0;
		border-radius: 10px;
		background: #ffffff;
		color: #555;
		font-size: 15px;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.18s, border-color 0.18s;
		white-space: nowrap;
	}

	.btn-secondary:hover:not(:disabled) {
		background: #f5f5f5;
		border-color: #ccc;
	}

	.btn-secondary:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	/* Success Overlay */
	.success-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.45);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		animation: fadeIn 0.25s ease;
	}

	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}

	.success-modal {
		background: #ffffff;
		border-radius: 18px;
		padding: 44px 40px;
		max-width: 360px;
		width: 90%;
		text-align: center;
		animation: slideUp 0.35s ease;
		box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
	}

	@keyframes slideUp {
		from { transform: translateY(16px); opacity: 0; }
		to { transform: translateY(0); opacity: 1; }
	}

	.success-icon {
		margin-bottom: 20px;
	}

	.success-title {
		font-size: 22px;
		font-weight: 700;
		color: #1a1a1a;
		margin: 0 0 10px;
	}

	.success-message {
		font-size: 14px;
		color: #666;
		margin: 0;
		line-height: 1.55;
	}

	/* Responsive */
	@media (max-width: 768px) {
		.page {
			padding: 20px 16px 40px;
		}

		.page-header h1 {
			font-size: 20px;
		}

		.form-card {
			padding: 20px 16px;
		}

		.field-grid {
			grid-template-columns: 1fr;
		}

		.form-actions {
			flex-direction: column;
		}

		.btn-secondary {
			padding: 14px;
		}
	}
</style>
