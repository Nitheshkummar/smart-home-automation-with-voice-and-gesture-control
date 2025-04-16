#!/bin/bash

echo "[INFO] Starting DHT11.py..."
python3 DHT11.py &

echo "[INFO] Starting voice_command_handler.py..."
python3 voice_command_handler.py &

echo "[INFO] Starting sarvamAPI2.py..."
python3 sarvamAPI2.py &

echo "[INFO] All scripts are running in the background."
echo "Use 'ps aux | grep python3' to see running processes."
echo "Press Ctrl+C to stop this terminal session (scripts will keep running unless killed manually)."
