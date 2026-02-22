<script lang="ts">
  import { page } from '$app/state';

  const navSections = [
    {
      title: 'Overview',
      items: [
        { href: '/', label: 'Dashboard', icon: '&#9670;' },
        { href: '/guide', label: 'Quick Start', icon: '&#9733;' },
      ],
    },
    {
      title: 'Workflows',
      items: [
        { href: '/workflows/relax', label: 'Perovskite Relax', icon: '&#9632;' },
        { href: '/workflows/surface', label: 'Surface Slab', icon: '&#9644;' },
        { href: '/workflows/vacancy', label: 'Vacancy Energy', icon: '&#9675;' },
        { href: '/workflows/dftu', label: 'PBE vs DFT+U', icon: '&#9830;' },
        { href: '/workflows/d3', label: 'DFT-D3 (vdW)', icon: '&#9776;' },
        { href: '/workflows/phonon', label: 'Phonons', icon: '&#8767;' },
      ],
    },
    {
      title: 'Data',
      items: [
        { href: '/materials', label: 'Materials Project', icon: '&#9906;' },
      ],
    },
  ];

  function isActive(href: string): boolean {
    if (href === '/') return page.url.pathname === '/';
    return page.url.pathname.startsWith(href);
  }
</script>

<nav class="sidebar">
  <div class="sidebar-header">
    <div class="logo">
      <span class="logo-icon">&#9883;</span>
      <div class="logo-text">
        <span class="logo-title">SiliconToPhonopy</span>
        <span class="logo-sub">DFT Workflows</span>
      </div>
    </div>
  </div>

  <div class="sidebar-body">
    {#each navSections as section}
      <div class="nav-section">
        <div class="nav-section-title">{section.title}</div>
        {#each section.items as item}
          <a
            href={item.href}
            class="nav-item"
            class:active={isActive(item.href)}
          >
            <span class="nav-icon">{@html item.icon}</span>
            <span class="nav-label">{item.label}</span>
          </a>
        {/each}
      </div>
    {/each}
  </div>

  <div class="sidebar-footer">
    <div class="footer-text">
      Built with ASE + pymatgen + Phonopy
    </div>
  </div>
</nav>

<style>
  .sidebar {
    width: var(--sidebar-width);
    height: 100vh;
    position: fixed;
    top: 0;
    left: 0;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-default);
    display: flex;
    flex-direction: column;
    z-index: 100;
    overflow-y: auto;
  }

  .sidebar-header {
    padding: 1.1rem 1.2rem;
    border-bottom: 1px solid var(--border-default);
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 0.7rem;
  }

  .logo-icon {
    font-size: 1.6rem;
    color: var(--accent-blue);
    line-height: 1;
  }

  .logo-text {
    display: flex;
    flex-direction: column;
  }

  .logo-title {
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--text-primary);
    line-height: 1.2;
  }

  .logo-sub {
    font-size: 0.7rem;
    color: var(--text-muted);
  }

  .sidebar-body {
    flex: 1;
    padding: 0.5rem 0;
  }

  .nav-section {
    padding: 0.4rem 0;
  }

  .nav-section-title {
    padding: 0.4rem 1.2rem;
    font-size: 0.68rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.45rem 1.2rem;
    font-size: 0.87rem;
    color: var(--text-secondary);
    text-decoration: none;
    transition: all 0.12s ease;
    border-left: 2px solid transparent;
  }

  .nav-item:hover {
    color: var(--text-primary);
    background: rgba(88, 166, 255, 0.05);
    text-decoration: none;
  }

  .nav-item.active {
    color: var(--accent-blue);
    background: rgba(88, 166, 255, 0.08);
    border-left-color: var(--accent-blue);
  }

  .nav-icon {
    width: 1.1rem;
    text-align: center;
    font-size: 0.9rem;
    flex-shrink: 0;
  }

  .sidebar-footer {
    padding: 0.8rem 1.2rem;
    border-top: 1px solid var(--border-default);
  }

  .footer-text {
    font-size: 0.68rem;
    color: var(--text-muted);
    line-height: 1.4;
  }
</style>
