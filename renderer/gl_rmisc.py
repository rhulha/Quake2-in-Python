import math
import numpy as np
import moderngl
from typing import Optional

from .gl_image import Image, ImageManager


def init_particle_texture(image_manager: ImageManager) -> Image:
    """Create the small soft-circle particle texture and register it.

    Returns the Image object.  The texture is a 16×16 RGBA image with a
    circular soft-edged white dot – identical to the original gl_rmisc.c
    R_InitParticleTexture().
    """
    SIZE = 16
    pixels = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)
    cx = cy = SIZE / 2.0

    for y in range(SIZE):
        for x in range(SIZE):
            dx = x + 0.5 - cx
            dy = y + 0.5 - cy
            dist = math.sqrt(dx * dx + dy * dy)
            radius = SIZE / 2.0
            if dist < radius:
                alpha = int(255 * (1.0 - dist / radius))
                pixels[y, x] = [255, 255, 255, alpha]

    tex = image_manager.ctx.texture((SIZE, SIZE), 4, pixels.tobytes())
    img = Image(
        name='__particle__',
        type='skin',
        width=SIZE,
        height=SIZE,
        upload_width=SIZE,
        upload_height=SIZE,
        texture=tex,
    )
    image_manager.gltextures['__particle__'] = img
    return img


def set_default_state(ctx: moderngl.Context):
    """Apply the standard GL state that the renderer assumes at the start of
    each frame and after any sub-system that might have altered it.

    Mirrors GL_SetDefaultState() from the original gl_rmisc.c.
    """
    ctx.enable(moderngl.DEPTH_TEST)
    ctx.enable(moderngl.CULL_FACE)
    ctx.front_face      = 'cw'     # Quake models use clockwise winding
    ctx.depth_func      = '<'
    ctx.depth_write_mask = True

    # No blending by default
    ctx.disable(moderngl.BLEND)

    # Viewport depth range is already [0, 1] in ModernGL – nothing to set.


def screenshot(ctx: moderngl.Context, filepath: str):
    """Read the current framebuffer and save it as a raw PPM file.

    PPM requires no external library and is universally readable.
    """
    vp = ctx.viewport               # (x, y, w, h)
    w, h = vp[2], vp[3]

    # Read RGBA pixels from front buffer
    raw = ctx.screen.read(viewport=(0, 0, w, h))
    pixels = np.frombuffer(raw, dtype=np.uint8).reshape(h, w, 4)

    # Flip vertically (OpenGL origin is bottom-left)
    pixels = pixels[::-1, :, :3]    # RGB only

    with open(filepath, 'wb') as f:
        header = f'P6\n{w} {h}\n255\n'.encode('ascii')
        f.write(header)
        f.write(pixels.tobytes())

    print(f'[gl_rmisc] screenshot saved to {filepath}')


def update_swap_interval(ctx: moderngl.Context, interval: int):
    """Enable or disable vsync.

    ModernGL does not expose a swap-interval API directly; this is a no-op
    placeholder that logs the request.  The interval is best set during
    context creation via pygame.display.gl_set_attribute before the window
    is created.
    """
    print(f'[gl_rmisc] swap interval requested: {interval} (set at context creation)')


def gl_strings(ctx: moderngl.Context):
    """Print vendor/renderer/version strings to stdout."""
    info = ctx.info
    print(f"[gl_rmisc] GL_VENDOR   : {info.get('GL_VENDOR', 'unknown')}")
    print(f"[gl_rmisc] GL_RENDERER : {info.get('GL_RENDERER', 'unknown')}")
    print(f"[gl_rmisc] GL_VERSION  : {info.get('GL_VERSION', 'unknown')}")
