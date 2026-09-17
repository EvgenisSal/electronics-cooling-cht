# electronics-cooling-cht

![Airflow streamlines](heatsink/full-sink/paraview/airflow_streamlines_opacity45.png)

**75 W chip load | 2.49 K/W baseline R_th (laminar) | 102,915 cells | 1–4 m/s airflow sweep, Pareto analysis**

CHT simulation of an air-cooled plate-fin heat sink, built in OpenFOAM v2606.
Run entirely on a MacBook Air M2, 8 GB RAM — no cluster, no GPU.

Second CFD portfolio project, after [propeller-cfd](https://github.com/EvgenisSal/propeller-cfd).
That project was about validating a solver against a fluid-dynamics benchmark
(marine propeller, rotating flow). This one is about applying CFD to a real
thermal management problem: conjugate heat transfer in electronics cooling,
the kind of problem that shows up in GPU/CPU heat sinks.

## What this project actually does

1. Verifies the numerical building blocks (conduction, forced convection,
   natural convection) against known analytical/benchmark solutions before
   trusting the solver on the real geometry.
2. Builds the heat sink mesh parametrically from a Python script rather than
   CAD, so the geometry can be regenerated at any refinement level.
3. Runs a formal mesh-independence study (GCI, Roache's method) on a unit-cell
   model to get a defensible thermal resistance number with an error bar,
   not just "a number."
4. Runs a full baseline CHT case on the real geometry (actual 20×20 mm chip
   footprint, 8 real fins, no symmetry shortcuts), laminar and k-omega SST,
   and compares the two.
5. Runs a parametric airflow sweep and builds a Pareto front (thermal
   resistance vs. pumping power) — the actual engineering trade-off a
   thermal design decision would be based on.

Each phase has a purpose. None of it is there to pad the repo.

## Physical setup

Air-cooled plate-fin heat sink, envelope 100×44×24.2 mm.

- Silicon chip: 20×20×1 mm, k = 150 W/mK, 75 W total heat load
- TIM (thermal interface material): 20×20×0.2 mm, k = 5 W/mK
- Aluminium base: 40×44×3 mm, k = 200 W/mK
- 8 aluminium fins: 40×1×20 mm, 4.5 mm gap, 5.5 mm pitch
- Air channel above the fins, inlet air at 300 K

Air properties assumed constant: rho = 1.1, mu = 1.9e-5, cp = 1005,
Pr = 0.71, k = 0.0269 (SI units). Channel Reynolds number is roughly
850–1700 depending on inlet velocity — the laminar/turbulent transition
range, which is why turbulence modelling gets checked explicitly rather
than assumed away.

## Phase 1 — Verification

Before touching the real geometry, three simple cases check that the
solver reproduces the three heat transfer modes present in the heat
sink: conduction, forced convection, natural convection.

| Case | Physics | Result | Reference | Error |
|---|---|---|---|---|
| composite-wall | 1D conduction, two solid regions (`chtMultiRegionSimpleFoam`) | T_interface = 344.437 K | Analytical (thermal circuit) | 0.0022% |
| flat-plate | Forced convection, laminar boundary layer | Nu_x vs Blasius | Blasius similarity solution | <3% over front 70% of plate |
| cavity | Natural convection, Ra = 1e5 | Nu_avg = 4.69 | de Vahl Davis (1983) benchmark | 3.8% |

Details, meshes, and reproduction steps are in `verification/<case>/README.md`
for each of the three.

One lesson worth stating: the cavity case initially showed 25–59% error,
and the cause was not the mesh or the Rayleigh number, it was
non-convergence — residuals had plateaued at 1e-4 without a
`residualControl` block. Every case in this repo since then uses explicit
residual control, and post-processing scripts auto-detect the latest
converged timestep instead of reading a hardcoded one.

## Phase 2 — Parametric geometry

The heat sink mesh is built by a Python script (`genBlockMesh.py`) that
writes `blockMeshDict` directly, rather than through CAD or snappyHexMesh.
The script classifies every block into one of four cellZones (air, chip,
TIM, heatsink) using a geometric rule — "is this block's (x,y) footprint
inside the chip window and this z inside the chip layer" — rather than a
hardcoded list of which block is which. That's what lets the same script
generate both the symmetric unit-cell mesh and the full 8-fin geometry
without rewriting the block-assignment logic.

After `blockMesh`, `splitMeshRegions -cellZones` splits the single mesh
into four conformal regions with automatically named coupling interfaces
(e.g. `chip_to_TIM`, `heatsink_to_air`), which `chtMultiRegionSimpleFoam`
solves as a proper conjugate problem.

## Phase 3 — Mesh independence (unit cell)

Because a mesh study needs many runs at increasing resolution, this part
uses a 1-pitch unit-cell slice (symmetry planes on both sides) rather
than the full 8-fin geometry — one fin, one channel, uniform heating
approximation. It is a proxy for convergence behaviour, not the final
answer.

Three meshes (49k / 111k / 238k cells, refinement ratio ≈1.3) were run
to steady state, and Roache's GCI method applied to the peak chip
temperature:

- Apparent order of convergence: p = 0.485
- Asymptotic range check: 1.003 (should be ≈1.0 — this is valid)
- Fine-mesh uncertainty: 3.0% on T_max, 13.5% on R_th
- R_th (fine mesh) = 17.39 K/W, Richardson-extrapolated R_th = 19.27 K/W

**Errata, kept for transparency:** the TIM thermal conductivity in this
case was originally entered as k = 4 W/mK instead of the verified value
of k = 5 W/mK (a data-entry error from when the file was first created).
I caught it while setting up the full-sink case in Phase 4 — I had
already set the correct k = 5 W/mK there, then went back and cross-checked
it against this unit-cell file and the composite-wall verification
material, and found the mismatch. Went back and reran the full GCI sweep
here with the corrected value; the old results are kept as
`heatsink/unit-cell/mesh-independence-k4-WRONG.dat`. Effect on the
numbers above: about 0.2 K lower T_max across all three meshes, GCI
methodology and asymptotic ratio essentially unchanged (the error was
systematic across all mesh levels, so it mostly cancels in the GCI ratio).
Full writeup in `docs/logbook.md`.


## Phase 4 — Full-geometry baseline

The unit-cell result above is a useful convergence check, but it isn't
the real heat sink — it assumes the heat is spread uniformly across the
whole fin footprint, which the real 20×20 mm chip obviously does not do.
Phase 4 drops that assumption: real chip footprint, real 8 fins, real
side walls instead of symmetry, 102,915 cells.

**Laminar run:** T_max (chip) = 486.55 K, R_th = 2.49 K/W. Energy
balance checked via a `wallHeatFlux` functionObject on the heatsink
region: 75.00 W in from the TIM side, 75.00 W out to the air side —
matches the applied 75 W load almost exactly.

**k-omega SST run** (same mesh, same load): T_max = 483.63 K,
R_th = 2.45 K/W — about 1.6% lower than laminar. Given the channel
Reynolds number sits in the transitional range, this was worth checking
explicitly rather than assuming laminar was fine. The difference turned
out small enough that laminar is a reasonable simplification for the
parametric study in Phase 5.

**Why R_th here (2.49 K/W) is so much lower than the unit-cell number
(17.4 K/W):** the unit-cell R_th is a per-fin number — one fin carrying
1/8 of the load. Eight fins carrying the full load in parallel behave
like eight resistances in parallel: R_th ≈ 17.4/8 ≈ 2.2 K/W would be
the naive estimate. The measured 2.49 K/W is about 13% higher than that
naive estimate, which is attributed to spreading resistance (heat has
to spread laterally from the small chip footprint into the full 40×44 mm
base before it reaches the outer fins) and edge effects (the outer fins
see different local flow conditions than the interior ones) — exactly
the effects the unit-cell/symmetry simplification cannot capture.

### Results

![Temperature distribution](heatsink/full-sink/paraview/baseline_temperature.png)
*Baseline temperature field, laminar, U = 2 m/s. Chip footprint visible
as the small hot square; heat spreads through the base before reaching
the fins.*

![Mid-plane temperature slice](heatsink/full-sink/paraview/midplane_temperature_slice.png)
*Vertical cross-section through the chip centreline: chip → TIM →
aluminium base → fins → air, in one view.*

![Airflow streamlines](heatsink/full-sink/paraview/airflow_streamlines_opacity45.png)
*Streamlines through the fin channels, coloured by velocity magnitude (2.5–5.9 m/s). 
Flow accelerates in the narrow channels between fins.*


## Phase 5 — Parametric airflow study and Pareto front

The design question that actually matters for a heat sink: how much
airflow is worth the pumping power it costs. Swept inlet velocity
(U = 1.0, 1.5, 2.0, 3.0, 4.0 m/s), laminar (justified above), same
full-sink mesh and load, extracting T_max and inlet/outlet pressure
drop via `surfaceFieldValue` functionObjects each run.

Airflow rate was chosen as the swept parameter over fin geometry (fin
spacing, fin height) because it requires no remeshing — each point is
just a change to `0/air/U` and a rerun, versus a full geometry
regeneration per point for a fin-spacing sweep. Given the time and
hardware constraints on this project, that was the right trade-off; a
fin-geometry sweep is a natural extension if more time is available.

| U (m/s) | T_max (K) | R_th (K/W) | dP (Pa) | Pumping power (mW) |
|---|---|---|---|---|
| 1.0 | 530.87 | 3.078 | 1.29 | 1.14 |
| 1.5 | 502.48 | 2.700 | 2.20 | 2.90 |
| 2.0 | 486.55 | 2.487 | 3.24 | 5.70 |
| 3.0 | 468.75 | 2.250 | 5.62 | 14.84 |
| 4.0 | 458.82 | 2.118 | 8.31 | 29.25 |

Pumping power = dP × Q, with Q = U × inlet cross-section area.

![Pareto front](heatsink/full-sink/pareto-plot.png)
*Thermal resistance vs. pumping power. All five points are Pareto-optimal
— none is beaten on both axes by another.*

**Reading the front:** below U ≈ 2 m/s, small increases in pumping power
buy large drops in R_th (U: 1→2 m/s costs +4.6 mW for -0.59 K/W). Above
U ≈ 2.5–3 m/s, returns diminish sharply (U: 3→4 m/s costs +14.4 mW for
only -0.13 K/W). Since there's no single optimal point on a Pareto front,
and given this trade-off, the sensible operating range is U ≈ 2.0–2.5 m/s.
A hard requirement elsewhere (a maximum allowable junction temperature, a
specific fan's pressure-flow curve, a noise or power budget) would push
the choice outside this range — the lowest airflow that satisfies it,
even past the knee if needed.


## Limitations

- Air properties are constant (no temperature-dependent rho, mu, k).
  Reasonable for the temperature range here (300–490 K) but would need
  revisiting for a wider range.
- The parametric sweep (Phase 5) is laminar throughout, based on the
  small laminar/SST difference found at one operating point in Phase 4.
  That difference (1.6%) may not hold exactly at every swept velocity —
  it wasn't rechecked at each point, to keep the sweep to a reasonable
  number of runs.
- No fin-geometry (spacing, height) sweep — see Phase 5 above for why,
  and it's the natural next step for this project.
- Steady-state RANS only. No transient effects, no vortex shedding in
  the wake of the fins.


## Reproduce

Requires OpenFOAM v2606.

```bash
# Verification cases
cd verification/<case-name>
blockMesh && <application>   # see each case's README for specifics

# Unit-cell mesh independence + GCI
cd heatsink/unit-cell
python3 genBlockMesh.py 1.0        # or 1.3, 1.69 for other refinement levels
blockMesh
splitMeshRegions -cellZones -overwrite
chtMultiRegionSimpleFoam
python3 gci.py                     # after all three refinement levels are run

# Full-sink baseline
cd heatsink/full-sink
python3 genBlockMesh.py
blockMesh
splitMeshRegions -cellZones -overwrite
chtMultiRegionSimpleFoam

# Airflow parametric sweep + Pareto plot
cd heatsink/full-sink
./airflowSweep.sh 2.0 U2            # repeat per velocity point
python3 parametric_pareto.py
```

## Repository structure

```
verification/            # Phase 1: composite-wall, flat-plate, cavity
docs/
  geometry-design.md      # geometry, materials, physics assumptions
  logbook.md               # chronological build log, including the TIM errata
heatsink/
  unit-cell/               # Phase 2-3: parametric geometry, GCI mesh study
  full-sink/               # Phase 4-5: full baseline, laminar/SST, airflow sweep
    paraview/               # result screenshots
```
