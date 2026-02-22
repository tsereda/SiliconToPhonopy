<script lang="ts">
  let { content, filename = '', language = '' }: {
    content: string;
    filename?: string;
    language?: string;
  } = $props();

  let copied = $state(false);

  function copyToClipboard() {
    navigator.clipboard.writeText(content);
    copied = true;
    setTimeout(() => { copied = false; }, 2000);
  }
</script>

<div class="file-viewer">
  <div class="file-header">
    <span class="file-name">{filename}</span>
    <button class="btn btn-sm" onclick={copyToClipboard}>
      {copied ? 'Copied!' : 'Copy'}
    </button>
  </div>
  <pre class="file-content"><code>{content}</code></pre>
</div>

<style>
  .file-viewer {
    border: 1px solid var(--border-default);
    border-radius: var(--radius);
    overflow: hidden;
  }

  .file-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0.8rem;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-default);
  }

  .file-name {
    font-family: var(--font-mono);
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .file-content {
    margin: 0;
    border: none;
    border-radius: 0;
    max-height: 500px;
    overflow-y: auto;
  }
</style>
