<script lang="ts">
  import WorkflowForm from '$lib/components/WorkflowForm.svelte';
  import FileViewer from '$lib/components/FileViewer.svelte';
  import { generateDftU } from '$lib/api';

  let material = $state('NiO');
  let u_value = $state(6.2);
  let j_value = $state(0.0);
  let loading = $state(false);
  let result: Record<string, any> | null = $state(null);
  let error: string | null = $state(null);
  let activeCalc = $state<'pbe' | 'pbe_plus_u'>('pbe');
  let activeTab = $state('incar');

  async function generate() {
    loading = true;
    error = null;
    try {
      result = await generateDftU({ material, u_value, j_value });
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  let currentExplanation = $derived.by(() => {
    if (!result) return '';
    const calcs = result.calculations as Record<string, any> | undefined;
    return calcs?.[activeCalc]?.explanation ?? '';
  });
</script>

<div class="page">
  <a href="/" class="back-link">&larr; Back to Dashboard</a>

  <WorkflowForm
    title="PBE vs DFT+U Comparison"
    description="Compare standard PBE with Hubbard U correction on a transition-metal oxide."
    badgeLabel="DFT+U"
    badgeClass="badge-purple"
    ongenerate={generate}
    {loading}
  >
    <div class="input-group">
      <label for="mat">Material</label>
      <select id="mat" bind:value={material}>
        <option value="NiO">NiO (Nickel oxide)</option>
        <option value="Fe2O3">Fe₂O₃ (Hematite)</option>
      </select>
    </div>
    <div class="input-group">
      <label for="u-val">U value (eV)</label>
      <input id="u-val" type="number" step="0.1" bind:value={u_value} />
    </div>
    <div class="input-group">
      <label for="j-val">J value (eV)</label>
      <input id="j-val" type="number" step="0.1" bind:value={j_value} />
    </div>
  </WorkflowForm>

  {#if error}
    <div class="alert alert-error" style="margin-top:1rem">{error}</div>
  {/if}

  {#if result}
    <div class="result-section">
      <h2>{result.material}: PBE vs PBE+U</h2>

      <div class="alert alert-warning" style="margin-bottom:1rem">
        <strong>Why DFT+U?</strong> Standard PBE predicts NiO is a <em>metal</em> (zero band gap),
        but experimentally it is a 4.3 eV insulator. DFT+U fixes this by adding on-site Coulomb
        repulsion (U_eff = {(u_value - j_value).toFixed(1)} eV) to the Ni 3d electrons.
      </div>

      <div class="expected-table card">
        <h3>Expected Results Comparison</h3>
        <table>
          <thead>
            <tr><th>Property</th><th>PBE</th><th>PBE+U (U={u_value})</th><th>Experiment</th></tr>
          </thead>
          <tbody>
            <tr><td>Band gap</td><td class="bad">~0 eV (metal!)</td><td class="good">~3-4 eV</td><td>4.3 eV</td></tr>
            <tr><td>Ni moment</td><td>~1 &mu;_B</td><td class="good">~1.7 &mu;_B</td><td>1.9 &mu;_B</td></tr>
            <tr><td>Lattice const.</td><td>~4.10 A</td><td class="good">~4.17 A</td><td>4.177 A</td></tr>
          </tbody>
        </table>
      </div>

      <div class="calc-switcher">
        <button class="btn" class:btn-primary={activeCalc === 'pbe'} onclick={() => { activeCalc = 'pbe'; activeTab = 'incar'; }}>
          PBE (no +U)
        </button>
        <button class="btn" class:btn-primary={activeCalc === 'pbe_plus_u'} onclick={() => { activeCalc = 'pbe_plus_u'; activeTab = 'incar'; }}>
          PBE+U (U_eff = {(u_value - j_value).toFixed(1)} eV)
        </button>
      </div>

      <div class="tabs">
        <button class="tab" class:active={activeTab === 'incar'} onclick={() => activeTab = 'incar'}>INCAR</button>
        <button class="tab" class:active={activeTab === 'explain'} onclick={() => activeTab = 'explain'}>Explanation</button>
      </div>

      {#if activeTab === 'explain'}
        <FileViewer content={currentExplanation} filename="{activeCalc} INCAR Explanation" />
      {/if}

      {#if activeCalc === 'pbe_plus_u'}
        <div class="card" style="margin-top:1rem">
          <h3>LDAU Parameters</h3>
          <p class="card-note" style="margin-bottom:0.6rem">These tags must match species order in POSCAR.</p>
          <pre><code>LDAU    = .TRUE.
LDAUTYPE = 2          # Dudarev: U_eff = U - J
LDAUL   = 2 -1        # 2=d-electrons for Ni, -1=none for O
LDAUU   = {u_value} 0.0      # U values (eV)
LDAUJ   = {j_value} 0.0      # J values (eV)
LDAUPRINT = 2         # Print occupation matrices</code></pre>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .page { max-width: 860px; }
  .back-link { font-size: 0.85rem; color: var(--text-secondary); display: inline-block; margin-bottom: 1rem; }
  .result-section { margin-top: 1.5rem; }
  .expected-table { margin-bottom: 1.25rem; }
  .expected-table h3 { margin-bottom: 0.5rem; }
  .bad { color: var(--accent-red); font-weight: 600; }
  .good { color: var(--accent-green); }
  .calc-switcher { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
  .card-note { font-size: 0.82rem; color: var(--text-muted); }
</style>
