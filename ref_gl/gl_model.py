"""
gl_model.py - Model loading and rendering
Handles BSP, MD2 (alias), and sprite model types
"""

import sys
import os
import struct
from OpenGL.GL import *
from wrapper_qpy.linker import LinkEmptyFunctions

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

LinkEmptyFunctions(globals(), ["Com_Printf"])

# ===== Model Types =====

MODEL_BRUSH = 1
MODEL_ALIAS = 2
MODEL_SPRITE = 3
MODEL_NULL = 4

# ===== Model Cache =====

mod_known = {}  # Map name -> Model
registration_sequence = 0


class Model:
    """BSP or MD2 model"""
    def __init__(self, name):
        self.name = name
        self.type = MODEL_NULL
        self.numframes = 0
        self.flags = 0
        self.radius = 0
        self.mins = [0, 0, 0]
        self.maxs = [0, 0, 0]

        # BSP data
        self.planes = []
        self.vertices = []
        self.edges = []
        self.nodes = []
        self.leafs = []
        self.faces = []
        self.texinfo = []
        self.models = []
        self.lightdata = None
        self.visdata = None
        self.brushes = []
        self.brush_sides = []

        # Registration
        self.registration_sequence = 0


def Mod_LoadModel(name, crash=True):
    """Load a model by name"""
    try:
        from quake2.files import FS_LoadFile
        from quake2 import qfiles

        # Check cache
        if name in mod_known:
            return mod_known[name]

        # Load model data
        data, length = FS_LoadFile(name)

        if data is None:
            if crash:
                from quake2.common import Com_Error
                Com_Error(0, f"Mod_Load: can't load {name}")
            return None

        # Detect model type by magic number
        magic = data[0:4]

        if magic == b'IBSP':
            result = Mod_LoadBrush(name, data)
            return result
        elif magic == b'IDP2':
            return Mod_LoadAlias(name, data)
        else:
            Com_Printf(f"Mod_LoadModel: unknown filetype for {name}\n")
            return None

    except Exception as e:
        import traceback
        traceback.print_exc()
        Com_Printf(f"Mod_LoadModel error: {e}\n")
        return None


def Mod_LoadBrush(name, data):
    """Load BSP (brush) model"""
    try:
        from quake2 import qfiles

        model = Model(name)
        model.type = MODEL_BRUSH

        # Verify magic and version
        magic = data[0:4]
        version = struct.unpack_from('<I', data, 4)[0]

        if magic != b'IBSP' or version != 38:
            Com_Printf(f"Mod_LoadBrush: {name} has wrong version\n")
            return None

        # Load all lumps
        lumps = qfiles.load_bsp(name)
        if lumps is None:
            return None

        # Load BSP data structures
        try:
            model.planes = qfiles.read_planes(lumps)
            model.vertices = qfiles.read_vertices(lumps)
            model.nodes = qfiles.read_nodes(lumps)
            model.leafs = qfiles.read_leafs(lumps)
            model.faces = qfiles.read_faces(lumps)
            model.models = qfiles.read_models(lumps)
            model.visdata = qfiles.read_visibility(lumps)
            model.lightdata = lumps[qfiles.LUMP_LIGHTMAPS] if len(lumps) > qfiles.LUMP_LIGHTMAPS else None
            model.brushes = qfiles.read_brushes(lumps)
            model.brush_sides = qfiles.read_brush_sides(lumps)

            # Store raw lumps for gl_rsurf to parse edges and texinfo
            model.lump_edges = lumps[qfiles.LUMP_EDGES] if len(lumps) > qfiles.LUMP_EDGES else b''
            model.lump_surfedges = lumps[qfiles.LUMP_FACE_EDGES] if len(lumps) > qfiles.LUMP_FACE_EDGES else b''
            model.lump_texinfo = lumps[qfiles.LUMP_TEXINFO] if len(lumps) > qfiles.LUMP_TEXINFO else b''

            # Set model bounds from first model
            if model.models:
                first_model = model.models[0]
                model.mins = first_model['mins']
                model.maxs = first_model['maxs']

            # Calculate radius
            model.radius = RadiusFromBounds(model.mins, model.maxs)

            mod_known[name] = model
            return model
        except Exception as e:
            raise

    except Exception as e:
        import traceback
        traceback.print_exc()
        Com_Printf(f"Mod_LoadBrush error: {e}\n")
        return None


def Mod_LoadAlias(name, data):
    """Load MD2 (alias) model"""
    try:
        from . import gl_mesh

        model = Model(name)
        model.type = MODEL_ALIAS

        # Load MD2 data
        if gl_mesh.Mod_LoadAlias(model, data):
            mod_known[name] = model
            return model

        return None

    except Exception as e:
        Com_Printf(f"Mod_LoadAlias error: {e}\n")
        return None


def RadiusFromBounds(mins, maxs):
    """Calculate radius from bounding box"""
    import math
    c = [(mins[i] + maxs[i]) * 0.5 for i in range(3)]
    d = [maxs[i] - c[i] for i in range(3)]
    return math.sqrt(d[0]*d[0] + d[1]*d[1] + d[2]*d[2])


# ===== Model Queries =====

def Mod_PointInLeaf(p, model):
    """Find leaf containing point in model"""
    try:
        if not model or not model.nodes:
            return None

        # Traverse BSP tree to find leaf
        node_idx = 0

        while True:
            if node_idx < 0:
                # Leaf node (negative index)
                leaf_idx = (-node_idx - 1)
                if 0 <= leaf_idx < len(model.leafs):
                    return model.leafs[leaf_idx]
                return None

            # Interior node
            if node_idx >= len(model.nodes):
                return None

            node = model.nodes[node_idx]
            if not node or len(node.plane_num) == 0:
                return None

            plane_idx = node.plane_num if isinstance(node.plane_num, int) else 0
            if plane_idx >= len(model.planes):
                return None

            plane = model.planes[plane_idx]
            if not plane:
                return None

            # Calculate distance from point to plane
            normal = plane.normal if hasattr(plane, 'normal') else [0, 0, 0]
            dist = sum(p[i] * normal[i] for i in range(3)) - (plane.dist if hasattr(plane, 'dist') else 0)

            # Choose front or back child
            node_idx = node.children[0] if dist >= 0 else node.children[1] if len(node.children) > 1 else node.children[0]

    except Exception as e:
        Com_Printf(f"Mod_PointInLeaf error: {e}\n")
        return None


def Mod_DecompressVis(vis_data, model):
    """Decompress visibility data for a cluster"""
    try:
        if not model.visdata or not vis_data:
            return None

        from quake2 import qfiles
        return qfiles.decompress_vis(vis_data, 0, len(model.leafs))

    except Exception as e:
        Com_Printf(f"Mod_DecompressVis error: {e}\n")
        return None


def Mod_ClusterPVS(cluster, model):
    """Get potentially visible set for cluster"""
    try:
        if not model or not model.visdata or cluster < 0:
            return None

        from quake2 import qfiles

        visdata = model.visdata
        if isinstance(visdata, dict) and 'data' in visdata:
            vis_data = visdata['data']
        else:
            vis_data = visdata

        if not vis_data:
            return [True] * len(model.leafs)  # Everything visible

        return qfiles.decompress_vis(vis_data, cluster, len(model.leafs))

    except Exception as e:
        Com_Printf(f"Mod_ClusterPVS error: {e}\n")
        return None


# ===== Model Registration =====

def R_BeginRegistration(map_name):
    """Begin model registration for new map"""
    global registration_sequence
    registration_sequence += 1

    try:
        # Load the world model
        world_model = Mod_ForName(map_name, True)
        return world_model

    except Exception as e:
        Com_Printf(f"R_BeginRegistration error: {e}\n")
        return None


def R_RegisterModel(name):
    """Register a model for current map"""
    try:
        return Mod_ForName(name, False)

    except Exception as e:
        Com_Printf(f"R_RegisterModel error: {e}\n")
        return None


def R_EndRegistration():
    """End model registration"""
    pass


def Mod_ForName(name, crash):
    """Load a model by name (main entry point)"""
    return Mod_LoadModel(name, crash)


# ===== Model Rendering =====

def R_DrawAliasModel(ent):
    """Draw MD2 alias model"""
    try:
        if not ent.model or ent.model.type != MODEL_ALIAS:
            return

        # TODO: Draw MD2 model frames with interpolation

    except Exception as e:
        Com_Printf(f"R_DrawAliasModel error: {e}\n")


def R_DrawBrushModel(ent):
    """Draw brush model (inline BSP)"""
    try:
        from . import gl_rsurf

        if not ent.model or ent.model.type != MODEL_BRUSH:
            return

        # Push entity transformation
        glPushMatrix()
        glTranslatef(ent.origin[0], ent.origin[1], ent.origin[2])

        if hasattr(gl_rsurf, 'R_DrawBrushModel'):
            gl_rsurf.R_DrawBrushModel(ent.model)

        glPopMatrix()

    except Exception as e:
        Com_Printf(f"R_DrawBrushModel error: {e}\n")


def R_DrawSpriteModel(ent):
    """Draw sprite model"""
    try:
        if not ent.model or ent.model.type != MODEL_SPRITE:
            return

        # TODO: Draw sprite facing camera

    except Exception as e:
        Com_Printf(f"R_DrawSpriteModel error: {e}\n")


# ===== Cleanup =====

def Mod_FreeAll():
    """Free all loaded models"""
    global mod_known
    mod_known = {}


def Mod_Free(name):
    """Free a specific model"""
    global mod_known
    if name in mod_known:
        del mod_known[name]


from quake2.common import Com_Printf
