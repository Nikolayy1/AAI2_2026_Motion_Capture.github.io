<script lang="ts">
	import { goto } from '$app/navigation';

	let email: string = $state('');
	let password: string = $state('');
	let rememberMe: boolean = $state(false);

	function handleLogin(event: Event) {
		event.preventDefault();

		// Authentication disabled - redirect directly to dashboard
		goto('/mobile/dashboard');
	}
</script>

<svelte:head>
	<title>Mobile Login</title>
</svelte:head>

<div class="screen">
	<div class="auth-box">
		<h1>Log In</h1>
		<p class="subtitle">Welcome back! Please enter your details.</p>

		<form onsubmit={handleLogin}>
			<div class="input-wrap">
				<span class="icon">✉️</span>
				<input type="email" bind:value={email} placeholder="E-mail Address" />
			</div>

			<div class="input-wrap">
				<span class="icon">🔒</span>
				<input type="password" bind:value={password} placeholder="Password" />
			</div>

			<a href="/" class="forgot-link">Forgot password?</a>

			<label class="remember-row">
				<input type="checkbox" bind:checked={rememberMe} />
				<span>Remember me</span>
			</label>

			<button type="submit" class="primary-btn">Log In</button>
		</form>

		<p class="bottom-link">
			Don’t have an account?
			<a href="/mobile/signup">Register here</a>
		</p>
	</div>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: Arial, sans-serif;
		background: linear-gradient(180deg, #eaf3fb 0%, #f8f8f8 55%, #f5f5f5 100%);
		color: #222;
	}

	:global(*) {
		box-sizing: border-box;
	}

	.screen {
		min-height: 100vh;
	min-width: 360px;
		max-width: 430px;
		margin: 0 auto;
		padding: 140px 24px 40px;
	}

	.auth-box {
		width: 100%;
	}

	h1 {
		margin: 0;
		text-align: center;
		font-size: 32px;
		font-weight: 500;
	}

	.subtitle {
		margin: 12px 0 42px;
		text-align: center;
		font-size: 18px;
		color: #333;
		line-height: 1.4;
	}

	form {
		display: flex;
		flex-direction: column;
		gap: 22px;
	}

	.input-wrap {
		height: 62px;
		background: #f7f7f7;
		border: 1px solid #d9d9d9;
		border-radius: 8px;
		display: flex;
		align-items: center;
		padding: 0 18px;
		box-shadow: 0 3px 10px rgba(0, 0, 0, 0.08);
	}

	.icon {
		font-size: 22px;
		margin-right: 14px;
		opacity: 0.55;
	}

	input[type='email'],
	input[type='password'] {
		border: none;
		outline: none;
		background: transparent;
		width: 100%;
		font-size: 18px;
		color: #222;
	}

	input[type='email']::placeholder,
	input[type='password']::placeholder {
		color: #a0a0a0;
	}

	.forgot-link {
		margin-top: -6px;
		color: #6a91c5;
		text-decoration: none;
		font-size: 17px;
	}

	.remember-row {
		display: flex;
		align-items: center;
		gap: 12px;
		font-size: 17px;
		color: #333;
	}

	.remember-row input {
		width: 24px;
		height: 24px;
		accent-color: #8399b6;
	}

	.primary-btn {
		margin-top: 10px;
		height: 68px;
		border: none;
		border-radius: 10px;
		background: #8399b6;
		color: #1f1f1f;
		font-size: 24px;
		font-weight: 700;
		box-shadow: 0 4px 10px rgba(0, 0, 0, 0.12);
		cursor: pointer;
	}

	.bottom-link {
		margin-top: 36px;
		text-align: center;
		font-size: 16px;
		color: #9a9a9a;
	}

	.bottom-link a {
		color: #6a91c5;
		text-decoration: none;
		font-weight: 700;
	}
</style>