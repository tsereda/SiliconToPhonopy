from ase.build import bulk
from ase.io import write
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os

app = FastAPI()

@app.get("/si_structure")
def get_si_structure():
    # Build diamond-cubic Si cell (2 atoms)
    si = bulk('Si', 'diamond', a=5.43)
    atoms_data = {
        "symbols": si.get_chemical_symbols(),
        "positions": si.get_positions().tolist(),
        "cell": si.cell.tolist(),
        "pbc": si.get_pbc().tolist()
    }
    # Read energy from output file if exists
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
