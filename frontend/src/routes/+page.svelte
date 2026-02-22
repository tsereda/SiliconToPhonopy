<script lang="ts">
  const workflows = [
    {
      num: '01',
      title: 'Perovskite Relaxation',
      desc: 'Full ionic + cell relaxation of SrTiO\u2083 with PBE. Learn ISIF, ENCUT, convergence criteria.',
      href: '/workflows/relax',
      badge: 'Relaxation',
      badgeClass: 'badge-blue',
      tags: ['ISIF=3', 'CG', 'PBE'],
    },
    {
      num: '02',
      title: 'Surface Slab Model',
      desc: 'Cut a (hkl) surface, add vacuum, apply selective dynamics. Compute surface energies.',
      href: '/workflows/surface',
      badge: 'Surface',
      badgeClass: 'badge-green',
      tags: ['Miller index', 'Vacuum', 'Dipole'],
    },
    {
      num: '03',
      title: 'Vacancy Formation Energy',
      desc: 'Build a supercell, remove an atom, compute E_f. Learn chemical potentials and finite-size effects.',
      href: '/workflows/vacancy',
      badge: 'Defects',
      badgeClass: 'badge-orange',
      tags: ['Supercell', '\u0394E', '\u03bc'],
    },
    {
      num: '04',
      title: 'PBE vs DFT+U',
      desc: 'Compare standard GGA with Hubbard U correction on NiO. See why PBE fails for correlated oxides.',
      href: '/workflows/dftu',
      badge: 'DFT+U',
      badgeClass: 'badge-purple',
      tags: ['LDAU', 'AFM', 'Band gap'],
    },
    {
      num: '05',
      title: 'DFT-D3 Corrections',
      desc: 'Add Grimme D3 van der Waals corrections to graphite. Compare interlayer distances.',
      href: '/workflows/d3',
      badge: 'vdW',
      badgeClass: 'badge-cyan',
      tags: ['IVDW=12', 'Dispersion', 'Layered'],
    },
    {
      num: '06',
      title: 'Phonon Dispersions',
      desc: 'Compute phonon band structures with Phonopy finite displacements. Detect instabilities.',
      href: '/workflows/phonon',
      badge: 'Phonons',
      badgeClass: 'badge-red',
      tags: ['Phonopy', 'Forces', '\u03c9(q)'],
    },
  ];
</script>

<div class="dashboard">
  <header class="page-header">
    <h1>DFT Workflows for Solid-State Materials</h1>
    <p class="subtitle">
      A hands-on toolkit for learning density functional theory calculations.
      Each workflow generates complete VASP input files with annotated parameters
      and explains common failure modes.
    </p>
  </header>

  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-num">6</div>
      <div class="stat-label">Workflows</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">5</div>
      <div class="stat-label">Crystal types</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">5</div>
      <div class="stat-label">INCAR presets</div>
    </div>
    <div class="stat-card">
      <div class="stat-num">MP</div>
      <div class="stat-label">API integrated</div>
    </div>
  </div>

  <h2 class="section-title">Calculation Workflows</h2>
  <p class="section-desc">Follow these in order for a structured learning path, or jump to any topic.</p>

  <div class="workflow-grid">
    {#each workflows as wf}
      <a href={wf.href} class="workflow-card card">
        <div class="wf-top">
          <span class="wf-num">{wf.num}</span>
          <span class="badge {wf.badgeClass}">{wf.badge}</span>
        </div>
        <h3>{wf.title}</h3>
        <p class="wf-desc">{wf.desc}</p>
        <div class="wf-tags">
          {#each wf.tags as tag}
            <code class="wf-tag">{tag}</code>
          {/each}
        </div>
      </a>
    {/each}
  </div>

  <div class="bottom-cards grid-2">
    <a href="/materials" class="card bottom-link">
      <h3>Materials Project Search</h3>
      <p>Search the MP database for structures, reference energies, and band gaps.
        Download structures and generate VASP inputs directly.</p>
    </a>
    <a href="/guide" class="card bottom-link">
      <h3>Quick-Start Guide</h3>
      <p>Prerequisites, installation, common VASP mistakes, and recommended
        reading for getting started with DFT.</p>
    </a>
  </div>
</div>

<style>
  .dashboard {
    max-width: 960px;
  }

  .page-header {
    margin-bottom: 1.5rem;
  }

  .subtitle {
    color: var(--text-secondary);
    font-size: 0.95rem;
    margin-top: 0.4rem;
    max-width: 640px;
  }

  .stats-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
    margin-bottom: 2rem;
  }

  .stat-card {
    background: var(--bg-card);
    border: 1px solid var(--border-default);
    border-radius: var(--radius);
    padding: 1rem;
    text-align: center;
  }

  .stat-num {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--accent-blue);
  }

  .stat-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .section-title {
    margin-bottom: 0.2rem;
  }

  .section-desc {
    color: var(--text-secondary);
    font-size: 0.88rem;
    margin-bottom: 1rem;
  }

  .workflow-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 0.85rem;
    margin-bottom: 2rem;
  }

  .workflow-card {
    text-decoration: none;
    color: inherit;
    transition: transform 0.12s ease, border-color 0.12s ease;
  }

  .workflow-card:hover {
    transform: translateY(-2px);
    text-decoration: none;
  }

  .wf-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.6rem;
  }

  .wf-num {
    font-family: var(--font-mono);
    font-size: 0.78rem;
    color: var(--text-muted);
    font-weight: 600;
  }

  .workflow-card h3 {
    margin-bottom: 0.35rem;
  }

  .wf-desc {
    font-size: 0.84rem;
    color: var(--text-secondary);
    line-height: 1.5;
    margin-bottom: 0.7rem;
  }

  .wf-tags {
    display: flex;
    gap: 0.4rem;
    flex-wrap: wrap;
  }

  .wf-tag {
    font-size: 0.7rem;
    padding: 0.1em 0.45em;
    background: rgba(88, 166, 255, 0.08);
    color: var(--text-muted);
    border-radius: var(--radius-sm);
  }

  .bottom-cards {
    margin-top: 0.5rem;
  }

  .bottom-link {
    text-decoration: none;
    color: inherit;
  }

  .bottom-link:hover {
    text-decoration: none;
  }

  .bottom-link h3 {
    margin-bottom: 0.3rem;
  }

  .bottom-link p {
    font-size: 0.84rem;
    color: var(--text-secondary);
  }
</style>
