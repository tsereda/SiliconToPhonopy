"""
VASP input file generation and output parsing.

Generates INCAR, POSCAR, KPOINTS and manages POTCAR references for
different calculation types.  Also parses vasprun.xml and OUTCAR for
energies, forces, and electronic structure data.

Teaching notes
--------------
Every VASP calculation needs four input files:
  INCAR   -- control parameters (what kind of calculation, convergence, etc.)
  POSCAR  -- crystal structure (lattice vectors + atomic positions)
  KPOINTS -- Brillouin-zone sampling grid
  POTCAR  -- pseudopotentials (not generated here -- see your VASP license)

This module builds INCAR/POSCAR/KPOINTS from Python dicts and ASE Atoms,
explains each tag with inline comments, and validates common mistakes
that trip up new users.
"""

from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path
from typing import Any

import numpy as np
from ase import Atoms
from ase.io import write as ase_write


# =====================================================================
# INCAR presets for different calculation types
# =====================================================================

# Each preset is a dict of VASP INCAR tags.  The comments dict maps
# tag -> explanation string for the tutorial output.

_INCAR_PRESETS: dict[str, dict[str, Any]] = {
    # ----- Structural relaxation (ions + cell) -----
    "relax": {
        "PREC": "Accurate",
        "ENCUT": 520,        # eV -- plane-wave cutoff
        "EDIFF": 1e-6,       # eV -- electronic convergence
        "EDIFFG": -0.01,     # eV/A -- ionic convergence (negative = force)
        "IBRION": 2,         # Conjugate-gradient relaxation
        "ISIF": 3,           # Relax ions + cell shape + cell volume
        "NSW": 100,          # Max ionic steps
        "ISMEAR": 0,         # Gaussian smearing (good for insulators)
        "SIGMA": 0.05,       # Smearing width (eV)
        "LREAL": "Auto",     # Real-space projection
        "LWAVE": False,      # Don't write WAVECAR (saves disk)
        "LCHARG": False,     # Don't write CHGCAR
        "NELM": 200,         # Max electronic steps
    },
    # ----- Single-point / SCF -----
    "scf": {
        "PREC": "Accurate",
        "ENCUT": 520,
        "EDIFF": 1e-6,
        "IBRION": -1,        # No ionic relaxation
        "NSW": 0,
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": "Auto",
        "LWAVE": True,
        "LCHARG": True,
        "NELM": 200,
    },
    # ----- DFT+U (Dudarev method, GGA+U) -----
    "dft_plus_u": {
        "PREC": "Accurate",
        "ENCUT": 520,
        "EDIFF": 1e-6,
        "EDIFFG": -0.01,
        "IBRION": 2,
        "ISIF": 3,
        "NSW": 100,
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": "Auto",
        "LWAVE": False,
        "LCHARG": False,
        "NELM": 200,
        # DFT+U specific tags
        "LDAU": True,           # Activate DFT+U
        "LDAUTYPE": 2,          # Dudarev (rotationally invariant)
        "LDAUPRINT": 2,         # Print occupancy matrices
        # LDAUL, LDAUU, LDAUJ must be set per-species by the workflow
    },
    # ----- DFT-D3 van der Waals correction -----
    "dft_d3": {
        "PREC": "Accurate",
        "ENCUT": 520,
        "EDIFF": 1e-6,
        "EDIFFG": -0.01,
        "IBRION": 2,
        "ISIF": 3,
        "NSW": 100,
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": "Auto",
        "LWAVE": False,
        "LCHARG": False,
        "NELM": 200,
        # D3 correction (Grimme)
        "IVDW": 12,            # DFT-D3 with BJ damping
    },
    # ----- Phonon (displaced supercell, tight forces) -----
    "phonon": {
        "PREC": "Accurate",
        "ENCUT": 520,
        "EDIFF": 1e-8,      # Very tight for accurate forces
        "IBRION": -1,
        "NSW": 0,
        "ISMEAR": 0,
        "SIGMA": 0.05,
        "LREAL": False,     # Must be False for phonon accuracy
        "LWAVE": False,
        "LCHARG": False,
        "NELM": 300,
    },
}

_TAG_COMMENTS: dict[str, str] = {
    "PREC": "Precision: Accurate gives good cutoff & FFT grid",
    "ENCUT": "Plane-wave energy cutoff (eV).  Rule: 1.3x max ENMAX in POTCAR",
    "EDIFF": "SCF energy convergence (eV).  1e-6 is standard",
    "EDIFFG": "Ionic convergence.  Negative = force criterion (eV/A)",
    "IBRION": "Relaxation algo: 2=CG, 1=quasi-Newton, -1=single point",
    "ISIF": "Stress tensor: 3=relax all, 2=fix cell, 0=fix cell+volume",
    "NSW": "Max number of ionic steps",
    "ISMEAR": "Smearing: 0=Gaussian (insulator), 1=MP (metal), -5=tetrahedron",
    "SIGMA": "Smearing width (eV).  Entropy term T*S should be < 1 meV/atom",
    "LREAL": "Real-space projectors: Auto or False for small cells",
    "LWAVE": "Write WAVECAR? True only if you need it for post-processing",
    "LCHARG": "Write CHGCAR? True for DOS, band structure, Bader",
    "NELM": "Max electronic (SCF) iterations",
    "LDAU": "Activate on-site Coulomb correction (DFT+U)",
    "LDAUTYPE": "DFT+U flavour: 2=Dudarev (U_eff = U - J)",
    "LDAUL": "Angular momentum for +U: -1=off, 2=d-electrons, 3=f-electrons",
    "LDAUU": "U parameter (eV) for each species",
    "LDAUJ": "J parameter (eV) for each species",
    "LDAUPRINT": "Print occupancy matrices (2=verbose)",
    "IVDW": "vdW correction: 11=D3(zero), 12=D3(BJ), 20=TS",
    "ISPIN": "1=non-spin-polarized, 2=spin-polarized",
    "MAGMOM": "Initial magnetic moments per atom",
}


class VaspInputSet:
    """Generate VASP input files for a given structure and calculation type.

    Parameters
    ----------
    atoms : ase.Atoms
        Crystal structure.
    calc_type : str
        One of the preset names: "relax", "scf", "dft_plus_u",
        "dft_d3", "phonon".
    overrides : dict, optional
        Additional INCAR tags that override the preset.
    kpoints_density : float
        k-point density in 1/A.  Higher = more k-points = more accurate
        but slower.  Typical values: 30-50 for relaxation, 50-80 for
        accurate energies.
    potcar_map : dict, optional
        Mapping element -> POTCAR variant, e.g. {"Sr": "Sr_sv", "O": "O"}.
        Used only to write a POTCAR reference file (actual POTCAR must
        come from your VASP license).
    """

    def __init__(
        self,
        atoms: Atoms,
        calc_type: str = "relax",
        overrides: dict[str, Any] | None = None,
        kpoints_density: float = 40.0,
        potcar_map: dict[str, str] | None = None,
    ):
        if calc_type not in _INCAR_PRESETS:
            raise ValueError(
                f"Unknown calc_type '{calc_type}'.  "
                f"Choose from: {list(_INCAR_PRESETS)}"
            )

        self.atoms = atoms.copy()
        self.calc_type = calc_type
        self.kpoints_density = kpoints_density
        self.potcar_map = potcar_map or {}

        # Merge preset + overrides
        self.incar_tags: dict[str, Any] = dict(_INCAR_PRESETS[calc_type])
        if overrides:
            self.incar_tags.update(overrides)

    # ------------------------------------------------------------------
    # INCAR
    # ------------------------------------------------------------------

    def _format_incar_value(self, value: Any) -> str:
        """Format a Python value as a VASP INCAR value string."""
        if isinstance(value, bool):
            return ".TRUE." if value else ".FALSE."
        if isinstance(value, (list, tuple)):
            return " ".join(str(v) for v in value)
        return str(value)

    def write_incar(self, directory: str | Path) -> Path:
        """Write an INCAR file with explanatory comments."""
        path = Path(directory) / "INCAR"
        lines = [f"# VASP INCAR -- {self.calc_type} calculation", ""]

        for tag, value in self.incar_tags.items():
            comment = _TAG_COMMENTS.get(tag, "")
            val_str = self._format_incar_value(value)
            if comment:
                lines.append(f"  {tag} = {val_str}    # {comment}")
            else:
                lines.append(f"  {tag} = {val_str}")

        lines.append("")
        path.write_text("\n".join(lines))
        return path

    # ------------------------------------------------------------------
    # POSCAR
    # ------------------------------------------------------------------

    def write_poscar(self, directory: str | Path) -> Path:
        """Write a POSCAR file using ASE."""
        path = Path(directory) / "POSCAR"
        ase_write(str(path), self.atoms, format="vasp", vasp5=True)
        return path

    # ------------------------------------------------------------------
    # KPOINTS
    # ------------------------------------------------------------------

    def _auto_kpoints(self) -> tuple[int, int, int]:
        """Compute a Gamma-centred k-point grid from density.

        Rule: k_i = max(1, ceil(density / |b_i|))  where b_i is the
        reciprocal lattice vector length.
        """
        recip_lengths = np.linalg.norm(
            self.atoms.cell.reciprocal() * 2 * np.pi, axis=1
        )
        kpts = [max(1, int(np.ceil(self.kpoints_density * r))) for r in recip_lengths]
        return tuple(kpts)

    def write_kpoints(self, directory: str | Path) -> Path:
        """Write a KPOINTS file (automatic Gamma-centred grid)."""
        kpts = self._auto_kpoints()
        path = Path(directory) / "KPOINTS"
        lines = [
            "Automatic mesh",
            "0",          # 0 = automatic generation
            "Gamma",      # Gamma-centred grid
            f"  {kpts[0]}  {kpts[1]}  {kpts[2]}",
            "  0  0  0",  # shift
        ]
        path.write_text("\n".join(lines) + "\n")
        return path

    # ------------------------------------------------------------------
    # POTCAR reference
    # ------------------------------------------------------------------

    def write_potcar_reference(self, directory: str | Path) -> Path:
        """Write a POTCAR_REFERENCE file listing required pseudopotentials.

        VASP pseudopotentials are licensed software.  This file tells
        the student which POTCAR files to concatenate.
        """
        species = []
        seen = set()
        for s in self.atoms.get_chemical_symbols():
            if s not in seen:
                species.append(s)
                seen.add(s)

        path = Path(directory) / "POTCAR_REFERENCE"
        lines = [
            "# POTCAR reference -- you must supply your own POTCAR from",
            "# your VASP pseudopotential library.",
            "#",
            "# Concatenate in this order:",
            "#   cat POT1 POT2 ... > POTCAR",
            "#",
            "# Recommended variants (PBE):",
        ]
        for s in species:
            variant = self.potcar_map.get(s, s)
            lines.append(f"#   {s}  ->  {variant}")

        lines.append("#")
        lines.append(f"# Species order in POSCAR: {' '.join(species)}")
        path.write_text("\n".join(lines) + "\n")
        return path

    # ------------------------------------------------------------------
    # Write all
    # ------------------------------------------------------------------

    def write_all(self, directory: str | Path) -> dict[str, Path]:
        """Write INCAR, POSCAR, KPOINTS, POTCAR_REFERENCE to *directory*.

        Creates the directory if it does not exist.

        Returns
        -------
        dict mapping filename -> Path.
        """
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        paths = {
            "INCAR": self.write_incar(directory),
            "POSCAR": self.write_poscar(directory),
            "KPOINTS": self.write_kpoints(directory),
            "POTCAR_REFERENCE": self.write_potcar_reference(directory),
        }

        # Also dump a machine-readable JSON summary
        meta = {
            "calc_type": self.calc_type,
            "formula": self.atoms.get_chemical_formula(),
            "n_atoms": len(self.atoms),
            "kpoints": list(self._auto_kpoints()),
            "incar_tags": {
                k: self._format_incar_value(v)
                for k, v in self.incar_tags.items()
            },
        }
        meta_path = directory / "calc_info.json"
        meta_path.write_text(json.dumps(meta, indent=2) + "\n")
        paths["calc_info.json"] = meta_path

        return paths

    def explain(self) -> str:
        """Return a human-readable explanation of all INCAR tags."""
        lines = [f"=== INCAR explanation for '{self.calc_type}' calculation ===", ""]
        for tag, value in self.incar_tags.items():
            comment = _TAG_COMMENTS.get(tag, "(no description)")
            lines.append(f"  {tag} = {self._format_incar_value(value)}")
            lines.append(f"    -> {comment}")
            lines.append("")
        return "\n".join(lines)


# =====================================================================
# Output parser
# =====================================================================

class VaspOutputParser:
    """Parse VASP output files for energies, forces, and convergence.

    This is a lightweight parser for teaching purposes.  For production
    work, use pymatgen.io.vasp.outputs.Vasprun.

    Parameters
    ----------
    directory : str or Path
        Path to the VASP calculation directory.
    """

    def __init__(self, directory: str | Path):
        self.directory = Path(directory)

    def _read_outcar_lines(self) -> list[str]:
        outcar = self.directory / "OUTCAR"
        if not outcar.exists():
            raise FileNotFoundError(f"OUTCAR not found in {self.directory}")
        return outcar.read_text().splitlines()

    def get_total_energy(self) -> float | None:
        """Extract the final total energy (eV) from OUTCAR."""
        energy = None
        for line in self._read_outcar_lines():
            if "free  energy   TOTEN" in line:
                energy = float(line.split()[-2])
        return energy

    def get_total_energy_sigma0(self) -> float | None:
        """Extract energy(sigma->0), the best energy for insulators."""
        energy = None
        for line in self._read_outcar_lines():
            if "energy  without entropy" in line:
                # Format: "energy  without entropy=   -XX.XXX  energy(sigma->0) =   -XX.XXX"
                parts = line.split("energy(sigma->0) =")
                if len(parts) == 2:
                    energy = float(parts[1].strip())
        return energy

    def get_forces(self) -> np.ndarray | None:
        """Extract the final forces (eV/A) from OUTCAR."""
        lines = self._read_outcar_lines()
        forces = []
        reading = False
        for line in reversed(lines):
            if "TOTAL-FORCE" in line:
                # We found the last force block; now collect
                reading = True
                forces = []
                continue
            if reading:
                if "---" in line:
                    if forces:
                        break
                    continue
                parts = line.split()
                if len(parts) == 6:
                    forces.append([float(parts[3]), float(parts[4]), float(parts[5])])

        if forces:
            forces.reverse()
            return np.array(forces)
        return None

    def is_converged(self) -> bool:
        """Check if the ionic relaxation converged."""
        for line in self._read_outcar_lines():
            if "reached required accuracy" in line:
                return True
        return False

    def get_band_gap(self) -> float | None:
        """Extract band gap from vasprun.xml using pymatgen (if available)."""
        vasprun_path = self.directory / "vasprun.xml"
        if not vasprun_path.exists():
            return None
        try:
            from pymatgen.io.vasp.outputs import Vasprun
            vrun = Vasprun(str(vasprun_path), parse_dos=False, parse_eigen=True)
            bg = vrun.get_band_structure().get_band_gap()
            return bg.get("energy")
        except Exception:
            return None

    def get_magnetization(self) -> float | None:
        """Extract total magnetization from OUTCAR."""
        mag = None
        for line in self._read_outcar_lines():
            if "number of electron" in line and "magnetization" in line:
                parts = line.split("magnetization")
                if len(parts) == 2:
                    mag = float(parts[1].strip())
        return mag

    def summary(self) -> dict:
        """Return a summary dict of parsed results."""
        result = {"directory": str(self.directory)}
        try:
            result["total_energy_eV"] = self.get_total_energy()
            result["energy_sigma0_eV"] = self.get_total_energy_sigma0()
            result["converged"] = self.is_converged()
            result["magnetization"] = self.get_magnetization()

            forces = self.get_forces()
            if forces is not None:
                result["max_force_eV_per_A"] = float(np.max(np.abs(forces)))
                result["n_atoms"] = len(forces)

            result["band_gap_eV"] = self.get_band_gap()
        except FileNotFoundError:
            result["error"] = "OUTCAR not found"

        return result
