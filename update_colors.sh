#!/bin/bash
echo "--- Updating Team Colors ---"

# 1. Scan all data files (including newly downloaded ones) and update fallback_teams.json
echo "1. Building color map..."
python3 build_fallbacks.py

# 2. Apply those colors to the data files
echo "2. Patching data files..."
python3 patch_colors.py

echo "--- Done! ---"
