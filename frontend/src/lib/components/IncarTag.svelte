<script lang="ts">
  let { tag, value, comment = '' }: {
    tag: string;
    value: string;
    comment?: string;
  } = $props();
</script>

<div class="incar-tag">
  <code class="tag-name">{tag}</code>
  <span class="tag-eq">=</span>
  <code class="tag-value">{value}</code>
  {#if comment}
    <span class="tag-comment"># {comment}</span>
  {/if}
</div>

<style>
  .incar-tag {
    display: flex;
    align-items: baseline;
    gap: 0.4rem;
    padding: 0.3rem 0;
    font-size: 0.85rem;
    flex-wrap: wrap;
  }

  .tag-name {
    color: var(--accent-blue);
    font-weight: 600;
    background: none;
    padding: 0;
  }

  .tag-eq {
    color: var(--text-muted);
  }

  .tag-value {
    color: var(--accent-green);
    background: none;
    padding: 0;
  }

  .tag-comment {
    color: var(--text-muted);
    font-size: 0.78rem;
    font-style: italic;
  }
</style>
