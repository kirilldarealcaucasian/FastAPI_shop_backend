<script lang="ts">
	import '$lib/../app.css';
	import { theme } from '$lib/stores/theme';

	let { children } = $props();

	$effect(() => {
		theme.init();
	});
</script>

<svelte:head>
	<link rel="preconnect" href="https://fonts.googleapis.com" />
	<link rel="preconnect" href="https://fonts.gstatic.com" />
	<link
		href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@600;700&display=swap"
		rel="stylesheet"
	/>
</svelte:head>

<div class="body-bg body-fg min-h-screen font-sans antialiased">
	{@render children()}
</div>
