"""
gl_draw.py - 2D drawing system for HUD, menus, and text
Handles text rendering, score display, and 2D screen elements
"""

import struct
from OpenGL.GL import *
from shared.QEnums import imagetype_t
from shared.QConstants import MAX_QPATH
from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), [])

# ===== Global State =====

conchars_pic = None
console_pic = None
char_width = 8
char_height = 8
screen_width = 800
screen_height = 600


# ===== Initialization =====

def Draw_InitLocal():
    """Initialize 2D drawing system"""
    try:
        from . import gl_image

        global conchars_pic, console_pic

        # Load console character set
        conchars_pic = gl_image.GL_FindImage("pics/conchars", imagetype_t.it_pic)
        if not conchars_pic:
            print("Draw_InitLocal: Failed to load conchars")

        # Load console background
        console_pic = gl_image.GL_FindImage("pics/console", imagetype_t.it_pic)

    except Exception as e:
        print(f"Draw_InitLocal error: {e}")


# ===== Screen Setup =====

def _setup_2d_mode(width=None, height=None):
    """Setup 2D orthographic projection"""
    try:
        global screen_width, screen_height

        if width is None:
            width = screen_width
        if height is None:
            height = screen_height

        screen_width = width
        screen_height = height

        # Save state
        glPushAttrib(GL_ALL_ATTRIB_BITS)

        # Setup orthographic projection
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, width, height, 0, -1, 1)

        # Setup modelview
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        # Setup for 2D rendering
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_CULL_FACE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    except Exception as e:
        print(f"_setup_2d_mode error: {e}")


def _restore_3d_mode():
    """Restore 3D projection"""
    try:
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()

        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        glPopAttrib()

    except Exception as e:
        print(f"_restore_3d_mode error: {e}")


# ===== Text Drawing =====

def Draw_Char(x, y, num):
    """Draw single character at screen position"""
    try:
        global conchars_pic, char_width, char_height

        if not conchars_pic:
            return

        num = int(num) & 255

        # Character grid is 16x16 in conchars.pcx
        cx = (num % 16) * char_width
        cy = (num // 16) * char_height

        # Bind character texture
        from . import gl_image
        gl_image.GL_BindTexture(conchars_pic)

        # Draw quad
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)

        # Calculate texture coordinates
        tex_x = cx / 128.0  # Assuming 128x128 texture
        tex_y = cy / 128.0
        tex_w = char_width / 128.0
        tex_h = char_height / 128.0

        # Draw character quad
        glTexCoord2f(tex_x, tex_y)
        glVertex2f(x, y)

        glTexCoord2f(tex_x + tex_w, tex_y)
        glVertex2f(x + char_width, y)

        glTexCoord2f(tex_x + tex_w, tex_y + tex_h)
        glVertex2f(x + char_width, y + char_height)

        glTexCoord2f(tex_x, tex_y + tex_h)
        glVertex2f(x, y + char_height)

        glEnd()

    except Exception as e:
        print(f"Draw_Char error: {e}")


def Draw_String(x, y, text, color=None):
    """Draw text string"""
    try:
        if not text:
            return

        _setup_2d_mode()

        if color:
            glColor4f(color[0], color[1], color[2], 1.0)
        else:
            glColor4f(1.0, 1.0, 1.0, 1.0)

        glEnable(GL_TEXTURE_2D)

        current_x = x
        for char in text:
            char_code = ord(char)
            Draw_Char(current_x, y, char_code)
            current_x += char_width

        glDisable(GL_TEXTURE_2D)

        _restore_3d_mode()

    except Exception as e:
        print(f"Draw_String error: {e}")


# ===== Picture Drawing =====

def Draw_Pic(x, y, pic):
    """Draw picture at screen position"""
    try:
        _setup_2d_mode()

        from . import gl_image

        if isinstance(pic, dict):
            pic_id = pic.get('id', pic)
        else:
            pic_id = pic

        gl_image.GL_BindTexture(pic_id)

        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)

        # Default pic size is 64x64 (can be overridden)
        pic_width = 64
        pic_height = 64

        glTexCoord2f(0, 0)
        glVertex2f(x, y)

        glTexCoord2f(1, 0)
        glVertex2f(x + pic_width, y)

        glTexCoord2f(1, 1)
        glVertex2f(x + pic_width, y + pic_height)

        glTexCoord2f(0, 1)
        glVertex2f(x, y + pic_height)

        glEnd()

        _restore_3d_mode()

    except Exception as e:
        print(f"Draw_Pic error: {e}")


def Draw_StretchPic(x, y, w, h, pic):
    """Draw picture stretched to size"""
    try:
        _setup_2d_mode()

        from . import gl_image

        if isinstance(pic, dict):
            pic_id = pic.get('id', pic)
        else:
            pic_id = pic

        gl_image.GL_BindTexture(pic_id)

        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)

        glTexCoord2f(0, 0)
        glVertex2f(x, y)

        glTexCoord2f(1, 0)
        glVertex2f(x + w, y)

        glTexCoord2f(1, 1)
        glVertex2f(x + w, y + h)

        glTexCoord2f(0, 1)
        glVertex2f(x, y + h)

        glEnd()

        _restore_3d_mode()

    except Exception as e:
        print(f"Draw_StretchPic error: {e}")


def Draw_GetPicSize(w, h, pic):
    """Get picture dimensions"""
    try:
        # For now, default to 64x64
        if hasattr(w, 'value'):
            w.value = 64
        if hasattr(h, 'value'):
            h.value = 64

        return (64, 64)

    except Exception as e:
        print(f"Draw_GetPicSize error: {e}")
        return (64, 64)


def Draw_FindPic(name):
    """Find and load picture by name"""
    try:
        from . import gl_image

        if not name:
            return None

        # Build full path
        if not name.startswith('/') and not name.startswith('\\'):
            full_name = f"pics/{name}"
        else:
            full_name = name

        # Add .pcx extension if needed
        if not full_name.endswith('.pcx'):
            full_name = full_name + '.pcx'

        # Load image
        pic_id = gl_image.GL_FindImage(full_name, imagetype_t.it_pic)

        return pic_id

    except Exception as e:
        print(f"Draw_FindPic error: {e}")
        return None


# ===== Primitives =====

def Draw_Fill(x, y, w, h, color):
    """Draw solid rectangle"""
    try:
        _setup_2d_mode()

        # Parse color (can be int or list)
        if isinstance(color, int):
            r = ((color >> 16) & 0xFF) / 255.0
            g = ((color >> 8) & 0xFF) / 255.0
            b = (color & 0xFF) / 255.0
            a = 1.0
        elif isinstance(color, (list, tuple)):
            r = color[0] if len(color) > 0 else 1.0
            g = color[1] if len(color) > 1 else 1.0
            b = color[2] if len(color) > 2 else 1.0
            a = color[3] if len(color) > 3 else 1.0
        else:
            r = g = b = 1.0
            a = 1.0

        glColor4f(r, g, b, a)
        glDisable(GL_TEXTURE_2D)

        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()

        _restore_3d_mode()

    except Exception as e:
        print(f"Draw_Fill error: {e}")


def Draw_TileClear(x, y, w, h, pic):
    """Draw tiled picture"""
    try:
        _setup_2d_mode()

        from . import gl_image

        if isinstance(pic, dict):
            pic_id = pic.get('id', pic)
        else:
            pic_id = pic

        gl_image.GL_BindTexture(pic_id)

        glColor4f(1.0, 1.0, 1.0, 1.0)

        # Tile picture across area
        tile_size = 64
        for ty in range(y, y + h, tile_size):
            for tx in range(x, x + w, tile_size):
                tile_w = min(tile_size, x + w - tx)
                tile_h = min(tile_size, y + h - ty)

                glBegin(GL_QUADS)
                glTexCoord2f(0, 0)
                glVertex2f(tx, ty)

                glTexCoord2f(tile_w / tile_size, 0)
                glVertex2f(tx + tile_w, ty)

                glTexCoord2f(tile_w / tile_size, tile_h / tile_size)
                glVertex2f(tx + tile_w, ty + tile_h)

                glTexCoord2f(0, tile_h / tile_size)
                glVertex2f(tx, ty + tile_h)
                glEnd()

        _restore_3d_mode()

    except Exception as e:
        print(f"Draw_TileClear error: {e}")


def Draw_FadeScreen():
    """Draw fade effect (death/pickup flash)"""
    try:
        _setup_2d_mode()

        glColor4f(0.0, 0.0, 0.0, 0.3)
        glDisable(GL_TEXTURE_2D)

        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(screen_width, 0)
        glVertex2f(screen_width, screen_height)
        glVertex2f(0, screen_height)
        glEnd()

        _restore_3d_mode()

    except Exception as e:
        print(f"Draw_FadeScreen error: {e}")


def Draw_StretchRaw(x, y, w, h, cols, rows, data):
    """Draw raw pixel data"""
    try:
        _setup_2d_mode()

        # Create temporary texture
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)

        # Convert data to proper format
        if isinstance(data, bytes):
            pixel_data = data
        else:
            pixel_data = bytes(data)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB,
                     cols, rows, 0,
                     GL_RGB, GL_UNSIGNED_BYTE,
                     pixel_data)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        # Draw quad
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)

        glTexCoord2f(0, 0)
        glVertex2f(x, y)

        glTexCoord2f(1, 0)
        glVertex2f(x + w, y)

        glTexCoord2f(1, 1)
        glVertex2f(x + w, y + h)

        glTexCoord2f(0, 1)
        glVertex2f(x, y + h)

        glEnd()

        # Clean up
        glDeleteTextures([tex_id])

        _restore_3d_mode()

    except Exception as e:
        print(f"Draw_StretchRaw error: {e}")


# ===== HUD Drawing =====

def SCR_DrawHUD(player_state):
    """Draw main HUD (health, ammo, score)"""
    try:
        if not player_state:
            return

        _setup_2d_mode()

        # Get player stats
        health = int(player_state.get('health', 100)) if isinstance(player_state, dict) else 100
        armor = int(player_state.get('armor', 0)) if isinstance(player_state, dict) else 0
        ammo = int(player_state.get('ammo', 30)) if isinstance(player_state, dict) else 30
        score = int(player_state.get('score', 0)) if isinstance(player_state, dict) else 0

        # Draw background bar
        Draw_Fill(0, screen_height - 32, screen_width, 32, [0.1, 0.1, 0.1])

        # Draw health
        health_color = _get_health_color(health)
        Draw_String(10, screen_height - 24, f"Health: {health}", health_color)

        # Draw armor
        armor_color = [0.0, 0.5, 1.0]
        Draw_String(150, screen_height - 24, f"Armor: {armor}", armor_color)

        # Draw ammo
        ammo_color = [1.0, 1.0, 0.0]
        Draw_String(290, screen_height - 24, f"Ammo: {ammo}", ammo_color)

        # Draw score
        score_color = [0.5, 1.0, 0.5]
        Draw_String(screen_width - 180, screen_height - 24, f"Score: {score}", score_color)

        _restore_3d_mode()

    except Exception as e:
        print(f"SCR_DrawHUD error: {e}")


def SCR_DrawCenterString(y, text):
    """Draw centered text string"""
    try:
        _setup_2d_mode()

        # Calculate center position
        text_width = len(text) * char_width
        x = (screen_width - text_width) // 2

        Draw_String(x, y, text, [1.0, 1.0, 1.0])

        _restore_3d_mode()

    except Exception as e:
        print(f"SCR_DrawCenterString error: {e}")


def _get_health_color(health):
    """Get color based on health value"""
    if health > 75:
        return [0.0, 1.0, 0.0]  # Green
    elif health > 50:
        return [1.0, 1.0, 0.0]  # Yellow
    elif health > 25:
        return [1.0, 0.5, 0.0]  # Orange
    else:
        return [1.0, 0.0, 0.0]  # Red


def DrawCrosshair():
    """Draw aiming crosshair"""
    try:
        _setup_2d_mode()

        center_x = screen_width / 2
        center_y = screen_height / 2
        size = 8

        glColor4f(1.0, 1.0, 1.0, 0.7)
        glDisable(GL_TEXTURE_2D)

        # Draw crosshair
        glBegin(GL_LINES)

        # Horizontal
        glVertex2f(center_x - size, center_y)
        glVertex2f(center_x + size, center_y)

        # Vertical
        glVertex2f(center_x, center_y - size)
        glVertex2f(center_x, center_y + size)

        glEnd()

        _restore_3d_mode()

    except Exception as e:
        print(f"DrawCrosshair error: {e}")


def DrawPause():
    """Draw pause screen"""
    try:
        _setup_2d_mode()

        # Draw fade
        Draw_Fill(0, 0, screen_width, screen_height, [0.0, 0.0, 0.0, 0.5])

        # Draw "PAUSED" text
        SCR_DrawCenterString(screen_height // 2 - 20, "PAUSED")

        _restore_3d_mode()

    except Exception as e:
        print(f"DrawPause error: {e}")


def DrawGameOver():
    """Draw game over screen"""
    try:
        _setup_2d_mode()

        # Draw fade
        Draw_Fill(0, 0, screen_width, screen_height, [0.0, 0.0, 0.0, 0.7])

        # Draw "GAME OVER" text
        SCR_DrawCenterString(screen_height // 2 - 20, "GAME OVER")

        _restore_3d_mode()

    except Exception as e:
        print(f"DrawGameOver error: {e}")
