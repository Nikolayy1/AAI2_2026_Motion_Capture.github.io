<script lang="ts">
	let isMenuOpen = $state(false);
</script>

<svelte:head>
	<title>Mobile Dashboard</title>
</svelte:head>

<div class="screen">
	<header class="topbar">
		<button
			class="menu-btn"
			type="button"
			aria-label="Open menu"
			onclick={() => (isMenuOpen = true)}
		>
			☰
		</button>

		<h1>Dashboard</h1>

		<button
			class="help-btn"
			type="button"
			aria-label="Help"
		>
			?
		</button>
	</header>

	{#if isMenuOpen}
		<div
			class="overlay"
			role="button"
			tabindex="0"
			aria-label="Close menu overlay"
			onclick={() => (isMenuOpen = false)}
			onkeydown={(e) => {
				if (e.key === 'Enter' || e.key === ' ') {
					isMenuOpen = false;
				}
			}}
		></div>

		<div class="drawer">
			<a href="/mobile/patients" class="drawer-item">
				<svg width="20" height="20" viewBox="0 0 20 20" fill="none" class="drawer-icon">
					<path d="M10 10a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM16 16v-1a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
				</svg>
				View Patients
			</a>
			<a href="/mobile/video-library" class="drawer-item">
				<svg width="20" height="20" viewBox="0 0 20 20" fill="none" class="drawer-icon">
					<path d="M3 5a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V5z" stroke="currentColor" stroke-width="1.5"/>
					<path d="M8 10l3-2v4l-3-2z" fill="currentColor"/>
				</svg>
				Video Library
			</a>
			<div class="drawer-divider"></div>
			<a href="/mobile" class="drawer-item logout">
				<svg width="20" height="20" viewBox="0 0 20 20" fill="none" class="drawer-icon">
					<path d="M7 17H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3M14 13l4-4-4-4M18 9H7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
				</svg>
				Logout
			</a>
		</div>
	{/if}

	<main class="content">
		<h2 class="welcome-title">Welcome!</h2>
		<p class="welcome-subtitle">What would you like to do?</p>

		<div class="action-cards">
			<a href="/mobile/create-patient" class="action-card create-patient">
				<div class="card-icon-wrapper blue-icon">
					<svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" xmlns="http://www.w3.org/2000/svg">
						<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
						<circle cx="9" cy="7" r="4"></circle>
						<line x1="19" y1="8" x2="19" y2="14"></line>
						<line x1="22" y1="11" x2="16" y2="11"></line>
					</svg>
				</div>
				<div class="card-content">
					<h3 class="card-title">Create Patient</h3>
					<p class="card-description">Add a new patient</p>
				</div>
				<div class="card-arrow">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" xmlns="http://www.w3.org/2000/svg">
						<polyline points="9 18 15 12 9 6"></polyline>
					</svg>
				</div>
			</a>

			<a href="/mobile/upload" class="action-card upload-video">
				<div class="card-icon-wrapper green-icon">
					<svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" xmlns="http://www.w3.org/2000/svg">
						<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
						<polyline points="17 8 12 3 7 8"></polyline>
						<line x1="12" y1="3" x2="12" y2="15"></line>
					</svg>
				</div>
				<div class="card-content">
					<h3 class="card-title">Upload Video</h3>
					<p class="card-description">Upload an existing recording</p>
				</div>
				<div class="card-arrow">
					<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" xmlns="http://www.w3.org/2000/svg">
						<polyline points="9 18 15 12 9 6"></polyline>
					</svg>
				</div>
			</a>
		</div>
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
		overflow-x: hidden;
	}

	.topbar {
		height: 84px;
		background: #ffffff;
		border-bottom: 1px solid #e0e0e0;
		display: flex;
		align-items: center;
		justify-content: center;
		position: sticky;
		top: 0;
		z-index: 20;
	}

	.menu-btn {
		position: absolute;
		left: 18px;
		top: 50%;
		transform: translateY(-50%);
		border: none;
		background: transparent;
		font-size: 28px;
		cursor: pointer;
		color: #000000;
		font-weight: 300;
	}

	.help-btn {
		position: absolute;
		right: 18px;
		top: 50%;
		transform: translateY(-50%);
		border: 2px solid #000000;
		background: transparent;
		width: 32px;
		height: 32px;
		border-radius: 50%;
		font-size: 20px;
		font-weight: 600;
		cursor: pointer;
		color: #000000;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.topbar h1 {
		margin: 0;
		font-size: 24px;
		font-weight: 600;
		color: #000000;
	}

	.content {
		padding: 40px 24px;
	}

	.welcome-title {
		margin: 0 0 8px;
		text-align: center;
		font-size: 32px;
		font-weight: 600;
		color: #000000;
	}

	.welcome-subtitle {
		margin: 0 0 40px;
		text-align: center;
		font-size: 18px;
		font-weight: 400;
		color: #000000;
	}

	.action-cards {
		display: flex;
		flex-direction: column;
		gap: 20px;
	}

	.action-card {
		display: flex;
		align-items: center;
		padding: 24px 20px;
		border-radius: 16px;
		text-decoration: none;
		box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
		transition: transform 0.2s, box-shadow 0.2s;
	}

	.action-card:hover {
		transform: translateY(-2px);
		box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
	}

	.create-patient {
		background: #E3F2FD;
	}

	.upload-video {
		background: #E8F5E9;
	}

	.card-icon-wrapper {
		width: 56px;
		height: 56px;
		border-radius: 50%;
		display: flex;
		align-items: center;
		justify-content: center;
		flex-shrink: 0;
		margin-right: 16px;
	}

	.blue-icon {
		background: #BBDEFB;
		color: #1976D2;
	}

	.green-icon {
		background: #C8E6C9;
		color: #388E3C;
	}

	.card-icon {
		width: 28px;
		height: 28px;
	}

	.card-content {
		flex: 1;
	}

	.card-title {
		margin: 0 0 4px;
		font-size: 20px;
		font-weight: 600;
		color: #000000;
	}

	.card-description {
		margin: 0;
		font-size: 16px;
		font-weight: 400;
		color: #666666;
	}

	.card-arrow {
		width: 24px;
		height: 24px;
		color: #999999;
		flex-shrink: 0;
	}

	.card-arrow svg {
		width: 100%;
		height: 100%;
	}

	.overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.3);
		z-index: 29;
		border: none;
	}

	.drawer {
		position: fixed;
		top: 84px;
		left: 0;
		width: 62%;
		max-width: 270px;
		height: calc(100vh - 84px);
		background: #ffffff;
		border-right: 1px solid #e0e0e0;
		box-shadow: 4px 0 12px rgba(0, 0, 0, 0.15);
		z-index: 30;
		padding: 20px 0;
		display: flex;
		flex-direction: column;
		gap: 4px;
	}

	.drawer-item {
		text-decoration: none;
		color: #000000;
		font-size: 16px;
		font-weight: 500;
		padding: 14px 20px;
		display: flex;
		align-items: center;
		gap: 12px;
		transition: background-color 0.2s;
	}

	.drawer-item:hover {
		background-color: #F5F8FA;
	}

	.drawer-icon {
		flex-shrink: 0;
		color: #666;
	}

	.drawer-divider {
		height: 1px;
		background-color: #E0E0E0;
		margin: 8px 0;
	}

	.drawer-item.logout {
		color: #f44336;
	}

	.drawer-item.logout .drawer-icon {
		color: #f44336;
	}
</style>