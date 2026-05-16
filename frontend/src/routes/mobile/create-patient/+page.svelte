<script lang="ts">
	import { goto } from '$app/navigation';

	let patientName = $state('');

	function handleCreatePatient() {
		if (patientName.trim()) {
			sessionStorage.setItem('newPatientName', patientName.trim());
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
	<title>Create Patient — Gait Analysis</title>
</svelte:head>

<div class="page">
	<a href="/mobile/dashboard" class="back-link">
		<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
			<path d="M10 12L6 8l4-4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
		</svg>
		Back to Dashboard
	</a>

	<div class="center-area">
		<div class="form-card">
			<div class="icon-wrapper">
				<svg class="patient-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
					<circle cx="9" cy="7" r="4"></circle>
					<line x1="19" y1="8" x2="19" y2="14"></line>
					<line x1="22" y1="11" x2="16" y2="11"></line>
				</svg>
			</div>

			<h1 class="form-title">Create New Patient</h1>
			<p class="form-description">Enter the patient's name to create a new profile and add their information.</p>

			<form onsubmit={(e) => { e.preventDefault(); handleCreatePatient(); }}>
				<div class="field">
					<label for="patientName" class="input-label">Full Name</label>
					<input
						type="text"
						id="patientName"
						class="input-field"
						placeholder="Enter patient's full name"
						bind:value={patientName}
						autocomplete="off"
					/>
				</div>

				<div class="form-actions">
					<button type="submit" class="btn-primary">Create Patient</button>
					<button type="button" class="btn-secondary" onclick={handleCancel}>Cancel</button>
				</div>
			</form>
		</div>
	</div>
</div>

<style>
	.page {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
		padding: 32px 40px;
	}

	.back-link {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 14px;
		font-weight: 500;
		color: #555;
		text-decoration: none;
		flex-shrink: 0;
		transition: color 0.15s;
	}

	.back-link:hover {
		color: #1565c0;
	}

	/* Takes remaining height and centers the card */
	.center-area {
		flex: 1;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 24px 0;
	}

	.form-card {
		width: 100%;
		max-width: 480px;
		background: #ffffff;
		border: 1px solid #e8eaed;
		border-radius: 18px;
		padding: 44px 48px;
		display: flex;
		flex-direction: column;
		align-items: center;
		box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
	}

	.icon-wrapper {
		width: 80px;
		height: 80px;
		border-radius: 50%;
		background: #bbdefb;
		display: flex;
		align-items: center;
		justify-content: center;
		margin-bottom: 20px;
	}

	.patient-icon {
		width: 38px;
		height: 38px;
		color: #1565c0;
	}

	.form-title {
		margin: 0 0 8px;
		font-size: 22px;
		font-weight: 700;
		color: #1a1a1a;
		text-align: center;
	}

	.form-description {
		margin: 0 0 32px;
		font-size: 14px;
		color: #666;
		text-align: center;
		line-height: 1.55;
	}

	form {
		width: 100%;
	}

	.field {
		margin-bottom: 24px;
	}

	.input-label {
		display: block;
		margin-bottom: 7px;
		font-size: 13px;
		font-weight: 600;
		color: #1a1a1a;
		text-transform: uppercase;
		letter-spacing: 0.4px;
	}

	.input-field {
		width: 100%;
		padding: 13px 16px;
		border: 1px solid #d0d0d0;
		border-radius: 10px;
		font-size: 15px;
		color: #1a1a1a;
		background: #fafafa;
		outline: none;
		transition: border-color 0.18s, box-shadow 0.18s, background 0.18s;
	}

	.input-field::placeholder {
		color: #aaa;
	}

	.input-field:focus {
		border-color: #90caf9;
		background: #ffffff;
		box-shadow: 0 0 0 3px rgba(144, 202, 249, 0.2);
	}

	.form-actions {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}

	.btn-primary {
		width: 100%;
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

	.btn-primary:hover {
		background: #64b5f6;
	}

	.btn-secondary {
		width: 100%;
		padding: 14px;
		border: 1px solid #e0e0e0;
		border-radius: 10px;
		background: #ffffff;
		color: #555;
		font-size: 15px;
		font-weight: 500;
		cursor: pointer;
		transition: background 0.18s, border-color 0.18s;
	}

	.btn-secondary:hover {
		background: #f5f5f5;
		border-color: #ccc;
	}

	@media (max-width: 768px) {
		.page {
			padding: 20px 16px 32px;
		}

		.form-card {
			padding: 28px 20px;
		}

		.form-title {
			font-size: 20px;
		}
	}
</style>
