"""
Materials Project API client for fetching structures and reference data.

Uses the mp-api package to query the Materials Project database for:
  - Crystal structures by formula or MP-ID
  - Reference energies (formation energy, energy above hull)
  - Band gaps, magnetic moments, elastic properties
  - Phase diagrams and thermodynamic stability

Teaching notes
--------------
The Materials Project (https://materialsproject.org) is a free database
of computed materials properties.  You need an API key:

  1. Register at https://materialsproject.org
  2. Go to Dashboard -> API -> Generate API Key
  3. Set the environment variable:
       export MP_API_KEY="your_key_here"
     or pass it directly to MaterialsProjectClient.

Common failure modes:
  - No API key set -> clear error message
  - Querying non-existent formula -> empty results
  - Rate limiting -> retry with backoff
"""

from __future__ import annotations

import os
import time
from typing import Any

import numpy as np


class MaterialsProjectClient:
    """Simplified client for Materials Project REST API.

    Parameters
    ----------
    api_key : str or None
        Materials Project API key.  If None, reads from the
        MP_API_KEY environment variable.

    Examples
    --------
    >>> client = MaterialsProjectClient()
    >>> struct = client.get_structure_by_formula("SrTiO3")
    >>> print(struct)
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("MP_API_KEY")
        if not self.api_key:
            raise EnvironmentError(
                "No Materials Project API key found.\n"
                "Set the MP_API_KEY environment variable:\n"
                "  export MP_API_KEY='your_key_here'\n"
                "Get a key at https://materialsproject.org/api"
            )
        self._mpr = None

    @property
    def mpr(self):
        """Lazy-initialise the MPRester client."""
        if self._mpr is None:
            from mp_api.client import MPRester
            self._mpr = MPRester(self.api_key)
        return self._mpr

    # ------------------------------------------------------------------
    # Structure queries
    # ------------------------------------------------------------------

    def get_structure_by_mpid(self, mp_id: str):
        """Fetch a pymatgen Structure by Materials Project ID.

        Parameters
        ----------
        mp_id : str
            E.g. "mp-5229" for SrTiO3.

        Returns
        -------
        pymatgen.core.Structure
        """
        doc = self.mpr.materials.summary.get_data_by_id(mp_id)
        return doc.structure

    def get_structure_by_formula(
        self,
        formula: str,
        most_stable: bool = True,
    ):
        """Fetch a structure by chemical formula.

        Parameters
        ----------
        formula : str
            E.g. "SrTiO3", "NiO", "Fe2O3".
        most_stable : bool
            If True, returns the ground-state structure (lowest
            energy_above_hull).

        Returns
        -------
        pymatgen.core.Structure
        """
        docs = self.mpr.materials.summary.search(
            formula=formula,
            fields=["material_id", "structure", "energy_above_hull",
                    "formation_energy_per_atom", "band_gap", "is_stable"],
        )
        if not docs:
            raise ValueError(
                f"No structures found for formula '{formula}'. "
                "Check spelling or try the reduced formula."
            )

        if most_stable:
            docs.sort(key=lambda d: d.energy_above_hull or 999)

        return docs[0].structure

    def search_materials(
        self,
        formula: str | None = None,
        elements: list[str] | None = None,
        band_gap_range: tuple[float, float] | None = None,
        is_stable: bool | None = None,
        max_results: int = 20,
    ) -> list[dict]:
        """Search the Materials Project database with filters.

        Parameters
        ----------
        formula : str, optional
            Chemical formula filter.
        elements : list of str, optional
            Elements that must be present.
        band_gap_range : tuple, optional
            (min_gap, max_gap) in eV.
        is_stable : bool, optional
            Only thermodynamically stable phases.
        max_results : int
            Maximum number of results.

        Returns
        -------
        list of dict
            Simplified results with key properties.
        """
        kwargs: dict[str, Any] = {
            "fields": [
                "material_id", "formula_pretty", "energy_above_hull",
                "formation_energy_per_atom", "band_gap", "is_stable",
                "nsites", "symmetry", "is_magnetic",
            ],
            "num_chunks": 1,
        }

        if formula:
            kwargs["formula"] = formula
        if elements:
            kwargs["elements"] = elements
        if band_gap_range:
            kwargs["band_gap"] = band_gap_range
        if is_stable is not None:
            kwargs["is_stable"] = is_stable

        docs = self.mpr.materials.summary.search(**kwargs)

        results = []
        for doc in docs[:max_results]:
            results.append({
                "material_id": str(doc.material_id),
                "formula": doc.formula_pretty,
                "energy_above_hull_eV": doc.energy_above_hull,
                "formation_energy_per_atom_eV": doc.formation_energy_per_atom,
                "band_gap_eV": doc.band_gap,
                "is_stable": doc.is_stable,
                "n_sites": doc.nsites,
                "spacegroup": (
                    doc.symmetry.symbol if doc.symmetry else None
                ),
                "is_magnetic": doc.is_magnetic,
            })

        return results

    # ------------------------------------------------------------------
    # Reference data for validation
    # ------------------------------------------------------------------

    def get_reference_energy(self, mp_id: str) -> dict:
        """Get reference energy data for a material.

        Useful for validating your VASP calculations against the
        Materials Project.

        Returns
        -------
        dict with energy_per_atom, formation_energy, energy_above_hull,
        band_gap, is_stable.
        """
        doc = self.mpr.materials.summary.get_data_by_id(mp_id)
        return {
            "material_id": str(doc.material_id),
            "formula": doc.formula_pretty,
            "energy_per_atom_eV": doc.energy_per_atom,
            "formation_energy_per_atom_eV": doc.formation_energy_per_atom,
            "energy_above_hull_eV": doc.energy_above_hull,
            "band_gap_eV": doc.band_gap,
            "is_stable": doc.is_stable,
        }

    def get_phonon_data(self, mp_id: str) -> dict | None:
        """Fetch phonon band structure data if available.

        Returns
        -------
        dict or None
        """
        try:
            ph_bs = self.mpr.phonon.get_data_by_id(mp_id)
            return {
                "material_id": str(mp_id),
                "has_phonon_data": True,
                "has_imaginary_modes": ph_bs.has_imaginary_freq if ph_bs else None,
            }
        except Exception:
            return None

    def get_structure_as_ase(self, mp_id: str | None = None, formula: str | None = None):
        """Fetch a structure and convert to ase.Atoms.

        Provide either mp_id or formula.

        Returns
        -------
        ase.Atoms
        """
        from pymatgen.io.ase import AseAtomsAdaptor

        if mp_id:
            struct = self.get_structure_by_mpid(mp_id)
        elif formula:
            struct = self.get_structure_by_formula(formula)
        else:
            raise ValueError("Provide either mp_id or formula")

        return AseAtomsAdaptor.get_atoms(struct)

    # ------------------------------------------------------------------
    # Convenience: elemental reference energies
    # ------------------------------------------------------------------

    def get_elemental_reference_energies(
        self,
        elements: list[str],
    ) -> dict[str, float]:
        """Get ground-state energies per atom for elemental references.

        These are needed to compute formation energies:
            E_f = E(compound) - sum_i(n_i * mu_i)

        Parameters
        ----------
        elements : list of str
            Element symbols, e.g. ["Sr", "Ti", "O"].

        Returns
        -------
        dict mapping element -> energy_per_atom (eV).
        """
        ref_energies = {}
        for el in elements:
            docs = self.mpr.materials.summary.search(
                formula=el,
                is_stable=True,
                fields=["material_id", "energy_per_atom"],
                num_chunks=1,
            )
            if docs:
                # Take the most stable elemental phase
                ref_energies[el] = min(d.energy_per_atom for d in docs)
            else:
                ref_energies[el] = None

        return ref_energies
