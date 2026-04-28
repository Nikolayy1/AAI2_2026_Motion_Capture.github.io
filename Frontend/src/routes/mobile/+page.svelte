<svelte:head>
	<title>Mobile Welcome</title>
</svelte:head>

<div class="screen">
	<div class="top-space"></div>

	<div class="center-text">
		<h1>Welcome to<br />Biomechanics 4 All</h1>
	</div>

	<div class="bottom-actions">
		<a href="/mobile/signup" class="primary-btn">Sign up</a>
		<a href="/mobile/login" class="secondary-btn">Log In</a>
	</div>
</div>

<style>
	:global(body) {
		margin: 0;
		font-family: Arial, sans-serif;
		background: #f5f5f5;
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
		padding: 32px 24px 56px;
		display: flex;
		flex-direction: column;
		background: #f5f5f5;
	}

	.top-space {
		height: 60px;
	}

	.center-text {
		flex: 1;
		display: flex;
		align-items: flex-start;
		justify-content: center;
		padding-top: 60px;
	}

	h1 {
		margin: 0;
		text-align: center;
		font-size: 38px;
		font-weight: 500;
		line-height: 1.25;
	}

	.bottom-actions {
		display: flex;
		flex-direction: column;
		gap: 20px;
	}

	.primary-btn,
	.secondary-btn {
		width: 100%;
		height: 68px;
		border-radius: 12px;
		display: flex;
		align-items: center;
		justify-content: center;
		text-decoration: none;
		font-size: 24px;
		font-weight: 700;
		box-shadow: 0 3px 8px rgba(0, 0, 0, 0.12);
	}

	.primary-btn {
		background: #a9c4e8;
		color: #1f1f1f;
	}

	.secondary-btn {
		background: #ffffff;
		color: #1f1f1f;
		border: 1px solid #ececec;
	}
</style>