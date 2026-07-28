import numpy as np

import glob, os

L      = 0.1
dT     = 1.28

times = sorted(glob.glob("postProcessing/sampleDict/*/grad(T)_hotWall.raw"),
               key=lambda p: int(p.split("/")[2]))
latest = times[-1]
print("reading:", latest)
data = np.loadtxt(latest) 
y      = data[:, 1]
gradTx = data[:, 3]

# sort by height (patch faces may be unordered)
idx    = np.argsort(y)
y      = y[idx]
gradTx = gradTx[idx]

# local Nusselt: Nu_y = |dT/dx| * L / dT
Nu_local = np.abs(gradTx) * L / dT

# average over wall height
Nu_avg = np.trapezoid(Nu_local, y) / (y[-1] - y[0])

print("Nu_avg (CFD)       = %.4f" % Nu_avg)
print("Nu_avg (benchmark) = 4.5190")
print("error              = %.2f %%" % (100.0 * (Nu_avg - 4.519) / 4.519))
print("Nu_local max       = %.4f  (benchmark 7.717)" % np.max(Nu_local))
