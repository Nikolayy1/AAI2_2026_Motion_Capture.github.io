<script lang="ts">
	import { goto } from '$app/navigation';

	let fullName: string = $state('');
	let email: string = $state('');
	let password: string = $state('');
	let confirmPassword: string = $state('');

	function handleSignup(event: Event) {
		event.preventDefault();

		// Authentication disabled - redirect directly to dashboard
		goto('/mobile/dashboard');
	}
</script>

<svelte:head>
	<title>Mobile Sign Up</title>
</svelte:head>

<div class="screen">
	<div class="auth-box">
		<h1>Create an Account</h1>
		<p class="subtitle">Sign up to get started.</p>

		<form onsubmit={handleSignup}>
			<div class="input-wrap">
				<span class="icon">👤</span>
				<input type="text" bind:value={fullName} placeholder="Full Name" />
			</div>

			<div class="input-wrap">
				<span class="icon">✉️</span>
				<input type="email" bind:value={email} placeholder="E-mail Address" />
			</div>

			<div class="input-wrap">
				<span class="icon">🔒</span>
				<input type="password" bind:value={password} placeholder="Password" />
			</div>

			<div class="input-wrap">
				<span class="icon">🔒</span>
				<input type="password" bind:value={confirmPassword} placeholder="Confirm Password" />
			</div>

			<button type="submit" class="primary-btn">Sign up</button>
		</form>

		<p class="bottom-link">
			Already have an account?
			<a href="/mobile/login">Log in</a>
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
		padding: 120px 24px 40px;
	}

	.auth-box {
		width: 100%;
	}

	h1 {
		margin: 0;
		text-align: center;
		font-size: 30px;
		font-weight: 500;
	}

	.subtitle {
		margin: 10px 0 42px;
		text-align: center;
		font-size: 18px;
		color: #333;
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

	input {
		border: none;
		outline: none;
		background: transparent;
		width: 100%;
		font-size: 18px;
		color: #222;
	}

	input::placeholder {
		color: #a0a0a0;
	}

	.primary-btn {
		margin-top: 18px;
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
		margin-top: 34px;
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