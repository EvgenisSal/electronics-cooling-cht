#!/usr/bin/env python3
# Generates blockMeshDict for the electronics-cooling-cht UNIT CELL.
# Geometry per docs/geometry-design.md. Units: mm (convertToMeters 0.001).

# --- Coordinate breakpoints (mm) ---
x = [0.0, 20.0, 60.0, 100.0]      # inlet | heatsink | outlet
y = [0.0, 0.5, 5.0, 5.5]          # half-fin | channel | half-fin
z = [0.0, 1.0, 1.2, 4.2, 24.2]    # chip | TIM | base | fins+channel

# --- Cells per interval (scaled by refinement factor) ---
import sys
REFINE = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0

def scale(lst):
    return [max(1, round(v * REFINE)) for v in lst]

nx = scale([15, 40, 20])   # inlet, heatsink, outlet
ny = scale([3, 16, 3])     # finL, channel, finR
nz = scale([3, 2, 6, 24])  # chip, TIM, base, fins

# --- Build vertex grid ---
nX, nY, nZ = len(x), len(y), len(z)

def vid(i, j, k):
    return i*nY*nZ + j*nZ + k

verts = []
for i in range(nX):
    for j in range(nY):
        for k in range(nZ):
            verts.append((x[i], y[j], z[k]))

# --- Block helper ---
def block(i, j, k, zone, grading="simpleGrading (1 1 1)"):
    c = [vid(i,   j,   k),   vid(i+1, j,   k),
         vid(i+1, j+1, k),   vid(i,   j+1, k),
         vid(i,   j,   k+1), vid(i+1, j,   k+1),
         vid(i+1, j+1, k+1), vid(i,   j+1, k+1)]
    n = f"({nx[i]} {ny[j]} {nz[k]})"
    return f"    hex ({' '.join(map(str, c))}) {zone} {n} {grading}"

# --- Blocks: i=x-interval, j=y-interval, k=z-interval ---
blocks = []

# Inlet duct: air only, top z-interval (k=3), all y
for j in range(3):
    blocks.append(block(0, j, 3, "air"))

# Heatsink slab (i=1): full stack
for j in range(3):
    blocks.append(block(1, j, 0, "chip"))      # k=0 chip
    blocks.append(block(1, j, 1, "TIM"))       # k=1 TIM
    blocks.append(block(1, j, 2, "heatsink"))  # k=2 base
# k=3: finL (solid) | channel (air) | finR (solid)
blocks.append(block(1, 0, 3, "heatsink"))
blocks.append(block(1, 1, 3, "air"))
blocks.append(block(1, 2, 3, "heatsink"))

# Outlet duct: air only, k=3, all y
for j in range(3):
    blocks.append(block(2, j, 3, "air"))

# --- Face helper: 4 vertices of one face of block (i,j,k) ---
def face(i, j, k, s):
    if s == "x-": return [vid(i,j,k),   vid(i,j+1,k),   vid(i,j+1,k+1), vid(i,j,k+1)]
    if s == "x+": return [vid(i+1,j,k), vid(i+1,j,k+1), vid(i+1,j+1,k+1), vid(i+1,j+1,k)]
    if s == "y-": return [vid(i,j,k),   vid(i,j,k+1),   vid(i+1,j,k+1), vid(i+1,j,k)]
    if s == "y+": return [vid(i,j+1,k), vid(i+1,j+1,k), vid(i+1,j+1,k+1), vid(i,j+1,k+1)]
    if s == "z-": return [vid(i,j,k),   vid(i+1,j,k),   vid(i+1,j+1,k), vid(i,j+1,k)]
    if s == "z+": return [vid(i,j,k+1), vid(i,j+1,k+1), vid(i+1,j+1,k+1), vid(i+1,j,k+1)]

# --- Boundary patches (name -> (type, list of faces)) ---
patches = {
    "inlet":    ["patch",         []],
    "outlet":   ["patch",         []],
    "symLeft":  ["symmetryPlane", []],
    "symRight": ["symmetryPlane", []],
}

# inlet: air front face at x=0 (blocks i=0, all j, k=3)
for j in range(3):
    patches["inlet"][1].append(face(0, j, 3, "x-"))

# outlet: air back face at x=100 (blocks i=2, all j, k=3)
for j in range(3):
    patches["outlet"][1].append(face(2, j, 3, "x+"))

# every block, as (i,k) pairs, that reaches the y-edges
edge_blocks = [(0,3), (1,0), (1,1), (1,2), (1,3), (2,3)]

# symLeft: y=0 face (j=0) of each edge block
for (i, k) in edge_blocks:
    patches["symLeft"][1].append(face(i, 0, k, "y-"))

# symRight: y=5.5 face (j=2) of each edge block
for (i, k) in edge_blocks:
    patches["symRight"][1].append(face(i, 2, k, "y+"))

# --- Write blockMeshDict ---
lines = []
lines.append("FoamFile")
lines.append("{")
lines.append("    version 2.0;")
lines.append("    format ascii;")
lines.append("    class dictionary;")
lines.append("    object blockMeshDict;")
lines.append("}")
lines.append("")
lines.append("convertToMeters 0.001;")
lines.append("")

lines.append("vertices")
lines.append("(")
for p in verts:
    lines.append(f"    ({p[0]:g} {p[1]:g} {p[2]:g})")
lines.append(");")
lines.append("")

lines.append("blocks")
lines.append("(")
lines.extend(blocks)
lines.append(");")
lines.append("")

lines.append("edges")
lines.append("(")
lines.append(");")
lines.append("")

lines.append("defaultPatch")
lines.append("{")
lines.append("    name walls;")
lines.append("    type wall;")
lines.append("}")
lines.append("")

lines.append("boundary")
lines.append("(")
for name, (ptype, faces) in patches.items():
    lines.append(f"    {name}")
    lines.append("    {")
    lines.append(f"        type {ptype};")
    lines.append("        faces")
    lines.append("        (")
    for f in faces:
        lines.append(f"            ({f[0]} {f[1]} {f[2]} {f[3]})")
    lines.append("        );")
    lines.append("    }")
lines.append(");")
lines.append("")

lines.append("mergePatchPairs")
lines.append("(")
lines.append(");")
lines.append("")

with open("system/blockMeshDict", "w") as fh:
    fh.write("\n".join(lines) + "\n")

print(f"Wrote system/blockMeshDict: {len(verts)} vertices, {len(blocks)} blocks")

