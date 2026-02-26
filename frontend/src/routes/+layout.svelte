<script lang="ts">
  import '../app.css';
  import Nav from '$lib/components/Nav.svelte';

  let { children } = $props();
</script>

<svelte:head>
  <title>SiliconToPhonopy - DFT Workflows</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin="anonymous">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
</svelte:head>

<div class="app-layout">
  <Nav />
  <main class="main-content">
    {@render children()}
  </main>
</div>

<style>
  .app-layout {
    display: flex;
    min-height: 100vh;
  }

  .main-content {
    margin-left: var(--sidebar-width);
    flex: 1;
    padding: 2rem;
    max-width: calc(100vw - var(--sidebar-width));
  }
</style>
