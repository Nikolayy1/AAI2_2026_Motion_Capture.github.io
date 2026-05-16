<script lang="ts">
	import { goto } from '$app/navigation';
	import { API_CONFIG } from '$lib/config';

	let email: string = $state('');
	let password: string = $state('');
	let rememberMe: boolean = $state(false);
	let error: string = $state('');
	let loading: boolean = $state(false);

	async function handleLogin(event: Event) {
		event.preventDefault();
		loading = true;
		error = '';

		const formData = new FormData();
		formData.append('email', email);
		formData.append('password', password);

		try {
			const res = await fetch(`${API_CONFIG.LOGIN_ENDPOINT}`, {
				method: 'POST',
				body: formData
			});

			const data = await res.json();

			if (!res.ok || data.error) {
				error = data.error || 'Login failed';
				return;
			}

			const storage = rememberMe ? localStorage : sessionStorage;
			storage.setItem('access_token', data.access_token);
			storage.setItem('user_id', String(data.user_id));

			goto('/mobile/dashboard');
		} catch (err) {
			error = 'Could not connect to server';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Log In — Gait Analysis</title>
</svelte:head>

<div class="page">
	<header class="topbar">
		<div class="brand">
			<img src="/logo.png" alt="Biomechanics4All logo" class="logo" />
			<span class="brand-text">
				<span class="dark">Biomechanics</span><span class="accent">4All</span>
			</span>
		</div>
	</header>

	<main class="content">
		<div class="card">
			<h1 class="card-title">Log In</h1>
			<p class="card-subtitle">Welcome back! Please enter your details.</p>

			<form onsubmit={handleLogin}>
				<div class="field">
					<label for="email">E-mail address</label>
					<input
						id="email"
						type="email"
						bind:value={email}
						placeholder="Enter your email address"
						autocomplete="email"
					/>
				</div>

				<div class="field">
					<label for="password">Password</label>
					<input
						id="password"
						type="password"
						bind:value={password}
						placeholder="Enter your password"
						autocomplete="current-password"
					/>
				</div>

				<div class="options-row">
					<label class="remember">
						<input type="checkbox" bind:checked={rememberMe} />
						<span>Remember me</span>
					</label>
					<a href="/" class="forgot-link">Forgot password?</a>
				</div>

				{#if error}
					<p class="error-msg">{error}</p>
				{/if}

				<button type="submit" class="primary-btn" disabled={loading}>
					{loading ? 'Logging in…' : 'Log In'}
				</button>

				<div class="divider"><span></span><p>or</p><span></span></div>

				<a href="/web/register" class="secondary-btn">Create account</a>
			</form>
		</div>
	</main>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
		background: linear-gradient(90deg, #f7fbff 0%, #ffffff 100%);
		color: #222;
	}

	:global(*) {
		box-sizing: border-box;
	}

	.page {
		min-height: 100vh;
	}

	/* ── Topbar ── */
	.topbar {
		height: 72px;
		background: #eef5fb;
		display: flex;
		align-items: center;
		padding: 0 28px;
		border-bottom: 1px solid rgba(0, 0, 0, 0.04);
	}

	.brand {
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.logo {
		height: 52px;
		width: auto;
		object-fit: contain;
	}

	.brand-text {
		font-size: 22px;
		font-weight: 700;
		line-height: 1;
	}

	.dark {
		color: #17345d;
	}

	.accent {
		color: #2db4bf;
	}

	/* ── Content ── */
	.content {
		min-height: calc(100vh - 72px);
		display: flex;
		justify-content: center;
		align-items: center;
		padding: 40px 20px;
	}

	/* ── Card ── */
	.card {
		width: 100%;
		max-width: 425px;
		background: #f8f8f8;
		border-radius: 22px;
		padding: 32px 36px 36px;
		box-shadow: 0 4px 14px rgba(0, 0, 0, 0.14);
	}

	.card-title {
		margin: 0 0 6px;
		text-align: center;
		font-size: 26px;
		font-weight: 700;
		color: #1a1a1a;
	}

	.card-subtitle {
		margin: 0 0 28px;
		text-align: center;
		font-size: 14px;
		color: #555;
	}

	/* ── Form ── */
	form {
		display: flex;
		flex-direction: column;
	}

	.field {
		display: flex;
		flex-direction: column;
		margin-bottom: 16px;
	}

	label {
		font-size: 14px;
		font-weight: 600;
		margin-bottom: 7px;
		color: #303030;
	}

	input[type='email'],
	input[type='password'] {
		width: 100%;
		height: 44px;
		padding: 0 14px;
		border: 1px solid #d0d0d0;
		border-radius: 8px;
		background: #ffffff;
		font-size: 14px;
		color: #222;
		outline: none;
		transition: border-color 0.18s, box-shadow 0.18s;
	}

	input[type='email']::placeholder,
	input[type='password']::placeholder {
		color: #aaa;
	}

	input[type='email']:focus,
	input[type='password']:focus {
		border-color: #97bbe8;
		box-shadow: 0 0 0 3px rgba(151, 187, 232, 0.2);
	}

	.options-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		margin: 0 0 18px;
		gap: 12px;
	}

	.remember {
		display: flex;
		align-items: center;
		gap: 8px;
		font-size: 13px;
		font-weight: 400;
		color: #333;
		cursor: pointer;
		margin: 0;
	}

	.remember input {
		width: 15px;
		height: 15px;
		margin: 0;
		accent-color: #97bbe8;
		cursor: pointer;
	}

	.forgot-link {
		font-size: 13px;
		color: #6f9bd3;
		text-decoration: none;
		white-space: nowrap;
	}

	.forgot-link:hover {
		text-decoration: underline;
	}

	.error-msg {
		margin: 0 0 14px;
		padding: 10px 14px;
		background: #ffebee;
		border: 1px solid #ffcdd2;
		border-radius: 8px;
		font-size: 13px;
		color: #c62828;
	}

	.primary-btn,
	.secondary-btn {
		width: 100%;
		height: 46px;
		border-radius: 8px;
		font-size: 15px;
		font-weight: 700;
		cursor: pointer;
		text-align: center;
		text-decoration: none;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: background 0.18s;
	}

	.primary-btn {
		border: none;
		background: #97bbe8;
		color: #1f1f1f;
		box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
	}

	.primary-btn:hover:not(:disabled) {
		background: #84aedf;
	}

	.primary-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.divider {
		margin: 18px 0;
		display: flex;
		align-items: center;
		gap: 12px;
	}

	.divider span {
		flex: 1;
		height: 1px;
		background: #d0d0d0;
	}

	.divider p {
		margin: 0;
		font-size: 14px;
		color: #888;
	}

	.secondary-btn {
		border: 1px solid #d0d0d0;
		background: #ffffff;
		color: #333;
		box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
	}

	.secondary-btn:hover {
		background: #f2f2f2;
	}

	/* ── Responsive ── */
	@media (max-width: 520px) {
		.topbar {
			padding: 0 16px;
		}

		.brand-text {
			font-size: 18px;
		}

		.logo {
			height: 42px;
		}

		.card {
			padding: 24px 20px 28px;
		}

		.options-row {
			flex-direction: column;
			align-items: flex-start;
		}
	}
</style>
