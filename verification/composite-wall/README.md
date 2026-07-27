cat > README.md << 'EOF'
# Verification: composite wall (1D conduction, two solid regions)

Purpose: prove that region coupling in chtMultiRegionSimpleFoam conserves heat flux across a solid-solid interface

##Geometry
Region A (aluminium): L = 0.010m, k = 200W/(m K)
Region B (TIM):       L = 0.002m, k = 5  W/(m K)
Cross-section:	      A = 0.01 x 0.01 m = 1e-4 m2
Sides: adiabatic (zeroGradient) -> pure 1D

## Boundary conditions
T_hot = 350 K at x = 0		(outer face of A)
T_cold = 300 K at x = 0.012	(outer face of B)

## Analytical solution (R = L / (k A))
R_A   = 0.5 K/W
R_B   = 4.0 K/W
R_tot = 4.5 K/w 

Q	= dT / R+tot = 50 / 4.5 = 11.1111 W
q''	= Q / A 		= 111111 W/m2
T_int	= 350 - Q*R_A		= 344.4444 K

dT/dx in A = 555.6 K/m	(drop 5.556 K)
dT/dx in B = 22222 K/m	(drop 44.44 K)

Note: 89% of the total resistance sits in the 2mm TIM layer.

## Pass criteria
- T_int within 0.1% of 344.4444 K
- q'' identical on both sides of the interface within 0.1%
EOF

