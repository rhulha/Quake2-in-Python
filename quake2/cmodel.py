"""
cmodel.py - Quake 2 collision model system
Handles BSP loading, box tracing, and collision detection
"""

import math
from wrapper_qpy.decorators import TODO
from wrapper_qpy.linker import LinkEmptyFunctions
from .qfiles import (
    load_bsp, read_planes, read_vertices, read_nodes, read_leafs,
    read_leaf_faces, read_leaf_brushes, read_brushes, read_brush_sides,
    read_models, read_areas, read_area_portals, read_visibility, read_entities,
    decompress_vis, CONTENTS_SOLID, CONTENTS_WINDOW, CONTENTS_MONSTER,
    MASK_SOLID, MASK_PLAYERSOLID, MASK_MONSTERSOLID
)

LinkEmptyFunctions(globals(), ["Com_Printf", "Com_Error"])

# ===== Global State =====

loaded_model = None
model_lumps = None

num_planes = 0
planes = []

num_vertexes = 0
vertexes = []

num_nodes = 0
nodes = []

num_leafs = 0
leafs = []

num_leafbrushes = 0
leafbrushes = []

num_brushes = 0
brushes = []

num_brushsides = 0
brushsides = []

num_models = 0
models = []

num_areas = 0
areas = []

num_areaportals = 0
areaportals = []

num_clusters = 0
visibility_data = None

entity_string = ""

# Trace state
trace = None
trace_contents = 0


# ===== Trace Structure =====

class CTrace:
    def __init__(self):
        self.allsolid = False       # if true, plane is not valid
        self.startsolid = False     # if true, the initial point was in a solid area
        self.fraction = 1.0         # time completed, 1.0 = didn't hit anything
        self.contents = 0           # contents on other side of surface hit
        self.surface = None         # surface hit (not set by CM functions)
        self.plane = None           # surface normal and dist, only valid if fraction < 1.0
        self.entnum = 0             # entity the surface is a part of


# ===== Map Loading =====

def CMod_LoadSubmodels(lumps):
    global num_models, models
    models = read_models(lumps)
    num_models = len(models)
    Com_Printf(f"loaded {num_models} submodels\n")


def CMod_LoadSurfaces(lumps):
    Com_Printf("loaded surfaces\n")


def CMod_LoadNodes(lumps):
    global num_nodes, nodes
    nodes = read_nodes(lumps)
    num_nodes = len(nodes)
    Com_Printf(f"loaded {num_nodes} nodes\n")


def CMod_LoadBrushes(lumps):
    global num_brushes, brushes
    brushes = read_brushes(lumps)
    num_brushes = len(brushes)
    Com_Printf(f"loaded {num_brushes} brushes\n")


def CMod_LoadLeafs(lumps):
    global num_leafs, leafs
    leafs = read_leafs(lumps)
    num_leafs = len(leafs)
    Com_Printf(f"loaded {num_leafs} leafs\n")


def CMod_LoadPlanes(lumps):
    global num_planes, planes
    planes = read_planes(lumps)
    num_planes = len(planes)
    Com_Printf(f"loaded {num_planes} planes\n")


def CMod_LoadLeafBrushes(lumps):
    global num_leafbrushes, leafbrushes
    leafbrushes = read_leaf_brushes(lumps)
    num_leafbrushes = len(leafbrushes)


def CMod_LoadBrushSides(lumps):
    global num_brushsides, brushsides
    brushsides = read_brush_sides(lumps)
    num_brushsides = len(brushsides)


def CMod_LoadAreas(lumps):
    global num_areas, areas
    areas = read_areas(lumps)
    num_areas = len(areas)


def CMod_LoadAreaPortals(lumps):
    global num_areaportals, areaportals
    areaportals = read_area_portals(lumps)
    num_areaportals = len(areaportals)


def CMod_LoadVisibility(lumps):
    global num_clusters, visibility_data
    vis_dict = read_visibility(lumps)
    num_clusters = vis_dict['num_clusters']
    visibility_data = vis_dict['data']
    Com_Printf(f"loaded visibility ({num_clusters} clusters)\n")


def CMod_LoadEntityString(lumps):
    global entity_string
    entity_string = read_entities(lumps)


def CM_LoadMap(name, clientload=False, checksum=None):
    """Load a BSP map and initialize collision model"""
    global loaded_model, model_lumps, vertexes, num_vertexes

    Com_Printf(f"Loading map: {name}\n")

    # Load BSP file
    try:
        lumps = load_bsp(name)
        if lumps is None:
            Com_Error(0, f"Couldn't load {name}")
            return
    except Exception as e:
        Com_Error(0, f"Error loading {name}: {e}")
        return

    loaded_model = name
    model_lumps = lumps

    # Load all lumps
    CMod_LoadPlanes(lumps)
    vertexes = read_vertices(lumps)
    num_vertexes = len(vertexes)

    CMod_LoadNodes(lumps)
    CMod_LoadLeafs(lumps)
    CMod_LoadLeafBrushes(lumps)
    CMod_LoadBrushes(lumps)
    CMod_LoadBrushSides(lumps)
    CMod_LoadSurfaces(lumps)
    CMod_LoadSubmodels(lumps)
    CMod_LoadAreas(lumps)
    CMod_LoadAreaPortals(lumps)
    CMod_LoadVisibility(lumps)
    CMod_LoadEntityString(lumps)

    Com_Printf(f"Loaded collision model: {name}\n")


def CM_InlineModel(name):
    """Get inline model by name (e.g., '*1' for model 1)"""
    if not name or name[0] != '*':
        return None

    try:
        num = int(name[1:])
        if 0 <= num < num_models:
            return models[num]
    except:
        pass

    return None


# ===== Cluster Functions =====

def CM_NumClusters():
    return num_clusters


def CM_NumInlineModels():
    return num_models


def CM_EntityString():
    return entity_string


def CM_LeafContents(leafnum):
    """Get contents flags of a leaf"""
    if leafnum < 0 or leafnum >= num_leafs:
        return 0
    return leafs[leafnum]['contents']


def CM_LeafCluster(leafnum):
    """Get cluster number of a leaf"""
    if leafnum < 0 or leafnum >= num_leafs:
        return -1
    return leafs[leafnum]['cluster']


def CM_LeafArea(leafnum):
    """Get area number of a leaf"""
    if leafnum < 0 or leafnum >= num_leafs:
        return 0
    return leafs[leafnum]['area']


# ===== Box Hull (for point traces) =====

def CM_InitBoxHull():
    """Initialize box hull for point-to-box collision"""
    pass


def CM_HeadnodeForBox(mins, maxs):
    """Get headnode for axis-aligned box"""
    # For now, use world headnode
    return 0


# ===== Point Functions =====

def CM_PointLeafnum_r(p, num):
    """Recursively find leaf containing point"""
    if num < 0:
        return -num - 1

    node = nodes[num]
    plane = planes[node['plane_num']]

    # Calculate distance from point to plane
    d = (p[0] * plane['normal'][0] +
         p[1] * plane['normal'][1] +
         p[2] * plane['normal'][2] - plane['dist'])

    if d > 0:
        return CM_PointLeafnum_r(p, node['children'][0])
    else:
        return CM_PointLeafnum_r(p, node['children'][1])


def CM_PointLeafnum(p):
    """Find leaf containing point"""
    if num_nodes == 0:
        return 0
    return CM_PointLeafnum_r(p, 0)


def CM_PointContents(p, headnode=0):
    """Get contents at point"""
    if headnode < 0 or headnode >= num_models:
        headnode = 0

    model = models[headnode]
    leafnum = CM_PointLeafnum_r(p, model['headnode'])

    if leafnum >= 0 and leafnum < num_leafs:
        return leafs[leafnum]['contents']

    return 0


def CM_TransformedPointContents(p, headnode, origin, angles):
    """Get contents at point with transformation"""
    # For now, ignore transformation and use raw point
    return CM_PointContents(p, headnode)


# ===== Box Tracing (Collision Detection) =====

def vec3_subtract(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def vec3_add(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def vec3_scale(v, s):
    return [v[0] * s, v[1] * s, v[2] * s]


def vec3_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def vec3_copy(v):
    return [v[0], v[1], v[2]]


def CM_ClipBoxToBrush(mins, maxs, p1, p2, trace_obj, brush_idx):
    """Clip movement against a brush"""
    if brush_idx < 0 or brush_idx >= num_brushes:
        return

    brush = brushes[brush_idx]
    brush_contents = brush['contents']

    if not (brush_contents & trace_contents):
        return

    # Check all sides of the brush
    entered = False
    exited = False

    for i in range(brush['first_side'], brush['first_side'] + brush['num_sides']):
        side = brushsides[i]
        plane = planes[side['plane_num']]

        # Compute distance from box to plane
        d1 = vec3_dot(p1, plane['normal']) - plane['dist']
        d2 = vec3_dot(p2, plane['normal']) - plane['dist']

        # Add extents
        for j in range(3):
            if plane['normal'][j] > 0:
                d1 -= mins[j]
                d2 -= mins[j]
            else:
                d1 += maxs[j]
                d2 += maxs[j]

        if d2 > 0:
            exited = True
        if d1 > 0:
            entered = True

        # If box is completely behind plane, stop
        if d1 > 0 and d2 >= d1:
            return

        # Calculate intersection
        if d1 > d2:
            # Entering
            if d2 < 0 and d1 > 0:
                f = max(0, d1) / (d1 - d2)
                if f < trace_obj.fraction:
                    trace_obj.fraction = f
                    trace_obj.plane = {'normal': plane['normal'], 'dist': plane['dist']}
                    trace_obj.contents = brush_contents
        else:
            # Exiting
            if d1 < 0 and d2 > 0:
                f = max(0, d1) / (d1 - d2)
                if f < trace_obj.fraction:
                    trace_obj.fraction = f
                    trace_obj.plane = {'normal': plane['normal'], 'dist': plane['dist']}
                    trace_obj.contents = brush_contents

    if entered and not exited:
        trace_obj.startsolid = True
        if trace_obj.fraction == 1.0:
            trace_obj.allsolid = True


def CM_TestBoxInBrush(mins, maxs, p1, trace_obj, brush_idx):
    """Test if box is in brush"""
    if brush_idx < 0 or brush_idx >= num_brushes:
        return

    brush = brushes[brush_idx]

    if not (brush['contents'] & trace_contents):
        return

    # Check if point is inside all planes of brush
    for i in range(brush['first_side'], brush['first_side'] + brush['num_sides']):
        side = brushsides[i]
        plane = planes[side['plane_num']]

        d = vec3_dot(p1, plane['normal']) - plane['dist']

        for j in range(3):
            if plane['normal'][j] > 0:
                d -= mins[j]
            else:
                d += maxs[j]

        if d > 0:
            return

    trace_obj.startsolid = True
    trace_obj.allsolid = True


def CM_TraceToLeaf(leafnum, trace_obj):
    """Trace against all brushes in a leaf"""
    if leafnum < 0 or leafnum >= num_leafs:
        return

    leaf = leafs[leafnum]

    for i in range(leaf['first_leaf_brush'], leaf['first_leaf_brush'] + leaf['num_leaf_brushes']):
        brush_idx = leafbrushes[i]
        CM_ClipBoxToBrush(trace.mins, trace.maxs, trace.p1, trace.p2, trace_obj, brush_idx)

        if trace_obj.allsolid:
            return


def CM_TestInLeaf(leafnum, trace_obj):
    """Test if box is solid in a leaf"""
    if leafnum < 0 or leafnum >= num_leafs:
        return

    leaf = leafs[leafnum]

    for i in range(leaf['first_leaf_brush'], leaf['first_leaf_brush'] + leaf['num_leaf_brushes']):
        brush_idx = leafbrushes[i]
        CM_TestBoxInBrush(trace.mins, trace.maxs, trace.p1, trace_obj, brush_idx)

        if trace_obj.allsolid:
            return


def CM_RecursiveHullCheck(num, p1f, p2f, p1, p2, trace_obj):
    """Recursively trace through BSP tree"""
    if trace_obj.fraction <= p1f:
        return

    if num < 0:
        # Leaf
        leafnum = -num - 1
        CM_TraceToLeaf(leafnum, trace_obj)
        return

    node = nodes[num]
    plane = planes[node['plane_num']]

    # Calculate plane distance for both points
    d1 = vec3_dot(p1, plane['normal']) - plane['dist']
    d2 = vec3_dot(p2, plane['normal']) - plane['dist']

    # Add extents
    for i in range(3):
        if plane['normal'][i] > 0:
            d1 -= trace.mins[i]
            d2 -= trace.mins[i]
        else:
            d1 += trace.maxs[i]
            d2 += trace.maxs[i]

    if d1 >= 0 and d2 >= 0:
        # Both in front
        CM_RecursiveHullCheck(node['children'][0], p1f, p2f, p1, p2, trace_obj)
        return

    if d1 < 0 and d2 < 0:
        # Both behind
        CM_RecursiveHullCheck(node['children'][1], p1f, p2f, p1, p2, trace_obj)
        return

    # Crosses plane
    if d1 < 0:
        side = 1
        f = (d1) / (d1 - d2)
    else:
        side = 0
        f = (d1) / (d1 - d2)

    f = max(0, min(1, f))

    mid = [
        p1[0] + f * (p2[0] - p1[0]),
        p1[1] + f * (p2[1] - p1[1]),
        p1[2] + f * (p2[2] - p1[2]),
    ]

    midf = p1f + f * (p2f - p1f)

    CM_RecursiveHullCheck(node['children'][side], p1f, midf, p1, mid, trace_obj)

    if trace_obj.fraction != midf:
        return

    CM_RecursiveHullCheck(node['children'][1 - side], midf, p2f, mid, p2, trace_obj)


def CM_BoxTrace(start, end, mins, maxs, headnode, brushmask):
    """Trace a box through the world"""
    global trace, trace_contents

    if headnode < 0 or headnode >= num_models:
        headnode = 0

    trace_contents = brushmask
    trace_obj = CTrace()

    trace = type('obj', (object,), {
        'mins': mins,
        'maxs': maxs,
        'p1': start,
        'p2': end,
    })()

    # Check if starting point is solid
    leafnum = CM_PointLeafnum_r(start, models[headnode]['headnode'])
    if leafnum >= 0 and leafnum < num_leafs:
        if leafs[leafnum]['contents'] & brushmask:
            trace_obj.startsolid = True

    # Recursively trace
    CM_RecursiveHullCheck(models[headnode]['headnode'], 0, 1, start, end, trace_obj)

    # Interpolate position
    if trace_obj.fraction < 1.0:
        for i in range(3):
            trace_obj.endpos = [
                start[0] + trace_obj.fraction * (end[0] - start[0]),
                start[1] + trace_obj.fraction * (end[1] - start[1]),
                start[2] + trace_obj.fraction * (end[2] - start[2]),
            ]
    else:
        trace_obj.endpos = list(end)

    return trace_obj


def CM_TransformedBoxTrace(start, end, mins, maxs, headnode, brushmask, origin, angles):
    """Trace a box with transformation (rotation + translation)"""
    # For now, ignore rotation and just use translation
    start_local = [start[0] - origin[0], start[1] - origin[1], start[2] - origin[2]]
    end_local = [end[0] - origin[0], end[1] - origin[1], end[2] - origin[2]]

    trace_obj = CM_BoxTrace(start_local, end_local, mins, maxs, headnode, brushmask)

    # Translate result back
    trace_obj.endpos = [
        trace_obj.endpos[0] + origin[0],
        trace_obj.endpos[1] + origin[1],
        trace_obj.endpos[2] + origin[2],
    ]

    return trace_obj


# ===== Visibility Functions =====

def CM_DecompressVis(vis_in, cluster):
    """Decompress visibility for a cluster"""
    if not visibility_data or cluster < 0 or cluster >= num_clusters:
        return [0] * num_clusters

    # Read PVS offset for cluster
    offset_pos = 4 + cluster * 8
    if offset_pos + 4 > len(visibility_data):
        return [0] * num_clusters

    import struct
    offset = struct.unpack_from("<i", visibility_data, offset_pos)[0]

    return decompress_vis(visibility_data, offset, num_clusters)


def CM_ClusterPVS(cluster):
    """Get PVS (Potentially Visible Set) for cluster"""
    return CM_DecompressVis(None, cluster)


def CM_ClusterPHS(cluster):
    """Get PHS (Potentially Hearable Set) for cluster"""
    # For now, use PVS
    if not visibility_data or cluster < 0 or cluster >= num_clusters:
        return [0] * num_clusters

    import struct
    offset_pos = 4 + cluster * 8 + 4  # PHS is after PVS
    if offset_pos + 4 > len(visibility_data):
        return [0] * num_clusters

    offset = struct.unpack_from("<i", visibility_data, offset_pos)[0]
    return decompress_vis(visibility_data, offset, num_clusters)


# ===== Area Portal Functions =====

def FloodArea_r(area, floodnum):
    """Recursively flood fill areas"""
    pass


def FloodAreaConnections():
    """Flood fill all area connections"""
    pass


def CM_SetAreaPortalState(portalnum, open):
    """Open or close area portal"""
    pass


def CM_AreasConnected(area1, area2):
    """Check if two areas are connected"""
    if area1 < 0 or area1 >= num_areas or area2 < 0 or area2 >= num_areas:
        return False
    if area1 == area2:
        return True
    return False


def CM_WriteAreaBits(buffer, area):
    """Write area portal state to buffer"""
    pass


def CM_WritePortalState(f):
    """Write portal state to file"""
    pass


def CM_ReadPortalState(f):
    """Read portal state from file"""
    pass


def CM_HeadnodeVisible(nodenum, visbits):
    """Check if node is visible"""
    pass


# ===== Import after function definitions =====

from .common import Com_Printf, Com_Error
