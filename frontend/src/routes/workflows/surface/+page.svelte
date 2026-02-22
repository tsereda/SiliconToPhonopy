<script lang="ts">
  import WorkflowForm from '$lib/components/WorkflowForm.svelte';
  import FileViewer from '$lib/components/FileViewer.svelte';
  import { generateSurface } from '$lib/api';

  let miller_h = $state(1);
  let miller_k = $state(0);
  let miller_l = $state(0);
  let min_slab_size = $state(10);
  let min_vacuum_size = $state(15);
  let freeze_bottom = $state(2);
  let loading = $state(false);
  let result: Record<string, any> | null = $state(null);
  let error: string | null = $state(null);
  let activeTab = $state('incar');

  async function generate() {
    loading = true;
    error = null;
    try {
      result = await generateSurface({ miller_h, miller_k, miller_l, min_slab_size, min_vacuum_size, freeze_bottom });
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
    title="Surface Slab Model"
    description="Cut a surface slab from bulk SrTiO₃, add vacuum, and apply selective dynamics."
    badgeLabel="Surface"
    badgeClass="badge-green"
    ongenerate={generate}
    {loading}
  >
    <div class="input-group">
      <label for="miller-h">Miller h</label>
      <input id="miller-h" type="number" min="0" max="3" bind:value={miller_h} />
    </div>
    <div class="input-group">
      <label for="miller-k">Miller k</label>
      <input id="miller-k" type="number" min="0" max="3" bind:value={miller_k} />
    </div>
    <div class="input-group">
      <label for="miller-l">Miller l</label>
      <input id="miller-l" type="number" min="0" max="3" bind:value={miller_l} />
    </div>
    <div class="input-group">
      <label for="slab-size">Slab thickness (A)</label>
      <input id="slab-size" type="number" step="1" bind:value={min_slab_size} />
    </div>
    <div class="input-group">
      <label for="vacuum-size">Vacuum thickness (A)</label>
      <input id="vacuum-size" type="number" step="1" bind:value={min_vacuum_size} />
    </div>
    <div class="input-group">
      <label for="freeze-n">Freeze bottom N layers</label>
      <input id="freeze-n" type="number" min="0" max="5" bind:value={freeze_bottom} />
    </div>
  </WorkflowForm>

  {#if error}
    <div class="alert alert-error" style="margin-top:1rem">{error}</div>
  {/if}

  {#if result}
    <div class="result-section">
      <div class="result-header">
        <h2>({miller_h}{miller_k}{miller_l}) Surface Slab</h2>
        <span class="badge badge-green">{result.n_atoms} atoms</span>
      </div>

      <div class="slab-stats grid-3">
        <div class="card mini-stat">
          <div class="mini-label">Slab thickness</div>
          <div class="mini-val">{result.slab_thickness_A?.toFixed(1)} A</div>
        </div>
        <div class="card mini-stat">
          <div class="mini-label">Vacuum thickness</div>
          <div class="mini-val">{result.vacuum_thickness_A?.toFixed(1)} A</div>
        </div>
        <div class="card mini-stat">
          <div class="mini-label">Formula</div>
          <div class="mini-val">{result.formula}</div>
        </div>
      </div>

      <div class="tabs">
        <button class="tab" class:active={activeTab === 'incar'} onclick={() => activeTab = 'incar'}>INCAR</button>
        <button class="tab" class:active={activeTab === 'poscar'} onclick={() => activeTab = 'poscar'}>POSCAR</button>
        <button class="tab" class:active={activeTab === 'kpoints'} onclick={() => activeTab = 'kpoints'}>KPOINTS</button>
      </div>

      {#if activeTab === 'incar' && result.incar}
        <FileViewer content={result.incar} filename="INCAR" />
      {:else if activeTab === 'poscar' && result.poscar}
        <FileViewer content={result.poscar} filename="POSCAR" />
      {:else if activeTab === 'kpoints' && result.kpoints}
        <FileViewer content={result.kpoints} filename="KPOINTS" />
      {/if}

      <div class="card" style="margin-top:1.25rem">
        <h3>Surface Energy Formula</h3>
        <pre><code>E_surf = (E_slab - N_slab/N_bulk * E_bulk) / (2 * A)</code></pre>
        <p class="formula-note">where A is the surface area and the factor 2 accounts for two surfaces.</p>
      </div>
    </div>
  {/if}
</div>

<style>
  .page { max-width: 860px; }
  .back-link { font-size: 0.85rem; color: var(--text-secondary); display: inline-block; margin-bottom: 1rem; }
  .result-section { margin-top: 1.5rem; }
  .result-header { display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1rem; }
  .slab-stats { margin-bottom: 1.25rem; }
  .mini-stat { text-align: center; padding: 0.8rem; }
  .mini-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em; }
  .mini-val { font-size: 1.15rem; font-weight: 600; color: var(--accent-green); margin-top: 0.2rem; }
  .formula-note { font-size: 0.82rem; color: var(--text-secondary); margin-top: 0.5rem; }
</style>
