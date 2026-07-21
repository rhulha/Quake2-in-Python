"""
gl_sky.py - ModernGL skybox renderer

Reimplements Quake 2's gl_warp.c sky path for the core-profile ModernGL
context. The sky is drawn as a cube centered on the camera (so it never
parallaxes) before the world; SURF_SKY faces are skipped when building the
world buffers so the sky shows through those openings.
"""

import struct
import numpy as np
import moderngl

SKY_DIST = 1024.0          # cube half-extent (arbitrary; stays inside far plane)
_SUFFIXES = ("rt", "bk", "lf", "ft", "up", "dn")

# Quake 2's st_to_vec table: for face `axis`, maps (s, t, dist) to a world
# vector. Index magnitude selects the axis (1..3), sign negates it.
_ST_TO_VEC = (
    (3, -1, 2),
    (-3, 1, 2),
    (1, 3, 2),
    (-1, -3, 2),
    (-2, -1, 3),
    (2, -1, -3),
)
# Face -> which loaded suffix image to use (Quake 2 skytexorder).
_TEX_ORDER = (0, 2, 1, 3, 4, 5)

_program = None
_vao = None
_vbo = None
_sky_name = None           # currently loaded sky base name (e.g. "unit1_")
_faces = []                # per axis: (texture, vertex_count) or None


def _get_program():
    global _program
    from . import gl_context
    if _program is not None:
        return _program
    if not gl_context.ctx:
        return None
    from . import shaders
    _program = gl_context.ctx.program(vertex_shader=shaders.MD2_VERT,
                                      fragment_shader=shaders.MD2_FRAG)
    return _program


# ===== Image loading =====

def _load_tga(path):
    """Load an uncompressed truecolor TGA (type 2, 24/32-bit) as RGBA."""
    from quake2.files import FS_LoadFile
    data, length = FS_LoadFile(path)
    if data is None or length < 18:
        return None
    id_len = data[0]
    img_type = data[2]
    width, height = struct.unpack_from('<HH', data, 12)
    bpp = data[16]
    descriptor = data[17]
    if img_type != 2 or bpp not in (24, 32):
        return None
    bytes_pp = bpp // 8
    start = 18 + id_len
    need = width * height * bytes_pp
    if start + need > length:
        return None

    src = np.frombuffer(data, dtype=np.uint8, count=need, offset=start)
    src = src.reshape((height, width, bytes_pp))
    rgba = np.empty((height, width, 4), dtype=np.uint8)
    rgba[:, :, 0] = src[:, :, 2]  # BGR -> RGB
    rgba[:, :, 1] = src[:, :, 1]
    rgba[:, :, 2] = src[:, :, 0]
    rgba[:, :, 3] = src[:, :, 3] if bytes_pp == 4 else 255

    # TGA origin: bit 5 of descriptor set => top-left, else bottom-left.
    if not (descriptor & 0x20):
        rgba = rgba[::-1, :, :]
    return rgba.tobytes(), width, height


def _load_pcx_own_palette(path):
    """Load an 8-bit PCX using its own embedded palette (last 768 bytes)."""
    from quake2.files import FS_LoadFile
    data, length = FS_LoadFile(path)
    if data is None or length < 128 + 769:
        return None
    if data[0] != 10 or data[2] != 1 or data[3] != 8:
        return None
    xmin, ymin, xmax, ymax = struct.unpack_from('<HHHH', data, 4)
    width = xmax - xmin + 1
    height = ymax - ymin + 1
    if width <= 0 or height <= 0:
        return None

    # Palette is the final 768 bytes, preceded by a 0x0C marker.
    if data[length - 769] != 0x0C:
        return None
    palette = data[length - 768:length]

    pixels = bytearray()
    i = 128
    need = width * height
    while i < length - 769 and len(pixels) < need:
        b = data[i]
        i += 1
        if (b & 0xC0) == 0xC0:
            count = b & 0x3F
            pixels.extend([data[i]] * count)
            i += 1
        else:
            pixels.append(b)
    if len(pixels) < need:
        return None

    idx = np.frombuffer(bytes(pixels[:need]), dtype=np.uint8)
    pal = np.frombuffer(palette, dtype=np.uint8).reshape((256, 3))
    rgb = pal[idx]
    rgba = np.empty((need, 4), dtype=np.uint8)
    rgba[:, :3] = rgb
    rgba[:, 3] = 255
    return rgba.tobytes(), width, height


def _load_sky_image(base, suffix):
    """Load one sky side, preferring TGA (truecolor) over PCX."""
    for loader, ext in ((_load_tga, 'tga'), (_load_pcx_own_palette, 'pcx')):
        result = loader(f"env/{base}{suffix}.{ext}")
        if result:
            return result
    return None


# ===== Geometry =====

def _make_sky_vec(s, t, axis):
    """Quake 2 MakeSkyVec: position + clamped texcoord for a sky corner."""
    b = (s * SKY_DIST, t * SKY_DIST, SKY_DIST)
    v = [0.0, 0.0, 0.0]
    for j in range(3):
        k = _ST_TO_VEC[axis][j]
        if k < 0:
            v[j] = -b[-k - 1]
        else:
            v[j] = b[k - 1]

    # Nudge s/t off the very edge to hide the bilinear seam between faces.
    sky_min = 1.0 / 512.0
    sky_max = 511.0 / 512.0
    cs = (s + 1.0) * 0.5
    ct = (t + 1.0) * 0.5
    cs = min(max(cs, sky_min), sky_max)
    ct = min(max(ct, sky_min), sky_max)
    ct = 1.0 - ct
    return v[0], v[1], v[2], cs, ct


def _build_geometry():
    """Build one VBO holding 6 quads (as triangles), 6 verts per face."""
    global _vao, _vbo
    from . import gl_context
    ctx = gl_context.ctx
    prog = _get_program()
    if not ctx or not prog:
        return False

    corners = ((-1, -1), (-1, 1), (1, 1), (1, -1))  # matches R_DrawSkyBox order
    verts = []
    for axis in range(6):
        quad = [_make_sky_vec(cs, ct, axis) for (cs, ct) in corners]
        for idx in (0, 1, 2, 0, 2, 3):  # two triangles
            verts.append(quad[idx])

    arr = np.array(verts, dtype=np.float32)
    _vbo = ctx.buffer(arr.tobytes())
    _vao = ctx.vertex_array(prog, [(_vbo, '3f 2f', 'in_position', 'in_texcoord')])
    return True


# ===== Public API =====

def R_SetSky(name):
    """Load the six sky sides for base name `name` (e.g. "unit1_")."""
    global _sky_name, _faces
    if name == _sky_name:
        return
    from . import gl_context
    ctx = gl_context.ctx
    if not ctx:
        return

    for entry in _faces:
        if entry:
            entry[0].release()
    _faces = []

    for suffix in _SUFFIXES:
        img = _load_sky_image(name, suffix)
        if not img:
            _faces.append(None)
            continue
        rgba, w, h = img
        tex = ctx.texture((w, h), 4, rgba)
        tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        tex.repeat_x = False
        tex.repeat_y = False
        _faces.append((tex, w, h))

    if _vao is None:
        _build_geometry()
    _sky_name = name


def R_DrawSkyBox(view_origin):
    """Draw the skybox centered on the camera, as scene background."""
    from . import gl_context
    ctx = gl_context.ctx
    prog = _get_program()
    if not ctx or not prog or gl_context.proj_matrix is None:
        return
    if _vao is None or not any(_faces):
        return

    model = np.eye(4, dtype=np.float32)
    model[0, 3] = view_origin[0]
    model[1, 3] = view_origin[1]
    model[2, 3] = view_origin[2]

    prog['u_proj'].write(gl_context.proj_matrix.T.tobytes())
    prog['u_view'].write(gl_context.view_matrix.T.tobytes())
    prog['u_model'].write(model.T.tobytes())
    prog['u_texture'].value = 0

    # Background pass: no depth test (which also disables depth writes) and no
    # culling, so the world geometry drawn afterwards paints over the sky.
    ctx.disable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
    try:
        for face in range(6):
            entry = _faces[_TEX_ORDER[face]]
            if not entry:
                continue
            entry[0].use(location=0)
            _vao.render(moderngl.TRIANGLES, first=face * 6, vertices=6)
    finally:
        ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)


def free_all():
    global _vao, _vbo, _faces, _sky_name
    for entry in _faces:
        if entry:
            entry[0].release()
    _faces = []
    if _vao:
        _vao.release()
        _vao = None
    if _vbo:
        _vbo.release()
        _vbo = None
    _sky_name = None
