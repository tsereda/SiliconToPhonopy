#!/usr/bin/env python3
"""
Master tutorial script: generates VASP inputs for ALL six workflows.

This script is the starting point for a graduate student learning DFT.
It generates complete VASP input files and explanatory READMEs for:

  1. SrTiO3 perovskite relaxation
  2. Surface slab model (SrTiO3 (100))
  3. Oxygen vacancy formation energy
  4. PBE vs DFT+U comparison (NiO)
  5. DFT-D3 corrections (graphite)
  6. Phonon dispersions (SrTiO3 with Phonopy)

Each workflow is self-contained with its own README explaining:
  - What the calculation does and why
  - Key INCAR parameters and what they mean
  - How to run the calculation
  - Common failure modes and how to fix them
  - How to analyse results

Usage
-----
    cd /path/to/SiliconToPhonopy/backend
    python -m dft_workflows.tutorials.run_all_workflows --output-dir ./dft_calculations

This creates a directory tree:
    dft_calculations/
    ├── 01_SrTiO3_relax/
    ├── 02_surface_slab/
    ├── 03_vacancy/
    ├── 04_dft_plus_u/
    ├── 05_dft_d3_graphite/
    └── 06_phonons/
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from dft_workflows.workflows import (
    PerovskiteRelaxation,
    SurfaceSlabWorkflow,
    VacancyFormationEnergy,
    DftPlusUComparison,
    DftD3Graphite,
    PhononDispersion,
)


def main():
    parser = argparse.ArgumentParser(
        description="Generate VASP inputs for DFT learning workflows"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./dft_calculations",
        help="Base directory for all calculation folders",
    )
    parser.add_argument(
        "--workflows",
        nargs="*",
        default=["all"],
        choices=["all", "relax", "surface", "vacancy", "dftu", "d3", "phonon"],
        help="Which workflows to generate (default: all)",
    )
    args = parser.parse_args()

    base = Path(args.output_dir)
    base.mkdir(parents=True, exist_ok=True)

    run_all = "all" in args.workflows

    results = {}

    # ------------------------------------------------------------------
    # 1. Perovskite relaxation
    # ------------------------------------------------------------------
    if run_all or "relax" in args.workflows:
        print("=" * 60)
        print("1. SrTiO3 Perovskite Relaxation")
        print("=" * 60)
        wf = PerovskiteRelaxation(
            A="Sr", B="Ti", a=3.905,
            output_dir=base / "01_SrTiO3_relax",
        )
        result = wf.setup()
        results["01_relax"] = result
        print(f"   Formula: {result['formula']}")
        print(f"   Atoms: {result['n_atoms']}")
        print(f"   Output: {result['output_dir']}")
        print()

    # ------------------------------------------------------------------
    # 2. Surface slab
    # ------------------------------------------------------------------
    if run_all or "surface" in args.workflows:
        print("=" * 60)
        print("2. Surface Slab Model: SrTiO3 (100)")
        print("=" * 60)
        wf = SurfaceSlabWorkflow(
            miller_index=(1, 0, 0),
            min_slab_size=10.0,
            min_vacuum_size=15.0,
            output_dir=base / "02_surface_slab",
        )
        result = wf.setup()
        results["02_surface"] = result
        print(f"   Formula: {result['formula']}")
        print(f"   Atoms: {result['n_atoms']}")
        print(f"   Slab thickness: {result['slab_thickness_A']:.1f} A")
        print(f"   Vacuum: {result['vacuum_thickness_A']:.1f} A")
        print(f"   Output: {result['output_dir']}")
        print()

    # ------------------------------------------------------------------
    # 3. Vacancy formation energy
    # ------------------------------------------------------------------
    if run_all or "vacancy" in args.workflows:
        print("=" * 60)
        print("3. Oxygen Vacancy in SrTiO3 (2x2x2 supercell)")
        print("=" * 60)
        wf = VacancyFormationEnergy(
            supercell_dims=(2, 2, 2),
            vacancy_element="O",
            output_dir=base / "03_vacancy",
        )
        result = wf.setup()
        results["03_vacancy"] = result
        info = result["vacancy_info"]
        print(f"   Pristine: {info['n_atoms_pristine']} atoms")
        print(f"   Defective: {info['n_atoms_defective']} atoms")
        print(f"   Removed: {info['removed_symbol']}")
        print(f"   Output: {base / '03_vacancy'}")
        print()

    # ------------------------------------------------------------------
    # 4. PBE vs DFT+U (NiO)
    # ------------------------------------------------------------------
    if run_all or "dftu" in args.workflows:
        print("=" * 60)
        print("4. PBE vs DFT+U: NiO")
        print("=" * 60)
        wf = DftPlusUComparison(
            material="NiO",
            u_value=6.2,
            j_value=0.0,
            output_dir=base / "04_dft_plus_u",
        )
        result = wf.setup()
        results["04_dftu"] = result
        print(f"   Material: {result['material']}")
        print(f"   U_eff: {result['calculations']['pbe_plus_u']['U_eff']} eV")
        print(f"   Output: {base / '04_dft_plus_u'}")
        print()

    # ------------------------------------------------------------------
    # 5. DFT-D3 for graphite
    # ------------------------------------------------------------------
    if run_all or "d3" in args.workflows:
        print("=" * 60)
        print("5. DFT-D3 Corrections: Graphite")
        print("=" * 60)
        wf = DftD3Graphite(
            a=2.464, c=6.711,
            output_dir=base / "05_dft_d3_graphite",
        )
        result = wf.setup()
        results["05_d3"] = result
        print(f"   Material: {result['material']}")
        print(f"   Initial c/a: {result['initial_c_over_a']:.3f}")
        n_calcs = len(result["calculations"])
        print(f"   Calculations: {n_calcs} (PBE, D3-BJ, D3-zero)")
        print(f"   Output: {base / '05_dft_d3_graphite'}")
        print()

    # ------------------------------------------------------------------
    # 6. Phonon dispersions
    # ------------------------------------------------------------------
    if run_all or "phonon" in args.workflows:
        print("=" * 60)
        print("6. Phonon Dispersions: SrTiO3 (Phonopy)")
        print("=" * 60)
        wf = PhononDispersion(
            supercell_matrix=[[2, 0, 0], [0, 2, 0], [0, 0, 2]],
            displacement=0.01,
            output_dir=base / "06_phonons",
        )
        result = wf.setup()
        results["06_phonon"] = result
        print(f"   Primitive cell: {result['n_atoms_primitive']} atoms")
        print(f"   Supercell: {result['n_atoms_supercell']} atoms")
        print(f"   Displacements: {result['n_displacements']}")
        print(f"   Output: {base / '06_phonons'}")
        print()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("=" * 60)
    print("ALL WORKFLOWS GENERATED SUCCESSFULLY")
    print("=" * 60)
    print()
    print(f"Output directory: {base.resolve()}")
    print()
    print("Next steps:")
    print("  1. Read the README.md in each subdirectory")
    print("  2. Copy your POTCAR files (see POTCAR_REFERENCE)")
    print("  3. Submit calculations to your HPC cluster")
    print("  4. Run the analysis scripts after calculations complete")
    print()
    print("Suggested learning order:")
    print("  01_SrTiO3_relax  -> Learn basic relaxation")
    print("  02_surface_slab  -> Learn surface modelling")
    print("  03_vacancy       -> Learn defect calculations")
    print("  04_dft_plus_u    -> Learn about correlated materials")
    print("  05_dft_d3        -> Learn about vdW corrections")
    print("  06_phonons       -> Learn about lattice dynamics")

    # Save summary JSON
    summary_path = base / "workflow_summary.json"
    summary_path.write_text(json.dumps(results, indent=2, default=str) + "\n")
    print(f"\nSummary saved to: {summary_path}")


if __name__ == "__main__":
    main()
