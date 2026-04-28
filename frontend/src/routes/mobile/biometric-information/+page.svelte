<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { CREATE_PATIENT_ENDPOINT, UPDATE_PATIENT_ENDPOINT } from '$lib/config';

	// Form state
	let fullName = $state('');
	let gender = $state('');
	let age = $state('');
	let height = $state('');
	let weight = $state('');
	let notes = $state('');
	let genderDropdownOpen = $state(false);
	let patientId: number | null = $state(null);

	// Validation
	let showErrors = $state(false);

	// Flow detection
	let mode = $state('create'); // 'create' or 'edit'
	let source = $state('upload'); // 'upload' or 'create-patient' or 'patient-detail'
	let showSuccess = $state(false);
	let isCreatingPatient = $state(false);

	const genderOptions = [
		{ value: 'female', label: 'Female' },
		{ value: 'male', label: 'Male' },
		{ value: 'other', label: 'Other' },
		{ value: 'prefer-not-to-say', label: 'Prefer not to say' }
	];

	// Get data from URL params or session storage
	onMount(() => {
		const urlParams = new URLSearchParams(window.location.search);
		const patientIdParam = urlParams.get('patientId');
		const patientNameParam = urlParams.get('patientName');
		const modeParam = urlParams.get('mode');
		source = urlParams.get('source') || 'create-patient';

		// Determine mode (create or edit)
		if (modeParam === 'edit' || source === 'patient-detail') {
			mode = 'edit';
			if (patientIdParam) {
				patientId = parseInt(patientIdParam);
				// Load existing patient data
				loadPatientData(patientId);
			}
		} else {
			mode = 'create';
		}

		// Pre-fill patient name if available (for create mode)
		if (mode === 'create' && patientNameParam) {
			fullName = patientNameParam;
		}

		// Store patient ID if provided
		if (patientIdParam && !patientId) {
			patientId = parseInt(patientIdParam);
		}
	});

	async function loadPatientData(id: number) {
		try {
			const response = await fetch(UPDATE_PATIENT_ENDPOINT.replace('{patient_id}', id.toString()));
			if (response.ok) {
				const data = await response.json();
				fullName = data.patient.name || '';
				gender = data.patient.gender || '';
				age = data.patient.age?.toString() || '';
				height = data.patient.height?.toString() || '';
				weight = data.patient.weight?.toString() || '';
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

		// Validate required fields
		if (!fullName || !gender || !age || !height || !weight) {
			return;
		}

		const biometricData = {
			patientId,
			fullName,
			gender,
			age,
			height,
			weight,
			notes
		};

		if (mode === 'edit') {
			// Edit existing patient
			await updatePatient(biometricData);
		} else if (source === 'create-patient') {
			// Create patient flow
			await createPatient(biometricData);
		}
	}

	async function createPatient(biometricData: any) {
		isCreatingPatient = true;

		try {
			// Create FormData for backend API
			const formData = new FormData();
			formData.append('user_id', '1'); // Using dummy user_id since auth is disabled
			formData.append('name', biometricData.fullName);
			formData.append('age', biometricData.age);
			formData.append('gender', biometricData.gender);
			formData.append('height', biometricData.height);
			formData.append('weight', biometricData.weight);

			const response = await fetch(CREATE_PATIENT_ENDPOINT, {
				method: 'POST',
				body: formData
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({}));
				throw new Error(errorData.error || 'Failed to create patient');
			}

			const result = await response.json();
			console.log('Patient created:', result);

			// Show success overlay
			showSuccess = true;

			// Clear session storage
			sessionStorage.removeItem('newPatientName');

			// Navigate to dashboard after 2 seconds
			setTimeout(() => {
				goto('/mobile/dashboard');
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
			if (!patientId) {
				throw new Error('Patient ID is required');
			}

			// Create FormData for backend API
			const formData = new FormData();
			formData.append('age', biometricData.age);
			formData.append('gender', biometricData.gender);
			formData.append('height', biometricData.height);
			formData.append('weight', biometricData.weight);

			const endpoint = UPDATE_PATIENT_ENDPOINT.replace('{patient_id}', patientId.toString());
			const response = await fetch(endpoint, {
				method: 'PUT',
				body: formData
			});

			if (!response.ok) {
				const errorData = await response.json().catch(() => ({}));
				throw new Error(errorData.error || 'Failed to update patient');
			}

			const result = await response.json();
			console.log('Patient updated:', result);

			// Show success overlay
			showSuccess = true;

			// Navigate back to patient detail after 1 second
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

	// Computed button text
	let buttonText = $derived(() => {
		if (isCreatingPatient) {
			return mode === 'edit' ? 'Updating...' : 'Creating Patient...';
		}
		return mode === 'edit' ? 'Save Changes' : 'Create Patient';
	});

	// Computed subtitle
	let subtitle = $derived(() => {
		return mode === 'edit'
			? 'Update patient information'
			: 'Add patient information';
	});
</script>

<div class="container">
	<header>
		<button class="back-button" onclick={handleBack} aria-label="Go back">
			<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
				<path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
			</svg>
		</button>
		<h1>Biometric Informations</h1>
	</header>

	<p class="subtitle">{subtitle()}</p>

	<form onsubmit={(e) => { e.preventDefault(); handleSaveAndContinue(); }}>
		<!-- Personal Details Section -->
		<section class="form-section">
			<h2>Personal details</h2>

			<div class="form-group">
				<input
					type="text"
					bind:value={fullName}
					placeholder="Full Name"
					class:error={showErrors && !fullName}
				/>
				{#if showErrors && !fullName}
					<span class="error-message">Required field</span>
				{/if}
			</div>

			<div class="form-group">
				<div class="dropdown" class:open={genderDropdownOpen}>
					<button
						type="button"
						class="dropdown-button"
						class:error={showErrors && !gender}
						class:placeholder={!gender}
						onclick={() => genderDropdownOpen = !genderDropdownOpen}
					>
						<span>{gender ? genderOptions.find(opt => opt.value === gender)?.label : 'Gender'}</span>
						<svg width="20" height="20" viewBox="0 0 20 20" fill="none" class="dropdown-icon">
							<path d="M5 7.5l5 5 5-5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
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
									<span>{option.label}</span>
									{#if gender === option.value}
										<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
											<path d="M16.666 5L7.5 14.167 3.333 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
										</svg>
									{/if}
								</button>
							{/each}
						</div>
					{/if}
				</div>
				{#if showErrors && !gender}
					<span class="error-message">Required field</span>
				{/if}
			</div>

			<div class="form-group">
				<input
					type="number"
					bind:value={age}
					placeholder="Age"
					min="0"
					max="150"
					class:error={showErrors && !age}
				/>
				{#if showErrors && !age}
					<span class="error-message">Required field</span>
				{/if}
			</div>
		</section>

		<!-- Body Metrics Section -->
		<section class="form-section">
			<h2>Body metrics</h2>

			<div class="form-group">
				<div class="input-with-unit">
					<input
						type="number"
						bind:value={height}
						placeholder="Height"
						min="0"
						step="0.1"
						class:error={showErrors && !height}
					/>
					<span class="unit">cm</span>
				</div>
				{#if showErrors && !height}
					<span class="error-message">Required field</span>
				{/if}
			</div>

			<div class="form-group">
				<div class="input-with-unit">
					<input
						type="number"
						bind:value={weight}
						placeholder="Weight"
						min="0"
						step="0.1"
						class:error={showErrors && !weight}
					/>
					<span class="unit">kg</span>
				</div>
				{#if showErrors && !weight}
					<span class="error-message">Required field</span>
				{/if}
			</div>

			<div class="form-group">
				<textarea
					bind:value={notes}
					placeholder="Notes (optional)"
					rows="4"
				></textarea>
			</div>
		</section>

		<button type="submit" class="save-button" disabled={isCreatingPatient}>{buttonText()}</button>
	</form>

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
				<p class="success-message">{mode === 'edit' ? `${fullName}'s information has been successfully updated.` : `${fullName} has been successfully added to the system.`}</p>
			</div>
		</div>
	{/if}
</div>

<style>
	.container {
		max-width: 430px;
		margin: 0 auto;
		padding: 20px;
		background-color: #ffffff;
		min-height: 100vh;
	}

	header {
		display: flex;
		align-items: center;
		gap: 12px;
		margin-bottom: 8px;
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

	.subtitle {
		font-size: 14px;
		color: #666;
		margin-bottom: 24px;
	}

	.form-section {
		margin-bottom: 32px;
	}

	.form-section h2 {
		font-size: 16px;
		font-weight: 600;
		color: #333;
		margin-bottom: 16px;
	}

	.form-group {
		margin-bottom: 16px;
	}

	input[type="text"],
	input[type="number"],
	textarea {
		width: 100%;
		padding: 12px 16px;
		border: 1px solid #E0E0E0;
		border-radius: 8px;
		font-size: 14px;
		color: #333;
		background-color: #ffffff;
		transition: border-color 0.2s;
		box-sizing: border-box;
	}

	input::placeholder,
	textarea::placeholder {
		color: #999;
	}

	input:focus,
	textarea:focus {
		outline: none;
		border-color: #64B5F6;
	}

	input.error {
		border-color: #f44336;
	}

	.error-message {
		display: block;
		font-size: 12px;
		color: #f44336;
		margin-top: 4px;
	}

	.input-with-unit {
		position: relative;
		display: flex;
		align-items: center;
	}

	.input-with-unit input {
		flex: 1;
		padding-right: 50px;
	}

	.unit {
		position: absolute;
		right: 16px;
		font-size: 14px;
		color: #666;
		pointer-events: none;
	}

	textarea {
		resize: vertical;
		min-height: 80px;
		font-family: inherit;
	}

	/* Dropdown Styles */
	.dropdown {
		position: relative;
	}

	.dropdown-button {
		width: 100%;
		padding: 12px 16px;
		border: 1px solid #E0E0E0;
		border-radius: 8px;
		font-size: 14px;
		color: #333;
		background-color: #ffffff;
		text-align: left;
		cursor: pointer;
		display: flex;
		justify-content: space-between;
		align-items: center;
		transition: border-color 0.2s;
	}

	.dropdown-button.placeholder {
		color: #999;
	}

	.dropdown-button:hover,
	.dropdown-button:focus {
		outline: none;
		border-color: #64B5F6;
	}

	.dropdown-button.error {
		border-color: #f44336;
	}

	.dropdown-icon {
		transition: transform 0.2s;
		color: #666;
	}

	.dropdown.open .dropdown-icon {
		transform: rotate(180deg);
	}

	.dropdown-menu {
		position: absolute;
		top: calc(100% + 4px);
		left: 0;
		right: 0;
		background-color: #ffffff;
		border: 1px solid #E0E0E0;
		border-radius: 8px;
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
		z-index: 10;
		overflow: hidden;
	}

	.dropdown-item {
		width: 100%;
		padding: 12px 16px;
		border: none;
		background: none;
		text-align: left;
		cursor: pointer;
		font-size: 14px;
		color: #333;
		display: flex;
		justify-content: space-between;
		align-items: center;
		transition: background-color 0.2s;
	}

	.dropdown-item:hover {
		background-color: #F5F8FA;
	}

	.dropdown-item.selected {
		color: #64B5F6;
	}

	.dropdown-item svg {
		color: #64B5F6;
	}

	.save-button {
		width: 100%;
		padding: 14px;
		background: linear-gradient(135deg, #5E92C3 0%, #4A7BA7 100%);
		color: white;
		border: none;
		border-radius: 8px;
		font-size: 16px;
		font-weight: 600;
		cursor: pointer;
		transition: opacity 0.2s;
		margin-top: 24px;
	}

	.save-button:hover {
		opacity: 0.9;
	}

	.save-button:active {
		opacity: 0.8;
	}

	.save-button:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	/* Success Overlay */
	.success-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background-color: rgba(0, 0, 0, 0.5);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		animation: fadeIn 0.3s ease;
	}

	@keyframes fadeIn {
		from {
			opacity: 0;
		}
		to {
			opacity: 1;
		}
	}

	.success-modal {
		background-color: white;
		border-radius: 16px;
		padding: 40px 32px;
		max-width: 320px;
		width: 90%;
		text-align: center;
		animation: slideUp 0.4s ease;
	}

	@keyframes slideUp {
		from {
			transform: translateY(20px);
			opacity: 0;
		}
		to {
			transform: translateY(0);
			opacity: 1;
		}
	}

	.success-icon {
		margin-bottom: 24px;
		animation: scaleIn 0.5s ease 0.2s both;
	}

	@keyframes scaleIn {
		from {
			transform: scale(0);
		}
		to {
			transform: scale(1);
		}
	}

	.success-title {
		font-size: 24px;
		font-weight: 600;
		color: #333;
		margin: 0 0 12px 0;
	}

	.success-message {
		font-size: 14px;
		color: #666;
		margin: 0;
		line-height: 1.5;
	}

	/* Close dropdown when clicking outside */
	:global(body) {
		-webkit-tap-highlight-color: transparent;
	}
</style>
