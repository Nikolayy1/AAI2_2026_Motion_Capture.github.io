<svelte:head>
	<title>Dashboard — Gait Analysis</title>
</svelte:head>

<div class="page">
	<div class="page-header">
		<h1 class="page-title">Welcome!</h1>
		<p class="page-subtitle">What would you like to do?</p>
	</div>

	<div class="action-grid">
		<a href="/mobile/create-patient" class="action-card create-patient">
			<div class="card-icon-wrapper blue-icon">
				<svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
					<circle cx="9" cy="7" r="4"></circle>
					<line x1="19" y1="8" x2="19" y2="14"></line>
					<line x1="22" y1="11" x2="16" y2="11"></line>
				</svg>
			</div>
			<div class="card-content">
				<h3 class="card-title">Create Patient</h3>
				<p class="card-description">Add a new patient profile to the system</p>
			</div>
			<div class="card-arrow">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="9 18 15 12 9 6"></polyline>
				</svg>
			</div>
		</a>

		<a href="/mobile/upload" class="action-card upload-video">
			<div class="card-icon-wrapper green-icon">
				<svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
					<polyline points="17 8 12 3 7 8"></polyline>
					<line x1="12" y1="3" x2="12" y2="15"></line>
				</svg>
			</div>
			<div class="card-content">
				<h3 class="card-title">Upload Video</h3>
				<p class="card-description">Upload an existing gait recording</p>
			</div>
			<div class="card-arrow">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="9 18 15 12 9 6"></polyline>
				</svg>
			</div>
		</a>

		<a href="/mobile/patients" class="action-card view-patients">
			<div class="card-icon-wrapper purple-icon">
				<svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
					<circle cx="9" cy="7" r="4"></circle>
					<path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
					<path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
				</svg>
			</div>
			<div class="card-content">
				<h3 class="card-title">View Patients</h3>
				<p class="card-description">Browse and manage all patient records</p>
			</div>
			<div class="card-arrow">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="9 18 15 12 9 6"></polyline>
				</svg>
			</div>
		</a>

		<a href="/mobile/video-library" class="action-card video-lib">
			<div class="card-icon-wrapper orange-icon">
				<svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
					<polygon points="10 8 16 11 10 14 10 8" fill="currentColor" stroke="none"></polygon>
				</svg>
			</div>
			<div class="card-content">
				<h3 class="card-title">Video Library</h3>
				<p class="card-description">View all annotated recordings</p>
			</div>
			<div class="card-arrow">
				<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
					<polyline points="9 18 15 12 9 6"></polyline>
				</svg>
			</div>
		</a>
	</div>
</div>

<style>
	.page {
		padding: 40px 48px;
		max-width: 1100px;
	}

	.page-header {
		margin-bottom: 36px;
	}

	.page-title {
		margin: 0 0 8px;
		font-size: 30px;
		font-weight: 700;
		color: #1a1a1a;
	}

	.page-subtitle {
		margin: 0;
		font-size: 16px;
		color: #666;
	}

	.action-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 20px;
	}

	.action-card {
		display: flex;
		align-items: center;
		padding: 24px 20px;
		border-radius: 14px;
		text-decoration: none;
		box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
		transition: transform 0.18s, box-shadow 0.18s;
		border: 1px solid transparent;
	}

	.action-card:hover {
		transform: translateY(-3px);
		box-shadow: 0 6px 18px rgba(0, 0, 0, 0.1);
	}

	.create-patient {
		background: #e3f2fd;
		border-color: #bbdefb;
	}

	.upload-video {
		background: #e8f5e9;
		border-color: #c8e6c9;
	}

	.view-patients {
		background: #ede7f6;
		border-color: #d1c4e9;
	}

	.video-lib {
		background: #fff3e0;
		border-color: #ffe0b2;
	}

	.card-icon-wrapper {
		width: 54px;
		height: 54px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		margin-right: 16px;
	}

	.blue-icon {
		background: #bbdefb;
		color: #1565c0;
	}

	.green-icon {
		background: #c8e6c9;
		color: #2e7d32;
	}

	.purple-icon {
		background: #d1c4e9;
		color: #4527a0;
	}

	.orange-icon {
		background: #ffe0b2;
		color: #e65100;
	}

	.card-icon {
		width: 26px;
		height: 26px;
	}

	.card-content {
		flex: 1;
		min-width: 0;
	}

	.card-title {
		margin: 0 0 4px;
		font-size: 17px;
		font-weight: 600;
		color: #1a1a1a;
	}

	.card-description {
		margin: 0;
		font-size: 13px;
		color: #555;
		line-height: 1.4;
	}

	.card-arrow {
		width: 20px;
		height: 20px;
		color: #aaa;
		flex-shrink: 0;
		margin-left: 12px;
	}

	.card-arrow svg {
		width: 100%;
		height: 100%;
	}

	@media (max-width: 768px) {
		.page {
			padding: 24px 16px 32px;
		}

		.page-title {
			font-size: 24px;
		}

		.action-grid {
			grid-template-columns: 1fr;
			gap: 14px;
		}

		.action-card {
			padding: 18px 16px;
		}
	}
</style>
