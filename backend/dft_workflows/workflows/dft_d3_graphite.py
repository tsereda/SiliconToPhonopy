"""
Workflow 5: DFT-D3 van der Waals corrections for graphite.

This teaches:
  - Why standard DFT (PBE) fails for layered / vdW materials
  - Grimme's DFT-D3 dispersion correction
  - BJ damping vs zero-damping
  - Comparing interlayer distances and binding energies

Learning objectives
-------------------
1. Understand that PBE cannot describe van der Waals (London dispersion)
   forces -- it overbinds or underbinds layered materials.
2. Know that DFT-D3 adds a semi-empirical C6/R^6 correction.
3. Be able to set IVDW in VASP for different vdW methods.
4. Compare PBE vs PBE-D3 interlayer spacing in graphite.

Common failure modes
--------------------
- **IVDW wrong number**: IVDW=11 is D3(zero), IVDW=12 is D3(BJ).
  BJ damping is generally recommended.
- **Forgetting ISIF=3**: Interlayer distance only relaxes if you
  allow cell shape/volume relaxation.
- **Too few k-points along c**: Graphite is quasi-2D; the c-axis
  dispersion is very flat, but you still need k-points for accuracy.
- **ENCUT too low**: Standard ENCUT may not capture vdW well; test
  convergence.
"""

from __future__ import annotations

from pathlib import Path

from ase import Atoms

from ..core.crystal_builders import build_graphite
from ..core.vasp_io import VaspInputSet


class DftD3Graphite:
    """Set up PBE and PBE-D3 calculations for graphite.

    Parameters
    ----------
    a : float
        In-plane lattice constant (angstroms).
    c : float
        Out-of-plane lattice constant (angstroms).
    output_dir : str or Path
        Base output directory.
    """

    def __init__(
        self,
        a: float = 2.464,
        c: float = 6.711,
        output_dir: str | Path = "05_dft_d3_graphite",
    ):
        self.a = a
        self.c = c
        self.output_dir = Path(output_dir)

    def setup(self) -> dict:
        """Generate VASP inputs for PBE and PBE-D3(BJ) calculations.

        Returns
        -------
        dict with structure info and file paths.
        """
        atoms = build_graphite(a=self.a, c=self.c)

        results = {
            "material": "graphite",
            "initial_c_over_a": self.c / self.a,
            "initial_interlayer_d_A": self.c / 2,
            "calculations": {},
        }

        # --- PBE (no vdW correction) ---
        pbe_dir = self.output_dir / "pbe_no_vdw"
        vis_pbe = VaspInputSet(
            atoms=atoms,
            calc_type="relax",
            overrides={"ISIF": 3},
            kpoints_density=50.0,  # Dense grid for good c-axis sampling
            potcar_map={"C": "C"},
        )
        paths_pbe = vis_pbe.write_all(pbe_dir)
        results["calculations"]["pbe"] = {
            "n_atoms": len(atoms),
            "output_dir": str(pbe_dir),
            "vdw_correction": "none",
            "files": {k: str(v) for k, v in paths_pbe.items()},
        }

        # --- PBE + D3(BJ) ---
        d3bj_dir = self.output_dir / "pbe_d3bj"
        vis_d3 = VaspInputSet(
            atoms=atoms,
            calc_type="dft_d3",
            overrides={"ISIF": 3, "IVDW": 12},  # D3 with BJ damping
            kpoints_density=50.0,
            potcar_map={"C": "C"},
        )
        paths_d3 = vis_d3.write_all(d3bj_dir)
        results["calculations"]["pbe_d3bj"] = {
            "n_atoms": len(atoms),
            "output_dir": str(d3bj_dir),
            "vdw_correction": "DFT-D3(BJ)",
            "IVDW": 12,
            "files": {k: str(v) for k, v in paths_d3.items()},
        }

        # --- PBE + D3(zero damping) for comparison ---
        d3zero_dir = self.output_dir / "pbe_d3zero"
        vis_d3z = VaspInputSet(
            atoms=atoms,
            calc_type="dft_d3",
            overrides={"ISIF": 3, "IVDW": 11},  # D3 with zero damping
            kpoints_density=50.0,
            potcar_map={"C": "C"},
        )
        paths_d3z = vis_d3z.write_all(d3zero_dir)
        results["calculations"]["pbe_d3_zero"] = {
            "n_atoms": len(atoms),
            "output_dir": str(d3zero_dir),
            "vdw_correction": "DFT-D3(zero)",
            "IVDW": 11,
            "files": {k: str(v) for k, v in paths_d3z.items()},
        }

        # --- Write comparison script ---
        script_path = self._write_comparison_script()
        results["comparison_script"] = str(script_path)

        # --- Write README ---
        readme = self._generate_readme(atoms)
        readme_path = self.output_dir / "README.md"
        readme_path.write_text(readme)

        return results

    def _write_comparison_script(self) -> Path:
        script = '''#!/usr/bin/env python3
"""
Compare PBE vs PBE-D3 results for graphite.

Extracts relaxed lattice constants and compares interlayer distances.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

try:
    from ase.io import read as ase_read
except ImportError:
    print("ASE not installed. Install with: pip install ase")
    sys.exit(1)


def compare_graphite():
    """Compare interlayer distances from PBE and PBE-D3 calculations."""

    methods = {
        "PBE (no vdW)": "pbe_no_vdw",
        "PBE-D3(BJ)":   "pbe_d3bj",
        "PBE-D3(zero)":  "pbe_d3zero",
    }

    print("=" * 65)
    print("Graphite: PBE vs DFT-D3 interlayer distance comparison")
    print("=" * 65)
    print(f"{'Method':<18} {'c (A)':>8} {'d_inter (A)':>12} {'c/a':>8}")
    print("-" * 65)

    exp_c = 6.711
    exp_d = exp_c / 2

    for label, dirname in methods.items():
        contcar = Path(dirname) / "CONTCAR"
        if contcar.exists():
            atoms = ase_read(str(contcar), format="vasp")
            c = atoms.cell[2, 2]
            a = atoms.cell[0, 0]
            d = c / 2  # Interlayer distance for AB graphite
            print(f"{label:<18} {c:>8.3f} {d:>12.3f} {c/a:>8.3f}")
        else:
            print(f"{label:<18} {'(not yet run)':>30}")

    print(f"{'Experiment':<18} {exp_c:>8.3f} {exp_d:>12.3f} {exp_c/2.464:>8.3f}")

    print()
    print("Key insight: PBE without vdW correction gives c >> 6.7 A")
    print("(layers barely bound), while D3 corrections recover the")
    print("experimental interlayer distance of ~3.35 A.")


if __name__ == "__main__":
    compare_graphite()
'''
        script_path = self.output_dir / "compare_d3.py"
        script_path.write_text(script)
        return script_path

    def _generate_readme(self, atoms) -> str:
        return f"""# DFT-D3 Corrections for Graphite

## Why vdW corrections?
Standard PBE (GGA) **cannot describe van der Waals interactions**.
Graphite layers are held together by London dispersion forces (vdW),
which arise from correlated electron fluctuations.  PBE misses this
physics entirely and predicts:
- Nearly unbound graphite layers (c ~ 8+ A instead of 6.7 A)
- Near-zero interlayer binding energy

## DFT-D3 correction (Grimme et al.)
Adds a semi-empirical pairwise correction to the DFT energy:

    E_DFT-D3 = E_DFT + E_disp

where E_disp = -sum_ij (s6*C6_ij/R^6 + s8*C8_ij/R^8) * f_damp(R)

Two damping schemes:
- **BJ damping** (IVDW=12): Becke-Johnson, recommended for most cases
- **Zero damping** (IVDW=11): Original Grimme, can give overbinding

## VASP settings
```
# Add this single line to INCAR for D3(BJ):
IVDW = 12
```

That's it!  The correction is computed on-the-fly and added to
energy, forces, and stress tensor.

## Other vdW methods in VASP
| IVDW | Method | Description |
|------|--------|-------------|
| 1    | DFT-D2 | Older Grimme, fixed C6 |
| 11   | DFT-D3(zero) | Geometry-dependent C6, zero damping |
| 12   | DFT-D3(BJ) | Geometry-dependent C6, BJ damping |
| 20   | TS    | Tkatchenko-Scheffler, density-dependent |
| 21   | TS+SCS | TS with self-consistent screening |
| 202  | MBD   | Many-body dispersion |

## Expected results
| Property | PBE | PBE-D3(BJ) | Experiment |
|----------|-----|------------|------------|
| c (A) | ~8+ | 6.6-6.8 | 6.711 |
| d_interlayer (A) | ~4+ | 3.3-3.4 | 3.356 |
| Binding energy (meV/atom) | ~0 | 25-30 | 31 ± 2 |
| a (A) | 2.47 | 2.46 | 2.464 |

## How to run
```bash
cd pbe_no_vdw && mpirun -np 4 vasp_std > vasp.log 2>&1 && cd ..
cd pbe_d3bj && mpirun -np 4 vasp_std > vasp.log 2>&1 && cd ..
cd pbe_d3zero && mpirun -np 4 vasp_std > vasp.log 2>&1 && cd ..
python compare_d3.py
```
"""
