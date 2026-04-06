"""
gl_image.py - OpenGL texture loading
Handles WAL, PCX, and TGA image formats
"""

import struct
import numpy as np
from OpenGL.GL import *
from wrapper_qpy.decorators import TODO
from wrapper_qpy.custom_classes import Mutable
from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), ["Com_Printf", "Com_Error"])

# ===== Texture Cache =====

texture_cache = {}
textures = []
palette_data = None  # Global palette (256 * 3 bytes RGB)

# ===== WAL Format =====

class WalHeader:
    def __init__(self):
        self.name = ""
        self.width = 0
        self.height = 0
        self.offset = [0, 0, 0, 0]
        self.next_name = ""
        self.flags = 0
        self.contents = 0
        self.value = 0


def LoadWal(filename):
    """Load WAL texture file"""
    try:
        import sys
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from quake2.files import FS_LoadFile, fs_searchpaths
        global palette_data

        if palette_data is None:
            return None

        data, length = FS_LoadFile(filename)
        if data is None:
            return None

        # Parse WAL header (32 + 4*4 + 32 + 4 + 4 + 4 = 84 bytes)
        if length < 84:
            return None

        header = WalHeader()
        header.name = data[0:32].decode('latin-1', errors='ignore').rstrip('\x00')
        header.width = struct.unpack_from('<I', data, 32)[0]
        header.height = struct.unpack_from('<I', data, 36)[0]

        for i in range(4):
            header.offset[i] = struct.unpack_from('<I', data, 40 + i*4)[0]

        header.next_name = data[56:88].decode('latin-1', errors='ignore').rstrip('\x00')
        header.flags = struct.unpack_from('<I', data, 88)[0]
        header.contents = struct.unpack_from('<I', data, 92)[0]
        header.value = struct.unpack_from('<I', data, 96)[0]

        # Load base texture (first mipmap)
        if header.offset[0] + header.width * header.height > length:
            return None

        pixel_data = data[header.offset[0]:header.offset[0] + header.width * header.height]

        # Convert palette indices to RGBA
        rgba_data = _palette_to_rgba(pixel_data)

        # Create OpenGL texture
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)

        # Upload as RGBA
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA,
                     header.width, header.height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE,
                     rgba_data)

        # Set texture parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

        return tex_id

    except Exception as e:
        print(f"LoadWal error: {e}")
        return None


def _palette_to_rgba(indexed_data):
    """Convert palette-indexed bytes to RGBA using global palette"""
    global palette_data
    if palette_data is None:
        return None

    # Create RGBA buffer
    rgba = bytearray(len(indexed_data) * 4)

    for i, idx in enumerate(indexed_data):
        pal_idx = min(int(idx), 255) * 3
        rgba[i*4 + 0] = palette_data[pal_idx + 0]
        rgba[i*4 + 1] = palette_data[pal_idx + 1]
        rgba[i*4 + 2] = palette_data[pal_idx + 2]
        rgba[i*4 + 3] = 255

    return bytes(rgba)


# ===== PCX Format =====

class PcxHeader:
    def __init__(self):
        self.manufacturer = 0
        self.version = 0
        self.encoding = 0
        self.bits_per_pixel = 0
        self.xmin = 0
        self.ymin = 0
        self.xmax = 0
        self.ymax = 0
        self.hres = 0
        self.vres = 0
        self.width = 0
        self.height = 0


def LoadPcx(filename):
    """Load PCX image file"""
    try:
        import sys
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from quake2.files import FS_LoadFile
        global palette_data

        data, length = FS_LoadFile(filename)
        if data is None or length < 128:
            return None

        header = PcxHeader()
        header.manufacturer = data[0]
        header.version = data[1]
        header.encoding = data[2]
        header.bits_per_pixel = data[3]
        header.xmin = struct.unpack_from('<H', data, 4)[0]
        header.ymin = struct.unpack_from('<H', data, 6)[0]
        header.xmax = struct.unpack_from('<H', data, 8)[0]
        header.ymax = struct.unpack_from('<H', data, 10)[0]
        header.hres = struct.unpack_from('<H', data, 12)[0]
        header.vres = struct.unpack_from('<H', data, 14)[0]

        header.width = header.xmax - header.xmin + 1
        header.height = header.ymax - header.ymin + 1

        if header.manufacturer != 10 or header.encoding != 1:
            return None

        # Decompress PCX data
        pixel_data = bytearray()
        i = 128
        while i < length and len(pixel_data) < header.width * header.height:
            b = data[i]
            i += 1

            if (b & 0xC0) == 0xC0:
                # RLE run
                count = b & 0x3F
                if i >= length:
                    break
                value = data[i]
                i += 1
                pixel_data.extend([value] * count)
            else:
                # Single pixel
                pixel_data.append(b)

        if len(pixel_data) < header.width * header.height:
            return None

        # Use palette conversion if available (for colormap), else greyscale
        if palette_data is not None:
            rgba_data = _palette_to_rgba(bytes(pixel_data[:header.width * header.height]))
            upload_format = GL_RGBA
            upload_type = GL_RGBA
        else:
            rgba_data = bytes(pixel_data[:header.width * header.height])
            upload_format = GL_LUMINANCE
            upload_type = GL_LUMINANCE

        # Create OpenGL texture
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)

        glTexImage2D(GL_TEXTURE_2D, 0, upload_format,
                     header.width, header.height, 0,
                     upload_type, GL_UNSIGNED_BYTE,
                     rgba_data)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

        return tex_id

    except Exception as e:
        print(f"LoadPcx error: {e}")
        return None


# ===== Texture Management =====

def GL_LoadImage(name):
    """Load image by name, checking cache first"""
    # Check cache
    if name in texture_cache:
        return texture_cache[name]

    tex_id = None

    # Try loading as WAL first (Quake format)
    if name.endswith('.wal') or '/' not in name:
        wal_name = name if name.endswith('.wal') else f"{name}.wal"
        tex_id = LoadWal(wal_name)

    # Try PCX if WAL failed
    if tex_id is None:
        pcx_name = name if name.endswith('.pcx') else f"{name}.pcx"
        tex_id = LoadPcx(pcx_name)

    # Try TGA if others failed
    if tex_id is None:
        tga_name = name if name.endswith('.tga') else f"{name}.tga"
        # TODO: Implement TGA loading
        pass

    if tex_id is not None:
        texture_cache[name] = tex_id
        textures.append(tex_id)

    return tex_id


def GL_BindTexture(tex_id):
    """Bind texture for rendering"""
    if tex_id:
        glBindTexture(GL_TEXTURE_2D, tex_id)


def GL_Bind(texnum):
    """Bind texture by number (Quake compatibility)"""
    if texnum < len(textures):
        GL_BindTexture(textures[texnum])


# ===== Colormap/Palette =====

def GL_LoadPalette():
    """Load Quake palette from colormap"""
    try:
        import sys
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from quake2.files import FS_LoadFile
        global palette_data

        data, length = FS_LoadFile("pics/colormap.pcx")
        if data is None or length < 768 + 128:
            return None

        # Palette is last 768 bytes (256 colors * 3 bytes RGB)
        palette = data[length - 768:length]
        palette_data = palette

        return len(palette) == 768

    except Exception as e:
        print(f"GL_LoadPalette error: {e}")
        return None




def GL_Upload32(data, width, height, mipmap):
    """Upload 32-bit RGBA texture data"""
    try:
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA,
                     width, height, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE,
                     data)

        if mipmap:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
            glGenerateMipmap(GL_TEXTURE_2D)
        else:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        return tex_id
    except Exception as e:
        print(f"GL_Upload32 error: {e}")
        return None


def GL_Upload8(data, width, height, mipmap, is_sky):
    """Upload 8-bit paletted texture data"""
    try:
        global palette_data
        if palette_data is None:
            return None

        # Convert palette indices to RGBA
        rgba_data = _palette_to_rgba(data)
        if rgba_data is None:
            return None

        return GL_Upload32(rgba_data, width, height, mipmap)

    except Exception as e:
        print(f"GL_Upload8 error: {e}")
        return None


def GL_LoadPic(name, pic, width, height, _type, bits):
    """Load and cache a picture"""
    try:
        if name in texture_cache:
            return texture_cache[name]

        # Upload the image data
        if bits == 32:
            tex_id = GL_Upload32(pic, width, height, False)
        elif bits == 8:
            tex_id = GL_Upload8(pic, width, height, False, False)
        else:
            return None

        if tex_id is not None:
            texture_cache[name] = tex_id
            textures.append(tex_id)

        return tex_id

    except Exception as e:
        print(f"GL_LoadPic error: {e}")
        return None


def GL_LoadWal(name):
    """Load WAL format image"""
    return LoadWal(name)


def GL_FindImage(name, _type):
    """Find or load an image by name"""
    try:
        if name in texture_cache:
            return texture_cache[name]

        if not name:
            return None

        # Try different extensions
        tex_id = None

        if name.endswith('.wal'):
            tex_id = LoadWal(name)
        elif name.endswith('.pcx'):
            tex_id = LoadPcx(name)
        else:
            # Try WAL first, with and without "textures/" prefix
            tex_id = LoadWal(f"{name}.wal")
            if tex_id is None and not name.startswith("textures/"):
                tex_id = LoadWal(f"textures/{name}.wal")
            if tex_id is None:
                tex_id = LoadPcx(f"{name}.pcx")
            if tex_id is None and not name.startswith("textures/"):
                tex_id = LoadPcx(f"textures/{name}.pcx")

        if tex_id is not None:
            texture_cache[name] = tex_id
            textures.append(tex_id)
            return tex_id

        return None

    except Exception as e:
        print(f"GL_FindImage error: {e}")
        return None


def R_RegisterSkin(name):
    """Register a skin texture"""
    return GL_FindImage(name, 1)  # 1 = skin type


def GL_FreeUnusedImages():
    """Free images not used recently"""
    pass


def Draw_GetPalette():
    """Get the current palette"""
    global palette_data
    return palette_data


def GL_InitImages():
    """Initialize texture system"""
    global texture_cache, textures, palette_data
    texture_cache = {}
    textures = []

    # Load palette
    GL_LoadPalette()

    # Load built-in images
    GL_FindImage("pics/conchars", 1)  # Console characters
    GL_FindImage("pics/console", 1)    # Console background


def GL_ShutdownImages():
    """Shutdown texture system"""
    global texture_cache, textures, palette_data

    # Delete all textures
    for tex_id in textures:
        try:
            glDeleteTextures([tex_id])
        except:
            pass

    texture_cache = {}
    textures = []
    palette_data = None
