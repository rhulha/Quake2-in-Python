#!/usr/bin/env python
"""Quick test of R_BuildWorldBuffers"""
import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load config first
try:
    with open("quake2_config.json") as f:
        config = json.load(f)
        os.environ['Q2DIR'] = config.get('quake2_directory', 'C:\\Action\\id\\q2unpacked')
except:
    os.environ['Q2DIR'] = 'C:\\Action\\id\\q2unpacked'

from ref_gl import gl_context, gl_rsurf, glw_imp, gl_model

# Initialize window and context
print("Creating window...")
glw_imp.VID_CreateWindow(800, 600, False)

print("Initializing GL context...")
gl_context.init()

# Load a map using gl_model
print("Loading map...")
try:
    worldmodel = gl_model.Mod_ForName("maps/base1.bsp", False)
    if not worldmodel:
        print("Failed to load map: Mod_ForName returned None")
        sys.exit(1)
except Exception as e:
    import traceback
    print(f"Failed to load map: {e}")
    traceback.print_exc()
    sys.exit(1)

print(f"Map loaded: {len(worldmodel.faces)} faces")

# Build buffers
print("Building world buffers...")
gl_rsurf.R_BuildWorldBuffers(worldmodel)

print("Done!")
