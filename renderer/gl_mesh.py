import struct
import numpy as np
import moderngl
from typing import Optional, List, Tuple

from .gl_model import Model, ModelType, MDLAliasHeader, MDLFrame
from .gl_image import Image


# Each MD2 glcmd vertex entry is two floats (s, t) + one int32 (vertex index)
_CMD_VERT_FMT = struct.Struct('<ffI')
_CMD_VERT_SIZE = _CMD_VERT_FMT.size   # 12 bytes


def _decompress_frame(frame: MDLFrame) -> np.ndarray:
    """Decompress a single MD2 frame into world-space float positions.

    frame.verts is shape (N, 4) uint8: (x_compressed, y, z, lightnormal_index).
    Returns float32 array of shape (N, 3).
    """
    compressed = frame.verts[:, :3].astype(np.float32)
    return compressed * frame.scale + frame.translate


def _lerp_positions(curr: np.ndarray, prev: np.ndarray, backlerp: float) -> np.ndarray:
    """Linearly interpolate between two decompressed frame position arrays."""
    front = 1.0 - backlerp
    return curr * front + prev * backlerp


def _normal_from_index(index: int) -> np.ndarray:
    """Return the Quake2 pre-computed vertex normal for the given lightnormal index."""
    from .gl_rmain import VERTEX_NORMALS
    if 0 <= index < len(VERTEX_NORMALS):
        return VERTEX_NORMALS[index]
    return np.array([0.0, 0.0, 1.0], dtype=np.float32)


def _lerp_normal(curr_idx: int, prev_idx: int, backlerp: float) -> np.ndarray:
    n0 = _normal_from_index(curr_idx)
    n1 = _normal_from_index(prev_idx)
    front = 1.0 - backlerp
    n = n0 * front + n1 * backlerp
    length = np.linalg.norm(n)
    if length > 0:
        n /= length
    return n


def _shade_normal(normal: np.ndarray, shade_light: np.ndarray,
                  shade_vector: np.ndarray) -> float:
    """Compute a simple dot-product shade value clamped to [0, 1]."""
    dot = np.dot(normal, shade_vector)
    if dot < 0.0:
        dot = 0.0
    return min(1.0, dot + 0.3)    # 0.3 ambient


class AliasRenderer:
    """Renders MD2 alias models with frame interpolation using the alias shader."""

    def __init__(self, ctx: moderngl.Context, program: moderngl.Program):
        self.ctx = ctx
        self.program = program

    # ------------------------------------------------------------------

    def draw_alias_model(self, model: Model, skin: Optional[Image],
                         curr_frame: int, next_frame: int, backlerp: float,
                         shade_light: np.ndarray, shade_vector: np.ndarray):
        """Build and draw the interpolated alias mesh for one entity.

        shade_light   - RGB ambient + directional light colour (float 0..1)
        shade_vector  - unit vec pointing toward dominant light source
        backlerp      - blend factor toward prev frame (0 = fully current)
        """
        if model.type != ModelType.ALIAS:
            return
        if not model.frames or model.glcmds is None:
            return

        num_frames = len(model.frames)
        curr_frame = curr_frame % num_frames
        next_frame = next_frame % num_frames

        frame_curr = model.frames[curr_frame]
        frame_prev = model.frames[next_frame]

        pos_curr = _decompress_frame(frame_curr)
        pos_prev = _decompress_frame(frame_prev)
        pos_lerp = _lerp_positions(pos_curr, pos_prev, backlerp)

        # Build draw calls by walking the glcmds list
        verts_data = self._build_vertex_data(
            model, pos_lerp,
            frame_curr.verts[:, 3],
            frame_prev.verts[:, 3],
            backlerp,
            shade_light, shade_vector,
        )

        if not verts_data:
            return

        combined = np.concatenate(verts_data['strip'] + verts_data['fan'], axis=0)
        if len(combined) == 0:
            return

        vbo = self.ctx.buffer(combined.astype(np.float32))
        vao = self.ctx.vertex_array(
            self.program,
            [(vbo, '3f 2f 4f 3f', 'pos', 'uv', 'color', 'normal')],
        )

        if skin and skin.texture:
            skin.texture.use(0)
            if 'skin_tex' in self.program:
                self.program['skin_tex'].value = 0

        # Draw strips
        offset = 0
        for n in verts_data['strip_counts']:
            vao.render(moderngl.TRIANGLE_STRIP, first=offset, vertices=n)
            offset += n
        for n in verts_data['fan_counts']:
            vao.render(moderngl.TRIANGLE_FAN, first=offset, vertices=n)
            offset += n

        vao.release()
        vbo.release()

    # ------------------------------------------------------------------

    def _build_vertex_data(self, model: Model,
                           pos_lerp: np.ndarray,
                           normals_curr: np.ndarray,
                           normals_prev: np.ndarray,
                           backlerp: float,
                           shade_light: np.ndarray,
                           shade_vector: np.ndarray) -> dict:
        """Walk the glcmds array and produce lists of vertex data arrays."""
        cmds = model.glcmds
        result = {'strip': [], 'strip_counts': [], 'fan': [], 'fan_counts': []}

        i = 0
        while i < len(cmds):
            count = int(cmds[i])
            i += 1
            if count == 0:
                break

            is_fan = count < 0
            count = abs(count)

            verts = np.empty((count, 12), dtype=np.float32)  # pos3, uv2, rgba4, normal3
            for v_idx in range(count):
                base = i * 4   # cmds are int32; stored as flat array in glcmds
                # glcmds interleaved: float s, float t, int32 vertnum
                # model.glcmds is a flat int32 ndarray, so we reinterpret s/t as float
                raw = cmds[i:i + 3]
                s = raw[0:1].view(np.float32)[0]
                t = raw[1:2].view(np.float32)[0]
                vert_num = int(raw[2])
                i += 3

                # Clamped vertex index
                if vert_num >= len(pos_lerp):
                    vert_num = 0

                pos = pos_lerp[vert_num]

                # Lighting
                ni_curr = int(normals_curr[vert_num]) if vert_num < len(normals_curr) else 0
                ni_prev = int(normals_prev[vert_num]) if vert_num < len(normals_prev) else 0
                normal = _lerp_normal(ni_curr, ni_prev, backlerp)
                shade = _shade_normal(normal, shade_light, shade_vector)
                r = min(1.0, shade_light[0] * shade)
                g = min(1.0, shade_light[1] * shade)
                b = min(1.0, shade_light[2] * shade)

                verts[v_idx, 0:3] = pos
                verts[v_idx, 3] = s
                verts[v_idx, 4] = t
                verts[v_idx, 5] = r
                verts[v_idx, 6] = g
                verts[v_idx, 7] = b
                verts[v_idx, 8] = 1.0   # alpha
                verts[v_idx, 9:12] = normal

            if is_fan:
                result['fan'].append(verts)
                result['fan_counts'].append(count)
            else:
                result['strip'].append(verts)
                result['strip_counts'].append(count)

        return result
