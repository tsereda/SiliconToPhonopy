<script lang="ts">
  import { searchMaterials, getMaterialById, type MaterialResult, type MaterialDetail } from '$lib/api';

  let formula = $state('SrTiO3');
  let maxResults = $state(10);
  let loading = $state(false);
  let results: MaterialResult[] = $state([]);
  let error: string | null = $state(null);
  let selectedMaterial: MaterialDetail | null = $state(null);
  let detailLoading = $state(false);

  async function search() {
    loading = true;
    error = null;
    selectedMaterial = null;
    try {
      const data = await searchMaterials(formula, maxResults);
      results = data.results;
      if (results.length === 0) {
        error = `No results found for "${formula}".`;
      }
    } catch (e: any) {
      error = e.message;
      results = [];
    } finally {
      loading = false;
    }
  }

  async function selectMaterial(mpId: string) {
    detailLoading = true;
    try {
      selectedMaterial = await getMaterialById(mpId);
    } catch (e: any) {
      error = e.message;
    } finally {
      detailLoading = false;
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') search();
  }
</script>

<div class="page">
  <h1>Materials Project Search</h1>
  <p class="subtitle">
    Search the Materials Project database for crystal structures, reference energies,
    and computed properties.  Requires <code>MP_API_KEY</code> environment variable on the backend.
  </p>

  <div class="search-bar">
    <div class="input-group" style="flex:1">
      <label for="formula">Chemical formula</label>
      <input id="formula" type="text" bind:value={formula} onkeydown={handleKeydown}
        placeholder="e.g. SrTiO3, NiO, Fe2O3, BaTiO3" />
    </div>
    <div class="input-group">
      <label for="max-res">Max results</label>
      <select id="max-res" bind:value={maxResults}>
        <option value={5}>5</option>
        <option value={10}>10</option>
        <option value={20}>20</option>
      </select>
    </div>
    <button class="btn btn-primary search-btn" onclick={search} disabled={loading || !formula.trim()}>
      {#if loading}
        <span class="spinner"></span>
      {:else}
        Search
      {/if}
    </button>
  </div>

  {#if error}
    <div class="alert alert-error">{error}</div>
  {/if}

  {#if results.length > 0}
    <div class="results-container">
      <div class="results-table">
        <table>
          <thead>
            <tr>
              <th>MP ID</th>
              <th>Formula</th>
              <th>Spacegroup</th>
              <th>E_hull (eV)</th>
              <th>E_form (eV/at)</th>
              <th>Band gap</th>
              <th>Stable</th>
              <th>Mag.</th>
            </tr>
          </thead>
          <tbody>
            {#each results as mat}
              <tr class="clickable" class:selected={selectedMaterial?.material_id === mat.material_id}
                onclick={() => selectMaterial(mat.material_id)}>
                <td><code>{mat.material_id}</code></td>
                <td class="formula-cell">{mat.formula}</td>
                <td>{mat.spacegroup ?? '-'}</td>
                <td>{mat.energy_above_hull_eV?.toFixed(4) ?? '-'}</td>
                <td>{mat.formation_energy_per_atom_eV?.toFixed(4) ?? '-'}</td>
                <td>{mat.band_gap_eV?.toFixed(2) ?? '-'} eV</td>
                <td>
                  {#if mat.is_stable}
                    <span class="badge badge-green">Yes</span>
                  {:else}
                    <span class="badge badge-red">No</span>
                  {/if}
                </td>
                <td>{mat.is_magnetic ? 'Yes' : 'No'}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>

      {#if detailLoading}
        <div class="detail-loading">
          <span class="spinner"></span>
          <span>Loading structure...</span>
        </div>
      {/if}

      {#if selectedMaterial}
        <div class="detail-panel card">
          <div class="detail-header">
            <h3>{selectedMaterial.formula}</h3>
            <code>{selectedMaterial.material_id}</code>
          </div>

          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">Energy per atom</span>
              <span class="detail-value">{selectedMaterial.energy_per_atom_eV?.toFixed(4)} eV</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Formation energy</span>
              <span class="detail-value">{selectedMaterial.formation_energy_per_atom_eV?.toFixed(4)} eV/atom</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">E above hull</span>
              <span class="detail-value">{selectedMaterial.energy_above_hull_eV?.toFixed(4)} eV</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Band gap</span>
              <span class="detail-value">{selectedMaterial.band_gap_eV?.toFixed(2)} eV</span>
            </div>
          </div>

          {#if selectedMaterial.structure}
            <div class="structure-section">
              <h4>Structure</h4>
              <div class="struct-meta">
                <span>{selectedMaterial.structure.n_atoms} atoms</span>
                <span>&bull;</span>
                <span>{selectedMaterial.structure.formula}</span>
              </div>
              <div class="atoms-table-wrap">
                <table class="atoms-table">
                  <thead>
                    <tr><th>#</th><th>Element</th><th>x (A)</th><th>y (A)</th><th>z (A)</th></tr>
                  </thead>
                  <tbody>
                    {#each selectedMaterial.structure.symbols as sym, i}
                      <tr>
                        <td>{i + 1}</td>
                        <td><strong>{sym}</strong></td>
                        <td>{selectedMaterial.structure.positions[i][0].toFixed(4)}</td>
                        <td>{selectedMaterial.structure.positions[i][1].toFixed(4)}</td>
                        <td>{selectedMaterial.structure.positions[i][2].toFixed(4)}</td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .page { max-width: 1050px; }
  .subtitle { color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 1.5rem; }

  .search-bar {
    display: flex;
    gap: 0.75rem;
    align-items: flex-end;
    margin-bottom: 1.5rem;
  }

  .search-btn {
    height: 38px;
  }

  .results-table {
    overflow-x: auto;
    margin-bottom: 1rem;
  }

  .clickable {
    cursor: pointer;
  }

  .clickable:hover td {
    background: rgba(88, 166, 255, 0.08);
  }

  .selected td {
    background: rgba(88, 166, 255, 0.12) !important;
    border-color: rgba(88, 166, 255, 0.2);
  }

  .formula-cell {
    font-weight: 600;
  }

  .detail-loading {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 1rem;
    color: var(--text-secondary);
  }

  .detail-panel {
    margin-top: 0.5rem;
  }

  .detail-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
  }

  .detail-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    gap: 0.75rem;
    margin-bottom: 1rem;
  }

  .detail-item {
    background: var(--bg-code);
    border-radius: var(--radius-sm);
    padding: 0.6rem 0.8rem;
  }

  .detail-label {
    display: block;
    font-size: 0.7rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.2rem;
  }

  .detail-value {
    font-family: var(--font-mono);
    font-size: 0.92rem;
    color: var(--accent-blue);
  }

  .structure-section h4 { margin-bottom: 0.3rem; }
  .struct-meta {
    font-size: 0.82rem;
    color: var(--text-muted);
    margin-bottom: 0.5rem;
    display: flex;
    gap: 0.4rem;
  }

  .atoms-table-wrap {
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid var(--border-default);
    border-radius: var(--radius-sm);
  }

  .atoms-table td, .atoms-table th {
    padding: 0.35rem 0.6rem;
    font-size: 0.82rem;
  }

  .atoms-table td:nth-child(n+3) {
    font-family: var(--font-mono);
    font-size: 0.8rem;
  }
</style>
