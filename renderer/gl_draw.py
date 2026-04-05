import numpy as np
import moderngl
from typing import Optional, Tuple

from .gl_image import Image, ImageManager

# Quake 2 charset: 256 chars laid out in a 16×16 grid on a 128×128 image.
# Each character cell is 8×8 pixels.
_CHARSET_COLS = 16
_CHARSET_ROWS = 16
_CHAR_W       = 1.0 / _CHARSET_COLS   # UV width  of one char
_CHAR_H       = 1.0 / _CHARSET_ROWS   # UV height of one char


def _char_uv(num: int) -> Tuple[float, float, float, float]:
    """Return (u0, v0, u1, v1) UV coordinates for character num in the Quake charset."""
    num = num & 0xFF
    col = num % _CHARSET_COLS
    row = num // _CHARSET_COLS
    u0 = col * _CHAR_W
    v0 = row * _CHAR_H
    return u0, v0, u0 + _CHAR_W, v0 + _CHAR_H


def _quad_verts(x: float, y: float, w: float, h: float,
                u0: float, v0: float, u1: float, v1: float,
                r: float = 1.0, g: float = 1.0, b: float = 1.0,
                a: float = 1.0) -> np.ndarray:
    """Build two-triangle (6-vertex) interleaved data for a 2-D quad.

    Vertex layout: pos2(x,y), uv2(u,v), color4(r,g,b,a)  → 8 floats per vertex.
    """
    return np.array([
        x,     y,     u0, v0, r, g, b, a,
        x + w, y,     u1, v0, r, g, b, a,
        x + w, y + h, u1, v1, r, g, b, a,
        x,     y,     u0, v0, r, g, b, a,
        x + w, y + h, u1, v1, r, g, b, a,
        x,     y + h, u0, v1, r, g, b, a,
    ], dtype=np.float32)


class HUDRenderer:
    """2-D drawing system for the HUD / console / menus.

    Uses the quad2d shader (ortho matrix, pos2 uv2 color4 layout).
    """

    def __init__(self, ctx: moderngl.Context, program: moderngl.Program,
                 image_manager: ImageManager):
        self.ctx      = ctx
        self.program  = program
        self.images   = image_manager

        self._charset: Optional[Image] = None

        # Batch accumulation: collect quads before flushing to GPU
        self._batch: list = []

        # Reusable VBO (resized as needed)
        self._vbo: Optional[moderngl.Buffer] = None
        self._vao: Optional[moderngl.VertexArray] = None

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def init(self, ortho: np.ndarray):
        """Load the charset and write the ortho matrix."""
        self._charset = self.images.find_image('pics/conchars.pcx', 'pic')
        self._update_ortho(ortho)

    def _update_ortho(self, ortho: np.ndarray):
        if 'ortho' in self.program:
            self.program['ortho'].write(ortho.astype(np.float32).tobytes())

    # ------------------------------------------------------------------
    # Public drawing API
    # ------------------------------------------------------------------

    def draw_char(self, x: int, y: int, num: int):
        """Queue a single 8×8 character from the Quake charset."""
        if num == 32:  # space
            return
        u0, v0, u1, v1 = _char_uv(num)
        self._batch.append((self._charset, _quad_verts(x, y, 8, 8, u0, v0, u1, v1)))

    def draw_string(self, x: int, y: int, text: str):
        """Draw an ASCII string using the Quake charset."""
        for i, ch in enumerate(text):
            self.draw_char(x + i * 8, y, ord(ch))

    def draw_pic(self, x: int, y: int, name: str):
        """Draw a full named 2-D image at pixel position (x, y)."""
        img = self._find_pic(name)
        if img is None:
            return
        verts = _quad_verts(x, y, img.width, img.height, 0.0, 0.0, 1.0, 1.0)
        self._batch.append((img, verts))

    def draw_stretch_pic(self, x: int, y: int, w: int, h: int, name: str):
        """Draw a named 2-D image stretched to (w, h)."""
        img = self._find_pic(name)
        if img is None:
            return
        verts = _quad_verts(x, y, w, h, 0.0, 0.0, 1.0, 1.0)
        self._batch.append((img, verts))

    def draw_fill(self, x: int, y: int, w: int, h: int,
                  r: float, g: float, b: float, a: float = 1.0):
        """Draw a solid-color rectangle.  Uses a 1×1 white pixel texture."""
        img = self._get_white()
        verts = _quad_verts(x, y, w, h, 0.0, 0.0, 1.0, 1.0, r, g, b, a)
        self._batch.append((img, verts))

    def draw_fill_color8(self, x: int, y: int, w: int, h: int, color_index: int):
        """Draw a fill using a Quake palette index (0-255)."""
        r, g, b = _quake_palette_rgb(color_index)
        self.draw_fill(x, y, w, h, r, g, b)

    def fade_screen(self, alpha: float = 0.6):
        """Darken the whole screen by overlaying a translucent black quad."""
        # We don't know screen size here; caller should use draw_fill with screen dims.
        # Provide a helper that flushes immediately to guarantee ordering.
        pass

    # ------------------------------------------------------------------
    # Flush batch to GPU
    # ------------------------------------------------------------------

    def flush(self):
        """Upload and draw all accumulated quads, then clear the batch."""
        if not self._batch:
            return

        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

        # Group consecutive quads by texture to minimise texture binds
        current_tex = None
        run_verts: list = []

        def _flush_run():
            nonlocal current_tex, run_verts
            if not run_verts:
                return
            data = np.concatenate(run_verts, axis=0).astype(np.float32)
            vbo = self.ctx.buffer(data.tobytes())
            vao = self.ctx.vertex_array(
                self.program,
                [(vbo, '2f 2f 4f', 'pos', 'uv', 'color')],
            )
            if current_tex and current_tex.texture:
                current_tex.texture.use(0)
                if 'tex' in self.program:
                    self.program['tex'].value = 0
            vao.render(moderngl.TRIANGLES)
            vao.release()
            vbo.release()
            run_verts.clear()

        for img, verts in self._batch:
            if img is not current_tex:
                _flush_run()
                current_tex = img
            run_verts.append(verts)

        _flush_run()
        self._batch.clear()

        self.ctx.disable(moderngl.BLEND)
        self.ctx.enable(moderngl.DEPTH_TEST)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_pic(self, name: str) -> Optional[Image]:
        if not name.startswith('/') and '.' not in name:
            name = f'pics/{name}.pcx'
        return self.images.find_image(name, 'pic')

    def _get_white(self) -> Optional[Image]:
        """Return (or create) a 1×1 white RGBA texture."""
        if '__white__' not in self.images.gltextures:
            pixels = np.full((1, 1, 4), 255, dtype=np.uint8)
            tex = self.images.ctx.texture((1, 1), 4, pixels.tobytes())
            from .gl_image import Image
            img = Image(
                name='__white__', type='pic',
                width=1, height=1, upload_width=1, upload_height=1,
                texture=tex,
            )
            self.images.gltextures['__white__'] = img
        return self.images.gltextures['__white__']


# -----------------------------------------------------------------------
# Quake 2 default palette (abridged – first 16 entries shown, rest are
# synthesised).  A real implementation would load the palette from the
# pak file.  This is sufficient for Draw_Fill color indices.
# -----------------------------------------------------------------------

_PALETTE_CACHE: Optional[np.ndarray] = None


def _quake_palette_rgb(index: int) -> Tuple[float, float, float]:
    """Return normalised RGB for Quake 2 palette index 0-255."""
    global _PALETTE_CACHE
    if _PALETTE_CACHE is None:
        _PALETTE_CACHE = _build_default_palette()
    idx = index & 0xFF
    r, g, b = _PALETTE_CACHE[idx]
    return r / 255.0, g / 255.0, b / 255.0


def _build_default_palette() -> np.ndarray:
    """Build a placeholder 256-colour palette (greyscale fallback)."""
    pal = np.zeros((256, 3), dtype=np.uint8)
    for i in range(256):
        v = i
        pal[i] = [v, v, v]
    return pal
