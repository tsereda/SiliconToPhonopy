"""
Workflow 6: Compute phonon dispersions with Phonopy.

This teaches:
  - The finite-displacement (frozen-phonon) method
  - Generating displaced supercells with Phonopy
  - Running force calculations on each displacement
  - Post-processing: phonon band structure and DOS
  - Detecting dynamical instabilities (imaginary modes)

Learning objectives
-------------------
1. Understand the harmonic approximation: F = -Phi * u, where Phi is the
   force constant matrix and u is the displacement.
2. Know the Phonopy workflow: (a) generate supercell, (b) displace atoms,
   (c) compute forces with VASP, (d) build force constants, (e) plot.
3. Be able to interpret a phonon band structure: acoustic vs optical
   modes, LO-TO splitting, imaginary modes.
4. Know that imaginary (negative) frequencies mean the structure is
   dynamically unstable -- it wants to distort.

Common failure modes
--------------------
- **Structure not fully relaxed**: Residual forces contaminate the
  phonon calculation.  Relax with tight EDIFFG < 1e-3 eV/A first.
- **Supercell too small**: Short-range force constants only.  Test
  2x2x2 vs 3x3x3.
- **EDIFF not tight enough**: Forces must be very accurate for phonons.
  Use EDIFF = 1e-8.
- **LREAL = Auto**: Must use LREAL = .FALSE. for phonon accuracy
  (especially with small cells).
- **Symmetry issues**: If input structure symmetry is wrong, Phonopy
  generates too many displacements.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from ase import Atoms

from ..core.crystal_builders import build_perovskite
from ..core.vasp_io import VaspInputSet


class PhononDispersion:
    """Set up a Phonopy phonon dispersion calculation.

    The workflow has these steps:
      1. Create a supercell from the relaxed primitive cell.
      2. Generate symmetry-inequivalent displaced configurations.
      3. Write VASP input files for each displacement.
      4. (User runs VASP on each)
      5. Collect forces and compute force constants with Phonopy.
      6. Plot phonon band structure and DOS.

    Parameters
    ----------
    atoms : ase.Atoms or None
        Relaxed primitive cell.  If None, uses SrTiO3.
    supercell_matrix : list of list or tuple
        Supercell dimensions, e.g. [[2,0,0],[0,2,0],[0,0,2]] for 2x2x2.
    displacement : float
        Atomic displacement magnitude (angstroms).  Phonopy default: 0.01.
    output_dir : str or Path
        Base output directory.
    """

    def __init__(
        self,
        atoms: Atoms | None = None,
        supercell_matrix: list[list[int]] | None = None,
        displacement: float = 0.01,
        output_dir: str | Path = "06_phonons",
    ):
        if atoms is None:
            atoms = build_perovskite("Sr", "Ti", a=3.905)

        self.atoms = atoms
        self.supercell_matrix = supercell_matrix or [[2, 0, 0], [0, 2, 0], [0, 0, 2]]
        self.displacement = displacement
        self.output_dir = Path(output_dir)

    def setup(self) -> dict:
        """Generate displaced supercells and VASP input files.

        Returns
        -------
        dict with displacement info and file paths.
        """
        from phonopy import Phonopy
        from phonopy.interface.calculator import get_default_physical_units

        # Convert ASE atoms to Phonopy PhonopyAtoms
        phonopy_atoms = self._ase_to_phonopy(self.atoms)

        # Create Phonopy object
        phonon = Phonopy(
            phonopy_atoms,
            supercell_matrix=self.supercell_matrix,
            factor=get_default_physical_units("vasp")["factor"],
        )

        # Generate displacements
        phonon.generate_displacements(distance=self.displacement)
        supercells = phonon.supercells_with_displacements

        n_displacements = len(supercells)

        results = {
            "n_atoms_primitive": len(self.atoms),
            "n_atoms_supercell": len(phonon.supercell),
            "supercell_matrix": self.supercell_matrix,
            "n_displacements": n_displacements,
            "displacement_A": self.displacement,
            "displacement_dirs": [],
        }

        # Write VASP inputs for each displaced supercell
        self.output_dir.mkdir(parents=True, exist_ok=True)

        for i, scell in enumerate(supercells):
            disp_dir = self.output_dir / f"disp-{i+1:03d}"
            ase_atoms = self._phonopy_to_ase(scell)

            vis = VaspInputSet(
                atoms=ase_atoms,
                calc_type="phonon",
                kpoints_density=25.0,  # Coarser for supercell
            )
            vis.write_all(disp_dir)
            results["displacement_dirs"].append(str(disp_dir))

        # Save Phonopy configuration for post-processing
        self._save_phonopy_yaml(phonon)

        # Write the post-processing script
        script_path = self._write_postprocess_script()
        results["postprocess_script"] = str(script_path)

        # Write the run script
        run_script_path = self._write_run_script(n_displacements)
        results["run_script"] = str(run_script_path)

        # Write README
        readme = self._generate_readme(n_displacements)
        readme_path = self.output_dir / "README.md"
        readme_path.write_text(readme)

        return results

    def _ase_to_phonopy(self, atoms: Atoms):
        """Convert ASE Atoms to Phonopy PhonopyAtoms."""
        from phonopy.structure.atoms import PhonopyAtoms

        return PhonopyAtoms(
            symbols=atoms.get_chemical_symbols(),
            cell=atoms.cell[:],
            scaled_positions=atoms.get_scaled_positions(),
        )

    def _phonopy_to_ase(self, phonopy_atoms) -> Atoms:
        """Convert PhonopyAtoms to ASE Atoms."""
        return Atoms(
            symbols=phonopy_atoms.symbols,
            cell=phonopy_atoms.cell,
            scaled_positions=phonopy_atoms.scaled_positions,
            pbc=True,
        )

    def _save_phonopy_yaml(self, phonon):
        """Save phonopy_disp.yaml for post-processing."""
        phonon.save(self.output_dir / "phonopy_disp.yaml")

    def _write_postprocess_script(self) -> Path:
        """Write a Python script for phonon post-processing."""
        sc = json.dumps(self.supercell_matrix)
        script = f'''#!/usr/bin/env python3
"""
Phonon post-processing: compute force constants, band structure, and DOS.

Run this after ALL displaced supercell VASP calculations are complete.
"""

import sys
from pathlib import Path

import numpy as np

try:
    from phonopy import Phonopy
    from phonopy.interface.vasp import read_vasp
    from phonopy.file_IO import parse_FORCE_SETS
    from phonopy.interface.calculator import get_default_physical_units
except ImportError:
    print("Phonopy not installed. Install with: pip install phonopy")
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


def collect_forces():
    """Read forces from each displacement directory's vasprun.xml."""
    from phonopy.interface.vasp import Vasprun as PhonopyVasprun

    disp_dirs = sorted(Path(".").glob("disp-*"))
    if not disp_dirs:
        print("ERROR: No disp-* directories found.")
        sys.exit(1)

    force_sets = []
    for d in disp_dirs:
        vasprun = d / "vasprun.xml"
        if not vasprun.exists():
            print(f"WARNING: {{vasprun}} not found, skipping")
            continue
        v = PhonopyVasprun(str(vasprun))
        forces = v.read_forces()
        force_sets.append(forces)

    print(f"Collected forces from {{len(force_sets)}} displacements")
    return np.array(force_sets)


def run_phonon_postprocess():
    """Main post-processing routine."""

    # Load the Phonopy displacement configuration
    from phonopy import load as phonopy_load

    phonon = phonopy_load(
        phonopy_yaml="phonopy_disp.yaml",
        force_sets_filename=None,
    )

    # Collect forces from VASP calculations
    forces = collect_forces()
    phonon.forces = forces

    # Produce force constants
    phonon.produce_force_constants()

    print("Force constants computed successfully!")
    print(f"Shape: {{phonon.force_constants.shape}}")

    # ----- Band structure -----
    # Common high-symmetry path for cubic perovskite
    # Gamma - X - M - Gamma - R - X
    band_labels = ["$\\\\Gamma$", "X", "M", "$\\\\Gamma$", "R", "X"]
    bands = [
        [[0.0, 0.0, 0.0], [0.5, 0.0, 0.0]],        # Gamma -> X
        [[0.5, 0.0, 0.0], [0.5, 0.5, 0.0]],        # X -> M
        [[0.5, 0.5, 0.0], [0.0, 0.0, 0.0]],        # M -> Gamma
        [[0.0, 0.0, 0.0], [0.5, 0.5, 0.5]],        # Gamma -> R
        [[0.5, 0.5, 0.5], [0.5, 0.0, 0.0]],        # R -> X
    ]

    phonon.run_band_structure(bands, labels=band_labels)

    if HAS_MPL:
        phonon.plot_band_structure().savefig("phonon_band_structure.png", dpi=200)
        print("Saved: phonon_band_structure.png")

    # ----- DOS -----
    phonon.run_mesh([20, 20, 20])
    phonon.run_total_dos()

    if HAS_MPL:
        phonon.plot_total_dos().savefig("phonon_dos.png", dpi=200)
        print("Saved: phonon_dos.png")

    # ----- Check for imaginary modes -----
    frequencies = phonon.get_mesh_dict()["frequencies"]
    min_freq = np.min(frequencies)
    if min_freq < -0.5:  # THz
        print(f"\\nWARNING: Imaginary frequencies detected! Min = {{min_freq:.2f}} THz")
        print("This indicates a dynamical instability.")
        print("The structure wants to distort. Check:")
        print("  1. Is the structure fully relaxed?")
        print("  2. Is the supercell large enough?")
    else:
        print(f"\\nNo significant imaginary modes (min freq = {{min_freq:.2f}} THz)")
        print("Structure is dynamically stable.")

    # ----- Save data -----
    phonon.write_yaml_band_structure()
    print("Saved: band.yaml")


if __name__ == "__main__":
    run_phonon_postprocess()
'''
        script_path = self.output_dir / "postprocess_phonons.py"
        script_path.write_text(script)
        return script_path

    def _write_run_script(self, n_disp: int) -> Path:
        """Write a bash script to run all displacement calculations."""
        script = f"""#!/bin/bash
# Run all {n_disp} displacement calculations for phonons.
#
# Usage:
#   bash run_all_displacements.sh
#
# For HPC with SLURM, modify the vasp command and add sbatch headers.

set -e

VASP_CMD="mpirun -np 4 vasp_std"

for i in $(seq -w 1 {n_disp}); do
    dir="disp-$i"
    if [ ! -d "$dir" ]; then
        echo "Directory $dir not found, skipping"
        continue
    fi

    if [ -f "$dir/vasprun.xml" ]; then
        echo "[$dir] Already completed, skipping"
        continue
    fi

    echo "[$dir] Running VASP..."
    cd "$dir"
    $VASP_CMD > vasp.log 2>&1
    cd ..
    echo "[$dir] Done"
done

echo ""
echo "All displacements complete!"
echo "Run: python postprocess_phonons.py"
"""
        script_path = self.output_dir / "run_all_displacements.sh"
        script_path.write_text(script)
        return script_path

    def _generate_readme(self, n_disp) -> str:
        sc_str = "x".join(str(s[i]) for i, s in enumerate(self.supercell_matrix))
        return f"""# Phonon Dispersion Calculation

## Method: Finite displacements (frozen phonon)
The harmonic phonon frequencies are computed by:
1. Displacing each atom slightly from equilibrium
2. Computing the resulting forces with DFT (VASP)
3. Building the force constant matrix from force-displacement pairs
4. Diagonalising the dynamical matrix at each q-point

## Setup
- Primitive cell: {len(self.atoms)} atoms, {self.atoms.get_chemical_formula()}
- Supercell: {sc_str} ({len(self.atoms) * np.prod([s[i] for i, s in enumerate(self.supercell_matrix)])} atoms)
- Displacement: {self.displacement} A
- Number of displaced configurations: {n_disp}

## Key INCAR settings for force calculations
- **EDIFF = 1e-8**: Very tight SCF convergence for accurate forces
- **LREAL = .FALSE.**: Reciprocal-space projection (required for phonon accuracy)
- **IBRION = -1, NSW = 0**: Single-point calculation (no relaxation)
- **PREC = Accurate**: Full precision FFT grid

## How to run
```bash
# Step 1: Run all displacement calculations
bash run_all_displacements.sh

# Step 2: Post-process with Phonopy
python postprocess_phonons.py
```

## Output files
- `phonon_band_structure.png` -- Phonon dispersion curves
- `phonon_dos.png` -- Phonon density of states
- `band.yaml` -- Raw band structure data

## Interpreting the band structure
- **Acoustic modes**: Start at 0 THz at Gamma point (3 branches)
- **Optical modes**: Higher frequency branches
- **Imaginary frequencies**: Plotted as negative -> dynamical instability
- **LO-TO splitting**: Splitting at Gamma for polar materials (not
  included by default; add with `NAC = .TRUE.` and Born effective charges)

## Convergence tests
1. **Supercell size**: Compare 2x2x2 vs 3x3x3
2. **k-points**: Increase k-point density for force calculations
3. **EDIFF**: Compare 1e-7 vs 1e-8 vs 1e-9
4. **Displacement magnitude**: 0.01 A is standard; test 0.005 and 0.02
"""
