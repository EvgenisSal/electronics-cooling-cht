# Geometry Design — Electronics Cooling CHT

Axes: x = flow, y = spanwise (across fins), z = height.
Envelope: 100 (x) x 44 (y) x 24.2 (z) mm.

## Solids (mm)
chip (Si, k=150): 20 x 20 x 1, centered on base
TIM (k=5):        20 x 20 x 0.2
base (Al, k=200): 40 (x) x 44 (y) x 3 (z)
fins (Al, k=200): 8 fins, 40 (x) x 1 (y) x 20 (z), gap 4.5, pitch 5.5

## Air
inlet 20 + heat sink 40 + outlet 40 = 100 (x); width 44; channel height 20.
x-map: 0-20 inlet | 20-30 bare base | 30-50 chip | 50-60 bare base | 60-100 outlet
z-stack: chip 0-1 | TIM 1-1.2 | base 1.2-4.2 | fins/channel 4.2-24.2

## Simplifications
- Shrouded top (no bypass over fin tips).
- Symmetry planes at outer fin centres (half-fins at edges = full by symmetry BC).

## Heat
Q = 75 W (assumed, realistic mid-range die TDP).
q''' = Q / V_chip = 75 / (0.02*0.02*0.001) = 1.875e8 W/m3.
Per unit cell: 75 / 8 fins = 9.375 W (uniform heating idealization).

## Air properties (constant)
rho 1.1 | mu 1.9e-5 | cp 1005 | Pr 0.71 | k 0.0269   (SI units)

## Physics — Reynolds
Channel 4.5 x 20 mm -> Dh = 4A/P = 360/49 = 7.35 mm
Re (U=2 m/s) = rho*U*Dh/mu ~ 850  -> laminar
Re (U=4 m/s) ~ 1700 -> still laminar (<2300)
Duct Re higher -> transitional -> baseline runs BOTH laminar and k-omega SST.

## Two-level strategy
Unit cell: y=5.5 slice (1 pitch), symmetry, 9.375 W, ~57k cells -> parametric.
Full sink: real 20mm chip centered, ~405k cells -> baseline + mesh independence.
Difference = spreading resistance + edge effects (validation).


