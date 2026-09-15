#!/bin/bash
# airflowSweep.sh <U> <name>
# Airflow parametric sweep: set inlet velocity, run laminar CHT,
# append (name, U, Tmax_chip, p_inlet, p_outlet) to airflow-sweep.dat
set -e

U=$1
NAME=$2
echo ">>> Airflow level '$NAME'  (U = $U m/s)"

# 1. remove previous run outputs (keep 0/, constant/, system/)
foamListTimes -rm >/dev/null 2>&1 || true
rm -rf postProcessing

# 2. set inlet velocity in 0/air/U (both internalField and inlet value)
sed -i.bak "s/uniform ([0-9.]* 0 0)/uniform ($U 0 0)/" 0/air/U
rm -f 0/air/U.bak

# 3. run the solver
chtMultiRegionSimpleFoam > log.$NAME 2>&1

# 4. extract converged chip T_max and inlet/outlet pressure
TMAX=$(grep -A2 'solid region chip' log.$NAME | grep 'Min/max' | tail -1 | awk '{print $NF}')
PIN=$(tail -1 postProcessing/air/inletPressure/0/surfaceFieldValue.dat | awk '{print $2}')
POUT=$(tail -1 postProcessing/air/outletPressure/0/surfaceFieldValue.dat | awk '{print $2}')

echo "$NAME $U $TMAX $PIN $POUT" | tee -a airflow-sweep.dat
