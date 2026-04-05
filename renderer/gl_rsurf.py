import numpy as np
from typing import List, Dict, Optional, Tuple
import moderngl
from .gl_model import Surface, Node, Leaf, Model, GLPoly, Plane

# Constants
BLOCK_WIDTH = BLOCK_HEIGHT = 128
MAX_LIGHTMAPS = 128
DLIGHT_CUTOFF = 64

class LightmapAtlas:
    """Manages a 128x128 lightmap atlas texture."""

    def __init__(self, ctx: moderngl.Context, index: int):
        self.ctx = ctx
        self.index = index
        self.texture = ctx.texture((BLOCK_WIDTH, BLOCK_HEIGHT), 4)
        self.buffer = np.zeros((BLOCK_HEIGHT, BLOCK_WIDTH, 4), dtype=np.uint8)
        self.allocated = np.zeros(BLOCK_WIDTH, dtype=np.int32)
        self.dirty = False

    def alloc_block(self, w: int, h: int) -> Tuple[Optional[int], Optional[int]]:
        """Shelf-packing allocation. Returns (x, y) or (None, None) if out of space."""
        if w > BLOCK_WIDTH or h > BLOCK_HEIGHT:
            return None, None

        for x in range(BLOCK_WIDTH - w + 1):
            y = 0
            for i in range(x, min(x + w, BLOCK_WIDTH)):
                if self.allocated[i] > y:
                    y = self.allocated[i]

            if y + h <= BLOCK_HEIGHT:
                for i in range(x, min(x + w, BLOCK_WIDTH)):
                    self.allocated[i] = y + h
                return x, y

        return None, None

    def write_lightmap(self, x: int, y: int, w: int, h: int, data: np.ndarray):
        """Write lightmap data to atlas buffer."""
        self.buffer[y:y+h, x:x+w] = data
        self.dirty = True

    def upload(self):
        """Upload buffer to GPU."""
        if self.dirty:
            self.texture.write(self.buffer.tobytes())
            self.dirty = False

class LightmapManager:
    """Manages all lightmap atlases."""

    def __init__(self, ctx: moderngl.Context):
        self.ctx = ctx
        self.atlases: List[LightmapAtlas] = []
        for i in range(MAX_LIGHTMAPS):
            self.atlases.append(LightmapAtlas(ctx, i))

    def alloc_surface_lightmap(self, surf: Surface) -> int:
        """Allocate lightmap space for a surface. Returns atlas index."""
        texturemins = surf.texturemins
        extents = surf.extents

        # Compute required size (lightmap texels, rounded up)
        smax = (extents[0] >> 4) + 1
        tmax = (extents[1] >> 4) + 1

        # Try to fit in an atlas
        for i, atlas in enumerate(self.atlases):
            x, y = atlas.alloc_block(smax, tmax)
            if x is not None:
                surf.light_s = x
                surf.light_t = y
                surf.lightmaptexturenum = i
                return i

        # Fallback: use first atlas (will overflow)
        surf.lightmaptexturenum = 0
        return 0

    def upload_all(self):
        """Upload all dirty atlases."""
        for atlas in self.atlases:
            atlas.upload()

class SurfaceRenderer:
    """Renders BSP surfaces."""

    def __init__(self, ctx: moderngl.Context, shader_program: moderngl.Program):
        self.ctx = ctx
        self.shader = shader_program
        self.world_vao = None
        self.world_vbo = None

    def build_world_vao(self, surfaces: List[Surface]) -> Tuple[moderngl.VertexArray, int]:
        """Build VAO from all surfaces."""
        all_verts = []
        vert_count = 0

        for surf in surfaces:
            if surf.polys:
                all_verts.extend(surf.polys.verts)
                vert_count += surf.polys.numverts

        if vert_count == 0:
            return None, 0

        # Create VBO
        vert_data = np.array(all_verts, dtype=np.float32)
        vbo = self.ctx.buffer(vert_data)

        # Create VAO: layout for 7 floats (pos3, uv2, lm_uv2)
        vao = self.ctx.vertex_array(
            self.shader,
            [(vbo, '3f 2f 2f', 'pos', 'uv', 'lm_uv')]
        )

        return vao, vert_count

    def render_surfaces(self, vao: moderngl.VertexArray, vert_count: int,
                       projection: np.ndarray, view: np.ndarray,
                       lightmap_textures: List[moderngl.Texture]):
        """Draw all surfaces."""
        if vao is None or vert_count == 0:
            return

        # Set uniforms
        self.shader['projection'].write(projection.astype(np.float32))
        self.shader['view'].write(view.astype(np.float32))

        # Bind textures and draw
        vao.render(moderngl.TRIANGLES, vertex_count=vert_count)

class PolygonBuilder:
    """Builds glpoly_t from BSP surfaces."""

    @staticmethod
    def build_polygon_for_surface(surf: Surface, model: Model):
        """Build glpoly_t from surface edge list."""
        if surf.numedges == 0:
            return

        verts = []
        for i in range(surf.numedges):
            surf_edge = model.surfedges[surf.firstedge + i]
            edge_idx = abs(surf_edge)
            edge = model.edges[edge_idx]

            vert_idx = edge.v[1] if surf_edge < 0 else edge.v[0]
            vert = model.vertexes[vert_idx]
            pos = vert.pos

            # Compute UV coordinates
            texinfo = surf.texinfo
            if texinfo and texinfo.image:
                s = np.dot(pos, texinfo.vecs[0][:3]) + texinfo.vecs[0][3]
                t = np.dot(pos, texinfo.vecs[1][:3]) + texinfo.vecs[1][3]
                s /= texinfo.image.width
                t /= texinfo.image.height
            else:
                s = t = 0.0

            # Lightmap UV (placeholder)
            lm_s = 0.0
            lm_t = 0.0

            verts.append(np.array([pos[0], pos[1], pos[2], s, t, lm_s, lm_t], dtype=np.float32))

        if verts:
            poly = GLPoly()
            poly.verts = np.array(verts, dtype=np.float32)
            poly.numverts = len(verts)
            surf.polys = poly

class BSPSurfaceWalker:
    """Traverses BSP tree and processes surfaces."""

    def __init__(self, frustum_planes: List[Plane]):
        self.frustum_planes = frustum_planes
        self.vis_surfaces = []

    def walk(self, node_or_leaf, model: Model, viewcluster: int, vis_bits: np.ndarray):
        """Recursively walk BSP tree, returning visible surfaces."""
        if isinstance(node_or_leaf, Leaf):
            self._process_leaf(node_or_leaf, model, viewcluster, vis_bits)
        elif isinstance(node_or_leaf, Node):
            self._process_node(node_or_leaf, model, viewcluster, vis_bits)

    def _process_leaf(self, leaf: Leaf, model: Model, viewcluster: int, vis_bits: np.ndarray):
        """Process leaf node."""
        # Check PVS: is this leaf cluster visible from viewer?
        if leaf.cluster >= 0:
            byte_idx = leaf.cluster >> 3
            bit_idx = leaf.cluster & 7
            if byte_idx >= len(vis_bits) or not (vis_bits[byte_idx] & (1 << bit_idx)):
                return  # Not visible

        # Mark surfaces in this leaf as visible
        for i in range(leaf.nummarksurfaces):
            surf_idx = leaf.firstmarksurface + i
            if surf_idx < len(model.marksurfaces):
                self.vis_surfaces.append(model.marksurfaces[surf_idx])

    def _process_node(self, node: Node, model: Model, viewcluster: int, vis_bits: np.ndarray):
        """Process node: check frustum culling, then recurse."""
        if not self._frustum_test(node.minmaxs):
            return  # Outside frustum

        if node.plane:
            # Front-to-back traversal
            self.walk(node.children[0], model, viewcluster, vis_bits)
            self.walk(node.children[1], model, viewcluster, vis_bits)

    def _frustum_test(self, minmaxs: np.ndarray) -> bool:
        """Test AABB against all frustum planes."""
        mins = minmaxs[:3]
        maxs = minmaxs[3:]

        for plane in self.frustum_planes:
            # Compute signed distance to plane
            if plane.normal[0] > 0:
                d_x = mins[0] if plane.normal[0] > 0 else maxs[0]
            else:
                d_x = maxs[0] if plane.normal[0] < 0 else mins[0]

            d = d_x * plane.normal[0]
            if plane.normal[1] != 0:
                d_y = mins[1] if plane.normal[1] > 0 else maxs[1]
                d += d_y * plane.normal[1]
            if plane.normal[2] != 0:
                d_z = mins[2] if plane.normal[2] > 0 else maxs[2]
                d += d_z * plane.normal[2]

            if d - plane.dist < 0:
                return False  # Box is behind plane

        return True

def build_frustum_planes(fov_x: float, fov_y: float, near: float, far: float) -> List[Plane]:
    """Build 4 frustum planes from FOV parameters."""
    planes = []

    # Simplified: create axis-aligned planes
    # In full impl, these would be computed from camera matrix
    for _ in range(4):
        plane = Plane()
        plane.normal = np.zeros(3, dtype=np.float32)
        plane.dist = 0.0
        planes.append(plane)

    return planes

def decompress_pvs(vis_data: bytes, cluster: int, num_clusters: int) -> np.ndarray:
    """Decompress Quake PVS RLE data."""
    if not vis_data:
        # No PVS: all clusters visible
        return np.ones((num_clusters + 7) // 8, dtype=np.uint8)

    row = bytearray()
    pos = 0
    c = 0

    # Find the right cluster row
    offset = cluster * ((num_clusters + 7) >> 3)

    while c < offset and pos < len(vis_data):
        byte = vis_data[pos]
        pos += 1
        if byte:
            row.extend([byte] * 1)
        else:
            count = vis_data[pos]
            pos += 1
            row.extend([0] * count)

    # Decompress that row
    result = bytearray()
    pos = 0
    while len(result) < ((num_clusters + 7) >> 3):
        if pos >= len(vis_data):
            break
        byte = vis_data[pos]
        pos += 1
        if byte == 0:
            count = vis_data[pos]
            pos += 1
            result.extend([0] * count)
        else:
            result.append(byte)

    return np.array(result, dtype=np.uint8)
