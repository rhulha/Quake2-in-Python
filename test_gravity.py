"""
test_gravity.py - Observe player Z position over 5 seconds to check if they fall forever.
Runs headless: no window, no rendering. Just physics + collision.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Init filesystem so BSP can be found
from quake2.files import FS_InitFilesystem
FS_InitFilesystem()

# Load collision data
from quake2 import cmodel
print("Loading BSP collision data...")
cmodel.CM_LoadMap("maps/base1.bsp")
print(f"  planes={cmodel.num_planes}  nodes={cmodel.num_nodes}  "
      f"brushes={cmodel.num_brushes}  models={cmodel.num_models}")

if cmodel.num_models == 0:
    print("FATAL: no models loaded - BSP failed to load")
    sys.exit(1)

# Find spawn point from entity string
def find_spawn():
    estr = cmodel.entity_string
    i = 0
    while i < len(estr):
        si = estr.find('{', i)
        if si == -1:
            break
        end = estr.find('}', si)
        if end == -1:
            break
        block = estr[si+1:end]
        i = end + 1
        keys = {}
        j = 0
        while j < len(block):
            q1 = block.find('"', j)
            if q1 == -1:
                break
            q2 = block.find('"', q1+1)
            q3 = block.find('"', q2+1)
            q4 = block.find('"', q3+1)
            if q4 == -1:
                break
            keys[block[q1+1:q2]] = block[q3+1:q4]
            j = q4 + 1
        if keys.get('classname') == 'info_player_start':
            parts = keys.get('origin', '').split()
            if len(parts) == 3:
                return [float(p) for p in parts]
    return [0.0, 0.0, 0.0]

spawn = find_spawn()
print(f"Spawn point: {spawn}")

# Quick sanity check: can we trace straight down from spawn?
from quake2.cmodel import CM_BoxTrace, MASK_PLAYERSOLID
MINS = [-16.0, -16.0, -24.0]
MAXS = [16.0, 16.0, 32.0]

down_end = [spawn[0], spawn[1], spawn[2] - 200.0]
tr = CM_BoxTrace(spawn, down_end, MINS, MAXS, 0, MASK_PLAYERSOLID)
print(f"Sanity trace down 200: fraction={tr.fraction:.3f}  endZ={tr.endpos[2]:.1f}  "
      f"startsolid={tr.startsolid}  allsolid={tr.allsolid}")
if tr.plane:
    print(f"  hit plane normal={[round(x,3) for x in tr.plane['normal']]}")

# Set up player state
from quake2.cl_input import _State, CL_ApplyMovement
from quake2.cl_input import usercmd_t

vieworg = list(spawn)
_State.velocity = [0.0, 0.0, 0.0]
_State.on_ground = False
_State.viewangles = [0.0, 0.0, 0.0]

cmd = usercmd_t()  # no keys pressed

# Simulate 5 seconds at 60 fps
FRAMETIME = 1.0 / 60.0
FRAMES = int(5.0 / FRAMETIME)

print(f"\nSimulating {FRAMES} frames ({FRAMES*FRAMETIME:.1f}s) - no input")
print(f"{'Frame':>6}  {'Time':>5}  {'Z':>10}  {'vZ':>9}  on_gnd")
print("-" * 48)

for frame in range(FRAMES):
    vieworg = CL_ApplyMovement(cmd, vieworg, _State.viewangles, FRAMETIME)

    if frame < 10 or frame % 30 == 0:
        t = frame * FRAMETIME
        print(f"{frame:>6}  {t:>5.2f}  {vieworg[2]:>10.2f}  "
              f"{_State.velocity[2]:>9.2f}  {_State.on_ground}")

    if vieworg[2] < spawn[2] - 10000:
        print(f"  ... fell below {spawn[2]-10000:.0f}, stopping early at frame {frame}")
        break

print("-" * 48)
drop = spawn[2] - vieworg[2]
print(f"\nSpawn Z: {spawn[2]:.1f}   Final Z: {vieworg[2]:.1f}   Drop: {drop:.1f} units")
if drop > 1000:
    print("FAIL: player fell through the floor")
elif drop > 10:
    print(f"WARN: player dropped {drop:.0f} units (partial fall)")
else:
    print("PASS: player stayed near spawn Z")
