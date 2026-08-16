"""
gl_rsurf_new.py - ModernGL BSP surface rendering
Replaces immediate-mode glBegin/glEnd with VBO-based batch rendering.
Builds all face geometry once at map load, renders in one call per frame.
"""

import struct
import numpy as np
import moderngl

# Module-level state
_world_vaos = {}  # id(model) -> dict of {tex_name: (vao, vbo, vert_count)}
_submodel_vaos = {}  # id(model) -> {submodel index -> {tex_name: (vao, vbo, vert_count)}}
_world_vbos = {}  # id(model) -> lm_tex (lightmap atlas texture)
_mgl_textures = {}  # gl_tex_id -> moderngl.Texture wrapper
_lm_atlas = None

_NO_OFFSET = (0.0, 0.0, 0.0)

VERTEX_STRIDE = 7  # x, y, z, u, v, lm_u, lm_v
TEXINFO_SIZE_BSP = 76  # Size of a texinfo entry in BSP file


class LightmapBlock:
    """Lightmap atlas for efficient rendering - RGB format for ModernGL"""
    def __init__(self, width=1024, height=1024):
        self.width = width
        self.height = height
        self.data = bytearray(width * height * 3)  # RGB (not RGBA)
        self.next_x = 0
        self.next_y = 0
        self.row_height = 0

    def allocate(self, w, h):
        """Allocate block in lightmap atlas"""
        if self.next_x + w > self.width:
            self.next_x = 0
            self.next_y += self.row_height
            self.row_height = 0

        if self.next_y + h > self.height:
            # Wrap to start (proper fix: multiple atlases)
            self.next_x = 0
            self.next_y = 0
            self.row_height = 0

        x, y = self.next_x, self.next_y
        self.next_x += w
        self.row_height = max(self.row_height, h)
        return x, y


def _resolve_face_vertices(model, first_edge, num_edges):
    """Extract face vertices from model's edge/surfedge lumps"""
    verts = []
    for i in range(num_edges):
        se_off = (first_edge + i) * 4
        if se_off + 4 > len(model.lump_surfedges):
            break
        se = struct.unpack_from('<i', model.lump_surfedges, se_off)[0]
        edge_idx = abs(se)
        e_off = edge_idx * 4
        if e_off + 4 > len(model.lump_edges):
            continue
        v0, v1 = struct.unpack_from('<HH', model.lump_edges, e_off)
        v_idx = v0 if se >= 0 else v1
        if 0 <= v_idx < len(model.vertices):
            v = model.vertices[v_idx]
            verts.append([float(v[0]), float(v[1]), float(v[2])])
    return verts


def _parse_texinfo_entry(lump_data, texinfo_idx):
    """Parse one texinfo entry (76 bytes) from raw texinfo lump."""
    try:
        if texinfo_idx < 0:
            return None

        offset = texinfo_idx * TEXINFO_SIZE_BSP
        if offset + TEXINFO_SIZE_BSP > len(lump_data):
            return None

        s_axis = list(struct.unpack_from('<fff', lump_data, offset + 0))
        s_off = struct.unpack_from('<f', lump_data, offset + 12)[0]
        t_axis = list(struct.unpack_from('<fff', lump_data, offset + 16))
        t_off = struct.unpack_from('<f', lump_data, offset + 28)[0]
        flags = struct.unpack_from('<I', lump_data, offset + 32)[0]
        texture = lump_data[offset + 40:offset + 72].decode('latin-1', errors='ignore').rstrip('\x00')
        nexttexinfo = struct.unpack_from('<i', lump_data, offset + 72)[0]

        return {
            's_axis': s_axis,
            's_off': s_off,
            't_axis': t_axis,
            't_off': t_off,
            'flags': flags,
            'texture': texture,
            'nexttexinfo': nexttexinfo,
        }
    except:
        return None


def _get_texinfo(model, texinfo_idx):
    """Get texinfo by index, with caching."""
    if not hasattr(model, '_texinfo_cache') or model._texinfo_cache is None:
        model._texinfo_cache = {}

    if texinfo_idx not in model._texinfo_cache:
        model._texinfo_cache[texinfo_idx] = _parse_texinfo_entry(model.lump_texinfo, texinfo_idx)

    return model._texinfo_cache.get(texinfo_idx)


def _uv(v, s_axis, t_axis, s_off, t_off, tex_w=64.0, tex_h=64.0):
    """Compute diffuse texture UVs"""
    s = (v[0]*s_axis[0] + v[1]*s_axis[1] + v[2]*s_axis[2] + s_off) / tex_w
    t = (v[0]*t_axis[0] + v[1]*t_axis[1] + v[2]*t_axis[2] + t_off) / tex_h
    return s, t


def _lm_uv(v, s_axis, t_axis, s_off, t_off, lm_x, lm_y, lm_w, lm_h, atlas_w, atlas_h):
    """Compute lightmap UVs"""
    s = (v[0]*s_axis[0] + v[1]*s_axis[1] + v[2]*s_axis[2] + s_off)
    t = (v[0]*t_axis[0] + v[1]*t_axis[1] + v[2]*t_axis[2] + t_off)
    # Normalize into lightmap block at 16 units per luxel (Quake 2 standard)
    lu = (lm_x + (s / 16.0)) / atlas_w
    lv = (lm_y + (t / 16.0)) / atlas_h
    return lu, lv


def _alloc_lightmap(lm_block, model, face, texinfo):
    """Compute lightmap extents and allocate in atlas"""
    first_edge = face['first_edge']
    num_edges = face['num_edges']
    verts = _resolve_face_vertices(model, first_edge, num_edges)

    if len(verts) < 3:
        return None

    s_axis = texinfo.get('s_axis', [1, 0, 0])
    t_axis = texinfo.get('t_axis', [0, 1, 0])
    s_off = float(texinfo.get('s_off', 0))
    t_off = float(texinfo.get('t_off', 0))

    min_s = min_t = float('inf')
    max_s = max_t = float('-inf')
    for v in verts:
        s = v[0]*s_axis[0] + v[1]*s_axis[1] + v[2]*s_axis[2] + s_off
        t = v[0]*t_axis[0] + v[1]*t_axis[1] + v[2]*t_axis[2] + t_off
        min_s = min(min_s, s)
        max_s = max(max_s, s)
        min_t = min(min_t, t)
        max_t = max(max_t, t)

    lm_w = max(1, int((max_s - min_s) / 16.0) + 1)
    lm_h = max(1, int((max_t - min_t) / 16.0) + 1)
    lm_w = min(lm_w, 18)
    lm_h = min(lm_h, 18)

    lm_x, lm_y = lm_block.allocate(lm_w, lm_h)
    return lm_x, lm_y, lm_w, lm_h


def _fill_lightmap(lm_block, model, face, lm_x, lm_y, lm_w, lm_h):
    """Copy raw lightdata into atlas"""
    lightofs = face.get('lightofs', -1)
    if lightofs < 0 or not model.lightdata:
        # Fill with mid-grey
        for row in range(lm_h):
            for col in range(lm_w):
                px = ((lm_y + row) * lm_block.width + (lm_x + col)) * 3
                lm_block.data[px:px+3] = b'\x80\x80\x80'
        return

    src = model.lightdata
    for row in range(lm_h):
        for col in range(lm_w):
            src_idx = lightofs + (row * lm_w + col) * 3
            dst_idx = ((lm_y + row) * lm_block.width + (lm_x + col)) * 3
            if src_idx + 3 <= len(src) and dst_idx + 3 <= len(lm_block.data):
                lm_block.data[dst_idx:dst_idx+3] = src[src_idx:src_idx+3]


def _get_or_wrap_texture(gl_tex_id):
    """Wrap OpenGL tex_id as ModernGL Texture"""
    if gl_tex_id is None or gl_tex_id == 0:
        return None
    if gl_tex_id in _mgl_textures:
        return _mgl_textures[gl_tex_id]

    from . import gl_context
    from OpenGL.GL import glBindTexture, glGetTexLevelParameteriv, GL_TEXTURE_2D, GL_TEXTURE_WIDTH, GL_TEXTURE_HEIGHT

    ctx = gl_context.ctx
    if not ctx:
        return None

    try:
        # Query actual texture dimensions from OpenGL
        glBindTexture(GL_TEXTURE_2D, gl_tex_id)
        width = glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_WIDTH)
        height = glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_HEIGHT)

        # Clamp to reasonable sizes (WAL textures are typically 64-512)
        width = max(1, min(width, 512))
        height = max(1, min(height, 512))

        # Wrap with proper ModernGL signature: (obj, size, components, samples, dtype)
        mgl_tex = ctx.external_texture(gl_tex_id, (width, height), 4, samples=0, dtype='f1')
        _mgl_textures[gl_tex_id] = mgl_tex
        return mgl_tex
    except Exception as e:
        # Silently fail - texture wrapping not critical
        return None


def _build_face_batches(model, first_face, num_faces, lm_block):
    """Triangulate a range of BSP faces into {tex_name: [floats]} batches."""
    from . import gl_image

    SURF_NODRAW = 0x80
    SURF_SKY = 0x4

    batches = {}

    for face_idx in range(first_face, min(first_face + num_faces, len(model.faces))):
        face = model.faces[face_idx]
        first_edge = face.get('first_edge', 0)
        num_edges = face.get('num_edges', 0)
        if num_edges < 3:
            continue

        # Get texinfo
        texinfo_idx = face.get('texinfo', 0)
        texinfo = _get_texinfo(model, texinfo_idx)
        if not texinfo:
            continue

        # Skip NODRAW faces
        if texinfo.get('flags', 0) & SURF_NODRAW:
            continue

        # Skip SKY faces - the skybox (gl_sky) is drawn through these openings
        if texinfo.get('flags', 0) & SURF_SKY:
            continue

        tex_name = texinfo.get('texture', '')
        if not tex_name:
            continue

        # Resolve vertices
        verts = _resolve_face_vertices(model, first_edge, num_edges)
        if len(verts) < 3:
            continue

        # Allocate lightmap
        lm_alloc = _alloc_lightmap(lm_block, model, face, texinfo)
        if not lm_alloc:
            continue
        lm_x, lm_y, lm_w, lm_h = lm_alloc
        _fill_lightmap(lm_block, model, face, lm_x, lm_y, lm_w, lm_h)

        # Get texture
        gl_image.GL_FindImage(tex_name, 1)

        # UV axes
        s_axis = texinfo.get('s_axis', [1, 0, 0])
        t_axis = texinfo.get('t_axis', [0, 1, 0])
        s_off = float(texinfo.get('s_off', 0))
        t_off = float(texinfo.get('t_off', 0))

        # Fan triangulate
        if tex_name not in batches:
            batches[tex_name] = []
        buf = batches[tex_name]

        v0 = verts[0]
        for i in range(1, len(verts) - 1):
            for vi in [v0, verts[i], verts[i+1]]:
                u, v = _uv(vi, s_axis, t_axis, s_off, t_off)
                lu, lv = _lm_uv(vi, s_axis, t_axis, s_off, t_off, lm_x, lm_y, lm_w, lm_h,
                                lm_block.width, lm_block.height)
                buf.extend([vi[0], vi[1], vi[2], u, v, lu, lv])

    return batches


def _batches_to_vaos(ctx, prog, batches):
    """Upload triangulated batches into one VAO per texture."""
    vaos = {}
    for tex_name, flat in batches.items():
        if not flat:
            continue
        arr = np.array(flat, dtype=np.float32)
        vbo = ctx.buffer(arr.tobytes())
        vao = ctx.vertex_array(prog,
                                [(vbo, '3f 2f 2f', 'in_position', 'in_texcoord', 'in_lm_coord')])
        vert_count = len(flat) // VERTEX_STRIDE
        vaos[tex_name] = (vao, vbo, vert_count)
    return vaos


def R_BuildWorldBuffers(worldmodel):
    """Build VAO/VBO for all BSP faces at map load time.

    Submodels (BSP models 1..n: doors, buttons, plats, func_wall) get their own
    VAOs so movers can be drawn at a per-frame offset instead of being baked
    into the static world geometry.
    """
    from . import gl_context

    model_key = id(worldmodel)
    if model_key in _world_vaos:
        return  # Already built

    ctx = gl_context.ctx
    prog = gl_context.bsp_program
    if not ctx or not prog:
        return

    # One lightmap atlas covers the world and every submodel
    lm_block = LightmapBlock()

    bsp_models = getattr(worldmodel, 'models', None) or []
    if bsp_models:
        world_first = bsp_models[0]['first_face']
        world_count = bsp_models[0]['num_faces']
    else:
        world_first, world_count = 0, len(worldmodel.faces)

    world_batches = _build_face_batches(worldmodel, world_first, world_count, lm_block)

    submodel_batches = {}
    for index in range(1, len(bsp_models)):
        batches = _build_face_batches(worldmodel, bsp_models[index]['first_face'],
                                      bsp_models[index]['num_faces'], lm_block)
        if batches:
            submodel_batches[index] = batches

    # Upload lightmap atlas
    lm_data = bytes(lm_block.data)
    lm_tex = ctx.texture((lm_block.width, lm_block.height), 3, data=lm_data, dtype='f1')
    lm_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)

    _world_vaos[model_key] = _batches_to_vaos(ctx, prog, world_batches)
    _submodel_vaos[model_key] = {index: _batches_to_vaos(ctx, prog, batches)
                                 for index, batches in submodel_batches.items()}
    _world_vbos[model_key] = lm_tex


def _draw_vaos(prog, vaos, offset):
    """Draw one batch group displaced by offset."""
    from . import gl_image

    prog['u_offset'].value = tuple(float(v) for v in offset)
    for tex_name, (vao, vbo, vert_count) in vaos.items():
        tex_id = gl_image.GL_FindImage(tex_name, 1)
        mgl_tex = _get_or_wrap_texture(tex_id)
        if mgl_tex:
            mgl_tex.use(location=0)
        vao.render(moderngl.TRIANGLES)


def R_DrawWorld(worldmodel, submodel_offsets=None):
    """Render world model and its submodels - ModernGL version.

    submodel_offsets maps a BSP submodel index to its current world-space
    displacement (see quake2/cl_doors.py); anything not listed draws in place.
    """
    from . import gl_context

    ctx = gl_context.ctx
    prog = gl_context.bsp_program
    if not ctx or not prog:
        return

    model_key = id(worldmodel)
    if model_key not in _world_vaos:
        R_BuildWorldBuffers(worldmodel)
        if model_key not in _world_vaos:
            return

    lm_tex = _world_vbos.get(model_key)
    if lm_tex:
        lm_tex.use(location=1)

    _draw_vaos(prog, _world_vaos[model_key], _NO_OFFSET)

    for index, vaos in _submodel_vaos.get(model_key, {}).items():
        offset = _NO_OFFSET
        if submodel_offsets:
            offset = submodel_offsets.get(index, _NO_OFFSET)
        _draw_vaos(prog, vaos, offset)

    prog['u_offset'].value = _NO_OFFSET


def R_FreeWorldBuffers(model=None):
    """Free GPU buffers"""
    model_key = id(model) if model else None
    keys = [model_key] if model_key else list(_world_vaos.keys())
    for k in keys:
        if k in _world_vaos:
            for tex_name, (vao, vbo, _) in _world_vaos[k].items():
                vao.release()
                vbo.release()
            del _world_vaos[k]
        if k in _submodel_vaos:
            for vaos in _submodel_vaos[k].values():
                for tex_name, (vao, vbo, _) in vaos.items():
                    vao.release()
                    vbo.release()
            del _submodel_vaos[k]
        if k in _world_vbos:
            _world_vbos[k].release()
            del _world_vbos[k]
    _mgl_textures.clear()


# Keep old stubs for compatibility
def R_DrawBrushModel(model):
    """Brush model rendering - TODO"""
    pass

def GL_BeginBuildingLightmaps():
    """Start lightmap building - TODO"""
    pass

def GL_EndBuildingLightmaps():
    """End lightmap building - TODO"""
    pass

def R_MarkLeaves():
    """Mark visible leaves - TODO"""
    pass

def R_SetFrustum():
    """Set frustum - TODO"""
    pass

def DrawGLPoly(poly_verts):
    """Draw polygon - TODO"""
    pass

def DrawTextureChains():
    """Draw texture chains - TODO"""
    pass

def R_DrawAlphaSurfaces():
    """Draw alpha surfaces - TODO"""
    pass
