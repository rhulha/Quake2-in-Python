"""
gl_mesh.py - MD2 model mesh rendering
Handles vertex interpolation and frame animation for alias models
"""

import struct
import math
import numpy as np
from OpenGL.GL import *
from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), ["Com_Printf"])

# ===== MD2 Format Constants =====

MD2_MAGIC = 0x32504449  # "IDP2"
MD2_VERSION = 8
MD2_FRAME_NAME_LEN = 16


# ===== MD2 Structures =====

class MD2Header:
    """MD2 file header"""
    def __init__(self):
        self.magic = 0
        self.version = 0
        self.skinwidth = 0
        self.skinheight = 0
        self.framesize = 0
        self.num_skins = 0
        self.num_vertices = 0
        self.num_texcoords = 0
        self.num_triangles = 0
        self.num_glcmds = 0
        self.num_frames = 0
        self.offset_skins = 0
        self.offset_texcoords = 0
        self.offset_triangles = 0
        self.offset_frames = 0
        self.offset_glcmds = 0
        self.offset_end = 0


class MD2Frame:
    """Single animation frame"""
    def __init__(self, num_vertices=0):
        self.scale = [1.0, 1.0, 1.0]
        self.translate = [0.0, 0.0, 0.0]
        self.name = ""
        self.vertices = []  # List of [x, y, z, normal_index]


class MD2Vertex:
    """Packed vertex data"""
    def __init__(self, x=0, y=0, z=0, normal_idx=0):
        self.x = x
        self.y = y
        self.z = z
        self.normal_idx = normal_idx


# ===== MD2 Loading =====

def Load_MD2(filename):
    """Load MD2 model file"""
    try:
        from ..quake2.files import FS_LoadFile

        data, length = FS_LoadFile(filename)
        if data is None or length < 68:
            return None

        # Parse header
        header = MD2Header()
        header.magic = struct.unpack_from('<I', data, 0)[0]
        header.version = struct.unpack_from('<I', data, 4)[0]
        header.skinwidth = struct.unpack_from('<I', data, 8)[0]
        header.skinheight = struct.unpack_from('<I', data, 12)[0]
        header.framesize = struct.unpack_from('<I', data, 16)[0]
        header.num_skins = struct.unpack_from('<I', data, 20)[0]
        header.num_vertices = struct.unpack_from('<I', data, 24)[0]
        header.num_texcoords = struct.unpack_from('<I', data, 28)[0]
        header.num_triangles = struct.unpack_from('<I', data, 32)[0]
        header.num_glcmds = struct.unpack_from('<I', data, 36)[0]
        header.num_frames = struct.unpack_from('<I', data, 40)[0]
        header.offset_skins = struct.unpack_from('<I', data, 44)[0]
        header.offset_texcoords = struct.unpack_from('<I', data, 48)[0]
        header.offset_triangles = struct.unpack_from('<I', data, 52)[0]
        header.offset_frames = struct.unpack_from('<I', data, 56)[0]
        header.offset_glcmds = struct.unpack_from('<I', data, 60)[0]
        header.offset_end = struct.unpack_from('<I', data, 64)[0]

        # Verify
        if header.magic != MD2_MAGIC or header.version != MD2_VERSION:
            return None

        # Load frames
        frames = []
        for frame_idx in range(header.num_frames):
            frame = MD2Frame(header.num_vertices)

            offset = header.offset_frames + frame_idx * header.framesize

            # Read scale and translate
            frame.scale = list(struct.unpack_from('<fff', data, offset))
            frame.translate = list(struct.unpack_from('<fff', data, offset + 12))

            # Frame name (16 bytes)
            frame.name = data[offset + 24:offset + 40].decode('latin-1', errors='ignore').rstrip('\x00')

            # Read vertices
            vert_offset = offset + 40
            for i in range(header.num_vertices):
                v_offset = vert_offset + i * 4
                if v_offset + 4 <= len(data):
                    x, y, z, normal_idx = struct.unpack_from('BBBB', data, v_offset)
                    # Unpack vertex (stored as signed bytes)
                    x = (x - 128) / 128.0 * frame.scale[0] + frame.translate[0]
                    y = (y - 128) / 128.0 * frame.scale[1] + frame.translate[1]
                    z = (z - 128) / 128.0 * frame.scale[2] + frame.translate[2]
                    frame.vertices.append(MD2Vertex(x, y, z, normal_idx))

            frames.append(frame)

        # Load triangles
        triangles = []
        for tri_idx in range(header.num_triangles):
            offset = header.offset_triangles + tri_idx * 12
            if offset + 12 <= len(data):
                v0, v1, v2, t0, t1, t2 = struct.unpack_from('<HHHHHH', data, offset)
                triangles.append([(v0, t0), (v1, t1), (v2, t2)])

        return {
            'header': header,
            'frames': frames,
            'triangles': triangles,
            'filename': filename,
        }

    except Exception as e:
        print(f"Load_MD2 error: {e}")
        return None


# ===== Render Pipeline =====

def R_DrawAliasModel(ent):
    """Draw MD2 (alias) model with animation and lighting"""
    try:
        if not ent or not ent.model:
            return

        model_type = ent.model.type if hasattr(ent.model, 'type') else None
        if model_type != 2:  # MODEL_ALIAS (2)
            return

        # Get model data
        model_data = ent.model.mesh_data if hasattr(ent.model, 'mesh_data') else None
        if not model_data:
            return

        # Setup entity lighting
        try:
            from . import gl_light
            gl_light.SetupEntityLighting(ent, ent.model)
        except:
            glColor3f(1.0, 1.0, 1.0)  # Default white if lighting fails

        # Get animation frame
        frame = int(ent.frame) % len(model_data['frames'])
        oldframe = int(ent.oldframe) % len(model_data['frames'])
        backlerp = float(ent.backlerp)

        # Setup entity transform
        glPushMatrix()

        # Translate to entity position
        glTranslatef(ent.origin[0], ent.origin[1], ent.origin[2])

        # Rotate by entity angles
        glRotatef(ent.angles[1], 0, 0, 1)  # Yaw
        glRotatef(ent.angles[0], 1, 0, 0)  # Pitch
        glRotatef(ent.angles[2], 0, 1, 0)  # Roll

        # Draw the frame(s)
        GL_DrawAliasFrameLerp(model_data, oldframe, frame, backlerp)

        glPopMatrix()

    except Exception as e:
        print(f"R_DrawAliasModel error: {e}")


def GL_DrawAliasFrameLerp(model_data, oldframe_idx, frame_idx, lerp):
    """Draw MD2 model with frame interpolation"""
    try:
        if not model_data or 'frames' not in model_data:
            return

        frames = model_data['frames']
        triangles = model_data['triangles']
        header = model_data['header']

        if oldframe_idx >= len(frames) or frame_idx >= len(frames):
            return

        oldframe = frames[oldframe_idx]
        frame = frames[frame_idx]

        # Ensure frames have vertices
        if not oldframe.vertices or not frame.vertices:
            return

        # Interpolate and render
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_TRIANGLES)

        for tri in triangles:
            for vert_idx, tex_idx in tri:
                if vert_idx < len(oldframe.vertices) and vert_idx < len(frame.vertices):
                    # Get vertices from both frames
                    old_v = oldframe.vertices[vert_idx]
                    new_v = frame.vertices[vert_idx]

                    # Interpolate position
                    x = old_v.x + (new_v.x - old_v.x) * lerp
                    y = old_v.y + (new_v.y - old_v.y) * lerp
                    z = old_v.z + (new_v.z - old_v.z) * lerp

                    glVertex3f(x, y, z)

        glEnd()

    except Exception as e:
        print(f"GL_DrawAliasFrameLerp error: {e}")


def GL_LerpVerts(nverts, v, ov, verts, lerp, move, frontv, backv):
    """Interpolate vertex positions between frames"""
    try:
        if not v or not ov or len(v) == 0 or len(ov) == 0:
            return

        # Linear interpolation: result = ov * (1 - lerp) + v * lerp
        result = []
        for i in range(min(nverts, len(v), len(ov))):
            old_vert = ov[i]
            new_vert = v[i]

            x = old_vert.x + (new_vert.x - old_vert.x) * lerp
            y = old_vert.y + (new_vert.y - old_vert.y) * lerp
            z = old_vert.z + (new_vert.z - old_vert.z) * lerp

            result.append(MD2Vertex(x, y, z, new_vert.normal_idx))

        return result

    except Exception as e:
        print(f"GL_LerpVerts error: {e}")
        return None


def GL_DrawAliasShadow(paliashdr, posenum):
    """Draw shadow beneath alias model"""
    try:
        # Draw a simple shadow polygon below the model
        glColor4f(0.0, 0.0, 0.0, 0.3)
        glBegin(GL_TRIANGLE_FAN)

        # Shadow circle
        for i in range(16):
            angle = (i / 16.0) * 2.0 * 3.14159
            x = 16.0 * math.cos(angle)
            y = 16.0 * math.sin(angle)
            glVertex3f(x, y, 0.0)

        glEnd()

    except Exception as e:
        print(f"GL_DrawAliasShadow error: {e}")


def GL_LightVertex(v, lv):
    """Apply lighting to vertex"""
    # Simple fullbright for now
    return [1.0, 1.0, 1.0]


def GL_DrawAliasFrame(paliashdr, posenum):
    """Draw single alias frame without interpolation"""
    try:
        if not paliashdr or 'frames' not in paliashdr:
            return

        frames = paliashdr['frames']
        triangles = paliashdr['triangles']

        if posenum >= len(frames):
            return

        frame = frames[posenum]

        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_TRIANGLES)

        for tri in triangles:
            for vert_idx, tex_idx in tri:
                if vert_idx < len(frame.vertices):
                    v = frame.vertices[vert_idx]
                    glVertex3f(v.x, v.y, v.z)

        glEnd()

    except Exception as e:
        print(f"GL_DrawAliasFrame error: {e}")


def R_CullAliasModel(bbox, e):
    """Frustum cull alias model bounding box"""
    # TODO: Implement frustum culling
    return False  # Not culled


def Mod_LoadAlias(mod, data):
    """Load alias (MD2) model into model structure"""
    try:
        md2_data = Load_MD2(mod.name)
        if md2_data:
            mod.mesh_data = md2_data
            mod.numframes = md2_data['header'].num_frames
            return True

        return False

    except Exception as e:
        print(f"Mod_LoadAlias error: {e}")
        return False


# ===== Quad Command Support (for optimized rendering) =====

def GL_DrawGLCmd(glcmd_data):
    """Draw using GL command list from MD2 file"""
    # TODO: Implement GL command list rendering for better performance
    pass


# ===== Normal Table (Quake 2 uses 162 predefined normals) =====

NORMAL_TABLE = [
    [-0.525731, 0.000000, 0.850651],
    [-0.442863, 0.238856, 0.864888],
    [-0.295242, 0.000000, 0.955423],
    [-0.309017, 0.500000, 0.809017],
    [-0.162460, 0.262866, 0.951056],
    [0.000000, 0.000000, 1.000000],
    [0.000000, 0.850651, 0.525731],
    [-0.147621, 0.716567, 0.681718],
    [0.147621, 0.716567, 0.681718],
    [0.000000, 0.525731, 0.850651],
    [0.309017, 0.500000, 0.809017],
    [0.525731, 0.000000, 0.850651],
    [0.295242, 0.000000, 0.955423],
    [0.442863, 0.238856, 0.864888],
    [0.162460, 0.262866, 0.951056],
    [-0.681718, 0.147621, 0.716567],
    [-0.809017, 0.309017, 0.500000],
    [-0.587785, 0.425325, 0.688191],
    [-0.850651, 0.525731, 0.000000],
    [-0.864888, 0.442863, 0.238856],
    [-0.716567, 0.681718, 0.147621],
    [-0.688191, 0.587785, 0.425325],
    [-0.500000, 0.809017, 0.309017],
    [-0.238856, 0.864888, 0.442863],
    [-0.425325, 0.688191, 0.587785],
    [-0.716567, 0.681718, -0.147621],
    [-0.500000, 0.809017, -0.309017],
    [-0.525731, 0.850651, 0.000000],
    [0.000000, 0.850651, -0.525731],
    [-0.238856, 0.864888, -0.442863],
    [0.000000, 0.955423, -0.295242],
    [-0.262866, 0.951056, -0.162460],
    [0.000000, 1.000000, 0.000000],
    [0.000000, 0.955423, 0.295242],
    [-0.262866, 0.951056, 0.162460],
    [0.238856, 0.864888, 0.442863],
    [0.262866, 0.951056, 0.162460],
    [0.500000, 0.809017, 0.309017],
    [0.238856, 0.864888, -0.442863],
    [0.262866, 0.951056, -0.162460],
    [0.500000, 0.809017, -0.309017],
    [0.850651, 0.525731, 0.000000],
    [0.716567, 0.681718, 0.147621],
    [0.716567, 0.681718, -0.147621],
    [0.525731, 0.850651, 0.000000],
    [0.425325, 0.688191, 0.587785],
    [0.864888, 0.442863, 0.238856],
    [0.688191, 0.587785, 0.425325],
    [0.809017, 0.309017, 0.500000],
    [0.681718, 0.147621, 0.716567],
    [0.587785, 0.425325, 0.688191],
    [0.442863, 0.238856, 0.864888],
    [0.428571, 0.857143, 0.285714],
    [0.000000, 0.000000, -1.000000],
]
