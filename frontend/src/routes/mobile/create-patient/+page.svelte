<script lang="ts">
	import { goto } from '$app/navigation';

	let patientName = $state('');

	function handleCreatePatient() {
		if (patientName.trim()) {
			// Store patient name in session storage for biometric page
			sessionStorage.setItem('newPatientName', patientName.trim());

			// Navigate to biometric information page
			goto(`/mobile/biometric-information?source=create-patient&patient=${encodeURIComponent(patientName.trim())}`);
		} else {
			alert('Please enter a patient name');
		}
	}

	function handleCancel() {
		goto('/mobile/dashboard');
	}
</script>

<svelte:head>
	<title>Create Patient</title>
</svelte:head>

<div class="screen">
	<header class="topbar">
		<a href="/mobile/dashboard" class="back-btn" aria-label="Go back">
			<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" xmlns="http://www.w3.org/2000/svg">
				<polyline points="15 18 9 12 15 6"></polyline>
			</svg>
		</a>
		<h1>Create Patient</h1>
	</header>

	
	<main class="content">
		<div class="icon-wrapper">
			<svg class="patient-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" xmlns="http://www.w3.org/2000/svg">
				<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
				<circle cx="9" cy="7" r="4"></circle>
				<line x1="19" y1="8" x2="19" y2="14"></line>
				<line x1="22" y1="11" x2="16" y2="11"></line>
			</svg>
		</div>

		<h2 class="page-title">Create New Patient</h2>
		<p class="page-description">Enter the patient's name to create a new profile.</p>

		<form onsubmit={(e) => { e.preventDefault(); handleCreatePatient(); }}>
			<label for="patientName" class="input-label">Full Name</label>
			<input
				type="text"
				id="patientName"
				class="input-field"
				placeholder="Enter patient name"
				bind:value={patientName}
			/>

			<button type="submit" class="btn-primary">Create Patient</button>
			<button type="button" class="btn-secondary" onclick={handleCancel}>Cancel</button>
		</form>
	</main>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
		background: #ffffff;
		color: #000000;
	}

	:global(*) {
		box-sizing: border-box;
	}

	.screen {
		min-height: 100vh;
		max-width: 430px;
		min-width: 360px;
		margin: 0 auto;
		background: #ffffff;
		position: relative;
	}

	.topbar {
		height: 84px;
		background: #ffffff;
		border-bottom: 1px solid #e0e0e0;
		display: flex;
		align-items: center;
		justify-content: center;
		position: relative;
	}

	.back-btn {
		position: absolute;
		left: 18px;
		top: 50%;
		transform: translateY(-50%);
		background: transparent;
		border: none;
		cursor: pointer;
		color: #000000;
		width: 32px;
		height: 32px;
		display: flex;
		align-items: center;
		justify-content: center;
		text-decoration: none;
	}

	.back-btn svg {
		width: 28px;
		height: 28px;
	}

	.topbar h1 {
		margin: 0;
		font-size: 24px;
		font-weight: 600;
		color: #000000;
	}

	.content {
		padding: 60px 24px 40px;
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.icon-wrapper {
		width: 120px;
		height: 120px;
		border-radius: 50%;
		background: #BBDEFB;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 40px;
	}

	.patient-icon {
		width: 56px;
		height: 56px;
		color: #1976D2;
	}

	.page-title {
		margin: 0 0 16px;
		font-size: 28px;
		font-weight: 600;
		color: #000000;
		text-align: center;
	}

	.page-description {
		margin: 0 0 48px;
		font-size: 16px;
		font-weight: 400;
		color: #666666;
		text-align: center;
		max-width: 320px;
		line-height: 1.5;
	}

	form {
		width: 100%;
		max-width: 400px;
	}

	.input-label {
		display: block;
		margin-bottom: 12px;
		font-size: 18px;
		font-weight: 600;
		color: #000000;
	}

	.input-field {
		width: 100%;
		padding: 16px 20px;
		border: 1px solid #d0d0d0;
		border-radius: 12px;
		font-size: 16px;
		color: #000000;
		background: #ffffff;
		margin-bottom: 40px;
		outline: none;
		transition: border-color 0.2s;
	}

	.input-field::placeholder {
		color: #999999;
	}

	.input-field:focus {
		border-color: #1976D2;
	}

	.btn-primary {
		width: 100%;
		padding: 18px;
		border: none;
		border-radius: 12px;
		background: #90CAF9;
		color: #000000;
		font-size: 18px;
		font-weight: 600;
		cursor: pointer;
		margin-bottom: 16px;
		transition: background 0.2s;
	}

	.btn-primary:hover {
		background: #64B5F6;
	}

	.btn-secondary {
		width: 100%;
		padding: 18px;
		border: none;
		border-radius: 12px;
		background: #E0E0E0;
		color: #000000;
		font-size: 18px;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.2s;
	}

	.btn-secondary:hover {
		background: #BDBDBD;
	}
</style>
