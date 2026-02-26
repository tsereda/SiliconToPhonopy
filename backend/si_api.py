"""
FastAPI backend for DFT workflow generation and structure visualization.
"""

from __future__ import annotations

import os
import tempfile
import traceback

from ase.build import bulk
from fastapi import FastAPI, HTTPException, Query, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

app = FastAPI(
    title="SiliconToPhonopy DFT Workflows",
    description="API for generating VASP inputs and learning DFT calculations",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================================
# Create the API Router with the /api prefix
# =====================================================================
api_router = APIRouter(prefix="/api")


# =====================================================================
# Pydantic models for request bodies
# =====================================================================

class RelaxRequest(BaseModel):
    A: str = Field("Sr", description="A-site cation (e.g. Sr, Ba, Pb)")
    B: str = Field("Ti", description="B-site cation (e.g. Ti, Zr, Nb)")
    a: float = Field(3.905, description="Lattice constant (angstroms)")
    encut: float = Field(520, description="Plane-wave cutoff (eV)")
    kpoints_density: float = Field(40.0, description="k-point density")

class SurfaceRequest(BaseModel):
    miller_h: int = Field(1, description="Miller index h")
    miller_k: int = Field(0, description="Miller index k")
    miller_l: int = Field(0, description="Miller index l")
    min_slab_size: float = Field(10.0, description="Min slab thickness (A)")
    min_vacuum_size: float = Field(15.0, description="Vacuum thickness (A)")
    freeze_bottom: int = Field(2, description="Bottom layers to freeze")

class VacancyRequest(BaseModel):
    supercell: list[int] = Field([2, 2, 2], description="Supercell dims")
    vacancy_element: str = Field("O", description="Element to remove")

class DftURequest(BaseModel):
    material: str = Field("NiO", description="NiO or Fe2O3")
    u_value: float = Field(6.2, description="Hubbard U (eV)")
    j_value: float = Field(0.0, description="Hund J (eV)")

class D3Request(BaseModel):
    a: float = Field(2.464, description="In-plane lattice constant (A)")
    c: float = Field(6.711, description="Out-of-plane lattice constant (A)")

class PhononRequest(BaseModel):
    supercell_matrix: list[list[int]] = Field(
        [[2, 0, 0], [0, 2, 0], [0, 0, 2]],
        description="Supercell matrix",
    )
    displacement: float = Field(0.01, description="Displacement (A)")


# =====================================================================
# Original Si endpoint
# =====================================================================

@api_router.get("/si_structure")
def get_si_structure():
    """Build diamond-cubic Si cell (2 atoms) and return structure data."""
    si = bulk("Si", "diamond", a=5.43)
    atoms_data = {
        "symbols": si.get_chemical_symbols(),
        "positions": si.get_positions().tolist(),
        "cell": si.cell.tolist(),
        "pbc": si.get_pbc().tolist(),
    }
    energy = None
    if os.path.exists("si_scf_output.txt"):
        with open("si_scf_output.txt") as f:
            for line in f:
                if "Total energy:" in line:
                    try:
                        energy = float(line.split()[-2])
                    except Exception:
                        continue
    return JSONResponse({"atoms": atoms_data, "energy": energy})


# =====================================================================
# Structure builders
# =====================================================================

def _atoms_to_dict(atoms) -> dict:
    """Convert ASE Atoms to a JSON-serialisable dict."""
    return {
        "symbols": atoms.get_chemical_symbols(),
        "positions": atoms.get_positions().tolist(),
        "cell": atoms.cell.tolist(),
        "pbc": atoms.get_pbc().tolist(),
        "formula": atoms.get_chemical_formula(),
        "n_atoms": len(atoms),
    }


@api_router.post("/structures/perovskite")
def build_perovskite_endpoint(req: RelaxRequest):
    """Build a cubic perovskite ABO3 unit cell."""
    from dft_workflows.core.crystal_builders import build_perovskite
    atoms = build_perovskite(A=req.A, B=req.B, a=req.a)
    return JSONResponse(_atoms_to_dict(atoms))


@api_router.post("/structures/rocksalt")
def build_rocksalt_endpoint(
    cation: str = Query("Ni"),
    anion: str = Query("O"),
    a: float = Query(4.177),
):
    """Build a rocksalt (NaCl-type) unit cell."""
    from dft_workflows.core.crystal_builders import build_rocksalt
    atoms = build_rocksalt(cation=cation, anion=anion, a=a)
    return JSONResponse(_atoms_to_dict(atoms))


@api_router.post("/structures/graphite")
def build_graphite_endpoint(req: D3Request):
    """Build an AB-stacked graphite unit cell."""
    from dft_workflows.core.crystal_builders import build_graphite
    atoms = build_graphite(a=req.a, c=req.c)
    return JSONResponse(_atoms_to_dict(atoms))


# =====================================================================
# Workflow endpoints
# =====================================================================

@api_router.post("/workflows/relax")
def workflow_relax(req: RelaxRequest):
    """Generate VASP inputs for perovskite relaxation."""
    try:
        from dft_workflows.workflows import PerovskiteRelaxation
        with tempfile.TemporaryDirectory() as tmpdir:
            wf = PerovskiteRelaxation(
                A=req.A, B=req.B, a=req.a,
                encut=req.encut,
                kpoints_density=req.kpoints_density,
                output_dir=tmpdir,
            )
            result = wf.setup()
            # Read generated files
            result["incar"] = _read_file(tmpdir, "INCAR")
            result["poscar"] = _read_file(tmpdir, "POSCAR")
            result["kpoints"] = _read_file(tmpdir, "KPOINTS")
            return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/workflows/surface")
def workflow_surface(req: SurfaceRequest):
    """Generate VASP inputs for surface slab model."""
    try:
        from dft_workflows.workflows import SurfaceSlabWorkflow
        with tempfile.TemporaryDirectory() as tmpdir:
            wf = SurfaceSlabWorkflow(
                miller_index=(req.miller_h, req.miller_k, req.miller_l),
                min_slab_size=req.min_slab_size,
                min_vacuum_size=req.min_vacuum_size,
                freeze_bottom=req.freeze_bottom,
                output_dir=tmpdir,
            )
            result = wf.setup()
            result["incar"] = _read_file(tmpdir, "INCAR")
            result["poscar"] = _read_file(tmpdir, "POSCAR")
            result["kpoints"] = _read_file(tmpdir, "KPOINTS")
            return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/workflows/vacancy")
def workflow_vacancy(req: VacancyRequest):
    """Generate VASP inputs for vacancy formation energy."""
    try:
        from dft_workflows.workflows import VacancyFormationEnergy
        with tempfile.TemporaryDirectory() as tmpdir:
            wf = VacancyFormationEnergy(
                supercell_dims=tuple(req.supercell),
                vacancy_element=req.vacancy_element,
                output_dir=tmpdir,
            )
            result = wf.setup()
            return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/workflows/dftu")
def workflow_dftu(req: DftURequest):
    """Generate PBE and PBE+U VASP inputs for comparison."""
    try:
        from dft_workflows.workflows import DftPlusUComparison
        with tempfile.TemporaryDirectory() as tmpdir:
            wf = DftPlusUComparison(
                material=req.material,
                u_value=req.u_value,
                j_value=req.j_value,
                output_dir=tmpdir,
            )
            result = wf.setup()
            return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/workflows/d3")
def workflow_d3(req: D3Request):
    """Generate PBE and PBE-D3 VASP inputs for graphite."""
    try:
        from dft_workflows.workflows import DftD3Graphite
        with tempfile.TemporaryDirectory() as tmpdir:
            wf = DftD3Graphite(a=req.a, c=req.c, output_dir=tmpdir)
            result = wf.setup()
            return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/workflows/phonon")
def workflow_phonon(req: PhononRequest):
    """Generate Phonopy displaced supercell VASP inputs."""
    try:
        from dft_workflows.workflows import PhononDispersion
        with tempfile.TemporaryDirectory() as tmpdir:
            wf = PhononDispersion(
                supercell_matrix=req.supercell_matrix,
                displacement=req.displacement,
                output_dir=tmpdir,
            )
            result = wf.setup()
            return JSONResponse(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# Materials Project endpoints
# =====================================================================

@api_router.get("/materials/{formula}")
def search_materials(
    formula: str,
    max_results: int = Query(10, ge=1, le=50),
):
    """Search Materials Project for structures by formula."""
    try:
        from dft_workflows.core.materials_project import MaterialsProjectClient
        client = MaterialsProjectClient()
        results = client.search_materials(formula=formula, max_results=max_results)
        return JSONResponse({"formula": formula, "results": results})
    except EnvironmentError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/materials/id/{mp_id}")
def get_material_by_id(mp_id: str):
    """Get structure and reference data by Materials Project ID."""
    try:
        from dft_workflows.core.materials_project import MaterialsProjectClient
        client = MaterialsProjectClient()
        ref = client.get_reference_energy(mp_id)
        struct = client.get_structure_by_mpid(mp_id)
        from pymatgen.io.ase import AseAtomsAdaptor
        atoms = AseAtomsAdaptor.get_atoms(struct)
        ref["structure"] = _atoms_to_dict(atoms)
        return JSONResponse(ref)
    except EnvironmentError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# Helpers
# =====================================================================

def _read_file(directory: str, filename: str) -> str | None:
    """Read a file from a directory, return None if not found."""
    path = os.path.join(directory, filename)
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return None

# Attach all API routes to the main app!
app.include_router(api_router)