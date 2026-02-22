<script lang="ts">
  const mistakes = [
    { problem: 'ENCUT too low', symptom: 'Pulay stress warning', fix: 'Increase to 1.3x ENMAX' },
    { problem: 'Not enough k-points', symptom: 'Energy not converged', fix: 'Increase k-point density' },
    { problem: 'EDIFF too loose', symptom: 'Noisy forces', fix: 'Tighten to 1e-6 or 1e-8' },
    { problem: 'LREAL=Auto for phonons', symptom: 'Wrong frequencies', fix: 'Use LREAL=.FALSE.' },
    { problem: 'No ISPIN=2 for magnetic', symptom: 'Wrong ground state', fix: 'Add ISPIN=2, set MAGMOM' },
    { problem: 'NSW too small', symptom: '"not converged"', fix: 'Increase NSW or restart from CONTCAR' },
    { problem: 'Wrong POTCAR order', symptom: 'Scrambled structure', fix: 'Match species order in POSCAR' },
    { problem: 'NPAR/KPAR wrong', symptom: 'Slow or crash', fix: 'KPAR divides k-points, NPAR divides bands' },
  ];

  const reading = [
    { title: 'Sholl & Steckel: "DFT: A Practical Introduction"', desc: 'Best intro textbook for DFT in materials science.' },
    { title: 'Martin: "Electronic Structure"', desc: 'More rigorous theoretical foundation for plane-wave DFT.' },
    { title: 'VASP Wiki', desc: 'Official documentation for all INCAR tags and calculation setups.' },
    { title: 'Materials Project Docs', desc: 'API documentation, data descriptions, and methodology.' },
    { title: 'Phonopy Documentation', desc: 'Phonon calculation methodology and tutorials.' },
  ];
</script>

<div class="page">
  <h1>Quick-Start Guide</h1>
  <p class="subtitle">Everything you need to get started with DFT calculations for solid-state materials.</p>

  <section class="section">
    <h2>Prerequisites</h2>
    <div class="card">
      <h3>Python environment</h3>
      <pre><code>conda create -n dft python=3.11
conda activate dft
pip install ase pymatgen phonopy mp-api fastapi uvicorn numpy scipy matplotlib</code></pre>
    </div>

    <div class="card" style="margin-top:0.75rem">
      <h3>VASP (commercial license required)</h3>
      <p class="card-text">Get access through your university or research group. See <a href="https://www.vasp.at/">vasp.at</a>.</p>
    </div>

    <div class="card" style="margin-top:0.75rem">
      <h3>Materials Project API key</h3>
      <ol class="card-list">
        <li>Create a free account at <a href="https://materialsproject.org">materialsproject.org</a></li>
        <li>Go to Dashboard &rarr; API &rarr; Generate API Key</li>
        <li>Set the environment variable:</li>
      </ol>
      <pre><code>export MP_API_KEY="your_key_here"</code></pre>
    </div>
  </section>

  <section class="section">
    <h2>Generate All Workflows</h2>
    <div class="card">
      <pre><code>cd backend
pip install -r requirements.txt
python -m dft_workflows.tutorials.run_all_workflows --output-dir ./my_calculations</code></pre>
      <p class="card-text" style="margin-top:0.5rem">
        This creates six directories with complete VASP inputs and READMEs.
      </p>
    </div>
  </section>

  <section class="section">
    <h2>Learning Path</h2>
    <div class="path-grid">
      <a href="/workflows/relax" class="path-step card">
        <span class="step-num">01</span>
        <span class="step-title">Perovskite Relax</span>
        <span class="step-desc">Basic relaxation</span>
      </a>
      <div class="path-arrow">&rarr;</div>
      <a href="/workflows/surface" class="path-step card">
        <span class="step-num">02</span>
        <span class="step-title">Surface Slab</span>
        <span class="step-desc">Surface modelling</span>
      </a>
      <div class="path-arrow">&rarr;</div>
      <a href="/workflows/vacancy" class="path-step card">
        <span class="step-num">03</span>
        <span class="step-title">Vacancy E_f</span>
        <span class="step-desc">Defect calculations</span>
      </a>
      <div class="path-arrow">&rarr;</div>
      <a href="/workflows/dftu" class="path-step card">
        <span class="step-num">04</span>
        <span class="step-title">DFT+U</span>
        <span class="step-desc">Correlated materials</span>
      </a>
      <div class="path-arrow">&rarr;</div>
      <a href="/workflows/d3" class="path-step card">
        <span class="step-num">05</span>
        <span class="step-title">DFT-D3</span>
        <span class="step-desc">vdW corrections</span>
      </a>
      <div class="path-arrow">&rarr;</div>
      <a href="/workflows/phonon" class="path-step card">
        <span class="step-num">06</span>
        <span class="step-title">Phonons</span>
        <span class="step-desc">Lattice dynamics</span>
      </a>
    </div>
  </section>

  <section class="section">
    <h2>Common VASP Mistakes</h2>
    <div class="card" style="padding:0">
      <table>
        <thead>
          <tr><th>Problem</th><th>Symptom</th><th>Fix</th></tr>
        </thead>
        <tbody>
          {#each mistakes as m}
            <tr>
              <td><strong>{m.problem}</strong></td>
              <td class="symptom">{m.symptom}</td>
              <td>{m.fix}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </section>

  <section class="section">
    <h2>API Endpoints</h2>
    <div class="card">
      <p class="card-text">Start the backend: <code>uvicorn si_api:app --reload</code></p>
      <p class="card-text">Interactive docs: <code>http://localhost:8000/docs</code></p>
      <table style="margin-top:0.75rem">
        <thead>
          <tr><th>Method</th><th>Endpoint</th><th>Description</th></tr>
        </thead>
        <tbody>
          <tr><td><code>POST</code></td><td><code>/workflows/relax</code></td><td>Perovskite relaxation</td></tr>
          <tr><td><code>POST</code></td><td><code>/workflows/surface</code></td><td>Surface slab</td></tr>
          <tr><td><code>POST</code></td><td><code>/workflows/vacancy</code></td><td>Vacancy formation</td></tr>
          <tr><td><code>POST</code></td><td><code>/workflows/dftu</code></td><td>PBE vs DFT+U</td></tr>
          <tr><td><code>POST</code></td><td><code>/workflows/d3</code></td><td>DFT-D3 graphite</td></tr>
          <tr><td><code>POST</code></td><td><code>/workflows/phonon</code></td><td>Phonon dispersions</td></tr>
          <tr><td><code>GET</code></td><td><code>/materials/{'<formula>'}</code></td><td>Search Materials Project</td></tr>
          <tr><td><code>GET</code></td><td><code>/materials/id/{'<mp_id>'}</code></td><td>Get by MP ID</td></tr>
        </tbody>
      </table>
    </div>
  </section>

  <section class="section">
    <h2>Recommended Reading</h2>
    <div class="reading-grid">
      {#each reading as book}
        <div class="card reading-card">
          <h4>{book.title}</h4>
          <p>{book.desc}</p>
        </div>
      {/each}
    </div>
  </section>
</div>

<style>
  .page { max-width: 900px; }
  .subtitle { color: var(--text-secondary); font-size: 0.92rem; margin-bottom: 1.5rem; }
  .section { margin-bottom: 2rem; }
  .section h2 { margin-bottom: 0.75rem; }

  .card-text { font-size: 0.88rem; color: var(--text-secondary); }
  .card-list { padding-left: 1.3rem; font-size: 0.88rem; color: var(--text-secondary); margin-bottom: 0.5rem; }
  .card-list li { padding: 0.15rem 0; }

  .path-grid {
    display: flex;
    align-items: center;
    gap: 0;
    flex-wrap: wrap;
    row-gap: 0.5rem;
  }

  .path-step {
    text-align: center;
    padding: 0.8rem 0.6rem;
    min-width: 100px;
    text-decoration: none;
    color: inherit;
    flex-shrink: 0;
  }

  .path-step:hover { text-decoration: none; }

  .step-num {
    display: block;
    font-family: var(--font-mono);
    font-size: 0.72rem;
    color: var(--text-muted);
  }

  .step-title {
    display: block;
    font-weight: 600;
    font-size: 0.88rem;
    margin: 0.15rem 0;
  }

  .step-desc {
    display: block;
    font-size: 0.72rem;
    color: var(--text-secondary);
  }

  .path-arrow {
    color: var(--text-muted);
    font-size: 1.2rem;
    padding: 0 0.15rem;
  }

  .symptom { color: var(--accent-orange); }

  .reading-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 0.75rem;
  }

  .reading-card h4 { font-size: 0.9rem; margin-bottom: 0.25rem; }
  .reading-card p { font-size: 0.82rem; color: var(--text-secondary); }
</style>
