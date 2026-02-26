<script lang="ts">
  import WorkflowForm from '$lib/components/WorkflowForm.svelte';
  import { generateVacancy } from '$lib/api';

  let sc_a = $state(2);
  let sc_b = $state(2);
  let sc_c = $state(2);
  let vacancy_element = $state('O');
  let loading = $state(false);
  let result: Record<string, any> | null = $state(null);
  let error: string | null = $state(null);

  async function generate() {
    loading = true;
    error = null;
    try {
      result = await generateVacancy({ supercell: [sc_a, sc_b, sc_c], vacancy_element });
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
    title="Vacancy Formation Energy"
    description="Create a supercell with a single vacancy to compute defect formation energy."
    badgeLabel="Defects"
    badgeClass="badge-orange"
    ongenerate={generate}
    {loading}
  >
    <div class="input-group">
      <label for="sc-a">Supercell a</label>
      <input id="sc-a" type="number" min="1" max="4" bind:value={sc_a} />
    </div>
    <div class="input-group">
      <label for="sc-b">Supercell b</label>
      <input id="sc-b" type="number" min="1" max="4" bind:value={sc_b} />
    </div>
    <div class="input-group">
      <label for="sc-c">Supercell c</label>
      <input id="sc-c" type="number" min="1" max="4" bind:value={sc_c} />
    </div>
    <div class="input-group">
      <label for="vac-el">Remove element</label>
      <select id="vac-el" bind:value={vacancy_element}>
        <option value="O">O (Oxygen vacancy)</option>
        <option value="Sr">Sr (A-site vacancy)</option>
        <option value="Ti">Ti (B-site vacancy)</option>
      </select>
    </div>
  </WorkflowForm>

  {#if error}
    <div class="alert alert-error" style="margin-top:1rem">{error}</div>
  {/if}

  {#if result}
    {@const info = result.vacancy_info}
    {@const calcs = result.calculations}
    <div class="result-section">
      <h2>Vacancy Calculation Setup</h2>

      <div class="compare-cards grid-2">
        <div class="card">
          <div class="card-label">Pristine supercell</div>
          <div class="big-num">{calcs.pristine.n_atoms}</div>
          <div class="big-label">atoms</div>
          <p class="card-note">Full {sc_a}&times;{sc_b}&times;{sc_c} supercell</p>
        </div>
        <div class="card">
          <div class="card-label">Defective supercell</div>
          <div class="big-num defective">{calcs.defective.n_atoms}</div>
          <div class="big-label">atoms</div>
          <p class="card-note">1 {info.removed_symbol} atom removed</p>
        </div>
      </div>

      <div class="card" style="margin-top:1rem">
        <h3>Formation Energy Formula</h3>
        <pre><code>E_f = E(defective) - E(pristine) + &mu;({info.removed_symbol})</code></pre>
        <table style="margin-top:0.8rem">
          <thead>
            <tr><th>Condition</th><th>&mu;(O)</th><th>Interpretation</th></tr>
          </thead>
          <tbody>
            <tr><td>O-rich</td><td>&frac12; E(O&sub2;)</td><td>Equilibrium with O&sub2; gas</td></tr>
            <tr><td>O-poor</td><td>&frac12; E(O&sub2;) + &Delta;H/3</td><td>Metal-rich limit</td></tr>
          </tbody>
        </table>
      </div>

      <div class="card" style="margin-top:1rem">
        <h3>Convergence Test</h3>
        <p class="card-note">Compare E_f for different supercell sizes to ensure the defect-defect interaction is negligible:</p>
        <table style="margin-top:0.5rem">
          <thead>
            <tr><th>Supercell</th><th>Atoms</th><th>Status</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>2&times;2&times;2</td><td>40</td>
              <td>{sc_a === 2 && sc_b === 2 && sc_c === 2 ? '← current' : ''}</td>
            </tr>
            <tr>
              <td>3&times;3&times;3</td><td>135</td>
              <td>{sc_a === 3 && sc_b === 3 && sc_c === 3 ? '← current' : ''}</td>
            </tr>
            <tr>
              <td>4&times;4&times;4</td><td>320</td>
              <td>{sc_a === 4 && sc_b === 4 && sc_c === 4 ? '← current' : ''}</td>
            </tr>
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
  .compare-cards { margin-top: 1rem; }
  .card-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.3rem; }
  .big-num { font-size: 2.2rem; font-weight: 700; color: var(--accent-blue); line-height: 1; }
  .big-num.defective { color: var(--accent-orange); }
  .big-label { font-size: 0.82rem; color: var(--text-secondary); }
  .card-note { font-size: 0.82rem; color: var(--text-muted); margin-top: 0.4rem; }
</style>
