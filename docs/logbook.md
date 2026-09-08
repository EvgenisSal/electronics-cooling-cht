Composite-wall verification: blockMeshDict (2 cellZones), controlDict, fvSchemes, fvSolution set up. blockMesh + checkMesh pass — 24 cells, non-orthogonality 0, Mesh OK.
First working chtMultiRegionSimpleFoam run. T_interface = 344.437 K vs analytical 344.444 K, error 0.0022%, within 0.1%. Temperature continuity confirmed at coupled interface.
Heat flux verification via wallHeatFlux functionObject. Interface flux +/-11.109 W (both sides agree 0.001%), vs analytical 11.111 W (error 0.015%). Both temperature and heat flux continuity confirmed. Verification phase complete.

## 2026-07-28 — flat-plate
Forced convection verification. blockMesh 2 blocks, 13.8k cells, y+ ~0.76 avg.
buoyantSimpleFoam laminar, g=0. Nu_x vs Blasius: <3% front 70%, ~11% trailing edge.
Total heat flux 1.96 W vs 1.92 analytical. Fixed gitignore (polyMesh escaping in nested cases).

## 2026-07-28 — cavity
de Vahl Davis natural convection, Ra=1e5. buoyantBoussinesqSimpleFoam Boussinesq.
Nu_avg 4.69 vs 4.519 benchmark (3.8%). Fought 25-59% error: was NON-CONVERGENCE,
not mesh. Added residualControl 1e-5, converged 9151 iter. Python was reading old
timestep 2000 not 9151 - fixed to auto-find latest. Phase 1 verification DONE.

## 2026-07-31 — Phase 2: unit cell mesh
- genBlockMesh.py: Python -> blockMeshDict, parametric, 4 cellZones (air/chip/TIM/heatsink).
- 18 blocks, tensor-product vertex grid, patches inlet/outlet/symLeft/symRight + defaultPatch walls.
- blockMesh + checkMesh OK: non-ortho 0, skew ~0, max aspect 12. Trimmed 168k -> ~49k baseline.
- Next: splitMeshRegions -cellZones, then per-region 0/ BCs + constant/ properties.

## 2026-08-04 — Phase 2 complete
- splitMeshRegions -cellZones: 4 regions (air / chip / TIM / heatsink)
- Conformal interfaces, CHT path: chip -> TIM -> heatsink -> air
- air_to_heatsink = single fluid-solid coupled patch
- regionProperties: fluid (air), solid (chip TIM heatsink)
- Mesh OK (non-ortho 0, skewness ~0)

## 2026-08-06 — Phase 3 substeps 3-4 (baseline)
- chtMultiRegionSimpleFoam case complete: materials, 0/ fields, fvOptions (5W chip), numerics
- Fluid air: rhoConst, laminar, U_in=2 m/s, T_in=300K
- Solid regions need dummy p field (thermo API requirement)
- Slow solid convergence fixed by relaxation boost: U 0.3->0.5, h 0.3->0.7
- Converged (residuals <1e-4) on coarse mesh ~49k cells
- Baseline: T_max chip = 384.43 K -> R_th = (384.43-300)/5 = 16.9 K/W
- Next: substep 5 mesh independence + GCI

## 2026-08-06 — Phase 3 substep 5 (mesh independence + GCI) — COMPLETE
- Parametrized genBlockMesh.py with refinement factor (argv)
- runLevel.sh: automated mesh -> split -> solve -> extract pipeline
- 3 meshes: coarse 49k, medium 111k, fine 238k (r ~1.3)
- T_max: 384.44 / 385.93 / 387.17 K (monotonic)
- GCI (Roache): p=0.49, asymptotic ratio 1.003 (valid)
- Fine-mesh uncertainty: 3.0% on T_max, 13.5% on R_th
- R_th fine = 17.4 K/W, Richardson extrapolation = 19.3 K/W
- Phase 3 COMPLETE

## 2026-09-08 — TIM material errata + GCI rerun
- Found TIM/thermophysicalProperties had kappa=4, Cp=800 since first commit
  (d6f1bbe, Aug 6) instead of the verified composite-wall values kappa=5, Cp=1000.
- Root cause: typo/data-entry error when creating the file, never corrected.
- Discovered while setting up Phase 4 full-sink (copied TIM properties, noticed
  mismatch vs composite-wall verification case).
- Corrected kappa 4->5, Cp 800->1000. Re-ran full GCI sweep (coarse/medium/fine).
- Impact: T_max shifted ~0.2K lower across all 3 meshes (higher TIM k = less
  thermal resistance = cooler chip), consistent direction and magnitude at
  every refinement level. GCI methodology unaffected: p=0.485 (was 0.49),
  asymptotic ratio 1.003 (unchanged), GCI fine T_max 3.04% (was ~3.0%).
- R_th fine = 17.39 K/W (was 17.4), Richardson extrap = 19.27 K/W (was 19.3).
  Negligible change to final engineering conclusion.
- Old (k=4) results kept as heatsink/unit-cell/mesh-independence-k4-WRONG.dat
  for transparency.

## 2026-09-08 — Phase 4.4: full-sink laminar baseline
- Full-sink case setup complete: 4 regions, real 20x20mm chip footprint
  centered in 40x44mm base, 8 full fins + side walls (not symmetry).
- 0/ BCs, materials, fvOptions (75W chip, real total load) ported from
  unit-cell and adapted (dropped symLeft/symRight, real walls patch).
- Added wallHeatFlux functionObject on heatsink region for energy balance check.
- Laminar run, 102915 cells, converged 10000 iterations, 694s compute time.
- Energy balance verified: heatsink_to_TIM = +75.00 W in, heatsink_to_air
  = -75.00 W out (matches applied 75W chip load almost exactly).
- T_max chip = 486.55 K, R_th = (486.55-300)/75 = 2.49 K/W.
- R_th much lower than unit-cell's 17.4 K/W (expected -- 8 fins operate in
  parallel on the real geometry, vs unit-cell's single-fin idealization).
  Naive parallel estimate: 17.4/8 = 2.18 K/W. Real R_th (2.49) is ~13%
  higher than this naive estimate, attributed to spreading resistance
  (heat must spread laterally from the small chip footprint into the full
  40x44mm base) and edge effects (outer fins see different local flow
  than the interior fins) -- exactly the effects the unit-cell/symmetry
  simplification could not capture.
- Next: Phase 4.5, same mesh with k-omega SST turbulence model.
