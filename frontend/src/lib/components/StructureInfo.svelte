<script lang="ts">
  let { data }: { data: Record<string, unknown> } = $props();

  /** Flatten a nested object into label/value pairs for display. */
  function flatEntries(obj: Record<string, unknown>, prefix = ''): Array<{ key: string; value: string }> {
    const entries: Array<{ key: string; value: string }> = [];
    for (const [k, v] of Object.entries(obj)) {
      const label = prefix ? `${prefix}.${k}` : k;
      if (v && typeof v === 'object' && !Array.isArray(v)) {
        entries.push(...flatEntries(v as Record<string, unknown>, label));
      } else if (Array.isArray(v)) {
        entries.push({ key: label, value: v.map(String).join(', ') });
      } else {
        entries.push({ key: label, value: String(v ?? '-') });
      }
    }
    return entries;
  }
</script>

<div class="structure-info">
  <table>
    <tbody>
      {#each flatEntries(data) as { key, value }}
        <tr>
          <td class="key-cell">{key}</td>
          <td class="value-cell">{value}</td>
        </tr>
      {/each}
    </tbody>
  </table>
</div>

<style>
  .structure-info {
    border: 1px solid var(--border-default);
    border-radius: var(--radius);
    overflow: hidden;
  }

  .key-cell {
    font-family: var(--font-mono);
    font-size: 0.82rem;
    color: var(--accent-cyan);
    white-space: nowrap;
    width: 1%;
    padding-right: 1.5rem;
  }

  .value-cell {
    font-size: 0.88rem;
    color: var(--text-primary);
    word-break: break-word;
  }
</style>
