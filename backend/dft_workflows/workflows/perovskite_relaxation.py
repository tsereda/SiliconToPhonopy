"""
Workflow 1: Relax a cubic perovskite (SrTiO3).

This teaches:
  - Building a crystal structure from Wyckoff positions
  - Setting up VASP input for full ionic + cell relaxation (ISIF=3)
  - Choosing appropriate ENCUT, k-points, and convergence criteria
  - Common failure modes: unconverged relaxation, Pulay stress, symmetry breaking

Learning objectives
-------------------
1. Understand the 5 Wyckoff positions of cubic perovskite ABO3.
2. Know why ISIF=3 relaxes both ions and cell shape/volume.
3. Know the effect of ENCUT on Pulay stress (always use >= 1.3 * ENMAX).
4. Be able to check convergence from OUTCAR or vasprun.xml.

Common failure modes
--------------------
- **Pulay stress**: If ENCUT is too low, the basis set changes as the
  cell volume changes, leading to artificial stress.  Fix: increase ENCUT.
- **Symmetry breaking**: VASP may break cubic symmetry during relaxation.
  Fix: set ISYM=2 or use SYMPREC.
- **Unconverged forces**: If NSW is too small or EDIFFG too tight.
- **Wrong k-points**: Too few k-points -> wrong energy; too many -> slow.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..core.crystal_builders import build_perovskite
from ..core.vasp_io import VaspInputSet


class PerovskiteRelaxation:
    """Set up a full relaxation calculation for a cubic perovskite.

    Parameters
    ----------
    A : str
        A-site cation ("Sr", "Ba", "Pb", ...).
    B : str
        B-site cation ("Ti", "Zr", "Nb", ...).
    a : float
        Initial lattice constant guess (angstroms).
    encut : float
        Plane-wave cutoff (eV).  Should be >= 1.3 * ENMAX from POTCAR.
    kpoints_density : float
        k-point density parameter.
    output_dir : str or Path
        Where to write VASP input files.
    """

    def __init__(
        self,
        A: str = "Sr",
        B: str = "Ti",
        a: float = 3.905,
        encut: float = 520,
        kpoints_density: float = 40.0,
        output_dir: str | Path = "01_SrTiO3_relax",
    ):
        self.A = A
        self.B = B
        self.a = a
        self.encut = encut
        self.kpoints_density = kpoints_density
        self.output_dir = Path(output_dir)

    def setup(self) -> dict:
        """Generate all VASP input files for the relaxation.

        Returns
        -------
        dict with structure info and file paths.
        """
        # Build the perovskite unit cell
        atoms = build_perovskite(A=self.A, B=self.B, a=self.a)

        formula = atoms.get_chemical_formula()

        # POTCAR mapping for perovskites
        # Sr_sv includes semi-core states; Ti_pv includes p-valence
        potcar_map = {
            "Sr": "Sr_sv",
            "Ba": "Ba_sv",
            "Pb": "Pb_d",
            "Ti": "Ti_pv",
            "Zr": "Zr_sv",
            "Nb": "Nb_pv",
            "O": "O",
        }

        # Create the VASP input set
        vis = VaspInputSet(
            atoms=atoms,
            calc_type="relax",
            overrides={"ENCUT": self.encut},
            kpoints_density=self.kpoints_density,
            potcar_map={el: potcar_map.get(el, el) for el in set(atoms.get_chemical_symbols())},
        )

        paths = vis.write_all(self.output_dir)

        # Write a README for the student
        readme = self._generate_readme(atoms, vis)
        readme_path = self.output_dir / "README.md"
        readme_path.write_text(readme)
        paths["README.md"] = readme_path

        return {
            "formula": formula,
            "n_atoms": len(atoms),
            "lattice_constant_A": self.a,
            "output_dir": str(self.output_dir),
            "files": {k: str(v) for k, v in paths.items()},
            "explanation": vis.explain(),
        }

    def _generate_readme(self, atoms, vis) -> str:
        kpts = vis._auto_kpoints()
        return f"""# Perovskite Relaxation: {atoms.get_chemical_formula()}

## What this calculation does
Full structural relaxation (ions + cell shape + cell volume) of cubic
{self.A}{self.B}O3 perovskite using PBE-GGA.

## Structure
- Space group: Pm-3m (#221), cubic perovskite
- {self.A} at corner (0,0,0), {self.B} at body centre (1/2,1/2,1/2)
- O at face centres
- Initial lattice constant: {self.a} A
- 5 atoms per unit cell

## Key INCAR settings
- **ISIF = 3**: Relax ions, cell shape, AND cell volume
- **IBRION = 2**: Conjugate-gradient algorithm
- **ENCUT = {self.encut} eV**: Plane-wave cutoff (must be >= 1.3 * ENMAX)
- **EDIFFG = -0.01 eV/A**: Force convergence criterion

## k-point grid
- Gamma-centred {kpts[0]}x{kpts[1]}x{kpts[2]} mesh

## How to run
```bash
# 1. Copy your POTCAR files (see POTCAR_REFERENCE)
# 2. Submit to your HPC queue or run directly:
mpirun -np 4 vasp_std > vasp.log 2>&1
```

## How to check convergence
```bash
# Check if relaxation converged:
grep "reached required accuracy" OUTCAR

# Check final energy:
grep "free  energy   TOTEN" OUTCAR | tail -1

# Check residual forces:
grep "FORCES:" OUTCAR | tail -1
```

## Common problems
1. **Pulay stress warning**: Increase ENCUT to 600+ eV
2. **Symmetry broken**: Add ISYM = 2 to INCAR
3. **Not converged after NSW steps**: Increase NSW or restart from CONTCAR
4. **Negative frequencies in phonons**: Structure not fully relaxed
"""
