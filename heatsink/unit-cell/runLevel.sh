#!/bin/bash
# runLevel.sh <factor> <name>
# Mesh-independence helper: regenerate mesh at <factor>, run the CHT case,
# append (name, factor, nCells, Tmax_chip) to mesh-independence.dat
set -e

FACTOR=$1
NAME=$2
echo ">>> Level '$NAME'  (refinement factor $FACTOR)"

# 1. remove previous mesh + run outputs (keep 0/, constant props, system/)
foamListTimes -rm >/dev/null 2>&1 || true
rm -rf constant/polyMesh constant/*/polyMesh constant/cellToRegion

# 2. build mesh at this level and split into regions
python3 genBlockMesh.py "$FACTOR"
blockMesh                               > log.blockMesh.$NAME 2>&1
splitMeshRegions -cellZones -overwrite  > log.split.$NAME     2>&1

# 3. restore per-region numerics (split writes empty stubs)
git checkout -- system/air system/chip system/TIM system/heatsink

# 4. run the solver
chtMultiRegionSimpleFoam > log.$NAME 2>&1

# 5. extract cell count and converged chip T_max
NCELLS=$(grep -m1 'nCells' log.blockMesh.$NAME | awk '{print $NF}')
TMAX=$(grep -A2 'solid region chip' log.$NAME | grep 'Min/max' | tail -1 | awk '{print $NF}')
echo "$NAME $FACTOR $NCELLS $TMAX" | tee -a mesh-independence.dat


