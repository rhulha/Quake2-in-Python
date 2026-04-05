import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum

class ModelType(Enum):
    BRUSH = 0
    ALIAS = 1
    SPRITE = 2

class SurfaceFlags(Enum):
    SKY = 4
    WARP = 8
    TRANS33 = 0x10
    TRANS66 = 0x20
    FLOWING = 0x40
    NODRAW = 0x80
    HINT = 0x100
    SKIP = 0x200
    LADDER = 0x8000

@dataclass
class Vector3:
    """3D vector."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def as_array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z], dtype=np.float32)

    def __add__(self, other):
        return Vector3(self.x + other.x, self.y + other.y, self.z + other.z)

@dataclass
class Plane:
    """BSP plane (Ax + By + Cz = D)."""
    normal: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    dist: float = 0.0
    type: int = 0  # PLANE_X, PLANE_Y, PLANE_Z, PLANE_ANYX, PLANE_ANYY, PLANE_ANYZ

@dataclass
class Edge:
    """BSP edge (connects two vertices)."""
    v: List[int] = field(default_factory=lambda: [0, 0])

@dataclass
class Vertex:
    """BSP vertex."""
    pos: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))

@dataclass
class TexInfo:
    """Texture projection info."""
    vecs: np.ndarray = field(default_factory=lambda: np.zeros((2, 4), dtype=np.float32))
    flags: int = 0
    nexttexinfo: Optional['TexInfo'] = None
    image: Optional['Image'] = None

@dataclass
class GLPoly:
    """Renderable polygon (from glpoly_t)."""
    verts: np.ndarray = field(default_factory=lambda: np.empty((0, 7), dtype=np.float32))
    numverts: int = 0
    flags: int = 0
    next: Optional['GLPoly'] = None
    chain: Optional['GLPoly'] = None  # for lightmap batching

@dataclass
class Surface:
    """BSP surface/face."""
    visframe: int = 0
    plane: Optional[Plane] = None
    flags: int = 0
    firstedge: int = 0
    numedges: int = 0
    texturemins: np.ndarray = field(default_factory=lambda: np.zeros(2, dtype=np.int16))
    extents: np.ndarray = field(default_factory=lambda: np.zeros(2, dtype=np.int16))
    light_s: int = 0
    light_t: int = 0
    dlight_s: int = 0
    dlight_t: int = 0
    lightmaptexturenum: int = 0
    polys: Optional[GLPoly] = None
    texturechain: Optional['Surface'] = None
    lightmapchain: Optional['Surface'] = None
    texinfo: Optional[TexInfo] = None
    dlightframe: int = 0
    dlightbits: int = 0
    styles: np.ndarray = field(default_factory=lambda: np.zeros(4, dtype=np.uint8))
    cached_light: np.ndarray = field(default_factory=lambda: np.ones(4, dtype=np.float32))
    samples: Optional[np.ndarray] = None  # raw RGB lightmap data

@dataclass
class Node:
    """BSP tree node."""
    contents: int = 0
    visframe: int = 0
    minmaxs: np.ndarray = field(default_factory=lambda: np.zeros(6, dtype=np.float32))
    parent: Optional['Node'] = None
    plane: Optional[Plane] = None
    children: List[Optional['Node']] = field(default_factory=lambda: [None, None])
    firstsurface: int = 0
    numsurfaces: int = 0

@dataclass
class Leaf:
    """BSP tree leaf."""
    contents: int = 0
    visframe: int = 0
    minmaxs: np.ndarray = field(default_factory=lambda: np.zeros(6, dtype=np.float32))
    parent: Optional[Node] = None
    cluster: int = -1
    area: int = 0
    firstmarksurface: int = 0
    nummarksurfaces: int = 0

@dataclass
class SubModel:
    """Inline BSP submodel (doors, platforms, etc.)."""
    mins: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    maxs: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    origin: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    headnode: int = 0
    firstface: int = 0
    numfaces: int = 0

@dataclass
class MDLAliasHeader:
    """MD2 alias model header."""
    ident: int = 0
    version: int = 0
    skinwidth: int = 0
    skinheight: int = 0
    framesize: int = 0
    num_skins: int = 0
    num_xyz: int = 0
    num_st: int = 0
    num_tris: int = 0
    num_frames: int = 0
    num_glcmds: int = 0
    num_tags: int = 0
    ofs_skins: int = 0
    ofs_st: int = 0
    ofs_tris: int = 0
    ofs_frames: int = 0
    ofs_glcmds: int = 0
    ofs_tags: int = 0
    ofs_end: int = 0

@dataclass
class MDLFrame:
    """MD2 frame data."""
    scale: np.ndarray = field(default_factory=lambda: np.ones(3, dtype=np.float32))
    translate: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    name: str = ""
    verts: np.ndarray = field(default_factory=lambda: np.empty((0, 4), dtype=np.uint8))

@dataclass
class Model:
    """Unified model type (BSP, MD2, SP2)."""
    name: str = ""
    type: ModelType = ModelType.BRUSH
    registration_sequence: int = 0
    radius: float = 0.0
    mins: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    maxs: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))

    # BSP-specific
    numframes: int = 0
    flags: int = 0
    firstmodelsurface: int = 0
    nummodelsurfaces: int = 0
    numsubmodels: int = 0
    submodels: List[SubModel] = field(default_factory=list)
    numplanes: int = 0
    planes: List[Plane] = field(default_factory=list)
    numleafs: int = 0
    leafs: List[Leaf] = field(default_factory=list)
    numvertexes: int = 0
    vertexes: List[Vertex] = field(default_factory=list)
    numedges: int = 0
    edges: List[Edge] = field(default_factory=list)
    numnodes: int = 0
    nodes: List[Node] = field(default_factory=list)
    numtexinfo: int = 0
    texinfos: List[TexInfo] = field(default_factory=list)
    numsurfaces: int = 0
    surfaces: List[Surface] = field(default_factory=list)
    numsurfedges: int = 0
    surfedges: List[int] = field(default_factory=list)
    nummarksurfaces: int = 0
    marksurfaces: List[Surface] = field(default_factory=list)
    lightdata: Optional[np.ndarray] = None
    vis: Optional[np.ndarray] = None  # decompressed PVS

    # MD2/SP2-specific
    skins: List['Image'] = field(default_factory=list)
    frames: List[MDLFrame] = field(default_factory=list)
    glcmds: Optional[np.ndarray] = None  # GL command list for alias models

@dataclass
class EntityType:
    """Entity data (from refdef_t entities)."""
    model: Optional[Model] = None
    origin: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    angles: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    oldorigin: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    frame: int = 0
    oldframe: int = 0
    backlerp: float = 0.0
    skinnum: int = 0
    lightstyle: int = 0
    alpha: float = 1.0
    skin: Optional['Image'] = None
    flags: int = 0  # RF_* flags

class EntityFlags(Enum):
    TRANSLUCENT = 1
    FULLBRIGHT = 2
    WEAPONMODEL = 4
    BEAM = 8
    SHELL_RED = 0x10
    SHELL_GREEN = 0x20
    SHELL_BLUE = 0x40
    DEPTHHACK = 0x80
    GLOW = 0x100
    MINLIGHT = 0x200
    IR_VISIBLE = 0x400

@dataclass
class DLight:
    """Dynamic light."""
    origin: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    color: np.ndarray = field(default_factory=lambda: np.ones(3, dtype=np.float32))
    intensity: float = 300.0

@dataclass
class Particle:
    """Particle."""
    origin: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    accel: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    color: np.ndarray = field(default_factory=lambda: np.ones(4, dtype=np.uint8))
    alpha: float = 1.0
    alphavel: float = 0.0

@dataclass
class LightStyle:
    """Animated lightstyle (for BSP surfaces)."""
    rgb: np.ndarray = field(default_factory=lambda: np.ones(3, dtype=np.float32))
    white: float = 1.0

@dataclass
class RenderDef:
    """Frame rendering parameters (from refdef_t)."""
    x: int = 0
    y: int = 0
    width: int = 640
    height: int = 480
    fov_x: float = 90.0
    fov_y: float = 90.0
    vieworg: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    viewangles: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float32))
    blend: np.ndarray = field(default_factory=lambda: np.zeros(4, dtype=np.float32))
    time: float = 0.0
    rdflags: int = 0
    areabits: Optional[np.ndarray] = None
    lightstyles: List[LightStyle] = field(default_factory=list)
    entities: List[EntityType] = field(default_factory=list)
    dlights: List[DLight] = field(default_factory=list)
    particles: List[Particle] = field(default_factory=list)
