<script lang="ts">
	let isMenuOpen: boolean = $state(false);

	const tasks = [
		{
			title: 'Sit-to-Stand',
			description: 'Stand up from a chair without using hands.',
			status: 'start'
		},
		{
			title: 'Balance Test',
			description: 'Stand on one leg for at least 10 seconds.',
			status: 'start'
		},
		{
			title: 'Walk Test',
			description: 'Walk straight for 5 meters at a normal pace.',
			status: 'done'
		}
	];
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
			<a href="/mobile" class="drawer-item">↪ Logout</a>
		</div>
	{/if}

	<main class="content">
		<div class="info-card">
			<p class="info-title">Record standardized gait tasks for AI analysis.</p>
			<p class="info-subtitle">Select a task below to begin a new recording</p>
		</div>

		<h2>Standardized Gait Tasks</h2>

		<div class="task-list">
			{#each tasks as task}
				<div class="task-card">
					<h3>{task.title}</h3>
					<p>{task.description}</p>

					{#if task.status === 'start'}
						<button type="button" class="task-btn">Start recording</button>
					{:else}
						<div class="completed">✓ Completed</div>
					{/if}
				</div>
			{/each}
		</div>
	</main>
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
		max-width: 430px;
	min-width: 360px;
		margin: 0 auto;
		background: #f5f5f5;
		position: relative;
		overflow-x: hidden;
	}

	.topbar {
		height: 84px;
		background: #f6f6f6;
		border-bottom: 1px solid #dddddd;
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
		font-size: 30px;
		cursor: pointer;
		color: #222;
	}

	.topbar h1 {
		margin: 0;
		font-size: 28px;
		font-weight: 700;
	}

	.content {
		padding: 22px 20px 40px;
	}

	.info-card {
		background: #ffffff;
		border: 1px solid #dddddd;
		border-radius: 10px;
		padding: 18px 16px;
		box-shadow: 0 3px 8px rgba(0, 0, 0, 0.1);
		margin-bottom: 24px;
	}

	.info-title {
		margin: 0 0 12px;
		text-align: center;
		font-size: 19px;
		font-weight: 500;
	}

	.info-subtitle {
		margin: 0;
		text-align: center;
		font-size: 17px;
	}

	h2 {
		margin: 0 0 16px;
		font-size: 22px;
		font-weight: 500;
	}

	.task-list {
		display: flex;
		flex-direction: column;
		gap: 18px;
	}

	.task-card {
		background: #ffffff;
		border: 1px solid #dddddd;
		border-radius: 10px;
		padding: 14px 14px 16px;
		box-shadow: 0 3px 8px rgba(0, 0, 0, 0.1);
	}

	.task-card h3 {
		margin: 0 0 10px;
		text-align: center;
		font-size: 22px;
		font-weight: 500;
	}

	.task-card p {
		margin: 0 0 14px;
		text-align: center;
		font-size: 17px;
		line-height: 1.35;
	}

	.task-btn {
		width: 100%;
		height: 46px;
		border: 1px solid #d6d6d6;
		border-radius: 8px;
		background: #d7e8fa;
		color: #5c89c7;
		font-size: 16px;
		font-weight: 500;
		cursor: pointer;
	}

	.completed {
		width: 100%;
		height: 46px;
		border: 1px solid #d6d6d6;
		border-radius: 8px;
		background: #ffffff;
		display: flex;
		align-items: center;
		justify-content: center;
		font-size: 18px;
		font-weight: 500;
		color: #222;
	}

	.overlay {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.08);
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
		background: #f8f8f8;
		border-right: 1px solid #dddddd;
		box-shadow: 4px 0 12px rgba(0, 0, 0, 0.08);
		z-index: 30;
		padding: 26px 20px;
	}

	.drawer-item {
		text-decoration: none;
		color: #222;
		font-size: 18px;
		font-weight: 500;
	}
</style>