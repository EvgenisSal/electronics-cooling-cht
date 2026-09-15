import numpy as np
import matplotlib.pyplot as plt

# --- Load sweep data (name, U, Tmax, p_inlet, p_outlet) ---
data = np.genfromtxt("airflow-sweep.dat", dtype=None, encoding=None,
                      names=["name", "U", "Tmax", "pin", "pout"])

# --- Constants ---
A_inlet = 8.8e-4   # m2, inlet cross-section (from surfaceFieldValue.dat)
Q_chip  = 75.0     # W, total chip heat load
T_ref   = 300.0    # K, inlet temperature

# --- Derived quantities ---
Rth    = (data["Tmax"] - T_ref) / Q_chip           # K/W
dP     = data["pin"] - data["pout"]                # Pa
Qflow  = data["U"] * A_inlet                       # m3/s
Ppump  = dP * Qflow                                # W

# --- Save results table ---
out = np.column_stack((data["U"], data["Tmax"], Rth, dP, Qflow, Ppump))
np.savetxt("pareto-results.csv", out, delimiter=",",
           header="U,Tmax,Rth,dP,Qflow,Ppump", comments="")

# --- Print summary ---
print(f"{'U (m/s)':>8} {'Tmax (K)':>10} {'Rth (K/W)':>10} {'dP (Pa)':>9} {'Ppump (mW)':>11}")
for i in range(len(data)):
    print(f"{data['U'][i]:8.1f} {data['Tmax'][i]:10.2f} {Rth[i]:10.4f} "
          f"{dP[i]:9.2f} {Ppump[i]*1000:11.4f}")

# --- Pareto plot ---
plt.figure(figsize=(7, 5))
plt.plot(Ppump * 1000, Rth, "o-", color="crimson")
for i in range(len(data)):
    plt.annotate(f"U={data['U'][i]:.1f} m/s",
                 (Ppump[i]*1000, Rth[i]),
                 textcoords="offset points", xytext=(8, 5), fontsize=8)
plt.xlabel("Pumping power [mW]")
plt.ylabel(r"Thermal resistance $R_{th}$ [K/W]")
plt.title("Pareto trade-off: cooling performance vs pumping power")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("pareto-plot.png", dpi=150)
print("\nSaved: pareto-results.csv, pareto-plot.png")
