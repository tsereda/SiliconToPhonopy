<script lang="ts">
  import WorkflowForm from '$lib/components/WorkflowForm.svelte';
  import FileViewer from '$lib/components/FileViewer.svelte';
  import { generateRelax } from '$lib/api';

  let A = $state('Sr');
  let B = $state('Ti');
  let a = $state(3.905);
  let encut = $state(520);
  let kpoints_density = $state(40);
  let loading = $state(false);
  let result: Record<string, any> | null = $state(null);
  let error: string | null = $state(null);
  let activeTab = $state('incar');

  async function generate() {
    loading = true;
    error = null;
    try {
      result = await generateRelax({ A, B, a, encut, kpoints_density });
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
    title="Perovskite Relaxation"
    description="Full structural relaxation (ions + cell shape + volume) of a cubic ABO₃ perovskite."
    badgeLabel="Relaxation"
    badgeClass="badge-blue"
    ongenerate={generate}
    {loading}
  >
    <div class="input-group">
      <label for="a-site">A-site cation</label>
      <select id="a-site" bind:value={A}>
        <option value="Sr">Sr (Strontium)</option>
        <option value="Ba">Ba (Barium)</option>
        <option value="Pb">Pb (Lead)</option>
        <option value="Ca">Ca (Calcium)</option>
      </select>
    </div>
    <div class="input-group">
      <label for="b-site">B-site cation</label>
      <select id="b-site" bind:value={B}>
        <option value="Ti">Ti (Titanium)</option>
        <option value="Zr">Zr (Zirconium)</option>
        <option value="Nb">Nb (Niobium)</option>
      </select>
    </div>
    <div class="input-group">
      <label for="lat-const">Lattice constant (A)</label>
      <input id="lat-const" type="number" step="0.001" bind:value={a} />
    </div>
    <div class="input-group">
      <label for="encut-val">ENCUT (eV)</label>
      <input id="encut-val" type="number" step="10" bind:value={encut} />
    </div>
    <div class="input-group">
      <label for="kpt-dens">k-point density</label>
      <input id="kpt-dens" type="number" step="5" bind:value={kpoints_density} />
    </div>
  </WorkflowForm>

  {#if error}
    <div class="alert alert-error" style="margin-top:1rem">{error}</div>
  {/if}

  {#if result}
    <div class="result-section">
      <div class="result-header">
        <h2>Generated Inputs: {result.formula}</h2>
        <span class="badge badge-green">{result.n_atoms} atoms</span>
      </div>

      <div class="tabs">
        <button class="tab" class:active={activeTab === 'incar'} onclick={() => activeTab = 'incar'}>INCAR</button>
        <button class="tab" class:active={activeTab === 'poscar'} onclick={() => activeTab = 'poscar'}>POSCAR</button>
        <button class="tab" class:active={activeTab === 'kpoints'} onclick={() => activeTab = 'kpoints'}>KPOINTS</button>
        <button class="tab" class:active={activeTab === 'explain'} onclick={() => activeTab = 'explain'}>Explanation</button>
      </div>

      {#if activeTab === 'incar' && result.incar}
        <FileViewer content={result.incar} filename="INCAR" />
      {:else if activeTab === 'poscar' && result.poscar}
        <FileViewer content={result.poscar} filename="POSCAR" />
      {:else if activeTab === 'kpoints' && result.kpoints}
        <FileViewer content={result.kpoints} filename="KPOINTS" />
      {:else if activeTab === 'explain' && result.explanation}
        <FileViewer content={result.explanation} filename="INCAR Explanation" />
      {/if}

      <div class="info-cards grid-2">
        <div class="card">
          <h3>Key Settings</h3>
          <dl class="key-vals">
            <dt>ISIF</dt><dd>3 (relax ions + cell shape + volume)</dd>
            <dt>IBRION</dt><dd>2 (conjugate gradient)</dd>
            <dt>ENCUT</dt><dd>{encut} eV</dd>
            <dt>EDIFFG</dt><dd>-0.01 eV/A (force criterion)</dd>
          </dl>
        </div>
        <div class="card">
          <h3>Common Pitfalls</h3>
          <ul class="pitfalls">
            <li><strong>Pulay stress</strong> &mdash; increase ENCUT to 600+ eV</li>
            <li><strong>Symmetry breaking</strong> &mdash; add ISYM = 2</li>
            <li><strong>Not converged</strong> &mdash; increase NSW or restart from CONTCAR</li>
          </ul>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .page { max-width: 860px; }
  .back-link { font-size: 0.85rem; color: var(--text-secondary); display: inline-block; margin-bottom: 1rem; }
  .result-section { margin-top: 1.5rem; }
  .result-header { display: flex; align-items: center; gap: 0.8rem; margin-bottom: 1rem; }
  .info-cards { margin-top: 1.25rem; }
  .key-vals { display: grid; grid-template-columns: auto 1fr; gap: 0.3rem 1rem; font-size: 0.88rem; }
  .key-vals dt { font-family: var(--font-mono); color: var(--accent-blue); font-size: 0.82rem; }
  .key-vals dd { color: var(--text-secondary); }
  .pitfalls { list-style: none; font-size: 0.85rem; color: var(--text-secondary); }
  .pitfalls li { padding: 0.25rem 0; }
  .pitfalls strong { color: var(--accent-orange); }
</style>
