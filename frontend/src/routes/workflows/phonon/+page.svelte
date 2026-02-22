<script lang="ts">
  import WorkflowForm from '$lib/components/WorkflowForm.svelte';
  import { generatePhonon } from '$lib/api';

  let sc_size = $state(2);
  let displacement = $state(0.01);
  let loading = $state(false);
  let result: Record<string, any> | null = $state(null);
  let error: string | null = $state(null);

  let supercell_matrix = $derived([
    [sc_size, 0, 0],
    [0, sc_size, 0],
    [0, 0, sc_size],
  ]);

  async function generate() {
    loading = true;
    error = null;
    try {
      result = await generatePhonon({ supercell_matrix, displacement });
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
    title="Phonon Dispersions"
    description="Compute phonon band structures using Phonopy finite displacements on SrTiO₃."
    badgeLabel="Phonons"
    badgeClass="badge-red"
    ongenerate={generate}
    {loading}
  >
    <div class="input-group">
      <label for="sc-size">Supercell size (NxNxN)</label>
      <select id="sc-size" bind:value={sc_size}>
        <option value={2}>2x2x2 (40 atoms)</option>
        <option value={3}>3x3x3 (135 atoms)</option>
      </select>
    </div>
    <div class="input-group">
      <label for="disp">Displacement (A)</label>
      <input id="disp" type="number" step="0.005" min="0.001" max="0.05" bind:value={displacement} />
    </div>
  </WorkflowForm>

  {#if error}
    <div class="alert alert-error" style="margin-top:1rem">{error}</div>
  {/if}

  {#if result}
    <div class="result-section">
      <h2>Phonopy Displacement Setup</h2>

      <div class="stats-row">
        <div class="card mini-stat">
          <div class="mini-val">{result.n_atoms_primitive}</div>
          <div class="mini-label">Primitive atoms</div>
        </div>
        <div class="card mini-stat">
          <div class="mini-val">{result.n_atoms_supercell}</div>
          <div class="mini-label">Supercell atoms</div>
        </div>
        <div class="card mini-stat">
          <div class="mini-val accent">{result.n_displacements}</div>
          <div class="mini-label">Displacements</div>
        </div>
        <div class="card mini-stat">
          <div class="mini-val">{displacement}</div>
          <div class="mini-label">Displacement (A)</div>
        </div>
      </div>

      <div class="card">
        <h3>Workflow Steps</h3>
        <ol class="steps">
          <li class="done">Generate displaced supercells with Phonopy</li>
          <li class="done">Write VASP input files for each displacement ({result.n_displacements} directories)</li>
          <li>Run VASP force calculations on each displaced supercell</li>
          <li>Collect forces and compute force constants</li>
          <li>Plot phonon band structure and DOS</li>
        </ol>
      </div>

      <div class="card" style="margin-top:1rem">
        <h3>Displacement Directories</h3>
        <div class="disp-grid">
          {#each result.displacement_dirs as dir, i}
            <div class="disp-chip">
              <code>disp-{String(i + 1).padStart(3, '0')}</code>
            </div>
          {/each}
        </div>
      </div>

      <div class="info-cards grid-2">
        <div class="card">
          <h3>Key INCAR Settings</h3>
          <dl class="key-vals">
            <dt>EDIFF</dt><dd>1e-8 (very tight for accurate forces)</dd>
            <dt>LREAL</dt><dd>.FALSE. (required for phonon accuracy)</dd>
            <dt>IBRION</dt><dd>-1 (single-point, no relaxation)</dd>
            <dt>NSW</dt><dd>0 (no ionic steps)</dd>
          </dl>
        </div>
        <div class="card">
          <h3>Interpreting Results</h3>
          <ul class="notes">
            <li><strong>Acoustic modes</strong> start at 0 THz at &Gamma;</li>
            <li><strong>Imaginary frequencies</strong> (negative) = dynamical instability</li>
            <li><strong>LO-TO splitting</strong> at &Gamma; for polar materials</li>
            <li>Structure <em>must</em> be fully relaxed first</li>
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
  .stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1.25rem; }
  .mini-stat { text-align: center; padding: 0.8rem; }
  .mini-val { font-size: 1.4rem; font-weight: 700; color: var(--accent-blue); }
  .mini-val.accent { color: var(--accent-red); }
  .mini-label { font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em; margin-top: 0.15rem; }
  .steps { padding-left: 1.4rem; font-size: 0.88rem; }
  .steps li { padding: 0.3rem 0; color: var(--text-secondary); }
  .steps li.done { color: var(--accent-green); }
  .steps li.done::marker { content: "\2713  "; }
  .disp-grid { display: flex; flex-wrap: wrap; gap: 0.4rem; margin-top: 0.5rem; }
  .disp-chip { background: var(--bg-code); border: 1px solid var(--border-default); border-radius: var(--radius-sm); padding: 0.25rem 0.6rem; }
  .disp-chip code { color: var(--text-secondary); font-size: 0.8rem; }
  .info-cards { margin-top: 1rem; }
  .key-vals { display: grid; grid-template-columns: auto 1fr; gap: 0.3rem 1rem; font-size: 0.85rem; }
  .key-vals dt { font-family: var(--font-mono); color: var(--accent-blue); font-size: 0.8rem; }
  .key-vals dd { color: var(--text-secondary); }
  .notes { list-style: none; font-size: 0.85rem; color: var(--text-secondary); }
  .notes li { padding: 0.25rem 0; }
  .notes strong { color: var(--text-primary); }
</style>
