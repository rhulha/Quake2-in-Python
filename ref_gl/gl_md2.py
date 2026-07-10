"""
gl_md2.py - ModernGL MD2 (alias) model renderer
Replaces the fixed-function pipeline in gl_mesh.py, which is incompatible
with the core-profile ModernGL context used for world rendering.
"""

import math
import numpy as np
import moderngl
from OpenGL.GL import glDepthRange

RF_VIEWERMODEL = 2
RF_WEAPONMODEL = 4
RF_DEPTHHACK = 16

_program = None
_model_cache = {}  # id(model) -> prepared draw data


def _get_program():
    global _program
    from . import gl_context
    if _program is not None:
        return _program
    if not gl_context.ctx:
        return None
    from . import shaders
    _program = gl_context.ctx.program(
        vertex_shader=shaders.MD2_VERT,
        fragment_shader=shaders.MD2_FRAG,
    )
    return _program


def _load_skin(mesh_data, skinnum=0):
    """Load one of the model's skins as a ModernGL texture."""
    skins = mesh_data.get('skins') or []
    if not skins:
        return None
    skinnum = max(0, min(skinnum, len(skins) - 1))
    from . import gl_image, gl_rsurf
    tex_id = gl_image.GL_LoadImage(skins[skinnum])
    return gl_rsurf._get_or_wrap_texture(tex_id)


def _build_cache(model):
    """Precompute numpy arrays and GL buffers for an MD2 model."""
    from . import gl_context
    ctx = gl_context.ctx
    prog = _get_program()
    if not ctx or not prog:
        return None

    md = model.mesh_data
    frames = md['frames']
    triangles = md['triangles']
    texcoords = md.get('texcoords') or []
    if not frames or not triangles:
        return None

    tri_vidx = np.array([v for tri in triangles for (v, _t) in tri], dtype=np.int32)
    tri_tidx = np.array([t for tri in triangles for (_v, t) in tri], dtype=np.int32)

    if texcoords:
        uv_table = np.array(texcoords, dtype=np.float32)
        uvs = uv_table[np.clip(tri_tidx, 0, len(uv_table) - 1)]
    else:
        uvs = np.zeros((len(tri_tidx), 2), dtype=np.float32)

    positions = np.array(
        [[[v.x, v.y, v.z] for v in f.vertices] for f in frames],
        dtype=np.float32,
    )

    vert_count = len(tri_vidx)
    vbo = ctx.buffer(reserve=vert_count * 5 * 4, dynamic=True)
    vao = ctx.vertex_array(prog, [(vbo, '3f 2f', 'in_position', 'in_texcoord')])

    cache = {
        'positions': positions,
        'tri_vidx': tri_vidx,
        'uvs': uvs,
        'vbo': vbo,
        'vao': vao,
        'vert_count': vert_count,
        'num_frames': len(frames),
        'skins': {},  # skinnum -> texture, loaded on demand
    }
    _model_cache[id(model)] = cache
    return cache


def _entity_matrix(origin, angles):
    """Quake-space model matrix: translate, then yaw/-pitch/-roll (Q2 order)."""
    def rot(axis, deg):
        a = math.radians(deg)
        c, s = math.cos(a), math.sin(a)
        m = np.eye(4, dtype=np.float32)
        i, j = [(1, 2), (0, 2), (0, 1)][axis]
        m[i, i] = c
        m[j, j] = c
        if axis == 1:
            m[i, j] = s
            m[j, i] = -s
        else:
            m[i, j] = -s
            m[j, i] = s
        return m

    t = np.eye(4, dtype=np.float32)
    t[0, 3] = origin[0]
    t[1, 3] = origin[1]
    t[2, 3] = origin[2]
    return t @ rot(2, angles[1]) @ rot(1, -angles[0]) @ rot(0, -angles[2])


def R_DrawAliasModel(ent):
    """Draw an MD2 model entity with the ModernGL pipeline."""
    from . import gl_context
    ctx = gl_context.ctx
    prog = _get_program()
    if not ctx or not prog or gl_context.proj_matrix is None:
        return
    if not ent or not ent.model or getattr(ent.model, 'mesh_data', None) is None:
        return

    cache = _model_cache.get(id(ent.model)) or _build_cache(ent.model)
    if not cache:
        return

    num_frames = cache['num_frames']
    frame = int(ent.frame) % num_frames
    oldframe = int(ent.oldframe) % num_frames
    backlerp = float(ent.backlerp)

    positions = cache['positions']
    if backlerp > 0.0 and oldframe != frame:
        pos = positions[frame] * (1.0 - backlerp) + positions[oldframe] * backlerp
    else:
        pos = positions[frame]

    verts = pos[cache['tri_vidx']]
    data = np.hstack([verts, cache['uvs']]).astype(np.float32)
    cache['vbo'].write(data.tobytes())

    prog['u_proj'].write(gl_context.proj_matrix.T.tobytes())
    prog['u_view'].write(gl_context.view_matrix.T.tobytes())
    prog['u_model'].write(_entity_matrix(ent.origin, ent.angles).T.tobytes())
    prog['u_texture'].value = 0

    skinnum = int(ent.skinnum)
    if skinnum not in cache['skins']:
        cache['skins'][skinnum] = _load_skin(ent.model.mesh_data, skinnum)
    skin = cache['skins'][skinnum]
    if skin:
        skin.use(location=0)

    depth_hack = bool(ent.flags & RF_DEPTHHACK)
    if depth_hack:
        glDepthRange(0.0, 0.3)

    # MD2 winding doesn't match the world's front_face setting; models are
    # cheap enough to draw double-sided.
    ctx.disable(moderngl.CULL_FACE)
    cache['vao'].render(moderngl.TRIANGLES)
    ctx.enable(moderngl.CULL_FACE)

    if depth_hack:
        glDepthRange(0.0, 1.0)


def free_all():
    """Release GL buffers (e.g. on map change)."""
    for cache in _model_cache.values():
        cache['vao'].release()
        cache['vbo'].release()
    _model_cache.clear()
