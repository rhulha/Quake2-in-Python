"""
qfiles.py - Quake 2 binary file format structures and readers
Adapted from BSPParserPythonQ2 project
"""

import io
import struct
from dataclasses import dataclass

# ===== Binary Reader =====

class BinaryReader:
    def __init__(self, data: bytes):
        self._buf = io.BytesIO(data)
        self._data_len = len(data)

    def read_bytes(self, count: int) -> bytes:
        data = self._buf.read(count)
        if len(data) != count:
            raise EOFError(f"expected {count} bytes, got {len(data)}")
        return data

    def read_int(self) -> int:
        return struct.unpack("<i", self.read_bytes(4))[0]

    def read_ints(self, count: int) -> list:
        if count == 0:
            return []
        return list(struct.unpack(f"<{count}i", self.read_bytes(4 * count)))

    def read_uint16(self) -> int:
        return struct.unpack("<H", self.read_bytes(2))[0]

    def read_uint16s(self, count: int) -> list:
        if count == 0:
            return []
        return list(struct.unpack(f"<{count}H", self.read_bytes(2 * count)))

    def read_int16(self) -> int:
        return struct.unpack("<h", self.read_bytes(2))[0]

    def read_int16s(self, count: int) -> list:
        if count == 0:
            return []
        return list(struct.unpack(f"<{count}h", self.read_bytes(2 * count)))

    def read_float(self) -> float:
        return struct.unpack("<f", self.read_bytes(4))[0]

    def read_floats(self, count: int) -> list:
        if count == 0:
            return []
        return list(struct.unpack(f"<{count}f", self.read_bytes(4 * count)))

    def read_string(self, length: int) -> str:
        return self.read_bytes(length).decode("latin-1", errors="ignore")

    def length(self) -> int:
        return self._data_len

    def tell(self) -> int:
        return self._buf.tell()

    def seek(self, offset: int):
        self._buf.seek(offset)


# ===== BSP Constants =====

LUMP_ENTITIES     = 0
LUMP_PLANES       = 1
LUMP_VERTICES     = 2
LUMP_VISIBILITY   = 3
LUMP_NODES        = 4
LUMP_TEXINFO      = 5
LUMP_FACES        = 6
LUMP_LIGHTMAPS    = 7
LUMP_LEAVES       = 8
LUMP_LEAF_FACES   = 9
LUMP_LEAF_BRUSHES = 10
LUMP_EDGES        = 11
LUMP_FACE_EDGES   = 12
LUMP_MODELS       = 13
LUMP_BRUSHES      = 14
LUMP_BRUSH_SIDES  = 15
LUMP_POP          = 16
LUMP_AREAS        = 17
LUMP_AREA_PORTALS = 18
NUM_LUMPS         = 19

Q2_VERSION = 38
Q2_MAGIC   = "IBSP"

# ===== Content Flags =====

CONTENTS_SOLID        = 1
CONTENTS_WINDOW       = 2
CONTENTS_AUX          = 4
CONTENTS_LAVA         = 8
CONTENTS_SLIME        = 16
CONTENTS_WATER        = 32
CONTENTS_MIST         = 64
CONTENTS_AREAPORTAL   = 128
CONTENTS_PLAYERCLIP   = 256
CONTENTS_MONSTERCLIP  = 512
CONTENTS_CURRENT_0    = 0x40000
CONTENTS_CURRENT_90   = 0x80000
CONTENTS_CURRENT_180  = 0x100000
CONTENTS_CURRENT_270  = 0x200000
CONTENTS_CURRENT_UP   = 0x400000
CONTENTS_CURRENT_DOWN = 0x800000
CONTENTS_ORIGIN       = 0x1000000
CONTENTS_MONSTER      = 0x2000000
CONTENTS_CORPSE       = 0x4000000
CONTENTS_DETAIL       = 0x8000000
CONTENTS_TRANSLUCENT  = 0x10000000
CONTENTS_LADDER       = 0x20000000

MASK_ALL            = 0xffffffff
MASK_SOLID          = CONTENTS_SOLID | CONTENTS_WINDOW
MASK_PLAYERSOLID    = CONTENTS_SOLID | CONTENTS_PLAYERCLIP | CONTENTS_WINDOW | CONTENTS_MONSTER
MASK_DEADSOLID      = CONTENTS_SOLID | CONTENTS_PLAYERCLIP | CONTENTS_WINDOW
MASK_MONSTERSOLID   = CONTENTS_SOLID | CONTENTS_MONSTERCLIP | CONTENTS_WINDOW | CONTENTS_MONSTER
MASK_WATER          = CONTENTS_WATER | CONTENTS_LAVA | CONTENTS_SLIME
MASK_OPAQUE         = CONTENTS_SOLID | CONTENTS_SLIME | CONTENTS_LAVA
MASK_SHOT           = CONTENTS_SOLID | CONTENTS_MONSTER | CONTENTS_WINDOW | CONTENTS_CORPSE

# ===== BSP Structures =====

@dataclass
class Plane:
    normal: list
    dist: float
    type: int
    SIZE = 20

@dataclass
class Vertex:
    point: list
    SIZE = 12

@dataclass
class Node:
    plane_num: int
    children: list
    mins: list
    maxs: list
    first_face: int
    num_faces: int
    SIZE = 28

@dataclass
class Leaf:
    contents: int
    cluster: int
    area: int
    mins: list
    maxs: list
    first_leaf_face: int
    num_leaf_faces: int
    first_leaf_brush: int
    num_leaf_brushes: int
    SIZE = 28

@dataclass
class Brush:
    first_side: int
    num_sides: int
    contents: int
    SIZE = 12

@dataclass
class BrushSide:
    plane_num: int
    texinfo: int
    SIZE = 4

@dataclass
class Model:
    mins: list
    maxs: list
    origin: list
    headnode: int
    first_face: int
    num_faces: int
    SIZE = 48

@dataclass
class Area:
    numareaportals: int
    firstareaportal: int
    SIZE = 8

@dataclass
class AreaPortal:
    portalnum: int
    otherarea: int
    SIZE = 8

@dataclass
class Face:
    plane_num: int
    side: int
    first_edge: int
    num_edges: int
    texinfo: int
    styles: list
    lightofs: int
    SIZE = 20

@dataclass
class TexInfo:
    vecs: list
    flags: int
    nexttexinfo: int
    imageindex: int
    SIZE = 40

@dataclass
class Edge:
    v: list
    SIZE = 4


# ===== BSP File Reader =====

def load_bsp(path: str) -> list:
    """Load BSP file and return lumps"""
    try:
        # Use Quake 2 filesystem to load the file
        from .files import FS_LoadFile
        data, length = FS_LoadFile(path)
        if data is None:
            return None
    except:
        return None

    br = BinaryReader(data)

    magic = br.read_string(4)
    version = br.read_int()
    if magic != Q2_MAGIC:
        raise ValueError(f"not a Q2 BSP (magic={magic!r})")
    if version != Q2_VERSION:
        raise ValueError(f"expected BSP version {Q2_VERSION}, got {version}")

    offsets, lengths = [], []
    for _ in range(NUM_LUMPS):
        offsets.append(br.read_int())
        lengths.append(br.read_int())

    return [data[offsets[i]: offsets[i] + lengths[i]] for i in range(NUM_LUMPS)]


# ===== Lump Readers =====

def read_planes(lumps: list) -> list:
    br = BinaryReader(lumps[LUMP_PLANES])
    result = []
    for _ in range(br.length() // Plane.SIZE):
        normal = br.read_floats(3)
        dist = br.read_float()
        ptype = br.read_int()
        result.append({'normal': normal, 'dist': dist, 'type': ptype})
    return result


def read_vertices(lumps: list) -> list:
    br = BinaryReader(lumps[LUMP_VERTICES])
    result = []
    for _ in range(br.length() // Vertex.SIZE):
        result.append(br.read_floats(3))
    return result


def read_nodes(lumps: list) -> list:
    br = BinaryReader(lumps[LUMP_NODES])
    result = []
    for _ in range(br.length() // Node.SIZE):
        node = {
            'plane_num': br.read_int(),
            'children': br.read_ints(2),
            'mins': br.read_int16s(3),
            'maxs': br.read_int16s(3),
            'first_face': br.read_uint16(),
            'num_faces': br.read_uint16(),
        }
        result.append(node)
    return result


def read_leafs(lumps: list) -> list:
    br = BinaryReader(lumps[LUMP_LEAVES])
    result = []
    for _ in range(br.length() // Leaf.SIZE):
        leaf = {
            'contents': br.read_int(),
            'cluster': br.read_int16(),
            'area': br.read_int16(),
            'mins': br.read_int16s(3),
            'maxs': br.read_int16s(3),
            'first_leaf_face': br.read_uint16(),
            'num_leaf_faces': br.read_uint16(),
            'first_leaf_brush': br.read_uint16(),
            'num_leaf_brushes': br.read_uint16(),
        }
        result.append(leaf)
    return result


def read_leaf_faces(lumps: list) -> list:
    br = BinaryReader(lumps[LUMP_LEAF_FACES])
    return br.read_uint16s(br.length() // 2)


def read_leaf_brushes(lumps: list) -> list:
    br = BinaryReader(lumps[LUMP_LEAF_BRUSHES])
    return br.read_uint16s(br.length() // 2)


def read_brushes(lumps: list) -> list:
    br = BinaryReader(lumps[LUMP_BRUSHES])
    result = []
    for _ in range(br.length() // Brush.SIZE):
        brush = {
            'first_side': br.read_int(),
            'num_sides': br.read_int(),
            'contents': br.read_int(),
        }
        result.append(brush)
    return result


def read_brush_sides(lumps: list) -> list:
    br = BinaryReader(lumps[LUMP_BRUSH_SIDES])
    result = []
    for _ in range(br.length() // BrushSide.SIZE):
        side = {
            'plane_num': br.read_uint16(),
            'texinfo': br.read_int16(),
        }
        result.append(side)
    return result


def read_models(lumps: list) -> list:
    br = BinaryReader(lumps[LUMP_MODELS])
    result = []
    for _ in range(br.length() // Model.SIZE):
        model = {
            'mins': br.read_floats(3),
            'maxs': br.read_floats(3),
            'origin': br.read_floats(3),
            'headnode': br.read_int(),
            'first_face': br.read_int(),
            'num_faces': br.read_int(),
        }
        result.append(model)
    return result


def read_areas(lumps: list) -> list:
    br = BinaryReader(lumps[LUMP_AREAS])
    result = []
    for _ in range(br.length() // Area.SIZE):
        area = {
            'numareaportals': br.read_int(),
            'firstareaportal': br.read_int(),
        }
        result.append(area)
    return result


def read_area_portals(lumps: list) -> list:
    br = BinaryReader(lumps[LUMP_AREA_PORTALS])
    result = []
    for _ in range(br.length() // AreaPortal.SIZE):
        portal = {
            'portalnum': br.read_int(),
            'otherarea': br.read_int(),
        }
        result.append(portal)
    return result


def read_visibility(lumps: list) -> dict:
    """Read visibility data and return decompressed PVS/PHS"""
    data = lumps[LUMP_VISIBILITY]
    if len(data) < 4:
        return {'num_clusters': 0, 'pvs': [], 'phs': []}

    br = BinaryReader(data)
    num_clusters = br.read_int()

    if num_clusters <= 0:
        return {'num_clusters': num_clusters, 'pvs': [], 'phs': []}

    # Read PVS and PHS offsets
    pvs_offsets = [br.read_int() for _ in range(num_clusters)]
    phs_offsets = [br.read_int() for _ in range(num_clusters)]

    result = {
        'num_clusters': num_clusters,
        'pvs': [],
        'phs': [],
        'data': data,
    }

    return result


def decompress_vis(vis_data: bytes, offset: int, num_clusters: int) -> list:
    """Decompress RLE-encoded visibility"""
    if offset >= len(vis_data):
        return [0] * num_clusters

    bits = []
    i = offset

    while len(bits) < num_clusters and i < len(vis_data):
        b = vis_data[i]
        i += 1

        if b != 0:
            for j in range(8):
                if len(bits) < num_clusters:
                    bits.append((b >> j) & 1)
        else:
            # RLE: next byte is count of 8-bit zeros
            count = vis_data[i] if i < len(vis_data) else 0
            i += 1
            bits.extend([0] * (count * 8))

    return bits[:num_clusters]


def read_entities(lumps: list) -> str:
    """Read entity string"""
    return lumps[LUMP_ENTITIES].decode("latin-1", errors="ignore")


def read_faces(lumps: list) -> list:
    br = BinaryReader(lumps[LUMP_FACES])
    result = []
    for _ in range(br.length() // Face.SIZE):
        face = {
            'plane_num': br.read_uint16(),
            'side': br.read_uint16(),
            'first_edge': br.read_int(),
            'num_edges': br.read_int16(),
            'texinfo': br.read_int16(),
            'styles': br.read_int16s(4),
            'lightofs': br.read_int(),
        }
        result.append(face)
    return result
