#!/usr/bin/env python3
# Generates blockMeshDict for the electronics-cooling-cht FULL SINK.
# Geometry per docs/geometry-design.md. Units: mm (convertToMeters 0.001).

# --- Coordinate breakpoints (mm) ---
# x: inlet | bare base | chip footprint | bare base | outlet
x = [0.0, 20.0, 30.0, 50.0, 60.0, 100.0]

# y: half-channel | [fin | channel] x7 | fin | half-channel
# chip window (12-32mm) cuts two of the channel intervals in half.
y = [0.0, 2.25, 3.25, 7.75, 8.75, 12.0, 13.25, 14.25,
     18.75, 19.75, 24.25, 25.25, 29.75, 30.75,
     32.0, 35.25, 36.25, 40.75, 41.75, 44.0]

# z: chip | TIM | base | fins+channel
z = [0.0, 1.0, 1.2, 4.2, 24.2]



# --- Cells per interval (scaled by refinement factor) ---
import sys
REFINE = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0

def scale(lst):
    return [max(1, round(v * REFINE)) for v in lst]

nx = scale([15, 8, 15, 8, 20])
ny = scale([3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3])
nz = scale([3, 2, 6, 24])

# --- Chip footprint bounds (mm), for zone classification ---
CHIP_X = (30.0, 50.0)
CHIP_Y = (12.0, 32.0)
HEATSINK_X = (20.0, 60.0)

def zone(i, j, k):
    """Classify block (i,j,k) into a cellZone name, or None if no solid/fluid exists there."""
    x_lo, x_hi = x[i], x[i+1]
    y_lo, y_hi = y[j], y[j+1]

    in_chip_x = (x_lo >= CHIP_X[0] - 1e-6) and (x_hi <= CHIP_X[1] + 1e-6)
    in_chip_y = (y_lo >= CHIP_Y[0] - 1e-6) and (y_hi <= CHIP_Y[1] + 1e-6)
    in_heatsink_x = (x_lo >= HEATSINK_X[0] - 1e-6) and (x_hi <= HEATSINK_X[1] + 1e-6)

    if k == 0:  # chip layer
        return "chip" if (in_chip_x and in_chip_y) else None
    if k == 1:  # TIM layer
        return "TIM" if (in_chip_x and in_chip_y) else None
    if k == 2:  # base layer
        return "heatsink" if in_heatsink_x else None
    if k == 3:  # fins/channel layer
        if not in_heatsink_x:
            return "air"          # inlet/outlet duct
        is_fin = (y_hi - y_lo) < 2.0 and abs((y_hi - y_lo) - 1.0) < 0.1
        return "heatsink" if is_fin else "air"


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
def block(i, j, k, zname, grading="simpleGrading (1 1 1)"):
    c = [vid(i,   j,   k),   vid(i+1, j,   k),
         vid(i+1, j+1, k),   vid(i,   j+1, k),
         vid(i,   j,   k+1), vid(i+1, j,   k+1),
         vid(i+1, j+1, k+1), vid(i,   j+1, k+1)]
    n = f"({nx[i]} {ny[j]} {nz[k]})"
    return f"    hex ({' '.join(map(str, c))}) {zname} {n} {grading}"

# --- Blocks: loop every (i,j,k), ask zone() what it is, skip if None ---
blocks = []
for i in range(nX - 1):
    for j in range(nY - 1):
        for k in range(nZ - 1):
            zname = zone(i, j, k)
            if zname is not None:
                blocks.append(block(i, j, k, zname))

# --- Face helper: 4 vertices of one face of block (i,j,k) ---
def face(i, j, k, s):
    if s == "x-": return [vid(i,j,k),   vid(i,j+1,k),   vid(i,j+1,k+1), vid(i,j,k+1)]
    if s == "x+": return [vid(i+1,j,k), vid(i+1,j,k+1), vid(i+1,j+1,k+1), vid(i+1,j+1,k)]
    if s == "y-": return [vid(i,j,k),   vid(i,j,k+1),   vid(i+1,j,k+1), vid(i+1,j,k)]
    if s == "y+": return [vid(i,j+1,k), vid(i+1,j+1,k), vid(i+1,j+1,k+1), vid(i,j+1,k+1)]
    if s == "z-": return [vid(i,j,k),   vid(i+1,j,k),   vid(i+1,j+1,k), vid(i,j+1,k)]
    if s == "z+": return [vid(i,j,k+1), vid(i,j+1,k+1), vid(i+1,j+1,k+1), vid(i+1,j,k+1)]

# --- Boundary patches: only inlet/outlet named explicitly ---
# All other exterior faces (side walls, exposed bare-base underside,
# fin tips, top) fall through to defaultPatch below -> "walls".
patches = {
    "inlet":  ["patch", []],
    "outlet": ["patch", []],
}

# inlet: air front face at x=0 (i=0, all j, k=3, air-only layer)
for j in range(nY - 1):
    patches["inlet"][1].append(face(0, j, nZ - 2, "x-"))

# outlet: air back face at x=100 (i=nX-2, all j, k=3)
for j in range(nY - 1):
    patches["outlet"][1].append(face(nX - 2, j, nZ - 2, "x+"))


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
