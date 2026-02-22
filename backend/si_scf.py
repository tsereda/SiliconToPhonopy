from ase.build import bulk
from gpaw import GPAW, PW

# Build diamond-cubic Si cell (2 atoms)
si = bulk('Si', 'diamond', a=5.43)

# Set up GPAW calculator
calc = GPAW(mode=PW(300),  # Plane-wave cutoff (eV)
            kpts=(4, 4, 4),  # k-point grid
            xc='PBE',
            txt='si_scf_output.txt')

si.calc = calc

# Run SCF calculation
energy = si.get_potential_energy()
print(f"Total energy: {energy} eV")
