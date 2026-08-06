#!/usr/bin/env python3
"""
Grid Convergence Index (Roache) for the electronics-cooling-cht mesh study.
Reads mesh-independence.dat (columns: name factor nCells Tmax_chip[K]),
computes apparent order p, Richardson extrapolation, and GCI.
"""
import math

Tin = 300.0   # inlet air temperature [K]
Q   = 5.0     # chip power in the unit cell [W]
Fs  = 1.25    # GCI safety factor (3+ meshes)

# read data, sort finest -> coarsest
rows = []
with open("mesh-independence.dat") as f:
    for line in f:
        name, factor, N, T = line.split()
        rows.append((name, int(N), float(T)))
rows.sort(key=lambda r: -r[1])
(_, N1, T1), (_, N2, T2), (_, N3, T3) = rows[:3]

# refinement ratios (3D: h ~ N^(-1/3))
r21 = (N1/N2)**(1/3)
r32 = (N2/N3)**(1/3)

e21, e32 = T1 - T2, T2 - T3
s = math.copysign(1.0, e32/e21)

# apparent order p (iterative, handles r21 != r32)
p = 2.0
for _ in range(200):
    q = math.log((r21**p - s)/(r32**p - s))
    p = abs(math.log(abs(e32/e21)) + q)/math.log(r21)

# Richardson extrapolation
T_ext = T1 + (T1 - T2)/(r21**p - 1)

def gci(f_fine, f_coarse, r):
    ea = abs((f_fine - f_coarse)/f_fine)
    return Fs*ea/(r**p - 1)

gci21_T = gci(T1, T2, r21)
gci32_T = gci(T2, T3, r32)
asymp   = gci32_T/(r21**p * gci21_T)

d1, d2 = T1-Tin, T2-Tin
gci21_d = gci(d1, d2, r21)
Rth = lambda T: (T - Tin)/Q

print(f"meshes (fine->coarse): N = {N1}, {N2}, {N3}")
print(f"T_max                : {T1:.3f}, {T2:.3f}, {T3:.3f} K")
print(f"r21 = {r21:.3f}   r32 = {r32:.3f}")
print(f"apparent order p        = {p:.3f}")
print(f"Richardson T_max (h->0) = {T_ext:.2f} K")
print(f"asymptotic-range check  = {asymp:.3f}   (want ~1.0)")
print()
print(f"GCI on T_max   : fine {gci21_T*100:.2f} %   medium {gci32_T*100:.2f} %")
print(f"GCI on dT/R_th : fine {gci21_d*100:.2f} %")
print()
print(f"R_th [K/W]: coarse {Rth(T3):.2f}  medium {Rth(T2):.2f}  fine {Rth(T1):.2f}  extrap {Rth(T_ext):.2f}")
