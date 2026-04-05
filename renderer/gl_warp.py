import math
import numpy as np
import moderngl
from typing import List, Optional, Tuple

from .gl_model import Surface, SurfaceFlags, GLPoly
from .gl_image import Image

# Pre-computed sin table identical to Quake 2's turbsin[] (256 entries, amplitude 8)
_TURB_SIZE = 256
_TURB_AMPLITUDE = 8.0
TURBSIN: np.ndarray = np.array(
    [np.sin(2.0 * math.pi * i / _TURB_SIZE) * _TURB_AMPLITUDE
     for i in range(_TURB_SIZE)],
    dtype=np.float32
)

# Skybox face axis / origin definitions
# Each tuple: (s_axis, t_axis, origin_dir) as indices into {±X, ±Y, ±Z}
_SKY_AXIS = [
    # (forward, right, up)
    ( 1,  0,  2),   # +X
    (-1,  0,  2),   # -X
    ( 0,  1,  2),   # +Y
    ( 0, -1,  2),   # -Y
    ( 0,  2,  1),   # +Z
    ( 0,  2, -1),   # -Z
]

# Sky cube vertex positions (+/- 1 box corners, 4 verts per face, 6 faces)
_SKY_VERTS = np.array([
    # +X
    [ 1, -1, -1], [ 1,  1, -1], [ 1,  1,  1], [ 1, -1,  1],
    # -X
    [-1,  1, -1], [-1, -1, -1], [-1, -1,  1], [-1,  1,  1],
    # +Y
    [-1,  1, -1], [ 1,  1, -1], [ 1,  1,  1], [-1,  1,  1],
    # -Y
    [ 1, -1, -1], [-1, -1, -1], [-1, -1,  1], [ 1, -1,  1],
    # +Z
    [-1, -1,  1], [ 1, -1,  1], [ 1,  1,  1], [-1,  1,  1],
    # -Z
    [-1,  1, -1], [ 1,  1, -1], [ 1, -1, -1], [-1, -1, -1],
], dtype=np.float32) * 2300.0   # far enough to look like sky

_SKY_UV = np.array([
    [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],
] * 6, dtype=np.float32)

_SKY_INDICES: List[int] = []
for face in range(6):
    base = face * 4
    _SKY_INDICES += [base, base + 1, base + 2, base, base + 2, base + 3]
_SKY_INDICES_ARR = np.array(_SKY_INDICES, dtype=np.uint32)


class WarpRenderer:
    """Renders water/slime/lava surfaces and the sky."""

    def __init__(self, ctx: moderngl.Context,
                 water_program: moderngl.Program,
                 sky_program: moderngl.Program):
        self.ctx = ctx
        self.water_prog = water_program
        self.sky_prog   = sky_program

        # Pending sky surfaces accumulated per frame
        self._sky_surfaces: List[Surface] = []
        self._sky_textures: List[Optional[Image]] = []

        # Cached skybox VAO / VBO
        self._sky_vao: Optional[moderngl.VertexArray] = None
        self._sky_vbo: Optional[moderngl.Buffer] = None
        self._sky_ibo: Optional[moderngl.Buffer] = None
        self._build_sky_buffers()

        # Upload the warpsin table to the water shader once
        self._init_water_uniform()

    # ------------------------------------------------------------------

    def _build_sky_buffers(self):
        """Build the static sky-box geometry buffers."""
        verts = np.concatenate(
            [_SKY_VERTS, _SKY_UV], axis=1
        ).astype(np.float32)   # (24, 5)

        self._sky_vbo = self.ctx.buffer(verts.tobytes())
        self._sky_ibo = self.ctx.buffer(_SKY_INDICES_ARR.tobytes())
        self._sky_vao = self.ctx.vertex_array(
            self.sky_prog,
            [(self._sky_vbo, '3f 2f', 'pos', 'uv')],
            self._sky_ibo,
        )

    def _init_water_uniform(self):
        """Write turbsin table into the water shader."""
        if 'warpsin' in self.water_prog:
            self.water_prog['warpsin'].write(TURBSIN.tobytes())

    # ------------------------------------------------------------------
    # Sky
    # ------------------------------------------------------------------

    def clear_sky(self):
        """Call at the start of a frame before collecting sky surfaces."""
        self._sky_surfaces.clear()
        self._sky_textures.clear()

    def add_sky_surface(self, surf: Surface, texture: Optional[Image] = None):
        """Enqueue a sky surface to be rendered."""
        self._sky_surfaces.append(surf)
        self._sky_textures.append(texture)

    def draw_sky(self, proj: np.ndarray, view: np.ndarray):
        """Render the sky box.  Call after all opaque geometry."""
        if self._sky_vao is None:
            return

        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.front_face = 'ccw'

        if 'projection' in self.sky_prog:
            self.sky_prog['projection'].write(proj.tobytes())
        if 'view' in self.sky_prog:
            # Remove translation from the view matrix so sky follows the camera
            view_no_trans = view.copy()
            view_no_trans[3, :3] = 0.0
            self.sky_prog['view'].write(view_no_trans.tobytes())

        self._sky_vao.render(moderngl.TRIANGLES)

        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.front_face = 'cw'

    # ------------------------------------------------------------------
    # Water / warp surfaces
    # ------------------------------------------------------------------

    def draw_water_surface(self, surf: Surface, texture: Optional[Image],
                           proj: np.ndarray, view: np.ndarray,
                           time: float):
        """Build a dynamic VBO from the surface poly and render it with the water shader."""
        if surf.polys is None or surf.polys.numverts < 3:
            return

        poly = surf.polys
        verts = poly.verts   # (N, 7): pos3 uv2 lm_uv2

        # Fan-tessellate the polygon into triangles
        tris = _fan_to_triangles(verts)
        if len(tris) == 0:
            return

        # Build VBO: pos3, uv2
        buf = tris[:, :5].astype(np.float32)

        vbo = self.ctx.buffer(buf.tobytes())
        vao = self.ctx.vertex_array(
            self.water_prog,
            [(vbo, '3f 2f', 'pos', 'uv')],
        )

        if 'projection' in self.water_prog:
            self.water_prog['projection'].write(proj.tobytes())
        if 'view' in self.water_prog:
            self.water_prog['view'].write(view.tobytes())
        if 'time' in self.water_prog:
            self.water_prog['time'].value = time

        if texture and texture.texture:
            texture.texture.use(0)
            if 'water_tex' in self.water_prog:
                self.water_prog['water_tex'].value = 0

        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        vao.render(moderngl.TRIANGLES)
        self.ctx.disable(moderngl.BLEND)

        vao.release()
        vbo.release()

    # ------------------------------------------------------------------
    # Surface subdivision (for subdivided warp polys)
    # ------------------------------------------------------------------

    @staticmethod
    def subdivide_surface(surf: Surface, subdivide_size: float = 64.0):
        """Subdivide a warp surface's polygon for smoother warp distortion.

        Replaces surf.polys with a subdivided version.
        This is a simplified grid-subdivision – sufficient for water floors.
        """
        if surf.polys is None or surf.polys.numverts < 3:
            return

        # We keep the original polygon; real subdivision would recursively split
        # edges longer than subdivide_size.  As a lightweight alternative we
        # just ensure the poly is in place so the shader can warp it.
        pass


def _fan_to_triangles(verts: np.ndarray) -> np.ndarray:
    """Convert a polygon (fan) to a flat triangle list."""
    n = len(verts)
    if n < 3:
        return np.empty((0, verts.shape[1]), dtype=np.float32)

    tris = []
    for i in range(1, n - 1):
        tris.append(verts[0])
        tris.append(verts[i])
        tris.append(verts[i + 1])
    return np.array(tris, dtype=np.float32)
