#!/bin/bash
# DDSM115 Motor Control - Easy Runner
cd "$(dirname "$0")"
source venv/bin/activate
python3 ddsm115_gui.py
