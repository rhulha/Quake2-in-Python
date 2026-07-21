"""
gl_hud.py - ModernGL 2D HUD renderer

Draws the in-game heads-up display (crosshair, health, current weapon) on top
of the 3D scene. The legacy gl_draw.py uses fixed-function OpenGL that the
core-profile ModernGL context can't run, so this module reimplements the 2D
draw path with shaders and a screen-space orthographic projection.
"""

import struct
import numpy as np
import moderngl

# HUD number pics (num_0..num_9) render at their native pixel size. The
# transparent color in Quake 2 pics is palette index 255.
TRANSPARENT_INDEX = 255

_program = None
_vbo = None
_vao = None
_textures = {}   # pic name -> (moderngl.Texture, width, height) or None

# Weapon list index / name -> weapon icon pic in pics/.
_WEAPON_ICONS = {
    'Blaster': 'w_blaster',
    'Shotgun': 'w_shotgun',
    'Super Shotgun': 'w_sshotgun',
    'Machinegun': 'w_machinegun',
    'Chaingun': 'w_chaingun',
    'Grenade Launcher': 'w_glauncher',
    'Rocket Launcher': 'w_rlauncher',
    'HyperBlaster': 'w_hyperblaster',
    'Railgun': 'w_railgun',
    'BFG10K': 'w_bfg',
}


def _get_program():
    global _program, _vbo, _vao
    from . import gl_context
    if _program is not None:
        return _program
    if not gl_context.ctx:
        return None
    from . import shaders
    ctx = gl_context.ctx
    _program = ctx.program(vertex_shader=shaders.HUD_VERT,
                           fragment_shader=shaders.HUD_FRAG)
    # 6 vertices (two triangles) * (2 pos + 2 uv) floats, rewritten per quad.
    _vbo = ctx.buffer(reserve=6 * 4 * 4, dynamic=True)
    _vao = ctx.vertex_array(_program, [(_vbo, '2f 2f', 'in_position', 'in_texcoord')])
    return _program


def _decode_pcx(name):
    """Decode a pics/<name>.pcx into (rgba_bytes, width, height).

    Palette index 255 is made fully transparent (Quake 2 pic convention)."""
    from quake2.files import FS_LoadFile
    from . import gl_image

    palette = gl_image.palette_data
    if palette is None:
        return None

    path = name if name.endswith('.pcx') else f"pics/{name}.pcx"
    data, length = FS_LoadFile(path)
    if data is None or length < 128:
        return None

    if data[0] != 10 or data[2] != 1:  # manufacturer / RLE encoding
        return None
    xmin = struct.unpack_from('<H', data, 4)[0]
    ymin = struct.unpack_from('<H', data, 6)[0]
    xmax = struct.unpack_from('<H', data, 8)[0]
    ymax = struct.unpack_from('<H', data, 10)[0]
    width = xmax - xmin + 1
    height = ymax - ymin + 1
    if width <= 0 or height <= 0 or width * height > 1 << 22:
        return None

    pixels = bytearray()
    i = 128
    need = width * height
    while i < length and len(pixels) < need:
        b = data[i]
        i += 1
        if (b & 0xC0) == 0xC0:
            count = b & 0x3F
            if i >= length:
                break
            pixels.extend([data[i]] * count)
            i += 1
        else:
            pixels.append(b)
    if len(pixels) < need:
        return None

    rgba = bytearray(need * 4)
    for p in range(need):
        idx = pixels[p]
        base = idx * 3
        rgba[p * 4 + 0] = palette[base + 0]
        rgba[p * 4 + 1] = palette[base + 1]
        rgba[p * 4 + 2] = palette[base + 2]
        rgba[p * 4 + 3] = 0 if idx == TRANSPARENT_INDEX else 255
    return bytes(rgba), width, height


def _get_pic(name):
    """Return (texture, width, height) for a pics/<name>, cached."""
    if name in _textures:
        return _textures[name]
    from . import gl_context
    ctx = gl_context.ctx
    result = None
    try:
        decoded = _decode_pcx(name)
        if decoded and ctx:
            rgba, w, h = decoded
            tex = ctx.texture((w, h), 4, rgba)
            tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
            tex.repeat_x = False
            tex.repeat_y = False
            result = (tex, w, h)
    except Exception as e:
        print(f"gl_hud._get_pic({name}) error: {e}")
    _textures[name] = result
    return result


def _screen_size():
    from . import glw_imp
    w = glw_imp.width if glw_imp.width > 0 else 800
    h = glw_imp.height if glw_imp.height > 0 else 600
    return w, h


def _draw_quad(x, y, w, h, texture=None, color=(1.0, 1.0, 1.0, 1.0)):
    """Draw one screen-space quad; textured if a texture is given."""
    prog = _get_program()
    from . import gl_context
    if not prog or not gl_context.ctx:
        return
    sw, sh = _screen_size()
    prog['u_screen'].value = (float(sw), float(sh))
    prog['u_color'].value = tuple(float(c) for c in color)
    prog['u_textured'].value = 1 if texture is not None else 0
    if texture is not None:
        prog['u_texture'].value = 0
        texture.use(location=0)

    x0, y0, x1, y1 = float(x), float(y), float(x + w), float(y + h)
    verts = np.array([
        x0, y0, 0.0, 0.0,
        x1, y0, 1.0, 0.0,
        x1, y1, 1.0, 1.0,
        x0, y0, 0.0, 0.0,
        x1, y1, 1.0, 1.0,
        x0, y1, 0.0, 1.0,
    ], dtype=np.float32)
    _vbo.write(verts.tobytes())
    _vao.render(moderngl.TRIANGLES)


def _draw_pic(x, y, name, color=(1.0, 1.0, 1.0, 1.0)):
    """Draw a named pic at its native size; returns its width (0 if missing)."""
    pic = _get_pic(name)
    if not pic:
        return 0
    tex, w, h = pic
    _draw_quad(x, y, w, h, texture=tex, color=color)
    return w


def _draw_field(x, y, value, digits=3):
    """Draw an integer right-justified in a field using the big HUD numbers.

    x is the right edge of the field. Matches Quake 2's SCR_DrawField layout."""
    s = str(int(value))
    if len(s) > digits:
        s = s[-digits:]  # never overflow the field width
    zero = _get_pic('num_0')
    cw = zero[1] if zero else 16
    draw_x = x - len(s) * cw
    for ch in s:
        if ch == '-':
            _draw_pic(draw_x, y, 'num_minus')
        else:
            _draw_pic(draw_x, y, f'num_{ch}')
        draw_x += cw


def _player_health():
    try:
        from quake2 import cl_monsters
        return int(cl_monsters.PlayerState.health)
    except Exception:
        return 100


def _current_weapon_name():
    try:
        from quake2 import cl_weapon
        return cl_weapon.WEAPONS[cl_weapon._WeaponState.current]['name']
    except Exception:
        return None


def SCR_DrawHUD():
    """Draw the in-game HUD: crosshair, health, and current weapon."""
    from . import gl_context
    ctx = gl_context.ctx
    if not ctx or not _get_program():
        return

    ctx.disable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
    ctx.enable(moderngl.BLEND)
    ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

    try:
        sw, sh = _screen_size()

        # Crosshair, centered.
        cross = _get_pic('ch1')
        if cross:
            _, cw, chh = cross
            _draw_pic((sw - cw) // 2, (sh - chh) // 2, 'ch1')

        num = _get_pic('num_0')
        num_h = num[2] if num else 24
        row_y = sh - num_h - 12

        # Health: icon + number, bottom-left.
        icon_w = _draw_pic(16, row_y, 'i_health')
        _draw_field(16 + icon_w + 4 + 3 * (num[1] if num else 16), row_y,
                    _player_health(), digits=3)

        # Current weapon icon, bottom-right.
        wname = _current_weapon_name()
        icon = _WEAPON_ICONS.get(wname)
        if icon:
            pic = _get_pic(icon)
            if pic:
                _, iw, ih = pic
                _draw_pic(sw - iw - 16, sh - ih - 12, icon)
    except Exception as e:
        print(f"SCR_DrawHUD error: {e}")
    finally:
        ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)


def free_all():
    """Release GL resources (e.g. on shutdown)."""
    for entry in _textures.values():
        if entry:
            entry[0].release()
    _textures.clear()
