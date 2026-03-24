<script lang="ts">
	let src: string | null = $state(null);
	let currentTime: number = $state(0);
</script>

<input 
	type="file" 
	accept="video/*" 
	onchange={(e) => {
		const input = e.currentTarget as HTMLInputElement;
		const file = input.files?.[0];
		if (file) {
			if (src) URL.revokeObjectURL(src);
			src = URL.createObjectURL(file);
			console.log('src set to', src);
		}
	}} 
/>

{#if src}
  <!-- svelte-ignore a11y-media-has-caption -->
  <video {src} bind:currentTime controls preload="metadata" />
  <p>
    Time: {currentTime}
  </p>
{/if}

<style>
	video {
		display: block;
		width: 100%;
		max-width: 800px;
		margin: 1rem 0;
	}
</style>