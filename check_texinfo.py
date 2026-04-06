import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

with open("quake2_config.json") as f:
    config = json.load(f)
    os.environ['Q2DIR'] = config.get('quake2_directory')

from quake2.qfiles import load_bsp
from ref_gl import gl_model

# Load model
lumps = load_bsp("maps/base1.bsp")
if lumps:
    from quake2 import qfiles
    # Parse texinfo from lumps
    texinfo_lump = lumps[qfiles.LUMP_TEXINFO]
    # Parse first texinfo entry
    import struct
    s_axis = list(struct.unpack_from('<fff', texinfo_lump, 0))
    s_off = struct.unpack_from('<f', texinfo_lump, 12)[0]
    t_axis = list(struct.unpack_from('<fff', texinfo_lump, 16))
    t_off = struct.unpack_from('<f', texinfo_lump, 28)[0]
    flags = struct.unpack_from('<I', texinfo_lump, 32)[0]
    texture = texinfo_lump[40:72].decode('latin-1', errors='ignore').rstrip('\x00')
    print(f"First texture name from BSP: '{texture}'")
    print(f"Texture name length: {len(texture)}")
    print(f"Bytes: {texinfo_lump[40:72]}")
