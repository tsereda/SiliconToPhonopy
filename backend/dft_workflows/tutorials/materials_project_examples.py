#!/usr/bin/env python3
"""
Materials Project API tutorial: fetch structures and reference data.

This script teaches how to use the Materials Project API to:
  1. Search for materials by formula
  2. Download crystal structures
  3. Get reference energies for validating your VASP calculations
  4. Convert between pymatgen and ASE formats
  5. Use MP data as starting points for your calculations

Prerequisites
-------------
1. Install mp-api:  pip install mp-api
2. Get an API key at https://materialsproject.org/api
3. Set the environment variable:
       export MP_API_KEY="your_key_here"

Usage
-----
    python materials_project_examples.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


def check_api_key():
    """Check if MP_API_KEY is set."""
    key = os.environ.get("MP_API_KEY")
    if not key:
        print("=" * 60)
        print("Materials Project API Key Required")
        print("=" * 60)
        print()
        print("To use these examples, you need a Materials Project API key.")
        print()
        print("Steps:")
        print("  1. Create a free account at https://materialsproject.org")
        print("  2. Go to Dashboard -> API -> Generate API Key")
        print("  3. Set the environment variable:")
        print("       export MP_API_KEY='your_key_here'")
        print()
        print("Then re-run this script.")
        return False
    return True


def example_1_search_by_formula():
    """Search for materials by chemical formula."""
    print("\n" + "=" * 60)
    print("Example 1: Search by formula")
    print("=" * 60)

    from dft_workflows.core.materials_project import MaterialsProjectClient
    client = MaterialsProjectClient()

    # Search for SrTiO3
    results = client.search_materials(formula="SrTiO3")

    print(f"\nFound {len(results)} entries for SrTiO3:\n")
    for r in results:
        print(f"  {r['material_id']:12s}  {r['formula']:10s}  "
              f"E_hull={r['energy_above_hull_eV']:.4f} eV  "
              f"Eg={r['band_gap_eV']:.2f} eV  "
              f"{'STABLE' if r['is_stable'] else 'metastable'}")


def example_2_get_structure():
    """Download a crystal structure and convert to ASE."""
    print("\n" + "=" * 60)
    print("Example 2: Download structure")
    print("=" * 60)

    from dft_workflows.core.materials_project import MaterialsProjectClient
    client = MaterialsProjectClient()

    # Get the most stable SrTiO3 structure
    atoms = client.get_structure_as_ase(formula="SrTiO3")

    print(f"\nSrTiO3 from Materials Project:")
    print(f"  Formula: {atoms.get_chemical_formula()}")
    print(f"  Atoms: {len(atoms)}")
    print(f"  Cell: {atoms.cell.lengths()}")
    print(f"  Symbols: {atoms.get_chemical_symbols()}")


def example_3_reference_energies():
    """Get reference energies for validation."""
    print("\n" + "=" * 60)
    print("Example 3: Reference energies for validation")
    print("=" * 60)

    from dft_workflows.core.materials_project import MaterialsProjectClient
    client = MaterialsProjectClient()

    # Get elemental reference energies (needed for formation energy)
    elements = ["Sr", "Ti", "O"]
    refs = client.get_elemental_reference_energies(elements)

    print(f"\nElemental reference energies (PBE):")
    for el, e in refs.items():
        print(f"  {el}: {e:.4f} eV/atom" if e else f"  {el}: not found")

    print("\nUse these to compute formation energy:")
    print("  E_f(SrTiO3) = E(SrTiO3) - E(Sr) - E(Ti) - 3*E(O)")


def example_4_compare_with_your_calc():
    """Show how to compare VASP results with MP reference data."""
    print("\n" + "=" * 60)
    print("Example 4: Compare your calculation with MP")
    print("=" * 60)

    from dft_workflows.core.materials_project import MaterialsProjectClient
    client = MaterialsProjectClient()

    # Get reference data for NiO
    results = client.search_materials(formula="NiO", is_stable=True)

    if results:
        r = results[0]
        print(f"\nNiO reference data from Materials Project:")
        print(f"  MP ID: {r['material_id']}")
        print(f"  Formation energy: {r['formation_energy_per_atom_eV']:.4f} eV/atom")
        print(f"  Band gap: {r['band_gap_eV']:.2f} eV")
        print(f"  Is magnetic: {r['is_magnetic']}")
        print(f"  Spacegroup: {r['spacegroup']}")

        print("\nAfter your VASP calculation, compare:")
        print("  - Your E_f vs MP E_f (should agree within ~0.1 eV/atom)")
        print("  - Your band gap vs MP band gap")
        print("  - Your lattice constant vs MP structure")
        print("  - Note: MP uses GGA+U for transition metal oxides")


def example_5_generate_vasp_from_mp():
    """Download a structure from MP and generate VASP inputs."""
    print("\n" + "=" * 60)
    print("Example 5: MP structure -> VASP inputs")
    print("=" * 60)

    from dft_workflows.core.materials_project import MaterialsProjectClient
    from dft_workflows.core.vasp_io import VaspInputSet

    client = MaterialsProjectClient()

    # Get Fe2O3 from MP
    atoms = client.get_structure_as_ase(formula="Fe2O3")

    print(f"\nFe2O3 from Materials Project:")
    print(f"  {len(atoms)} atoms, {atoms.get_chemical_formula()}")

    # Generate VASP inputs
    vis = VaspInputSet(atoms=atoms, calc_type="relax", kpoints_density=40.0)

    output_dir = Path("mp_Fe2O3_relax")
    paths = vis.write_all(output_dir)

    print(f"\nVASP inputs written to: {output_dir}")
    for name, path in paths.items():
        print(f"  {name}: {path}")


def main():
    if not check_api_key():
        print("\n--- Running in demo mode (no API calls) ---\n")
        print("The following examples are available when you set MP_API_KEY:")
        print("  1. Search by formula (SrTiO3, NiO, Fe2O3, ...)")
        print("  2. Download crystal structures")
        print("  3. Get reference energies for validation")
        print("  4. Compare your VASP results with MP data")
        print("  5. Download from MP -> generate VASP inputs")
        return

    try:
        example_1_search_by_formula()
        example_2_get_structure()
        example_3_reference_energies()
        example_4_compare_with_your_calc()
        example_5_generate_vasp_from_mp()
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure your MP_API_KEY is valid and you have internet access.")


if __name__ == "__main__":
    main()
