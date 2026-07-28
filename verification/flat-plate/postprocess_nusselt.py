import numpy as np
import matplotlib.pyplot as plt

# --- Air properties (must match thermophysicalProperties) ---
rho = 1.1
mu  = 1.9e-05
cp  = 1005.0
Pr  = 0.71
k   = mu * cp / Pr        # 0.0269 W/mK

# --- Flow / geometry ---
U      = 5.0
T_wall = 350.0
T_inf  = 300.0
dT     = T_wall - T_inf
x0     = 0.02             # leading edge of plate (buffer ends here)

# --- Load sampled data (x, qflux) ---
data = np.loadtxt("postProcessing/sampleDict/1000/plateLine_wallHeatFlux.xy")
x_abs = data[:, 0]
q     = np.abs(data[:, 1])

# distance from the plate leading edge (not from domain origin)
x = x_abs - x0
mask = x > 1e-6          # drop the singular leading-edge point
x = x[mask]
q = q[mask]

# --- Local convection coefficient and Nusselt (CFD) ---
h_cfd  = q / dT
Nu_cfd = h_cfd * x / k

# --- Analytical Blasius local Nusselt ---
Re_x    = U * x / (mu / rho)
Nu_blas = 0.332 * np.sqrt(Re_x) * Pr**(1.0/3.0)

# --- Relative error ---
err = 100.0 * (Nu_cfd - Nu_blas) / Nu_blas

# --- Save CSV ---
out = np.column_stack((x, Re_x, Nu_cfd, Nu_blas, err))
np.savetxt("nusselt_comparison.csv", out,
           delimiter=",",
           header="x,Re_x,Nu_cfd,Nu_analytical,error_percent",
           comments="")

# --- Plot ---
plt.figure(figsize=(8, 5))
plt.plot(x, Nu_blas, "k-",  label="Blasius (analytical)")
plt.plot(x, Nu_cfd,  "ro", markersize=3, label="OpenFOAM (CFD)")
plt.xlabel("x from leading edge [m]")
plt.ylabel("local Nusselt number $Nu_x$")
plt.title("Flat plate: local Nusselt, CFD vs Blasius")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig("nusselt_comparison.png", dpi=150, bbox_inches="tight")

# --- Print summary (skip first 10% near leading edge) ---
core = x > 0.1 * (0.22 - x0)
print("Mean abs error (core region): %.2f %%" % np.mean(np.abs(err[core])))
print("Nu_cfd at trailing edge:  %.2f" % Nu_cfd[-1])
print("Nu_blas at trailing edge: %.2f" % Nu_blas[-1])


