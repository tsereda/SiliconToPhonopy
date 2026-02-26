"""
Workflow 4: Compare PBE vs DFT+U on a transition-metal oxide (NiO).

This teaches:
  - Why standard PBE fails for correlated materials
  - The Dudarev DFT+U method (LDAUTYPE=2)
  - How to set U parameters (LDAUL, LDAUU, LDAUJ)
  - Spin-polarized calculations (ISPIN=2) and magnetic ordering
  - Comparing band gaps, magnetic moments, and lattice constants

Learning objectives
-------------------
1. Understand why PBE underestimates the band gap of NiO (predicts
   a metal instead of a 4.3 eV insulator).
2. Know that DFT+U adds an on-site Coulomb repulsion U to localized
   d/f electrons, opening the gap.
3. Be able to set up LDAU tags: LDAUL, LDAUU, LDAUJ for each species.
4. Understand that U is semi-empirical and must be benchmarked.

Common failure modes
--------------------
- **Wrong LDAUL order**: LDAUL must match species order in POSCAR.
  If POSCAR has Ni then O, use LDAUL = 2 -1 (d for Ni, none for O).
- **Non-magnetic initial state**: NiO is antiferromagnetic.  If you
  start with MAGMOM = 0, it may converge to a non-magnetic (metallic)
  state.  Fix: set MAGMOM explicitly.
- **U too large**: Over-localises d-electrons, gives wrong structure.
  Typical U(Ni) = 5-6.4 eV.
- **Convergence issues**: DFT+U can have multiple local minima.
  Try different initial magnetic configurations.
"""

from __future__ import annotations

from pathlib import Path

from ase import Atoms

from ..core.crystal_builders import build_rocksalt
from ..core.vasp_io import VaspInputSet


class DftPlusUComparison:
    """Set up PBE and DFT+U calculations for NiO comparison.

    Parameters
    ----------
    material : str
        "NiO" or "Fe2O3".
    u_value : float
        Hubbard U parameter for the transition metal d-electrons (eV).
    j_value : float
        Hund's J parameter (eV).  Often 0 for Dudarev (U_eff = U - J).
    output_dir : str or Path
        Base output directory.
    """

    def __init__(
        self,
        material: str = "NiO",
        u_value: float = 6.2,
        j_value: float = 0.0,
        output_dir: str | Path = "04_dft_plus_u",
    ):
        self.material = material
        self.u_value = u_value
        self.j_value = j_value
        self.output_dir = Path(output_dir)

    def _build_nio(self) -> Atoms:
        """Build NiO with initial magnetic moments for AFM ordering."""
        atoms = build_rocksalt("Ni", "O", a=4.177)

        # Make a 2x2x2 supercell for AFM ordering
        atoms = atoms.repeat((2, 2, 2))

        # Set up antiferromagnetic ordering on Ni atoms
        # Type-II AFM: ferromagnetic (111) planes with alternating sign
        symbols = atoms.get_chemical_symbols()
        positions = atoms.get_positions()
        magmoms = []

        for i, sym in enumerate(symbols):
            if sym == "Ni":
                # Simple AFM: alternate sign based on position
                layer = int(round(
                    (positions[i][0] + positions[i][1] + positions[i][2])
                    / (4.177 / 2)
                ))
                magmoms.append(2.0 if layer % 2 == 0 else -2.0)
            else:
                magmoms.append(0.0)

        atoms.set_initial_magnetic_moments(magmoms)
        return atoms

    def _build_fe2o3(self) -> Atoms:
        """Build Fe2O3 (hematite) with initial magnetic moments."""
        from ..core.crystal_builders import build_corundum
        atoms = build_corundum("Fe", a=5.038, c=13.772)

        # Set initial magnetic moments
        symbols = atoms.get_chemical_symbols()
        magmoms = []
        fe_count = 0
        for sym in symbols:
            if sym == "Fe":
                # AFM ordering in corundum: alternating pairs
                magmoms.append(5.0 if fe_count % 2 == 0 else -5.0)
                fe_count += 1
            else:
                magmoms.append(0.0)

        atoms.set_initial_magnetic_moments(magmoms)
        return atoms

    def setup(self) -> dict:
        """Generate VASP inputs for both PBE and PBE+U calculations.

        Returns
        -------
        dict with structure info and file paths for both calculations.
        """
        if self.material == "NiO":
            atoms = self._build_nio()
            metal = "Ni"
        elif self.material == "Fe2O3":
            atoms = self._build_fe2o3()
            metal = "Fe"
        else:
            raise ValueError(f"Unsupported material: {self.material}")

        # Determine species order
        species_order = []
        seen = set()
        for s in atoms.get_chemical_symbols():
            if s not in seen:
                species_order.append(s)
                seen.add(s)

        results = {"material": self.material, "calculations": {}}

        # --- PBE (standard GGA, no +U) ---
        pbe_dir = self.output_dir / "pbe"
        magmom_str = " ".join(
            f"{m:.1f}" for m in atoms.get_initial_magnetic_moments()
        )
        pbe_overrides = {
            "ISPIN": 2,
            "MAGMOM": magmom_str,
        }

        vis_pbe = VaspInputSet(
            atoms=atoms,
            calc_type="relax",
            overrides=pbe_overrides,
            kpoints_density=35.0,
        )
        paths_pbe = vis_pbe.write_all(pbe_dir)
        results["calculations"]["pbe"] = {
            "n_atoms": len(atoms),
            "output_dir": str(pbe_dir),
            "files": {k: str(v) for k, v in paths_pbe.items()},
            "explanation": vis_pbe.explain(),
        }

        # --- PBE+U (DFT+U with Dudarev method) ---
        u_dir = self.output_dir / "pbe_plus_u"

        # LDAUL, LDAUU, LDAUJ must match species order in POSCAR
        ldaul = []
        ldauu = []
        ldauj = []
        for sp in species_order:
            if sp == metal:
                ldaul.append(2)               # d-electrons
                ldauu.append(self.u_value)
                ldauj.append(self.j_value)
            else:
                ldaul.append(-1)              # No +U correction
                ldauu.append(0.0)
                ldauj.append(0.0)

        u_overrides = {
            "ISPIN": 2,
            "MAGMOM": magmom_str,
            "LDAUL": ldaul,
            "LDAUU": ldauu,
            "LDAUJ": ldauj,
        }

        vis_u = VaspInputSet(
            atoms=atoms,
            calc_type="dft_plus_u",
            overrides=u_overrides,
            kpoints_density=35.0,
        )
        paths_u = vis_u.write_all(u_dir)
        results["calculations"]["pbe_plus_u"] = {
            "n_atoms": len(atoms),
            "output_dir": str(u_dir),
            "U_eff": self.u_value - self.j_value,
            "files": {k: str(v) for k, v in paths_u.items()},
            "explanation": vis_u.explain(),
        }

        # --- Write comparison script ---
        script_path = self._write_comparison_script(species_order, metal)
        results["comparison_script"] = str(script_path)

        # --- Write README ---
        readme = self._generate_readme(atoms, species_order, metal)
        readme_path = self.output_dir / "README.md"
        readme_path.write_text(readme)

        return results

    def _write_comparison_script(self, species_order, metal) -> Path:
        script = f'''#!/usr/bin/env python3
"""
Compare PBE vs PBE+U results for {self.material}.

Run this after both VASP calculations are complete.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from dft_workflows.core.vasp_io import VaspOutputParser


def compare_pbe_vs_u():
    pbe = VaspOutputParser("pbe")
    u = VaspOutputParser("pbe_plus_u")

    print("=" * 60)
    print(f"PBE vs PBE+U Comparison for {self.material}")
    print("=" * 60)

    # Energies
    e_pbe = pbe.get_total_energy()
    e_u = u.get_total_energy()
    print(f"\\nTotal energy (PBE):   {{e_pbe}} eV")
    print(f"Total energy (PBE+U): {{e_u}} eV")

    # Band gaps
    bg_pbe = pbe.get_band_gap()
    bg_u = u.get_band_gap()
    print(f"\\nBand gap (PBE):   {{bg_pbe}} eV")
    print(f"Band gap (PBE+U): {{bg_u}} eV")
    print(f"Experimental:     4.3 eV (NiO)" if "{self.material}" == "NiO" else "")

    # Magnetic moments
    m_pbe = pbe.get_magnetization()
    m_u = u.get_magnetization()
    print(f"\\nTotal magnetization (PBE):   {{m_pbe}} mu_B")
    print(f"Total magnetization (PBE+U): {{m_u}} mu_B")

    # Convergence
    print(f"\\nConvergence:")
    print(f"  PBE converged:   {{pbe.is_converged()}}")
    print(f"  PBE+U converged: {{u.is_converged()}}")

    print("\\n" + "=" * 60)
    print("Key takeaway: PBE predicts NiO to be metallic (zero gap),")
    print("while PBE+U opens the gap via on-site Coulomb repulsion.")
    print("=" * 60)


if __name__ == "__main__":
    compare_pbe_vs_u()
'''
        script_path = self.output_dir / "compare_pbe_u.py"
        script_path.write_text(script)
        return script_path

    def _generate_readme(self, atoms, species_order, metal) -> str:
        u_eff = self.u_value - self.j_value
        ldaul_str = " ".join(
            "2" if sp == metal else "-1" for sp in species_order
        )
        ldauu_str = " ".join(
            f"{self.u_value}" if sp == metal else "0.0" for sp in species_order
        )
        ldauj_str = " ".join(
            f"{self.j_value}" if sp == metal else "0.0" for sp in species_order
        )

        return f"""# PBE vs DFT+U Comparison: {self.material}

## Why DFT+U?
Standard PBE (GGA) badly fails for strongly correlated transition-metal
oxides.  For NiO, PBE predicts a **metal** instead of the experimental
**4.3 eV insulator**.  The problem: PBE delocalises Ni 3d electrons.

DFT+U adds an on-site Hubbard correction that penalises partial
d-orbital occupancy, forcing electrons to be more localised.  This
opens the band gap.

## LDAU parameters (species order: {' '.join(species_order)})
```
LDAU    = .TRUE.
LDAUTYPE = 2          # Dudarev: U_eff = U - J
LDAUL   = {ldaul_str}       # 2 = d-electrons for {metal}, -1 = none for O
LDAUU   = {ldauu_str}   # U values (eV)
LDAUJ   = {ldauj_str}   # J values (eV)
LDAUPRINT = 2         # Print occupation matrices
```

**U_eff = {u_eff} eV** for {metal} 3d electrons.

## Magnetic ordering
{self.material} is antiferromagnetic (AFM).  The initial MAGMOM must
reflect this: alternating +/- moments on {metal} sites, 0 on O.

ISPIN = 2 enables spin-polarised calculation.

## Expected results
| Property | PBE | PBE+U (U={u_eff}) | Experiment |
|----------|-----|-------|------------|
| Band gap | ~0 eV (metal!) | ~3-4 eV | 4.3 eV |
| {metal} moment | ~1 mu_B | ~1.7 mu_B | 1.9 mu_B |
| Lattice const. | ~4.10 A | ~4.17 A | 4.177 A |

## How to run
```bash
# Run PBE calculation:
cd pbe && mpirun -np 16 vasp_std > vasp.log 2>&1 && cd ..

# Run PBE+U calculation:
cd pbe_plus_u && mpirun -np 16 vasp_std > vasp.log 2>&1 && cd ..

# Compare results:
python compare_pbe_u.py
```

## Choosing U
Common approaches:
1. **Literature values**: NiO U=6.2 eV (Dudarev 1998)
2. **Linear response**: Calculate U self-consistently (Cococcioni & de Gironcoli 2005)
3. **Fit to experiment**: Adjust U until band gap / lattice constant matches
4. **ACBN0**: Self-consistent U from pseudohybrid functional
"""
