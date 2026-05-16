<script lang="ts">
	import { goto } from '$app/navigation';
	import { API_CONFIG } from '$lib/config';

	let fullName: string = $state('');
	let email: string = $state('');
	let password: string = $state('');
	let confirmPassword: string = $state('');
	let error: string = $state('');
	let loading: boolean = $state(false);

	async function handleSignup(event: Event) {
		event.preventDefault();
		error = '';

		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}

		loading = true;

		try {
			const formData = new FormData();
			formData.append('email', email);
			formData.append('password', password);

			const res = await fetch(`${API_CONFIG.BASE_URL}/register`, {
				method: 'POST',
				body: formData
			});

			const data = await res.json();

			if (!res.ok || data.error) {
				error = data.error || 'Registration failed';
				return;
			}

			const loginRes = await fetch(`${API_CONFIG.BASE_URL}/login`, {
				method: 'POST',
				body: formData
			});

			const loginData = await loginRes.json();

			if (loginRes.ok) {
				localStorage.setItem('access_token', loginData.access_token);
				localStorage.setItem('user_id', String(loginData.user_id));
			}

			goto('/mobile/dashboard');
		} catch (err) {
			error = 'Server error';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Register — Gait Analysis</title>
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
			<h1 class="card-title">Create an Account</h1>
			<p class="card-subtitle">Sign up to get started.</p>

			<form onsubmit={handleSignup}>
				<div class="field">
					<label for="fullName">Full name</label>
					<input
						id="fullName"
						type="text"
						bind:value={fullName}
						placeholder="Enter your full name"
						autocomplete="name"
					/>
				</div>

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
						placeholder="Create a password"
						autocomplete="new-password"
					/>
				</div>

				<div class="field">
					<label for="confirmPassword">Confirm password</label>
					<input
						id="confirmPassword"
						type="password"
						bind:value={confirmPassword}
						placeholder="Confirm your password"
						autocomplete="new-password"
					/>
				</div>

				{#if error}
					<p class="error-msg">{error}</p>
				{/if}

				<button type="submit" class="primary-btn" disabled={loading}>
					{loading ? 'Creating account…' : 'Create Account'}
				</button>

				<div class="divider"><span></span><p>or</p><span></span></div>

				<a href="/web/login" class="secondary-btn">Log in</a>
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

	input[type='text'],
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

	input[type='text']::placeholder,
	input[type='email']::placeholder,
	input[type='password']::placeholder {
		color: #aaa;
	}

	input[type='text']:focus,
	input[type='email']:focus,
	input[type='password']:focus {
		border-color: #97bbe8;
		box-shadow: 0 0 0 3px rgba(151, 187, 232, 0.2);
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
		margin-top: 4px;
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
	}
</style>
