# Cavity — Natural Convection Verification

Verification of buoyancy-driven flow in a differentially heated square
cavity, compared against the de Vahl Davis (1983) benchmark at Ra = 1e5.

## Purpose

Confirms the solver reproduces natural convection (buoyancy-driven flow
and its heat transfer) correctly. Together with composite-wall
(conduction) and flat-plate (forced convection), this closes the three
heat-transfer modes present in the heat sink.

## Physical setup

- Square cavity L = 0.1 m, air, Boussinesq approximation
- Left wall hot (301.28 K), right wall cold (300 K), top/bottom adiabatic
- All walls no-slip, closed domain (no inlet/outlet)
- Rayleigh Ra = g*beta*dT*L^3 / (nu*alpha) = 1e5
  (nu=1.727e-5, beta=3.333e-3, Pr=0.71)
- Gravity active: g = (0 -9.81 0)

## Mesh

- blockMesh, single block, 120x120 hexahedral cells
- Double-sided grading toward both vertical walls (thermal boundary layers)
- checkMesh: non-orthogonality 0

## Solver

- buoyantBoussinesqSimpleFoam, steadyState, laminar
- residualControl 1e-5 (all fields) -> guaranteed convergence
- Converged in 9151 iterations

## Results

| Quantity        | CFD    | Benchmark | Error |
|-----------------|--------|-----------|-------|
| Nu_avg (hot)    | 4.688  | 4.519     | 3.8%  |
| Nu_local max    | 8.039  | 7.717     | 4.2%  |
| v_max* (mid)    | 73.5   | 68.6      | 7.1%  |

PASS: natural convection reproduced within ~4% of benchmark.

## Key lesson

Initial runs showed 25-59% Nu error. Root cause was NOT mesh or Ra, but
incomplete convergence (residuals plateaued at 1e-4 without
residualControl). Post-processing must read the latest converged time,
not a fixed timestep. Nu measured on a non-converged field is meaningless.

## Reproduce

    blockMesh
    buoyantBoussinesqSimpleFoam > log.solver 2>&1
    postProcess -func "grad(T)" -latestTime
    postProcess -func sampleDict -latestTime
    python3 postprocess_nusselt.py
