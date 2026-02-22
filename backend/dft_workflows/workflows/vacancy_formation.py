"""
Workflow 3: Compute vacancy formation energy in a supercell.

This teaches:
  - Building supercells from primitive cells
  - Creating point defects (vacancies)
  - Computing defect formation energies
  - Finite-size effects and supercell convergence

Learning objectives
-------------------
1. Understand the supercell approach to defect calculations.
2. Know how to compute vacancy formation energy:
       E_f = E(defective) - E(pristine) + mu(removed_atom)
3. Understand finite-size effects: defect-defect interactions across
   periodic images -> need to converge vs. supercell size.
4. Know that chemical potentials (mu) depend on growth conditions.

Common failure modes
--------------------
- **Supercell too small**: Defect-defect interaction -> wrong E_f.
  Fix: test 2x2x2, 3x3x3, 4x4x4 supercells.
- **Insufficient relaxation**: Atoms near vacancy need to relax
  significantly.  Use tight EDIFFG.
- **Wrong chemical potential**: E_f depends on whether you use
  oxygen-rich or metal-rich conditions.
- **Charge state not considered**: Vacancies can be charged.
  Neutral vacancy is the starting point.
"""

from __future__ import annotations

import json
from pathlib import Path

from ase import Atoms

from ..core.crystal_builders import build_perovskite, build_supercell_with_vacancy
from ..core.vasp_io import VaspInputSet


class VacancyFormationEnergy:
    """Set up vacancy formation energy calculations.

    Generates VASP inputs for:
      1. Pristine supercell relaxation
      2. Defective supercell relaxation (one vacancy)

    Parameters
    ----------
    bulk_atoms : ase.Atoms or None
        Primitive cell.  If None, builds SrTiO3.
    supercell_dims : tuple
        Supercell size, e.g. (2,2,2) = 8x unit cell.
    vacancy_element : str
        Element to remove.  "O" for oxygen vacancy, "Sr" for A-site, etc.
    output_dir : str or Path
        Base output directory.
    """

    def __init__(
        self,
        bulk_atoms: Atoms | None = None,
        supercell_dims: tuple[int, int, int] = (2, 2, 2),
        vacancy_element: str = "O",
        output_dir: str | Path = "03_vacancy",
    ):
        if bulk_atoms is None:
            bulk_atoms = build_perovskite("Sr", "Ti", a=3.905)

        self.bulk_atoms = bulk_atoms
        self.supercell_dims = supercell_dims
        self.vacancy_element = vacancy_element
        self.output_dir = Path(output_dir)

    def setup(self) -> dict:
        """Generate VASP inputs for pristine and defective supercells.

        Returns
        -------
        dict with structure info and file paths for both calculations.
        """
        pristine, defective, info = build_supercell_with_vacancy(
            self.bulk_atoms,
            supercell_dims=self.supercell_dims,
            vacancy_element=self.vacancy_element,
        )

        results = {
            "vacancy_info": info,
            "calculations": {},
        }

        # --- Pristine supercell ---
        pristine_dir = self.output_dir / "pristine"
        vis_pristine = VaspInputSet(
            atoms=pristine,
            calc_type="relax",
            overrides={"ISIF": 2},  # Fix cell, relax ions
            kpoints_density=30.0,   # Coarser grid for supercell
        )
        paths_p = vis_pristine.write_all(pristine_dir)
        results["calculations"]["pristine"] = {
            "n_atoms": len(pristine),
            "output_dir": str(pristine_dir),
            "files": {k: str(v) for k, v in paths_p.items()},
        }

        # --- Defective supercell ---
        defective_dir = self.output_dir / "defective"
        vis_defective = VaspInputSet(
            atoms=defective,
            calc_type="relax",
            overrides={"ISIF": 2},
            kpoints_density=30.0,
        )
        paths_d = vis_defective.write_all(defective_dir)
        results["calculations"]["defective"] = {
            "n_atoms": len(defective),
            "output_dir": str(defective_dir),
            "files": {k: str(v) for k, v in paths_d.items()},
        }

        # --- Write analysis script ---
        script_path = self._write_analysis_script()
        results["analysis_script"] = str(script_path)

        # --- Write README ---
        readme = self._generate_readme(pristine, defective, info)
        readme_path = self.output_dir / "README.md"
        readme_path.write_text(readme)

        return results

    def _write_analysis_script(self) -> Path:
        """Write a Python script to compute E_f from VASP results."""
        script = '''#!/usr/bin/env python3
"""
Compute vacancy formation energy from VASP results.

Usage:
    python analyze_vacancy.py

Requires completed VASP calculations in pristine/ and defective/ subdirectories.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dft_workflows.core.vasp_io import VaspOutputParser


def compute_vacancy_formation_energy(
    pristine_dir: str = "pristine",
    defective_dir: str = "defective",
    mu_vacancy_atom: float = None,
):
    """
    Compute vacancy formation energy:

        E_f = E(defective) - E(pristine) + mu(removed_atom)

    Parameters
    ----------
    pristine_dir : str
        Path to pristine supercell VASP output.
    defective_dir : str
        Path to defective supercell VASP output.
    mu_vacancy_atom : float or None
        Chemical potential of the removed atom (eV).
        If None, uses the energy per atom from a reference calculation.
        For oxygen vacancy under O-rich conditions, use half the O2 energy.

    Notes on chemical potentials
    ----------------------------
    For SrTiO3 oxygen vacancy:
      O-rich:   mu_O = 1/2 * E(O2)   (oxygen gas reference)
      O-poor:   mu_O = 1/2 * E(O2) + Delta_H_f(SrTiO3) / 3
    """
    parser_p = VaspOutputParser(pristine_dir)
    parser_d = VaspOutputParser(defective_dir)

    E_pristine = parser_p.get_total_energy()
    E_defective = parser_d.get_total_energy()

    if E_pristine is None or E_defective is None:
        print("ERROR: Could not read energies from OUTCAR files.")
        print(f"  Pristine energy:  {E_pristine}")
        print(f"  Defective energy: {E_defective}")
        return None

    print(f"Pristine supercell energy:  {E_pristine:.6f} eV")
    print(f"Defective supercell energy: {E_defective:.6f} eV")

    if mu_vacancy_atom is None:
        # Default: use O2 molecule energy / 2 as reference
        # Typical PBE value for E(O2) ~ -9.86 eV
        mu_vacancy_atom = -9.86 / 2
        print(f"Using default mu(O) = {mu_vacancy_atom:.3f} eV (half of O2 PBE energy)")

    E_f = E_defective - E_pristine + mu_vacancy_atom
    print(f"\\nVacancy formation energy: {E_f:.4f} eV")

    # Check convergence
    print(f"\\nConvergence checks:")
    print(f"  Pristine converged:  {parser_p.is_converged()}")
    print(f"  Defective converged: {parser_d.is_converged()}")

    return E_f


if __name__ == "__main__":
    compute_vacancy_formation_energy()
'''
        script_path = self.output_dir / "analyze_vacancy.py"
        script_path.write_text(script)
        return script_path

    def _generate_readme(self, pristine, defective, info) -> str:
        dims = "x".join(str(d) for d in self.supercell_dims)
        return f"""# Vacancy Formation Energy Calculation

## What this calculation does
Computes the formation energy of a {self.vacancy_element} vacancy in
a {dims} supercell.

## Structures
- **Pristine**: {len(pristine)} atoms, {pristine.get_chemical_formula()}
- **Defective**: {len(defective)} atoms, {defective.get_chemical_formula()}
- Removed: 1 {info['removed_symbol']} atom at position {info['removed_position']}

## Vacancy formation energy formula
```
E_f = E(defective) - E(pristine) + mu(removed_atom)
```

where mu is the chemical potential of the removed atom, which depends
on thermodynamic conditions:

| Condition | mu(O) | Interpretation |
|-----------|-------|----------------|
| O-rich    | 1/2 E(O2) | Equilibrium with O2 gas |
| O-poor    | 1/2 E(O2) + Delta_H / 3 | Metal-rich limit |

## How to run
```bash
# 1. Run pristine supercell:
cd pristine && mpirun -np 16 vasp_std > vasp.log 2>&1 && cd ..

# 2. Run defective supercell:
cd defective && mpirun -np 16 vasp_std > vasp.log 2>&1 && cd ..

# 3. Analyze results:
python analyze_vacancy.py
```

## Convergence test: supercell size
You should compare E_f for different supercell sizes:
- 2x2x2 ({2**3 * len(self.bulk_atoms)} atoms)
- 3x3x3 ({3**3 * len(self.bulk_atoms)} atoms)
- 4x4x4 ({4**3 * len(self.bulk_atoms)} atoms) -- expensive!

E_f should converge to within ~0.05 eV.

## Expected results
For SrTiO3 oxygen vacancy (PBE):
- E_f ~ 6-7 eV (O-rich conditions)
- E_f ~ 2-3 eV (O-poor conditions)
"""
