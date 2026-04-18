#!/bin/bash
# Jebi Hackathon 2026 — Grupo 7
# Ejecutar desde la raíz del repo: bash run.sh
#
# Inputs esperados en ./inputs/:
#   - *left*.mp4  o  shovel_left.mp4
#   - *right*.mp4 o  shovel_right.mp4
#   - *.npy       o  imu_data.csv
#
# Outputs en ./outputs/:
#   - metrics.json, cycles.json, truck_events.json, fill_factor.json
#   - report.html, summary.md

set -e

echo "=== Jebi Hackathon 2026 — Grupo 7 ==="
echo "Inputs:"
ls -la inputs/
echo ""

# 1. IMU: ciclos, paradas y suavidad del operador
echo "[1/4] IMU pipeline (ciclos + jerk)..."
python3 solution/imu_pipeline.py
echo ""

# 2. Intercambios de camión (tiempo muerto) — usa IMU como fuente principal
echo "[2/4] Truck exchange pipeline..."
python3 solution/truck_pipeline.py
echo ""

# 3. Fill factor estéreo — puede tardar ~3-4 min
echo "[3/4] Stereo fill factor pipeline..."
python3 solution/video/stereo_pipeline.py
echo ""

# 4. Agregar métricas + report.html + summary.md
echo "[4/4] Generando métricas y reporte final..."
python3 solution/main.py
echo ""

echo "=== COMPLETADO ==="
echo "Outputs generados:"
ls -la outputs/
