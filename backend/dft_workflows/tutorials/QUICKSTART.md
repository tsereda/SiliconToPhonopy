# DFT Calculations Quick-Start Guide

A step-by-step guide for graduate students learning density functional theory
calculations on solid-state materials.

## Prerequisites

### Software you need
```bash
# Python packages (install in a conda environment)
conda create -n dft python=3.11
conda activate dft
pip install ase pymatgen phonopy mp-api fastapi uvicorn numpy scipy matplotlib

# VASP (commercial license required)
# Get access through your university or research group
# https://www.vasp.at/

# Optional: GPAW (open-source DFT, good for learning)
conda install -c conda-forge gpaw
```

### Materials Project API key
1. Create a free account at https://materialsproject.org
2. Go to Dashboard -> API -> Generate API Key
3. Add to your shell profile:
```bash
echo 'export MP_API_KEY="your_key_here"' >> ~/.bashrc
source ~/.bashrc
```

## Project Structure

```
backend/
├── si_api.py                          # FastAPI server (all endpoints)
├── si_scf.py                          # Original Si SCF calculation
├── requirements.txt                   # Python dependencies
└── dft_workflows/
    ├── core/
    │   ├── crystal_builders.py        # Build crystal structures
    │   ├── vasp_io.py                 # VASP input/output handling
    │   └── materials_project.py       # Materials Project API client
    ├── workflows/
    │   ├── perovskite_relaxation.py   # Workflow 1: SrTiO3 relaxation
    │   ├── surface_slab.py            # Workflow 2: Surface model
    │   ├── vacancy_formation.py       # Workflow 3: Vacancy E_f
    │   ├── dft_plus_u_comparison.py   # Workflow 4: PBE vs DFT+U
    │   ├── dft_d3_graphite.py         # Workflow 5: vdW corrections
    │   └── phonon_dispersion.py       # Workflow 6: Phonon dispersions
    └── tutorials/
        ├── run_all_workflows.py       # Generate all VASP inputs at once
        ├── materials_project_examples.py  # MP API tutorial
        └── QUICKSTART.md              # This file
```

## Getting Started

### Step 1: Generate all VASP input files
```bash
cd backend
python -m dft_workflows.tutorials.run_all_workflows --output-dir ./my_calculations
```

This creates six calculation directories with complete VASP inputs and
explanatory READMEs.

### Step 2: Start with the perovskite relaxation
```bash
cd my_calculations/01_SrTiO3_relax
cat README.md     # Read the explanation
cat INCAR         # Examine the input parameters
cat POSCAR        # Look at the crystal structure
cat KPOINTS       # Check the k-point grid
cat POTCAR_REFERENCE  # See which POTCARs you need
```

### Step 3: Run the API server (optional, for web interface)
```bash
cd backend
uvicorn si_api:app --reload --port 8000
# API docs at http://localhost:8000/docs
```

## The Six Workflows

### 1. Perovskite Relaxation (SrTiO3)
**Teaches**: Full structural relaxation, ISIF settings, convergence criteria

Key concepts:
- ISIF=3 relaxes ions, cell shape, AND cell volume
- ENCUT must be high enough to avoid Pulay stress
- Always check convergence: `grep "reached required accuracy" OUTCAR`

### 2. Surface Slab Model
**Teaches**: Miller indices, vacuum layers, selective dynamics, surface energy

Key concepts:
- Surfaces need vacuum (15-20 A) and enough slab layers (5-9)
- Freeze bottom layers with selective dynamics (F F F)
- Use LDIPOL/IDIPOL for dipole correction on asymmetric slabs
- Surface energy: E_surf = (E_slab - n*E_bulk) / (2*A)

### 3. Vacancy Formation Energy
**Teaches**: Supercell approach, point defects, chemical potentials

Key concepts:
- Create a supercell, remove one atom, relax
- E_f = E(defective) - E(pristine) + mu(removed_atom)
- Chemical potential mu depends on growth conditions (O-rich vs O-poor)
- Converge E_f vs supercell size (2x2x2, 3x3x3, ...)

### 4. PBE vs DFT+U (NiO)
**Teaches**: Failure of GGA for correlated materials, Hubbard U correction

Key concepts:
- PBE predicts NiO is a metal (wrong! it's a 4.3 eV insulator)
- DFT+U (LDAU=.TRUE.) adds on-site Coulomb repulsion to d-electrons
- LDAUL, LDAUU, LDAUJ must be set per species in POSCAR order
- NiO is antiferromagnetic: set ISPIN=2 and MAGMOM carefully

### 5. DFT-D3 Corrections (Graphite)
**Teaches**: Van der Waals interactions, dispersion corrections

Key concepts:
- PBE cannot describe London dispersion forces
- Just add IVDW=12 to INCAR for DFT-D3(BJ) correction
- Graphite: PBE gives c~8+ A, D3 recovers experimental c=6.71 A
- Must use ISIF=3 to allow interlayer distance to relax

### 6. Phonon Dispersions (Phonopy)
**Teaches**: Lattice dynamics, finite-displacement method, stability analysis

Key concepts:
- Displace atoms, compute forces, build force constant matrix
- Use very tight EDIFF (1e-8) and LREAL=.FALSE. for phonon forces
- Imaginary frequencies = dynamical instability
- Structure must be fully relaxed first!

## Common VASP Mistakes (and how to fix them)

| Problem | Symptom | Fix |
|---------|---------|-----|
| ENCUT too low | Pulay stress warning | Increase to 1.3x ENMAX |
| Not enough k-points | Energy not converged | Increase k-point density |
| EDIFF too loose | Noisy forces | Tighten to 1e-6 or 1e-8 |
| LREAL=Auto for phonons | Wrong frequencies | Use LREAL=.FALSE. |
| No ISPIN=2 for magnetic | Wrong ground state | Add ISPIN=2, set MAGMOM |
| NSW too small | "not converged" | Increase NSW or restart from CONTCAR |
| Wrong POTCAR order | Scrambled structure | Match species order in POSCAR |
| NPAR/KPAR wrong | Slow or crash | KPAR divides k-points, NPAR divides bands |

## Materials Project Integration

```python
from dft_workflows.core.materials_project import MaterialsProjectClient

# Initialize (reads MP_API_KEY from environment)
client = MaterialsProjectClient()

# Search for materials
results = client.search_materials(formula="SrTiO3")

# Download a structure as ASE Atoms
atoms = client.get_structure_as_ase(formula="NiO")

# Get reference energies for validation
refs = client.get_elemental_reference_energies(["Sr", "Ti", "O"])

# Get full reference data by MP ID
ref = client.get_reference_energy("mp-5229")
```

## API Endpoints

Start the server: `uvicorn si_api:app --reload`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/si_structure` | Silicon structure + energy |
| POST | `/workflows/relax` | Perovskite relaxation inputs |
| POST | `/workflows/surface` | Surface slab inputs |
| POST | `/workflows/vacancy` | Vacancy formation inputs |
| POST | `/workflows/dftu` | PBE vs DFT+U inputs |
| POST | `/workflows/d3` | DFT-D3 graphite inputs |
| POST | `/workflows/phonon` | Phonon dispersion inputs |
| GET | `/materials/{formula}` | Search Materials Project |
| GET | `/materials/id/{mp_id}` | Get structure by MP ID |
| POST | `/structures/perovskite` | Build perovskite cell |
| POST | `/structures/rocksalt` | Build rocksalt cell |
| POST | `/structures/graphite` | Build graphite cell |

Interactive API docs at `http://localhost:8000/docs`

## Recommended Reading

1. **Sholl & Steckel**: "Density Functional Theory: A Practical Introduction"
   - Best intro textbook for DFT in materials science
2. **Martin**: "Electronic Structure: Basic Theory and Practical Methods"
   - More rigorous theoretical foundation
3. **VASP wiki**: https://www.vasp.at/wiki/
   - Official documentation for all INCAR tags
4. **Materials Project docs**: https://docs.materialsproject.org/
   - API documentation and data descriptions
5. **Phonopy docs**: https://phonopy.github.io/phonopy/
   - Phonon calculation methodology
