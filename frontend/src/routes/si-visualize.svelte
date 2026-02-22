<script lang="ts">
import { onMount } from 'svelte';
import { Canvas, Mesh, PerspectiveCamera, AmbientLight, PointLight, BoxGeometry, SphereGeometry, MeshStandardMaterial } from 'threlte';

let atoms = [];
let cell = [];
let energy: number | null = null;

onMount(async () => {
  const res = await fetch('http://localhost:8000/si_structure');
  const data = await res.json();
  atoms = data.atoms.positions.map((pos: number[], i: number) => ({
    symbol: data.atoms.symbols[i],
    position: pos
  }));
  cell = data.atoms.cell;
  energy = data.energy;
});

function getColor(symbol: string) {
  // Simple color mapping for Si
  return symbol === 'Si' ? '#a0a0ff' : '#cccccc';
}
</script>

<Canvas style="height: 400px; width: 100%;">
  <PerspectiveCamera position={{ x: 10, y: 10, z: 10 }} lookAt={{ x: 0, y: 0, z: 0 }} />
  <AmbientLight intensity={0.5} />
  <PointLight position={{ x: 10, y: 10, z: 10 }} intensity={0.8} />

  {#each atoms as atom}
    <Mesh position={{ x: atom.position[0], y: atom.position[1], z: atom.position[2] }}>
      <SphereGeometry args={[0.5, 32, 32]} />
      <MeshStandardMaterial color={getColor(atom.symbol)} />
    </Mesh>
  {/each}

  <!-- Optionally render cell box -->
  <Mesh position={{ x: cell[0][0]/2, y: cell[1][1]/2, z: cell[2][2]/2 }}>
    <BoxGeometry args={[cell[0][0], cell[1][1], cell[2][2]]} />
    <MeshStandardMaterial color="#ffffff" wireframe={true} />
  </Mesh>
</Canvas>

<div>
  <h3>Diamond-cubic Si</h3>
  <p>Total energy: {energy !== null ? energy.toFixed(4) + ' eV' : 'Loading...'}</p>
</div>
