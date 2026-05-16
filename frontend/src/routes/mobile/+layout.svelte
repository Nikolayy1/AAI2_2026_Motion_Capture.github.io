<script lang="ts">
	import { page } from '$app/stores';

	let { children } = $props();
	let isMobileMenuOpen = $state(false);

	const noLayoutPaths = ['/mobile', '/mobile/', '/mobile/login', '/mobile/signup'];

	let showLayout = $derived(!noLayoutPaths.includes($page.url.pathname));

	const navItems = [
		{
			href: '/mobile/dashboard',
			label: 'Dashboard',
			icon: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="2" y="2" width="7" height="7" rx="1.5" stroke="currentColor" stroke-width="1.5"/><rect x="11" y="2" width="7" height="7" rx="1.5" stroke="currentColor" stroke-width="1.5"/><rect x="2" y="11" width="7" height="7" rx="1.5" stroke="currentColor" stroke-width="1.5"/><rect x="11" y="11" width="7" height="7" rx="1.5" stroke="currentColor" stroke-width="1.5"/></svg>`
		},
		{
			href: '/mobile/patients',
			label: 'Patients',
			icon: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M10 10a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M16 17v-1a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>`
		},
		{
			href: '/mobile/video-library',
			label: 'Video Library',
			icon: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="2" y="4" width="16" height="12" rx="2" stroke="currentColor" stroke-width="1.5"/><path d="M8 8l5 2.5L8 13V8z" fill="currentColor"/></svg>`
		},
		{
			href: '/mobile/upload',
			label: 'Upload Video',
			icon: `<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17 13v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><path d="M13 7l-3-3-3 3M10 4v9" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
		}
	];

	const pageTitles: Record<string, string> = {
		'/mobile/dashboard': 'Dashboard',
		'/mobile/patients': 'Patients',
		'/mobile/create-patient': 'Create Patient',
		'/mobile/upload': 'Upload Video',
		'/mobile/video-library': 'Video Library',
		'/mobile/patient-detail': 'Patient Detail',
		'/mobile/biometric-information': 'Patient Information',
		'/mobile/recording-overview': 'Recording Overview'
	};

	let currentTitle = $derived(pageTitles[$page.url.pathname] ?? 'Gait Analysis');

	function isActive(href: string): boolean {
		return $page.url.pathname === href;
	}
</script>

{#if showLayout}
	<div class="app-layout">
		<!-- Desktop Sidebar -->
		<aside class="sidebar">
			<div class="sidebar-logo">
				<img src="/logo.png" alt="Gait Analysis Logo" class="logo-img" />
				<span class="app-name">Gait Analysis</span>
			</div>

			<nav class="sidebar-nav">
				{#each navItems as item}
					<a href={item.href} class="nav-item" class:active={isActive(item.href)}>
						{@html item.icon}
						<span>{item.label}</span>
					</a>
				{/each}
			</nav>

			<div class="sidebar-footer">
				<a href="/mobile" class="nav-item logout">
					<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M7 17H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
						<path d="M13 14l4-4-4-4M17 10H7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
					</svg>
					<span>Logout</span>
				</a>
			</div>
		</aside>

		<!-- Mobile Top Bar -->
		<div class="mobile-topbar">
			<button
				class="hamburger"
				type="button"
				aria-label="Open menu"
				onclick={() => (isMobileMenuOpen = true)}
			>
				<svg width="22" height="22" viewBox="0 0 22 22" fill="none">
					<path d="M3 11h16M3 5.5h16M3 16.5h16" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
				</svg>
			</button>
			<span class="mobile-title">{currentTitle}</span>
			<div class="topbar-spacer"></div>
		</div>

		<!-- Mobile Drawer Overlay -->
		{#if isMobileMenuOpen}
			<div
				class="mobile-overlay"
				role="button"
				tabindex="0"
				aria-label="Close menu"
				onclick={() => (isMobileMenuOpen = false)}
				onkeydown={(e) => {
					if (e.key === 'Enter' || e.key === ' ') isMobileMenuOpen = false;
				}}
			></div>

			<div class="mobile-drawer">
				<div class="drawer-logo">
					<img src="/logo.png" alt="Logo" class="logo-img" />
					<span class="app-name">Gait Analysis</span>
				</div>

				<nav class="drawer-nav">
					{#each navItems as item}
						<a
							href={item.href}
							class="nav-item"
							class:active={isActive(item.href)}
							onclick={() => (isMobileMenuOpen = false)}
						>
							{@html item.icon}
							<span>{item.label}</span>
						</a>
					{/each}
				</nav>

				<div class="drawer-footer">
					<a href="/mobile" class="nav-item logout" onclick={() => (isMobileMenuOpen = false)}>
						<svg width="20" height="20" viewBox="0 0 20 20" fill="none">
							<path d="M7 17H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
							<path d="M13 14l4-4-4-4M17 10H7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
						</svg>
						<span>Logout</span>
					</a>
				</div>
			</div>
		{/if}

		<!-- Main Content -->
		<main class="main-content">
			{@render children()}
		</main>
	</div>
{:else}
	{@render children()}
{/if}

<style>
	:global(body) {
		margin: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
		background: #f5f8fa;
		color: #1a1a1a;
	}

	:global(*) {
		box-sizing: border-box;
	}

	.app-layout {
		display: flex;
		min-height: 100vh;
	}

	/* ── Sidebar ── */
	.sidebar {
		width: 232px;
		min-width: 232px;
		background: #ffffff;
		border-right: 1px solid #e8eaed;
		display: flex;
		flex-direction: column;
		position: sticky;
		top: 0;
		height: 100vh;
		overflow-y: auto;
		z-index: 10;
	}

	.sidebar-logo {
		padding: 22px 20px 18px;
		display: flex;
		align-items: center;
		gap: 11px;
		border-bottom: 1px solid #e8eaed;
	}

	.logo-img {
		width: 36px;
		height: 36px;
		object-fit: contain;
		border-radius: 8px;
	}

	.app-name {
		font-size: 15px;
		font-weight: 700;
		color: #1a1a1a;
		letter-spacing: -0.2px;
	}

	.sidebar-nav {
		flex: 1;
		padding: 10px 10px;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.sidebar-footer {
		padding: 10px 10px 16px;
		border-top: 1px solid #e8eaed;
	}

	/* ── Nav Items (shared by sidebar & drawer) ── */
	.nav-item {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 9px 12px;
		border-radius: 8px;
		text-decoration: none;
		color: #555;
		font-size: 14px;
		font-weight: 500;
		transition: background-color 0.15s, color 0.15s;
		cursor: pointer;
		border: none;
		background: none;
		width: 100%;
		text-align: left;
	}

	.nav-item:hover {
		background-color: #f0f7ff;
		color: #1565c0;
	}

	.nav-item.active {
		background-color: #e3f2fd;
		color: #1565c0;
		font-weight: 600;
	}

	.nav-item.logout {
		color: #e53935;
	}

	.nav-item.logout:hover {
		background-color: #ffebee;
		color: #c62828;
	}

	/* ── Main Content ── */
	.main-content {
		flex: 1;
		min-width: 0;
		overflow-x: hidden;
	}

	/* ── Mobile Top Bar ── */
	.mobile-topbar {
		display: none;
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		height: 58px;
		background: #ffffff;
		border-bottom: 1px solid #e8eaed;
		align-items: center;
		padding: 0 12px;
		z-index: 100;
		box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
	}

	.hamburger {
		border: none;
		background: none;
		padding: 8px;
		cursor: pointer;
		color: #333;
		display: flex;
		align-items: center;
		justify-content: center;
		border-radius: 8px;
		transition: background 0.15s;
		flex-shrink: 0;
	}

	.hamburger:hover {
		background: #f5f5f5;
	}

	.mobile-title {
		flex: 1;
		text-align: center;
		font-size: 16px;
		font-weight: 600;
		color: #1a1a1a;
	}

	.topbar-spacer {
		width: 38px;
		flex-shrink: 0;
	}

	/* ── Mobile Overlay & Drawer ── */
	.mobile-overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.35);
		z-index: 200;
		border: none;
		cursor: pointer;
	}

	.mobile-drawer {
		position: fixed;
		top: 0;
		left: 0;
		width: 256px;
		height: 100vh;
		background: #ffffff;
		z-index: 201;
		display: flex;
		flex-direction: column;
		box-shadow: 4px 0 20px rgba(0, 0, 0, 0.12);
		animation: slideIn 0.2s ease;
	}

	@keyframes slideIn {
		from {
			transform: translateX(-100%);
		}
		to {
			transform: translateX(0);
		}
	}

	.drawer-logo {
		padding: 28px 20px 18px;
		display: flex;
		align-items: center;
		gap: 11px;
		border-bottom: 1px solid #e8eaed;
	}

	.drawer-nav {
		flex: 1;
		padding: 10px 10px;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}

	.drawer-footer {
		padding: 10px 10px 20px;
		border-top: 1px solid #e8eaed;
	}

	/* ── Responsive ── */
	@media (max-width: 768px) {
		.sidebar {
			display: none;
		}

		.mobile-topbar {
			display: flex;
		}

		.main-content {
			padding-top: 58px;
		}
	}
</style>
