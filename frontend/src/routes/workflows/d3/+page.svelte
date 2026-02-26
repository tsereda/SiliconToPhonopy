<script lang="ts">
  import WorkflowForm from '$lib/components/WorkflowForm.svelte';
  import { generateD3 } from '$lib/api';

  let a = $state(2.464);
  let c = $state(6.711);
  let loading = $state(false);
  let result: Record<string, any> | null = $state(null);
  let error: string | null = $state(null);

  async function generate() {
    loading = true;
    error = null;
    try {
      result = await generateD3({ a, c });
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }
</script>

<div class="page">
  <a href="/" class="back-link">&larr; Back to Dashboard</a>

  <WorkflowForm
    title="DFT-D3 van der Waals Corrections"
    description="Compare PBE with and without D3 dispersion correction on graphite."
    badgeLabel="vdW"
    badgeClass="badge-cyan"
    ongenerate={generate}
    {loading}
  >
    <div class="input-group">
      <label for="a-lat">In-plane a (A)</label>
      <input id="a-lat" type="number" step="0.001" bind:value={a} />
    </div>
    <div class="input-group">
      <label for="c-lat">Out-of-plane c (A)</label>
      <input id="c-lat" type="number" step="0.001" bind:value={c} />
    </div>
  </WorkflowForm>

  {#if error}
    <div class="alert alert-error" style="margin-top:1rem">{error}</div>
  {/if}

  {#if result}
    <div class="result-section">
      <h2>Graphite: PBE vs DFT-D3</h2>

      <div class="alert alert-info" style="margin-bottom:1rem">
        <strong>Why vdW corrections?</strong> PBE cannot describe London dispersion forces.
        Graphite layers are held by vdW interactions, so PBE predicts nearly unbound layers
        (c ~ 8+ A instead of the experimental 6.71 A).
      </div>

      <div class="comparison-grid grid-3">
        {#each Object.entries(result.calculations) as [key, calc]}
          {@const c_val = calc as Record<string, any>}
          <div class="card method-card">
            <div class="method-label">{c_val.vdw_correction === 'none' ? 'PBE (no vdW)' : c_val.vdw_correction}</div>
            {#if c_val.IVDW}
              <code class="ivdw-tag">IVDW = {c_val.IVDW}</code>
            {:else}
              <code class="ivdw-tag none">no IVDW</code>
            {/if}
            <div class="method-atoms">{c_val.n_atoms} atoms</div>
          </div>
        {/each}
      </div>

      <div class="card" style="margin-top:1.25rem">
        <h3>Expected Results</h3>
        <table>
          <thead>
            <tr><th>Property</th><th>PBE</th><th>PBE-D3(BJ)</th><th>Experiment</th></tr>
          </thead>
          <tbody>
            <tr><td>c (A)</td><td class="bad">~8+</td><td class="good">6.6-6.8</td><td>6.711</td></tr>
            <tr><td>d_interlayer (A)</td><td class="bad">~4+</td><td class="good">3.3-3.4</td><td>3.356</td></tr>
            <tr><td>Binding (meV/atom)</td><td class="bad">~0</td><td class="good">25-30</td><td>31 &plusmn; 2</td></tr>
            <tr><td>a (A)</td><td>2.47</td><td>2.46</td><td>2.464</td></tr>
          </tbody>
        </table>
      </div>

      <div class="card" style="margin-top:1.25rem">
        <h3>VASP vdW Methods</h3>
        <table>
          <thead>
            <tr><th>IVDW</th><th>Method</th><th>Description</th></tr>
          </thead>
          <tbody>
            <tr><td><code>1</code></td><td>DFT-D2</td><td>Older Grimme, fixed C6</td></tr>
            <tr><td><code>11</code></td><td>DFT-D3(zero)</td><td>Geometry-dependent C6, zero damping</td></tr>
            <tr class="highlight"><td><code>12</code></td><td>DFT-D3(BJ)</td><td>BJ damping (recommended)</td></tr>
            <tr><td><code>20</code></td><td>TS</td><td>Tkatchenko-Scheffler</td></tr>
            <tr><td><code>202</code></td><td>MBD</td><td>Many-body dispersion</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  {/if}
</div>

<style>
  .page { max-width: 860px; }
  .back-link { font-size: 0.85rem; color: var(--text-secondary); display: inline-block; margin-bottom: 1rem; }
  .result-section { margin-top: 1.5rem; }
  .method-card { text-align: center; padding: 1.2rem; }
  .method-label { font-weight: 600; font-size: 0.95rem; margin-bottom: 0.4rem; }
  .ivdw-tag { display: inline-block; margin-bottom: 0.3rem; background: rgba(86, 212, 221, 0.12); color: var(--accent-cyan); padding: 0.15em 0.5em; border-radius: var(--radius-sm); }
  .ivdw-tag.none { color: var(--text-muted); background: rgba(255,255,255,0.05); }
  .method-atoms { font-size: 0.78rem; color: var(--text-muted); }
  .bad { color: var(--accent-red); font-weight: 600; }
  .good { color: var(--accent-green); }
  .highlight td { background: rgba(86, 212, 221, 0.06); }
</style>
