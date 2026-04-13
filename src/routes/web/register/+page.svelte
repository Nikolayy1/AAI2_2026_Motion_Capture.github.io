<script lang="ts">
	let fullName: string = $state('');
	let email: string = $state('');
	let password: string = $state('');
	let confirmPassword: string = $state('');

	function handleRegister() {
		if (!fullName || !email || !password || !confirmPassword) {
			alert('Please fill in all fields.');
			return;
		}

		if (password !== confirmPassword) {
			alert('Passwords do not match.');
			return;
		}

		alert(`Registered:\nName: ${fullName}\nEmail: ${email}`);
	}
</script>

<svelte:head>
	<title>Register</title>
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
			<h1>Register</h1>

			<form onsubmit={handleRegister}>
				<div class="field">
					<label for="fullName">Full name</label>
					<input
						id="fullName"
						type="text"
						bind:value={fullName}
						placeholder="Enter your full name"
					/>
				</div>

				<div class="field">
					<label for="email">E-mail address</label>
					<input
						id="email"
						type="email"
						bind:value={email}
						placeholder="Enter your E-mail address"
					/>
				</div>

				<div class="field">
					<label for="password">Password</label>
					<input
						id="password"
						type="password"
						bind:value={password}
						placeholder="Create a password"
					/>
				</div>

				<div class="field">
					<input
						id="confirmPassword"
						type="password"
						bind:value={confirmPassword}
						placeholder="Confirm password"
					/>
				</div>

				<button type="submit" class="primary-btn">Create account</button>

				<div class="divider">
					<span></span>
					<p>or</p>
					<span></span>
				</div>

				<a href="/login" class="secondary-btn">Log in</a>
			</form>
		</div>
	</main>
</div>

<style>
	:global(body) {
	margin: 0;
	font-family: Arial, sans-serif;
	background: linear-gradient(90deg, #f7fbff 0%, #ffffff 100%);
	color: #222;
}

	:global(*) {
		box-sizing: border-box;
	}

	.page {
		min-height: 100vh;
	}

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
	height: 80px;
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

	.content {
		min-height: calc(100vh - 72px);
		display: flex;
		justify-content: center;
		align-items: center;
		padding: 40px 20px;
	}

	.card {
		width: 100%;
		max-width: 425px;
		background: #f8f8f8;
		border-radius: 22px;
		padding: 28px 34px 34px;
		box-shadow: 0 4px 14px rgba(0, 0, 0, 0.16);
	}

	h1 {
		margin: 0 0 26px;
		text-align: center;
		font-size: 28px;
		font-weight: 700;
	}

	form {
		display: flex;
		flex-direction: column;
	}

	.field {
		display: flex;
		flex-direction: column;
		margin-bottom: 18px;
	}

	label {
		font-size: 15px;
		font-weight: 600;
		margin-bottom: 8px;
		color: #303030;
	}

	input {
		width: 100%;
		height: 44px;
		padding: 0 18px;
		border: 1px solid #cfcfcf;
		border-radius: 4px;
		background: #f7f7f7;
		font-size: 14px;
		color: #222;
		outline: none;
		box-shadow: inset 0 1px 1px rgba(0, 0, 0, 0.03);
	}

	input::placeholder {
		color: #a0a0a0;
	}

	input:focus {
		border-color: #8ab2df;
		background: white;
	}

	.primary-btn,
	.secondary-btn {
		width: 100%;
		height: 46px;
		border-radius: 4px;
		font-size: 16px;
		font-weight: 700;
		cursor: pointer;
		text-align: center;
		text-decoration: none;
		display: flex;
		align-items: center;
		justify-content: center;
	}

	.primary-btn {
		margin-top: 8px;
		border: none;
		background: #97bbe8;
		color: #1f1f1f;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12);
	}

	.primary-btn:hover {
		background: #89aedc;
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
		background: #bdbdbd;
	}

	.divider p {
		margin: 0;
		font-size: 15px;
		color: #444;
	}

	.secondary-btn {
		border: 1px solid #d0d0d0;
		background: #f7f7f7;
		color: #222;
		box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
	}

	.secondary-btn:hover {
		background: #efefef;
	}

	@media (max-width: 520px) {
		.topbar {
			padding: 0 16px;
		}

		.brand-text {
			font-size: 18px;
		}

		.logo {
	height: 130px;
	width: auto;
	object-fit: contain;
}

		.card {
			padding: 24px 20px 26px;
		}
	}
</style>