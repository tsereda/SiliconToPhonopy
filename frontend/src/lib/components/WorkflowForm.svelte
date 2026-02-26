<script lang="ts">
  import type { Snippet } from 'svelte';

  let {
    title,
    description,
    badgeLabel,
    badgeClass = 'badge-blue',
    ongenerate,
    loading = false,
    children,
  }: {
    title: string;
    description: string;
    badgeLabel: string;
    badgeClass?: string;
    ongenerate: () => void;
    loading?: boolean;
    children?: Snippet;
  } = $props();
</script>

<div class="workflow-form">
  <div class="form-header">
    <div>
      <h2>{title}</h2>
      <p class="form-desc">{description}</p>
    </div>
    <span class="badge {badgeClass}">{badgeLabel}</span>
  </div>

  <div class="form-body">
    {#if children}
      {@render children()}
    {/if}
  </div>

  <div class="form-actions">
    <button class="btn btn-primary" onclick={ongenerate} disabled={loading}>
      {#if loading}
        <span class="spinner"></span>
        Generating...
      {:else}
        Generate VASP Inputs
      {/if}
    </button>
  </div>
</div>

<style>
  .workflow-form {
    background: var(--bg-card);
    border: 1px solid var(--border-default);
    border-radius: var(--radius);
    overflow: hidden;
  }

  .form-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    padding: 1.25rem;
    border-bottom: 1px solid var(--border-muted);
  }

  .form-header h2 {
    margin-bottom: 0.25rem;
  }

  .form-desc {
    color: var(--text-secondary);
    font-size: 0.88rem;
  }

  .form-body {
    padding: 1.25rem;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 1rem;
  }

  .form-actions {
    padding: 1rem 1.25rem;
    border-top: 1px solid var(--border-muted);
    display: flex;
    justify-content: flex-end;
  }
</style>
