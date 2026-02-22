"""
Workflow 2: Build a surface slab model from a bulk crystal.

This teaches:
  - Cutting surfaces along Miller indices (hkl)
  - Adding vacuum layers for surface calculations
  - Selective dynamics (freezing bottom layers)
  - Dipole corrections for polar surfaces
  - Surface energy calculations

Learning objectives
-------------------
1. Understand Miller indices and how they define crystal planes.
2. Know why vacuum is needed and how much is "enough" (convergence test).
3. Understand selective dynamics: freeze bulk-like layers, relax surface.
4. Know when dipole corrections (LDIPOL/IDIPOL) are needed.

Common failure modes
--------------------
- **Not enough vacuum**: Slab images interact through vacuum -> wrong energy.
  Fix: converge surface energy vs. vacuum thickness (typically 15-20 A).
- **Not enough layers**: Surface energy not converged vs. slab thickness.
  Fix: converge vs. number of layers (typically 5-9 for metals, more for oxides).
- **Polar surface**: Divergent electrostatic potential.
  Fix: use symmetric slab termination or LDIPOL=.TRUE.
- **Wrong k-points**: Surface calculations need dense in-plane k-points
  but only 1 k-point along the surface normal (vacuum direction).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from ase import Atoms

from ..core.crystal_builders import build_perovskite, build_surface_slab
from ..core.vasp_io import VaspInputSet


class SurfaceSlabWorkflow:
    """Build a surface slab and generate VASP inputs.

    Parameters
    ----------
    bulk_atoms : ase.Atoms or None
        Bulk unit cell.  If None, builds SrTiO3.
    miller_index : tuple
        Surface orientation.
    min_slab_size : float
        Minimum slab thickness (angstroms).
    min_vacuum_size : float
        Vacuum thickness (angstroms).
    freeze_bottom : int
        Number of bottom layers to freeze (selective dynamics).
    output_dir : str or Path
        Where to write files.
    """

    def __init__(
        self,
        bulk_atoms: Atoms | None = None,
        miller_index: tuple[int, int, int] = (1, 0, 0),
        min_slab_size: float = 10.0,
        min_vacuum_size: float = 15.0,
        freeze_bottom: int = 2,
        output_dir: str | Path = "02_surface_slab",
    ):
        if bulk_atoms is None:
            bulk_atoms = build_perovskite("Sr", "Ti", a=3.905)

        self.bulk_atoms = bulk_atoms
        self.miller_index = miller_index
        self.min_slab_size = min_slab_size
        self.min_vacuum_size = min_vacuum_size
        self.freeze_bottom = freeze_bottom
        self.output_dir = Path(output_dir)

    def setup(self) -> dict:
        """Generate slab structure and VASP inputs.

        Returns
        -------
        dict with structure info and file paths.
        """
        # Build the surface slab
        slab = build_surface_slab(
            self.bulk_atoms,
            miller_index=self.miller_index,
            min_slab_size=self.min_slab_size,
            min_vacuum_size=self.min_vacuum_size,
        )

        # Apply selective dynamics: freeze bottom layers
        slab = self._apply_selective_dynamics(slab)

        # For surface calculations, use 1 k-point along vacuum direction
        # Dense in-plane k-points
        overrides = {
            "ISIF": 2,          # Fix cell shape/volume, relax ions only
            "LDIPOL": True,     # Dipole correction
            "IDIPOL": 3,        # Along z (vacuum direction)
        }

        vis = VaspInputSet(
            atoms=slab,
            calc_type="relax",
            overrides=overrides,
            kpoints_density=40.0,
        )

        paths = vis.write_all(self.output_dir)

        # Write README
        readme = self._generate_readme(slab)
        readme_path = self.output_dir / "README.md"
        readme_path.write_text(readme)
        paths["README.md"] = readme_path

        return {
            "formula": slab.get_chemical_formula(),
            "n_atoms": len(slab),
            "miller_index": list(self.miller_index),
            "slab_thickness_A": self._get_slab_thickness(slab),
            "vacuum_thickness_A": self._get_vacuum_thickness(slab),
            "output_dir": str(self.output_dir),
            "files": {k: str(v) for k, v in paths.items()},
        }

    def _apply_selective_dynamics(self, slab: Atoms) -> Atoms:
        """Freeze the bottom N layers of the slab.

        Layers are determined by sorting atoms by z-coordinate and
        grouping atoms within a tolerance.
        """
        if self.freeze_bottom <= 0:
            return slab

        positions = slab.get_positions()
        z_coords = positions[:, 2]

        # Cluster z-coordinates into layers (tolerance = 0.5 A)
        sorted_z = np.sort(np.unique(np.round(z_coords, 1)))
        layer_boundaries = []
        current_z = sorted_z[0]
        layer_boundaries.append(current_z)
        for z in sorted_z[1:]:
            if z - current_z > 0.5:
                layer_boundaries.append(z)
                current_z = z

        if len(layer_boundaries) <= self.freeze_bottom:
            # Not enough layers to freeze
            return slab

        # Atoms in the bottom N layers are frozen
        freeze_threshold = layer_boundaries[self.freeze_bottom]
        selective_dynamics = []
        for z in z_coords:
            if z < freeze_threshold:
                selective_dynamics.append([False, False, False])
            else:
                selective_dynamics.append([True, True, True])

        # Store selective dynamics as arrays in atoms.arrays
        slab.arrays["selective_dynamics"] = np.array(selective_dynamics)

        return slab

    def _get_slab_thickness(self, slab: Atoms) -> float:
        """Estimate slab thickness (max z - min z of atoms)."""
        z = slab.get_positions()[:, 2]
        return float(np.max(z) - np.min(z))

    def _get_vacuum_thickness(self, slab: Atoms) -> float:
        """Estimate vacuum thickness."""
        z = slab.get_positions()[:, 2]
        cell_z = slab.cell[2, 2]
        return float(cell_z - (np.max(z) - np.min(z)))

    def _generate_readme(self, slab: Atoms) -> str:
        hkl = "".join(str(i) for i in self.miller_index)
        return f"""# Surface Slab Model: ({hkl}) surface

## What this calculation does
Relaxation of a ({hkl}) surface slab cut from the bulk crystal.
Bottom {self.freeze_bottom} layers are frozen (selective dynamics),
top layers are free to relax.

## Structure details
- Formula: {slab.get_chemical_formula()}
- {len(slab)} atoms
- Slab thickness: {self._get_slab_thickness(slab):.1f} A
- Vacuum thickness: {self._get_vacuum_thickness(slab):.1f} A

## Key INCAR settings
- **ISIF = 2**: Relax ions only, fix cell shape and volume
- **LDIPOL = .TRUE.**: Dipole correction for asymmetric slabs
- **IDIPOL = 3**: Dipole correction along z (vacuum direction)

## Selective dynamics
Bottom {self.freeze_bottom} layers have F F F (frozen).
Top layers have T T T (free to relax).

## Surface energy calculation
After running both bulk and slab calculations:

    E_surf = (E_slab - N_slab/N_bulk * E_bulk) / (2 * A)

where A is the surface area and the factor 2 accounts for two surfaces.

## Convergence tests you should do
1. **Vacuum thickness**: Run with 10, 15, 20, 25 A vacuum
2. **Slab thickness**: Run with 3, 5, 7, 9 layers
3. **k-points**: Increase in-plane k-points until E_surf converges
"""
