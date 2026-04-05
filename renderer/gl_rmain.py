import math
import os
import numpy as np
import moderngl
from typing import Optional, List, Tuple

from .gl_model import Model, ModelType, SurfaceFlags
from .gl_state import GLState, CVarManager, gl_state, cvar_manager
from .gl_image import ImageManager, Image

SHADER_DIR = os.path.join(os.path.dirname(__file__), 'shaders')

# Quake 2 light normals table (used for pre-computed vertex normals in MD2)
VERTEX_NORMALS = np.array([
    [-0.525731,  0.000000,  0.850651],
    [-0.442863,  0.238856,  0.864188],
    [-0.295242,  0.000000,  0.955423],
    [-0.309017,  0.500000,  0.809017],
    [-0.162460,  0.262866,  0.951056],
    [ 0.000000,  0.000000,  1.000000],
    [ 0.000000,  0.850651,  0.525731],
    [-0.147621,  0.716567,  0.681718],
    [ 0.147621,  0.716567,  0.681718],
    [ 0.000000,  0.525731,  0.850651],
    [ 0.309017,  0.500000,  0.809017],
    [ 0.525731,  0.000000,  0.850651],
    [ 0.295242,  0.000000,  0.955423],
    [ 0.442863,  0.238856,  0.864188],
    [ 0.162460,  0.262866,  0.951056],
    [-0.681718,  0.147621,  0.716567],
    [-0.809017,  0.309017,  0.500000],
    [-0.587785,  0.425325,  0.688191],
    [-0.850651,  0.525731,  0.000000],
    [-0.864188,  0.442863,  0.238856],
    [-0.716567,  0.681718,  0.147621],
    [-0.688191,  0.587785, -0.425325],
    [-0.500000,  0.809017,  0.309017],
    [-0.238856,  0.864188,  0.442863],
    [-0.425325,  0.688191,  0.587785],
    [-0.716567,  0.681718, -0.147621],
    [-0.500000,  0.809017, -0.309017],
    [-0.525731,  0.850651,  0.000000],
    [ 0.000000,  0.850651, -0.525731],
    [-0.238856,  0.864188, -0.442863],
    [ 0.000000,  0.955423, -0.295242],
    [-0.262866,  0.951056, -0.162460],
    [ 0.000000,  1.000000,  0.000000],
    [ 0.000000,  0.955423,  0.295242],
    [-0.262866,  0.951056,  0.162460],
    [ 0.238856,  0.864188,  0.442863],
    [ 0.262866,  0.951056,  0.162460],
    [ 0.500000,  0.809017,  0.309017],
    [ 0.238856,  0.864188, -0.442863],
    [ 0.262866,  0.951056, -0.162460],
    [ 0.500000,  0.809017, -0.309017],
    [ 0.850651,  0.525731,  0.000000],
    [ 0.716567,  0.681718,  0.147621],
    [ 0.716567,  0.681718, -0.147621],
    [ 0.525731,  0.850651,  0.000000],
    [ 0.425325,  0.688191,  0.587785],
    [ 0.864188,  0.442863,  0.238856],
    [ 0.688191,  0.587785,  0.425325],
    [ 0.809017,  0.309017,  0.500000],
    [ 0.681718,  0.147621,  0.716567],
    [ 0.587785,  0.425325,  0.688191],
    [ 0.955423,  0.295242,  0.000000],
    [ 1.000000,  0.000000,  0.000000],
    [ 0.951056,  0.162460,  0.262866],
    [ 0.850651, -0.525731,  0.000000],
    [ 0.955423, -0.295242,  0.000000],
    [ 0.864188, -0.442863,  0.238856],
    [ 0.951056, -0.162460,  0.262866],
    [ 0.809017, -0.309017,  0.500000],
    [ 0.681718, -0.147621,  0.716567],
    [ 0.850651,  0.000000,  0.525731],
    [ 0.864188,  0.442863, -0.238856],
    [ 0.809017,  0.309017, -0.500000],
    [ 0.951056,  0.162460, -0.262866],
    [ 0.525731,  0.000000, -0.850651],
    [ 0.681718,  0.147621, -0.716567],
    [ 0.681718, -0.147621, -0.716567],
    [ 0.850651,  0.000000, -0.525731],
    [ 0.809017, -0.309017, -0.500000],
    [ 0.864188, -0.442863, -0.238856],
    [ 0.951056, -0.162460, -0.262866],
    [ 0.955423,  0.000000, -0.295242],
    [ 1.000000,  0.000000,  0.000000],
    [ 0.951056,  0.000000,  0.309017],
    [ 0.716567, -0.681718,  0.147621],
    [ 0.716567, -0.681718, -0.147621],
    [ 0.525731, -0.850651,  0.000000],
    [ 0.500000, -0.809017,  0.309017],
    [ 0.238856, -0.864188,  0.442863],
    [ 0.262866, -0.951056,  0.162460],
    [ 0.000000, -0.850651,  0.525731],
    [ 0.000000, -0.955423,  0.295242],
    [ 0.262866, -0.951056, -0.162460],
    [ 0.000000, -1.000000,  0.000000],
    [ 0.000000, -0.955423, -0.295242],
    [-0.262866, -0.951056, -0.162460],
    [-0.238856, -0.864188, -0.442863],
    [-0.500000, -0.809017, -0.309017],
    [-0.262866, -0.951056,  0.162460],
    [-0.850651, -0.525731,  0.000000],
    [-0.716567, -0.681718, -0.147621],
    [-0.716567, -0.681718,  0.147621],
    [-0.525731, -0.850651,  0.000000],
    [-0.500000, -0.809017,  0.309017],
    [-0.238856, -0.864188,  0.442863],
    [-0.262866, -0.951056,  0.162460],
    [ 0.000000, -0.850651, -0.525731],
    [-0.147621, -0.716567, -0.681718],
    [ 0.147621, -0.716567, -0.681718],
    [ 0.000000, -0.525731, -0.850651],
    [ 0.309017, -0.500000, -0.809017],
    [ 0.525731,  0.000000, -0.850651],
    [ 0.295242,  0.000000, -0.955423],
    [ 0.442863, -0.238856, -0.864188],
    [ 0.162460, -0.262866, -0.951056],
    [ 0.000000,  0.000000, -1.000000],
    [ 0.000000,  0.850651, -0.525731],
    [ 0.000000,  0.525731, -0.850651],
    [ 0.147621,  0.716567, -0.681718],
    [-0.147621,  0.716567, -0.681718],
    [-0.309017,  0.500000, -0.809017],
    [-0.442863,  0.238856, -0.864188],
    [-0.295242,  0.000000, -0.955423],
    [-0.162460,  0.262866, -0.951056],
    [ 0.442863, -0.238856,  0.864188],
    [ 0.162460, -0.262866,  0.951056],
    [ 0.309017, -0.500000,  0.809017],
    [ 0.147621, -0.716567,  0.681718],
    [-0.147621, -0.716567,  0.681718],
    [-0.309017, -0.500000,  0.809017],
    [-0.162460, -0.262866,  0.951056],
    [-0.442863, -0.238856,  0.864188],
    [ 0.000000,  0.000000,  1.000000],
], dtype=np.float32)


def _load_shader(ctx: moderngl.Context, name: str) -> moderngl.Program:
    """Load and compile a vertex+fragment shader pair from the shaders/ directory."""
    vert_path = os.path.join(SHADER_DIR, f'{name}.vert')
    frag_path = os.path.join(SHADER_DIR, f'{name}.frag')
    with open(vert_path) as f:
        vert_src = f.read()
    with open(frag_path) as f:
        frag_src = f.read()
    return ctx.program(vertex_shader=vert_src, fragment_shader=frag_src)


def perspective_matrix(fov_y_deg: float, aspect: float, near: float, far: float) -> np.ndarray:
    """Build a column-major perspective projection matrix."""
    fov_rad = math.radians(fov_y_deg)
    f = 1.0 / math.tan(fov_rad * 0.5)
    nf = 1.0 / (near - far)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) * nf
    m[2, 3] = -1.0
    m[3, 2] = 2.0 * far * near * nf
    return m


def ortho_matrix(left: float, right: float, bottom: float, top: float,
                 near: float = -1.0, far: float = 1.0) -> np.ndarray:
    """Build a column-major orthographic projection matrix for 2D drawing."""
    rl = 1.0 / (right - left)
    tb = 1.0 / (top - bottom)
    fn = 1.0 / (far - near)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = 2.0 * rl
    m[1, 1] = 2.0 * tb
    m[2, 2] = -2.0 * fn
    m[3, 0] = -(right + left) * rl
    m[3, 1] = -(top + bottom) * tb
    m[3, 2] = -(far + near) * fn
    m[3, 3] = 1.0
    return m


def view_matrix(origin: np.ndarray, yaw_deg: float, pitch_deg: float,
                roll_deg: float = 0.0) -> np.ndarray:
    """Build a view matrix from Quake-style camera angles (yaw/pitch/roll in degrees).

    Quake coordinate system: X=forward, Y=left, Z=up
    We rotate the world to align it with OpenGL view space.
    """
    yaw   = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    roll  = math.radians(roll_deg)

    sy, cy = math.sin(yaw),   math.cos(yaw)
    sp, cp = math.sin(pitch), math.cos(pitch)
    sr, cr = math.sin(roll),  math.cos(roll)

    # Forward/right/up vectors from Quake angles
    forward = np.array([cp * cy, cp * sy, -sp], dtype=np.float32)
    right   = np.array([-sr * sp * cy + cr * sy,
                         -sr * sp * sy - cr * cy,
                         -sr * cp], dtype=np.float32)
    up      = np.array([cr * sp * cy + sr * sy,
                         cr * sp * sy - sr * cy,
                          cr * cp], dtype=np.float32)

    # Build a look-at style matrix (world → camera)
    m = np.identity(4, dtype=np.float32)
    m[0, 0:3] = right
    m[1, 0:3] = up
    m[2, 0:3] = -forward
    m[3, 0:3] = -np.array([np.dot(right,   origin),
                             np.dot(up,      origin),
                             np.dot(-forward, origin)], dtype=np.float32)
    m[3, 3] = 1.0
    return m


class Renderer:
    """Top-level ModernGL renderer.  Owns all shader programs and sub-systems."""

    def __init__(self, ctx: moderngl.Context, width: int, height: int):
        self.ctx = ctx
        self.width = width
        self.height = height

        self.programs: dict = {}
        self.image_manager: Optional[ImageManager] = None

        # Camera state – filled in before each frame
        self.proj_matrix  = np.identity(4, dtype=np.float32)
        self.view_matrix  = np.identity(4, dtype=np.float32)
        self.ortho_matrix = np.identity(4, dtype=np.float32)
        self.view_origin  = np.zeros(3, dtype=np.float32)
        self.view_angles  = np.zeros(3, dtype=np.float32)  # pitch, yaw, roll
        self.fov_x        = 90.0
        self.fov_y        = 70.0
        self.time         = 0.0

        # Cached forward/right/up (derived from view_angles)
        self.v_forward = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        self.v_right   = np.array([0.0, -1.0, 0.0], dtype=np.float32)
        self.v_up      = np.array([0.0, 0.0, 1.0], dtype=np.float32)

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def init(self):
        """Load shaders, create image manager, set GL defaults."""
        for name in ('world', 'alias', 'particle', 'quad2d', 'water', 'sky', 'sprite'):
            try:
                self.programs[name] = _load_shader(self.ctx, name)
            except FileNotFoundError as e:
                print(f'[gl_rmain] shader not found: {e}')

        self.image_manager = ImageManager(self.ctx)
        self._set_default_state()

        self.ortho_matrix = ortho_matrix(0.0, float(self.width),
                                          float(self.height), 0.0)

    def shutdown(self):
        """Release all GL resources."""
        for prog in self.programs.values():
            prog.release()
        self.programs.clear()

    # ------------------------------------------------------------------
    # Frame entry point
    # ------------------------------------------------------------------

    def begin_frame(self):
        """Clear buffers at the start of a frame."""
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)

    def end_frame(self):
        """Nothing needed here; buffer swap is handled by GLContext."""
        pass

    # ------------------------------------------------------------------
    # View / matrix setup
    # ------------------------------------------------------------------

    def setup_view(self, origin: np.ndarray, angles: np.ndarray,
                   fov_x: float = 90.0, fov_y: float = 70.0):
        """Set projection and view matrices from camera parameters.
        angles = (pitch, yaw, roll) in degrees.
        """
        self.view_origin = origin.copy()
        self.view_angles = angles.copy()
        self.fov_x = fov_x
        self.fov_y = fov_y

        aspect = self.width / max(self.height, 1)
        self.proj_matrix = perspective_matrix(fov_y, aspect, 4.0, 4096.0)
        self.view_matrix = view_matrix(origin, angles[1], angles[0], angles[2])
        self._update_axis_vectors()

    def _update_axis_vectors(self):
        """Derive forward/right/up from current view angles."""
        yaw   = math.radians(self.view_angles[1])
        pitch = math.radians(self.view_angles[0])
        self.v_forward = np.array([
            math.cos(pitch) * math.cos(yaw),
            math.cos(pitch) * math.sin(yaw),
            -math.sin(pitch),
        ], dtype=np.float32)
        self.v_right = np.array([
            math.sin(yaw),
            -math.cos(yaw),
            0.0,
        ], dtype=np.float32)
        self.v_up = np.cross(self.v_right, self.v_forward)

    def get_frustum_planes(self) -> List[np.ndarray]:
        """Extract 6 frustum planes (nx,ny,nz,d) from the combined MVP matrix.
        Used for frustum culling in the BSP walker.
        """
        clip = (self.proj_matrix @ self.view_matrix).T
        planes = []
        # Left, right, bottom, top, near, far
        combos = [
            clip[3] + clip[0],
            clip[3] - clip[0],
            clip[3] + clip[1],
            clip[3] - clip[1],
            clip[3] + clip[2],
            clip[3] - clip[2],
        ]
        for c in combos:
            length = np.linalg.norm(c[:3])
            if length > 0:
                planes.append(c / length)
            else:
                planes.append(c)
        return planes

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _set_default_state(self):
        """Apply sensible starting GL state."""
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.CULL_FACE)
        self.ctx.front_face = 'cw'
        self.ctx.depth_func = '<'

    def bind_3d_uniforms(self, prog: moderngl.Program):
        """Write shared 3-D uniforms into prog (projection + view)."""
        if 'projection' in prog:
            prog['projection'].write(self.proj_matrix.tobytes())
        if 'view' in prog:
            prog['view'].write(self.view_matrix.tobytes())

    def bind_2d_uniforms(self, prog: moderngl.Program):
        """Write the orthographic matrix into prog."""
        if 'ortho' in prog:
            prog['ortho'].write(self.ortho_matrix.tobytes())
