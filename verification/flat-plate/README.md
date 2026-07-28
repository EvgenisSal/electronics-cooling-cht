# Flat Plate — Forced Convection Verification

Verification of forced-convection heat transfer over an isothermal flat
plate, comparing the local Nusselt number against the Blasius laminar
boundary-layer solution.

## Purpose

Confirms that the mesh and wall treatment resolve the thermal boundary
layer correctly, so the convection coefficient `h` (the basis of all air
cooling in the main heat-sink study) can be trusted.

## Physical setup

- Air, constant properties at film temperature
  (rho=1.1, mu=1.9e-5, cp=1005, Pr=0.71, k=0.0269 W/mK)
- Free-stream velocity U = 5 m/s
- Plate length L = 0.2 m, isothermal wall T = 350 K, inlet T = 300 K
- Re_L = 5.79e4  (< 5e5, laminar) -> Blasius applies
- 0.02 m symmetry buffer upstream of the plate

## Analytical reference

Local Nusselt (Blasius):  Nu_x = 0.332 * Re_x^0.5 * Pr^(1/3)
Average Nusselt:          Nu_L = 0.664 * Re_L^0.5 * Pr^(1/3) = 142.5
Average coefficient:      h_avg = Nu_L * k / L = 19.2 W/m2K

## Mesh

- blockMesh, 2 blocks (buffer + plate), 13,800 hexahedral cells
- Wall-normal grading -> first cell ~0.09 mm
- Measured y+ on plate: min 0.53, max 2.98, avg 0.76 (wall-resolved)
- checkMesh: non-orthogonality 0, max skewness ~0

## Solver

- buoyantSimpleFoam, steadyState, laminar
- g = 0 (pure forced convection, buoyancy suppressed)
- rhoConst (constant density -> clean comparison with constant-property Blasius)

## Results

- Total wall heat flux (CFD): 1.961 W  vs  analytical 1.92 W  (~2%)
- Local Nu_x profile matches Blasius within ~3% over the front 70% of
  the plate, rising to ~11% near the trailing edge (x-grading coarsening
  + Blasius asymptotic behaviour). See nusselt_comparison.png.

PASS: convection coefficient correctly reproduced.

## Reproduce

    blockMesh
    checkMesh
    buoyantSimpleFoam > log.buoyantSimpleFoam 2>&1
    buoyantSimpleFoam -postProcess -func yPlus -latestTime
    buoyantSimpleFoam -postProcess -func wallHeatFlux -latestTime
    postProcess -func sampleDict -latestTime
    python3 postprocess_nusselt.py

## Possible improvement

Reduce x-direction grading (currently 5) to shrink trailing-edge error.


