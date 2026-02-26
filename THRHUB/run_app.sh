#!/usr/bin/env bash
# THRHUB launcher for Linux/macOS
set -e

echo "=== THRHUB — Test Hole Resolution Hub ==="

# Install Python deps
pip install -r backend/requirements.txt -q

# Build React frontend
echo "Building React frontend..."
(cd frontend && npm install -s && npm run build)

# Launch Flask backend (serves API + React SPA)
echo ""
echo "THRHUB running at http://localhost:5050"
echo "Press Ctrl+C to stop."
echo ""
cd backend
python app.py
