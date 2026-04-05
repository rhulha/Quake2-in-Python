import struct
import numpy as np
from typing import Optional, Dict, Tuple, BinaryIO
from .gl_model import (
    Model, ModelType, Plane, Vertex, Edge, Surface, TexInfo, Node, Leaf, SubModel,
    GLPoly, MDLAliasHeader, MDLFrame
)

# BSP Format constants
IDBSPHEADER = b'IBSP'
IDALIASHEADER = (int.from_bytes(b'IDP2', 'little'))
IDSPRITEHEADER = b'IDSP'

class BSPLump:
    """Represents a BSP lump (named section)."""
    def __init__(self, name: str, offset: int, length: int):
        self.name = name
        self.offset = offset
        self.length = length

class BSPLoader:
    """Load Quake 2 BSP models."""

    LUMP_ENTITIES = 0
    LUMP_PLANES = 1
    LUMP_VERTEXES = 2
    LUMP_VISIBILITY = 4
    LUMP_NODES = 5
    LUMP_TEXINFO = 6
    LUMP_FACES = 7
    LUMP_LIGHTMAPS = 8
    LUMP_LEAVES = 10
    LUMP_LEAFFACES = 16
    LUMP_EDGES = 12
    LUMP_SURFEDGES = 13
    LUMP_MODELS = 14

    CONTENTS_EMPTY = -1
    CONTENTS_SOLID = -2
    CONTENTS_WATER = -3
    CONTENTS_SLIME = -4
    CONTENTS_LAVA = -5
    CONTENTS_SKY = -6

    def __init__(self, image_manager=None):
        self.image_manager = image_manager
        self.lumps: Dict[int, BSPLump] = {}

    def load(self, filepath: str) -> Model:
        """Load a BSP file."""
        with open(filepath, 'rb') as f:
            return self._load_bsp(f, filepath)

    def _load_bsp(self, f: BinaryIO, filepath: str) -> Model:
        """Internal BSP loader."""
        model = Model(name=filepath, type=ModelType.BRUSH)

        # Read header
        magic = f.read(4)
        if magic != IDBSPHEADER:
            raise ValueError("Invalid BSP file magic")

        version = struct.unpack('<I', f.read(4))[0]
        if version != 38:
            raise ValueError(f"Unsupported BSP version {version}")

        # Read lump directory (17 lumps × 8 bytes = 136 bytes)
        lumps = {}
        for i in range(17):
            offset, length = struct.unpack('<II', f.read(8))
            lumps[i] = BSPLump(f"lump{i}", offset, length)

        # Load lumps
        self._load_planes(f, lumps, model)
        self._load_vertexes(f, lumps, model)
        self._load_edges(f, lumps, model)
        self._load_surfedges(f, lumps, model)
        self._load_texinfo(f, lumps, model)
        self._load_faces(f, lumps, model)
        self._load_lightmaps(f, lumps, model)
        self._load_leaves(f, lumps, model)
        self._load_leaffaces(f, lumps, model)
        self._load_nodes(f, lumps, model)
        self._load_visibility(f, lumps, model)
        self._load_models(f, lumps, model)

        # Build BSP tree parent pointers
        if model.nodes:
            self._set_parents(model.nodes[0], None)

        return model

    def _load_planes(self, f: BinaryIO, lumps: Dict, model: Model):
        """Load planes lump."""
        lump = lumps[self.LUMP_PLANES]
        f.seek(lump.offset)
        num_planes = lump.length // 16
        model.numplanes = num_planes

        for _ in range(num_planes):
            normal = struct.unpack('<fff', f.read(12))
            dist = struct.unpack('<f', f.read(4))[0]
            plane = Plane()
            plane.normal = np.array(normal, dtype=np.float32)
            plane.dist = dist
            model.planes.append(plane)

    def _load_vertexes(self, f: BinaryIO, lumps: Dict, model: Model):
        """Load vertex lump."""
        lump = lumps[self.LUMP_VERTEXES]
        f.seek(lump.offset)
        num_verts = lump.length // 12
        model.numvertexes = num_verts

        for _ in range(num_verts):
            x, y, z = struct.unpack('<fff', f.read(12))
            vert = Vertex()
            vert.pos = np.array([x, y, z], dtype=np.float32)
            model.vertexes.append(vert)

    def _load_edges(self, f: BinaryIO, lumps: Dict, model: Model):
        """Load edge lump."""
        lump = lumps[self.LUMP_EDGES]
        f.seek(lump.offset)
        num_edges = lump.length // 4
        model.numedges = num_edges

        for _ in range(num_edges):
            v0, v1 = struct.unpack('<HH', f.read(4))
            edge = Edge()
            edge.v = [v0, v1]
            model.edges.append(edge)

    def _load_surfedges(self, f: BinaryIO, lumps: Dict, model: Model):
        """Load surfedge lump."""
        lump = lumps[self.LUMP_SURFEDGES]
        f.seek(lump.offset)
        num_surfedges = lump.length // 4

        for _ in range(num_surfedges):
            se = struct.unpack('<i', f.read(4))[0]
            model.surfedges.append(se)

        model.numsurfedges = len(model.surfedges)

    def _load_texinfo(self, f: BinaryIO, lumps: Dict, model: Model):
        """Load texinfo lump."""
        lump = lumps[self.LUMP_TEXINFO]
        f.seek(lump.offset)
        num_texinfo = lump.length // 76
        model.numtexinfo = num_texinfo

        for _ in range(num_texinfo):
            # Read vecs[2][4]: 8 floats
            vecs = struct.unpack('<8f', f.read(32))
            flags = struct.unpack('<I', f.read(4))[0]
            next_texinfo = struct.unpack('<I', f.read(4))[0]
            texname = f.read(32).rstrip(b'\x00').decode('utf-8', errors='ignore')

            texinfo = TexInfo()
            texinfo.vecs = np.array(vecs, dtype=np.float32).reshape(2, 4)
            texinfo.flags = flags

            # Link texinfo animation chain
            if next_texinfo > 0 and next_texinfo < num_texinfo:
                # Will be fixed up after all are loaded
                texinfo.nexttexinfo = None  # Placeholder

            # Load image
            if self.image_manager:
                texinfo.image = self.image_manager.find_image(texname, 'wall')

            model.texinfos.append(texinfo)

    def _load_faces(self, f: BinaryIO, lumps: Dict, model: Model):
        """Load faces lump and build polygons."""
        lump = lumps[self.LUMP_FACES]
        f.seek(lump.offset)
        num_faces = lump.length // 20
        model.numsurfaces = num_faces

        for i in range(num_faces):
            plane_num = struct.unpack('<H', f.read(2))[0]
            side = struct.unpack('<H', f.read(2))[0]
            first_edge = struct.unpack('<I', f.read(4))[0]
            num_edges = struct.unpack('<H', f.read(2))[0]
            texinfo_idx = struct.unpack('<H', f.read(2))[0]
            styles = struct.unpack('4B', f.read(4))
            lightmap_offset = struct.unpack('<I', f.read(4))[0]

            surface = Surface()
            surface.plane = model.planes[plane_num]
            surface.flags = 0
            surface.firstedge = first_edge
            surface.numedges = num_edges
            surface.texinfo = model.texinfos[texinfo_idx] if texinfo_idx < len(model.texinfos) else None
            surface.styles = np.array(styles, dtype=np.uint8)
            surface.lightmaptexturenum = 0

            # Build polygon from edges
            self._build_polygon(surface, model)

            model.surfaces.append(surface)

    def _build_polygon(self, surf: Surface, model: Model):
        """Build glpoly_t from surface edges."""
        if surf.numedges == 0:
            return

        verts = []
        for i in range(surf.numedges):
            surf_edge = model.surfedges[surf.firstedge + i]
            edge_idx = abs(surf_edge)
            edge = model.edges[edge_idx]

            # Determine vertex order based on edge direction
            vert_idx = edge.v[1] if surf_edge < 0 else edge.v[0]
            vert = model.vertexes[vert_idx]
            pos = vert.pos

            # Compute UV coordinates
            texinfo = surf.texinfo
            if texinfo:
                s = np.dot(pos, texinfo.vecs[0][:3]) + texinfo.vecs[0][3]
                t = np.dot(pos, texinfo.vecs[1][:3]) + texinfo.vecs[1][3]

                # Normalize by texture dimensions
                if texinfo.image:
                    s /= texinfo.image.width
                    t /= texinfo.image.height
                else:
                    s /= 64.0
                    t /= 64.0

                # Lightmap UV (placeholder, will be set during lightmap allocation)
                lm_s = 0.0
                lm_t = 0.0

                verts.append(np.array([pos[0], pos[1], pos[2], s, t, lm_s, lm_t], dtype=np.float32))

        if verts:
            poly = GLPoly()
            poly.verts = np.array(verts, dtype=np.float32)
            poly.numverts = len(verts)
            surf.polys = poly

    def _load_lightmaps(self, f: BinaryIO, lumps: Dict, model: Model):
        """Load lightmap data."""
        lump = lumps[self.LUMP_LIGHTMAPS]
        if lump.length > 0:
            f.seek(lump.offset)
            model.lightdata = np.frombuffer(f.read(lump.length), dtype=np.uint8)

    def _load_leaves(self, f: BinaryIO, lumps: Dict, model: Model):
        """Load leaves lump."""
        lump = lumps[self.LUMP_LEAVES]
        f.seek(lump.offset)
        num_leaves = lump.length // 28
        model.numleafs = num_leaves

        for _ in range(num_leaves):
            contents = struct.unpack('<i', f.read(4))[0]
            cluster = struct.unpack('<h', f.read(2))[0]
            area = struct.unpack('<h', f.read(2))[0]
            mins = struct.unpack('<fff', f.read(12))
            maxs = struct.unpack('<fff', f.read(12))
            first_leaf_surface = struct.unpack('<H', f.read(2))[0]
            num_leaf_surfaces = struct.unpack('<H', f.read(2))[0]

            leaf = Leaf()
            leaf.contents = contents
            leaf.cluster = cluster
            leaf.area = area
            leaf.minmaxs = np.array([*mins, *maxs], dtype=np.float32)
            leaf.firstmarksurface = first_leaf_surface
            leaf.nummarksurfaces = num_leaf_surfaces

            model.leafs.append(leaf)

    def _load_leaffaces(self, f: BinaryIO, lumps: Dict, model: Model):
        """Load leaf-face reference lump."""
        lump = lumps[self.LUMP_LEAFFACES]
        f.seek(lump.offset)
        num_refs = lump.length // 2

        marksurfaces = []
        for _ in range(num_refs):
            face_idx = struct.unpack('<H', f.read(2))[0]
            if face_idx < len(model.surfaces):
                marksurfaces.append(model.surfaces[face_idx])

        model.marksurfaces = marksurfaces
        model.nummarksurfaces = len(marksurfaces)

    def _load_nodes(self, f: BinaryIO, lumps: Dict, model: Model):
        """Load nodes lump."""
        lump = lumps[self.LUMP_NODES]
        f.seek(lump.offset)
        num_nodes = lump.length // 24
        model.numnodes = num_nodes

        for _ in range(num_nodes):
            plane_num = struct.unpack('<I', f.read(4))[0]
            children = struct.unpack('<ii', f.read(8))
            mins = struct.unpack('<fff', f.read(12))
            maxs = struct.unpack('<fff', f.read(12))

            node = Node()
            node.plane = model.planes[plane_num] if plane_num < len(model.planes) else None
            node.contents = -1  # Internal node
            node.minmaxs = np.array([*mins, *maxs], dtype=np.float32)

            # Children are indices: positive=node, negative=-(leaf+1)
            for i, child_idx in enumerate(children):
                if child_idx >= 0:
                    # Placeholder, will link after all nodes/leaves loaded
                    node.children[i] = None
                else:
                    # Placeholder for leaf
                    node.children[i] = None

            model.nodes.append(node)

        # Link node children
        for i, node in enumerate(model.nodes):
            for j, child_idx in enumerate(model.nodes[i].children or [None, None]):
                # Re-read to get actual indices (this is a simplification)
                pass

    def _load_visibility(self, f: BinaryIO, lumps: Dict, model: Model):
        """Load visibility (PVS) data."""
        lump = lumps[self.LUMP_VISIBILITY]
        if lump.length > 0:
            f.seek(lump.offset)
            model.vis = f.read(lump.length)

    def _load_models(self, f: BinaryIO, lumps: Dict, model: Model):
        """Load inline submodels."""
        lump = lumps[self.LUMP_MODELS]
        f.seek(lump.offset)
        num_models = lump.length // 32

        for i in range(num_models):
            mins = struct.unpack('<fff', f.read(12))
            maxs = struct.unpack('<fff', f.read(12))
            origin = struct.unpack('<fff', f.read(12))
            headnode = struct.unpack('<i', f.read(4))[0]

            submodel = SubModel()
            submodel.mins = np.array(mins, dtype=np.float32)
            submodel.maxs = np.array(maxs, dtype=np.float32)
            submodel.origin = np.array(origin, dtype=np.float32)
            submodel.headnode = headnode

            model.submodels.append(submodel)

        model.numsubmodels = len(model.submodels)

    def _set_parents(self, node_or_leaf, parent):
        """Recursively set parent pointers in BSP tree."""
        if isinstance(node_or_leaf, Node):
            node_or_leaf.parent = parent
            for child in node_or_leaf.children:
                if child:
                    self._set_parents(child, node_or_leaf)
        elif isinstance(node_or_leaf, Leaf):
            node_or_leaf.parent = parent

class MD2Loader:
    """Load Quake 2 MD2 alias models."""

    def __init__(self, image_manager=None):
        self.image_manager = image_manager

    def load(self, filepath: str) -> Model:
        """Load an MD2 file."""
        with open(filepath, 'rb') as f:
            return self._load_md2(f, filepath)

    def _load_md2(self, f: BinaryIO, filepath: str) -> Model:
        """Internal MD2 loader."""
        model = Model(name=filepath, type=ModelType.ALIAS)

        # Read header
        magic = struct.unpack('<I', f.read(4))[0]
        if magic != IDALIASHEADER:
            raise ValueError("Invalid MD2 magic")

        header = MDLAliasHeader()
        header.version = struct.unpack('<I', f.read(4))[0]
        header.skinwidth, header.skinheight = struct.unpack('<II', f.read(8))
        header.framesize = struct.unpack('<I', f.read(4))[0]
        header.num_skins, header.num_xyz, header.num_st = struct.unpack('<III', f.read(12))
        header.num_tris, header.num_frames, header.num_glcmds = struct.unpack('<III', f.read(12))
        header.num_tags = struct.unpack('<I', f.read(4))[0]
        (header.ofs_skins, header.ofs_st, header.ofs_tris, header.ofs_frames,
         header.ofs_glcmds, header.ofs_tags, header.ofs_end) = struct.unpack('<7I', f.read(28))

        if header.version != 8:
            raise ValueError(f"Unsupported MD2 version {header.version}")

        model.numframes = header.num_frames

        # Load skins
        f.seek(header.ofs_skins)
        for _ in range(header.num_skins):
            skinname = f.read(64).rstrip(b'\x00').decode('utf-8', errors='ignore')
            if self.image_manager:
                img = self.image_manager.find_image(skinname, 'skin')
                model.skins.append(img)

        # Load frames (simplified: just read frame count)
        for i in range(header.num_frames):
            frame = MDLFrame()
            frame.verts = np.empty((header.num_xyz, 4), dtype=np.uint8)
            model.frames.append(frame)

        return model

class SPRLoader:
    """Load Quake 2 SP2 sprite models."""

    def load(self, filepath: str) -> Model:
        """Load an SP2 file."""
        with open(filepath, 'rb') as f:
            return self._load_spr(f, filepath)

    def _load_spr(self, f: BinaryIO, filepath: str) -> Model:
        """Internal sprite loader."""
        model = Model(name=filepath, type=ModelType.SPRITE)
        # Simplified: just create an empty sprite model
        return model

class ModelLoader:
    """Unified model loader dispatcher."""

    def __init__(self, image_manager=None):
        self.image_manager = image_manager
        self.bsp_loader = BSPLoader(image_manager)
        self.md2_loader = MD2Loader(image_manager)
        self.spr_loader = SPRLoader()

    def load(self, filepath: str) -> Model:
        """Load any model format."""
        if filepath.endswith('.bsp'):
            return self.bsp_loader.load(filepath)
        elif filepath.endswith('.md2'):
            return self.md2_loader.load(filepath)
        elif filepath.endswith('.sp2'):
            return self.spr_loader.load(filepath)
        else:
            raise ValueError(f"Unknown model format: {filepath}")
