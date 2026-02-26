"""
Crystal structure builders for common solid-state materials.

Uses ASE and pymatgen to construct bulk crystals, surface slabs, and
defective supercells from scratch -- no CIF files required.

Teaching notes
--------------
* Every builder returns an ase.Atoms object so it plugs straight into
  VASP / GPAW / any ASE calculator.
* ``build_surface_slab`` wraps pymatgen's SlabGenerator, which correctly
  handles Miller indices, slab thickness, vacuum, and symmetry.
* ``build_supercell_with_vacancy`` shows how to create a point defect
  by removing an atom from a supercell -- the starting point for
  vacancy-formation-energy calculations.
"""

from __future__ import annotations

import numpy as np
from ase import Atoms
from ase.build import bulk


# ---------------------------------------------------------------------------
# Perovskite  ABO3  (cubic, space group Pm-3m, #221)
# ---------------------------------------------------------------------------

def build_perovskite(
    A: str = "Sr",
    B: str = "Ti",
    a: float = 3.905,
) -> Atoms:
    """Build a cubic perovskite ABO3 unit cell.

    The conventional cubic perovskite has 5 atoms:
        A  at (0,   0,   0)          -- corner
        B  at (0.5, 0.5, 0.5)        -- body centre
        O1 at (0.5, 0.5, 0)          -- face centres
        O2 at (0.5, 0,   0.5)
        O3 at (0,   0.5, 0.5)

    Parameters
    ----------
    A : str
        A-site cation symbol (e.g. "Sr", "Ba", "Pb").
    B : str
        B-site cation symbol (e.g. "Ti", "Zr", "Nb").
    a : float
        Lattice constant in angstroms.  SrTiO3 experimental ≈ 3.905 A.

    Returns
    -------
    ase.Atoms
        5-atom cubic unit cell with periodic boundary conditions.
    """
    cell = np.eye(3) * a
    positions = np.array([
        [0.0, 0.0, 0.0],       # A
        [0.5, 0.5, 0.5],       # B
        [0.5, 0.5, 0.0],       # O
        [0.5, 0.0, 0.5],       # O
        [0.0, 0.5, 0.5],       # O
    ]) * a
    symbols = [A, B, "O", "O", "O"]
    atoms = Atoms(symbols=symbols, positions=positions, cell=cell, pbc=True)
    return atoms


# ---------------------------------------------------------------------------
# Rocksalt  (NaCl structure, space group Fm-3m, #225)
# ---------------------------------------------------------------------------

def build_rocksalt(
    cation: str = "Ni",
    anion: str = "O",
    a: float = 4.177,
) -> Atoms:
    """Build a rocksalt (NaCl-type) unit cell.

    Used for NiO (antiferromagnetic Mott insulator) and many other
    transition-metal monoxides.

    Parameters
    ----------
    cation, anion : str
        Chemical symbols.
    a : float
        Cubic lattice constant in angstroms.  NiO exp. ≈ 4.177 A.

    Returns
    -------
    ase.Atoms
        2-atom primitive cell (or use ``bulk()`` convention).
    """
    # ASE's bulk() builds the primitive 2-atom cell for rocksalt
    atoms = bulk(cation + anion, crystalstructure="rocksalt", a=a)
    return atoms


# ---------------------------------------------------------------------------
# Corundum  alpha-Fe2O3 / alpha-Al2O3 (R-3c, #167)
# ---------------------------------------------------------------------------

def build_corundum(
    metal: str = "Fe",
    a: float = 5.038,
    c: float = 13.772,
) -> Atoms:
    """Build the corundum (alpha-M2O3) conventional hexagonal cell.

    The corundum structure has 30 atoms in the conventional hexagonal
    cell (12 metal + 18 oxygen).  We build it from known Wyckoff positions.

    Parameters
    ----------
    metal : str
        Metal symbol.  "Fe" for hematite, "Al" for sapphire.
    a, c : float
        Hexagonal lattice constants.  Fe2O3 exp: a=5.038, c=13.772 A.

    Returns
    -------
    ase.Atoms
    """
    from pymatgen.core import Lattice, Structure
    from pymatgen.io.ase import AseAtomsAdaptor

    lattice = Lattice.hexagonal(a, c)

    # Wyckoff positions for corundum (R-3c)
    # Metal at 12c: (0, 0, z) with z ≈ 0.3553 for Fe2O3
    # Oxygen at 18e: (x, 0, 1/4) with x ≈ 0.3059 for Fe2O3
    species = [metal, "O"]
    coords = [
        [0.0, 0.0, 0.3553],   # Metal 12c
        [0.3059, 0.0, 0.25],  # Oxygen 18e
    ]

    struct = Structure.from_spacegroup(
        167,  # R-3c
        lattice,
        species,
        coords,
    )

    return AseAtomsAdaptor.get_atoms(struct)


# ---------------------------------------------------------------------------
# Graphite  (P6_3/mmc, #194)
# ---------------------------------------------------------------------------

def build_graphite(
    a: float = 2.464,
    c: float = 6.711,
) -> Atoms:
    """Build an AB-stacked graphite unit cell (4 atoms).

    Parameters
    ----------
    a, c : float
        Hexagonal lattice constants.  Experimental: a=2.464, c=6.711 A.

    Returns
    -------
    ase.Atoms
    """
    from pymatgen.core import Lattice, Structure
    from pymatgen.io.ase import AseAtomsAdaptor

    lattice = Lattice.hexagonal(a, c)

    # Graphite P63/mmc Wyckoff positions:
    # C1 at 2b: (0, 0, 1/4)
    # C2 at 2c: (1/3, 2/3, 1/4)
    struct = Structure.from_spacegroup(
        194,  # P6_3/mmc
        lattice,
        ["C", "C"],
        [[0, 0, 0.25], [1 / 3, 2 / 3, 0.25]],
    )
    return AseAtomsAdaptor.get_atoms(struct)


# ---------------------------------------------------------------------------
# Surface slab builder
# ---------------------------------------------------------------------------

def build_surface_slab(
    atoms: Atoms,
    miller_index: tuple[int, int, int] = (1, 0, 0),
    min_slab_size: float = 10.0,
    min_vacuum_size: float = 15.0,
    center_slab: bool = True,
) -> Atoms:
    """Cut a surface slab from a bulk crystal.

    Wraps pymatgen's SlabGenerator for robust slab construction that
    respects crystal symmetry.

    Parameters
    ----------
    atoms : ase.Atoms
        Bulk unit cell.
    miller_index : tuple of int
        Surface orientation, e.g. (1,0,0), (1,1,0), (1,1,1).
    min_slab_size : float
        Minimum slab thickness in angstroms.
    min_vacuum_size : float
        Vacuum layer thickness in angstroms.
    center_slab : bool
        If True, centre the slab in the vacuum.

    Returns
    -------
    ase.Atoms
        Slab supercell with vacuum along the c-axis.
    """
    from pymatgen.core import Structure
    from pymatgen.core.surface import SlabGenerator
    from pymatgen.io.ase import AseAtomsAdaptor

    # ASE -> pymatgen
    adaptor = AseAtomsAdaptor()
    struct = adaptor.get_structure(atoms)

    slabgen = SlabGenerator(
        struct,
        miller_index=miller_index,
        min_slab_size=min_slab_size,
        min_vacuum_size=min_vacuum_size,
        center_slab=center_slab,
        in_unit_planes=False,
    )

    slabs = slabgen.get_slabs()
    if not slabs:
        raise ValueError(
            f"No slabs generated for Miller index {miller_index}. "
            "Try a different orientation or larger slab size."
        )

    # Take the first (most stoichiometric / symmetric) slab
    slab_struct = slabs[0]

    return adaptor.get_atoms(slab_struct)


# ---------------------------------------------------------------------------
# Supercell with vacancy
# ---------------------------------------------------------------------------

def build_supercell_with_vacancy(
    atoms: Atoms,
    supercell_dims: tuple[int, int, int] = (2, 2, 2),
    vacancy_element: str | None = None,
    vacancy_index: int | None = None,
) -> tuple[Atoms, Atoms, dict]:
    """Build a supercell and create a single vacancy.

    Returns both the pristine and defective supercells, plus metadata
    needed to compute the vacancy formation energy.

    Parameters
    ----------
    atoms : ase.Atoms
        Primitive / unit cell.
    supercell_dims : tuple of int
        Repetitions along a, b, c.
    vacancy_element : str or None
        Which element to remove.  If None, removes the first atom.
    vacancy_index : int or None
        Specific atom index to remove.  Overrides vacancy_element.

    Returns
    -------
    pristine : ase.Atoms
        Supercell without defect.
    defective : ase.Atoms
        Supercell with one atom removed.
    info : dict
        {"removed_symbol": str, "removed_position": array,
         "n_atoms_pristine": int, "n_atoms_defective": int,
         "supercell_dims": tuple}
    """
    pristine = atoms.repeat(supercell_dims)

    # Decide which atom to remove
    if vacancy_index is not None:
        idx = vacancy_index
    elif vacancy_element is not None:
        symbols = pristine.get_chemical_symbols()
        indices = [i for i, s in enumerate(symbols) if s == vacancy_element]
        if not indices:
            raise ValueError(
                f"Element '{vacancy_element}' not found in supercell. "
                f"Available: {set(symbols)}"
            )
        idx = indices[0]
    else:
        idx = 0

    removed_symbol = pristine[idx].symbol
    removed_position = pristine[idx].position.copy()

    defective = pristine.copy()
    del defective[idx]

    info = {
        "removed_symbol": removed_symbol,
        "removed_position": removed_position.tolist(),
        "n_atoms_pristine": len(pristine),
        "n_atoms_defective": len(defective),
        "supercell_dims": supercell_dims,
    }

    return pristine, defective, info
