"""
gl_model.py - Model loading and rendering
Handles BSP, MD2 (alias), and sprite model types
"""

from OpenGL.GL import *
from wrapper_qpy.decorators import TODO
from wrapper_qpy.custom_classes import Mutable
from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), ["Com_Printf"])

# ===== Model Cache =====

mod_known = []
mod_numknown = 0

# ===== Model Types =====

MODEL_BRUSH = 1
MODEL_ALIAS = 2
MODEL_SPRITE = 3
MODEL_NULL = 4


class Model:
    def __init__(self, name):
        self.name = name
        self.type = MODEL_NULL
        self.numframes = 0
        self.flags = 0
        self.radius = 0
        self.mins = [0, 0, 0]
        self.maxs = [0, 0, 0]


# ===== Model Loading =====

def Mod_LoadModel(name, crash=True):
    """Load a model by name"""
    try:
        from ..quake2.files import FS_LoadFile, FS_FOpenFile

        # Check cache
        for m in mod_known:
            if m.name == name:
                return m

        # Load model data
        data, length = FS_LoadFile(name)

        if data is None:
            if crash:
                from ..quake2.common import Com_Error
                Com_Error(0, f"Mod_Load: can't load {name}")
            return None

        # Detect model type by magic number
        magic = data[0:4]

        if magic == b'IBSP':
            # BSP model
            return Mod_LoadBrush(name, data)
        elif magic == b'IDP2':
            # MD2 alias model
            return Mod_LoadAlias(name, data)
        else:
            Com_Printf(f"Mod_LoadModel: unknown filetype for {name}\n")
            return None

    except Exception as e:
        Com_Printf(f"Mod_LoadModel error: {e}\n")
        return None


def Mod_LoadBrush(name, data):
    """Load BSP (brush) model"""
    try:
        from ..quake2 import qfiles

        model = Model(name)
        model.type = MODEL_BRUSH

        # Parse BSP header
        magic = data[0:4].decode('latin-1')
        version = int.from_bytes(data[4:8], 'little')

        if magic != 'IBSP' or version != 38:
            Com_Printf(f"Mod_LoadBrush: {name} has wrong version\n")
            return None

        # Load lumps
        lumps = qfiles.load_bsp(name)

        if lumps is None:
            return None

        # Get model bounds
        models = qfiles.read_models(lumps)
        if models:
            first_model = models[0]
            model.mins = first_model['mins']
            model.maxs = first_model['maxs']

        # TODO: Set up rendering structures

        mod_known.append(model)
        return model

    except Exception as e:
        Com_Printf(f"Mod_LoadBrush error: {e}\n")
        return None


def Mod_LoadAlias(name, data):
    """Load MD2 (alias) model"""
    try:
        model = Model(name)
        model.type = MODEL_ALIAS

        # TODO: Parse MD2 header and frames

        mod_known.append(model)
        return model

    except Exception as e:
        Com_Printf(f"Mod_LoadAlias error: {e}\n")
        return None


# ===== Model Queries =====

def Mod_PointInLeaf(p, model):
    """Find leaf containing point in model"""
    # TODO: Traverse BSP tree to find leaf
    return None


def Mod_DecompressVis(_in, model):
    """Decompress visibility data"""
    # TODO: Decompress RLE visibility
    return None


def Mod_ClusterPVS(cluster, model):
    """Get PVS for cluster"""
    # TODO: Get cluster visibility
    return None


def Mod_Extracts(name):
    """Extract model name"""
    # Remove extension
    if '.' in name:
        return name[:name.rfind('.')]
    return name


# ===== Rendering =====

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

        # TODO: Render brush model surfaces

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


# ===== Model Utilities =====

def Mod_FrameExpires():
    """Get frame expiration time"""
    # TODO: Return expiration time
    return 0


def Mod_Hurry():
    """Mark models for quick loading"""
    pass


@TODO
def Mod_Extracts_f():
    pass


@TODO
def Mod_BuildLightmaps():
    pass


@TODO
def Mod_Init():
    pass


@TODO
def Mod_Free(mod):
    pass


@TODO
def Mod_FreeAll():
    pass


@TODO
def Mod_AllocBlock(w, h, inuse):
    pass


@TODO
def Mod_PointInLeaf(p, model):
    pass


@TODO
def Mod_DecompressVis(_in, model):
    pass


@TODO
def Mod_ClusterPVS(cluster, model):
    pass


@TODO
def Mod_Modellist_f():
    pass


@TODO
def Mod_Init():
    pass


@TODO
def Mod_ForName(name, crash):
    pass


@TODO
def Mod_LoadLighting(l):
    pass


@TODO
def Mod_LoadVisibility(l):
    pass


@TODO
def Mod_LoadVertexes(l):
    pass


@TODO
def RadiusFromBounds(mins, maxs):
    pass


@TODO
def Mod_LoadSubmodels(l):
    pass


@TODO
def Mod_LoadEdges(l):
    pass


@TODO
def Mod_LoadTexinfo(l):
    pass


@TODO
def CalcSurfaceExtents(s):
    pass


@TODO
def Mod_LoadFaces(l):
    pass


@TODO
def Mod_SetParent(node, parent):
    pass


@TODO
def Mod_LoadNodes(l):
    pass


@TODO
def Mod_LoadLeafs(l):
    pass


@TODO
def Mod_LoadMarksurfaces(l):
    pass


@TODO
def Mod_LoadSurfedges(l):
    pass


@TODO
def Mod_LoadPlanes(l):
    pass


@TODO
def Mod_LoadBrushModel(_mod, buffer):
    pass


@TODO
def Mod_LoadAliasModel(_mod, buffer):
    pass


@TODO
def Mod_LoadSpriteModel(_mod, buffer):
    pass


@TODO
def R_BeginRegistration(model):
    pass


@TODO
def R_RegisterModel(name):
    pass


@TODO
def R_EndRegistration():
    pass


@TODO
def Mod_Free(_mod):
    pass


@TODO
def Mod_FreeAll():
    pass
