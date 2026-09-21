#!/usr/bin/env bash
# Compile the solution and generate test cases.
#
# Usage:
#   cd examples/aplusb
#   bash run.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Compiling solution ==="
g++ -std=c++17 -O2 -o solution solution.cpp
echo "Compiled: ./solution"

echo ""
echo "=== Generating test cases ==="
python3 spec.py

echo ""
echo "=== Generated files ==="
ls tc/
