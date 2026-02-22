const API_BASE = 'http://localhost:8000';

export interface AtomsData {
  symbols: string[];
  positions: number[][];
  cell: number[][];
  pbc: boolean[];
  formula: string;
  n_atoms: number;
}

export interface WorkflowResult {
  formula?: string;
  n_atoms?: number;
  output_dir?: string;
  explanation?: string;
  incar?: string;
  poscar?: string;
  kpoints?: string;
  files?: Record<string, string>;
  [key: string]: unknown;
}

export interface MaterialResult {
  material_id: string;
  formula: string;
  energy_above_hull_eV: number | null;
  formation_energy_per_atom_eV: number | null;
  band_gap_eV: number | null;
  is_stable: boolean;
  n_sites: number;
  spacegroup: string | null;
  is_magnetic: boolean;
}

export interface MaterialSearchResponse {
  formula: string;
  results: MaterialResult[];
}

export interface MaterialDetail {
  material_id: string;
  formula: string;
  energy_per_atom_eV: number;
  formation_energy_per_atom_eV: number;
  energy_above_hull_eV: number;
  band_gap_eV: number;
  is_stable: boolean;
  structure: AtomsData;
}

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error: ${res.status}`);
  }
  return res.json();
}

// ---- Structure builders ----

export function buildPerovskite(A = 'Sr', B = 'Ti', a = 3.905): Promise<AtomsData> {
  return apiFetch('/structures/perovskite', {
    method: 'POST',
    body: JSON.stringify({ A, B, a }),
  });
}

export function buildGraphite(a = 2.464, c = 6.711): Promise<AtomsData> {
  return apiFetch('/structures/graphite', {
    method: 'POST',
    body: JSON.stringify({ a, c }),
  });
}

// ---- Workflow generators ----

export function generateRelax(params: {
  A?: string; B?: string; a?: number; encut?: number; kpoints_density?: number;
}): Promise<WorkflowResult> {
  return apiFetch('/workflows/relax', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export function generateSurface(params: {
  miller_h?: number; miller_k?: number; miller_l?: number;
  min_slab_size?: number; min_vacuum_size?: number; freeze_bottom?: number;
}): Promise<WorkflowResult> {
  return apiFetch('/workflows/surface', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export function generateVacancy(params: {
  supercell?: number[]; vacancy_element?: string;
}): Promise<WorkflowResult> {
  return apiFetch('/workflows/vacancy', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export function generateDftU(params: {
  material?: string; u_value?: number; j_value?: number;
}): Promise<WorkflowResult> {
  return apiFetch('/workflows/dftu', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export function generateD3(params: {
  a?: number; c?: number;
}): Promise<WorkflowResult> {
  return apiFetch('/workflows/d3', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

export function generatePhonon(params: {
  supercell_matrix?: number[][]; displacement?: number;
}): Promise<WorkflowResult> {
  return apiFetch('/workflows/phonon', {
    method: 'POST',
    body: JSON.stringify(params),
  });
}

// ---- Materials Project ----

export function searchMaterials(formula: string, maxResults = 10): Promise<MaterialSearchResponse> {
  return apiFetch(`/materials/${encodeURIComponent(formula)}?max_results=${maxResults}`);
}

export function getMaterialById(mpId: string): Promise<MaterialDetail> {
  return apiFetch(`/materials/id/${encodeURIComponent(mpId)}`);
}

// ---- Silicon (original endpoint) ----

export function getSiStructure(): Promise<{ atoms: AtomsData; energy: number | null }> {
  return apiFetch('/si_structure');
}
