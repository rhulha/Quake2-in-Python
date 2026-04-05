"""
gl_image.py - OpenGL texture loading
Handles WAL, PCX, and TGA image formats
"""

import struct
from OpenGL.GL import *
from wrapper_qpy.decorators import TODO
from wrapper_qpy.custom_classes import Mutable
from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), ["Com_Printf", "Com_Error"])

# ===== Texture Cache =====

texture_cache = {}
textures = []

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
        from ..quake2.files import FS_LoadFile

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

        # Create OpenGL texture
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)

        # Upload as indexed color (8-bit paletted)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE,
                     header.width, header.height, 0,
                     GL_LUMINANCE, GL_UNSIGNED_BYTE,
                     pixel_data)

        # Set texture parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)

        # Generate mipmaps
        glGenerateMipmap(GL_TEXTURE_2D)

        return tex_id

    except Exception as e:
        print(f"LoadWal error: {e}")
        return None


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
        from ..quake2.files import FS_LoadFile

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

        # Create OpenGL texture
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE,
                     header.width, header.height, 0,
                     GL_LUMINANCE, GL_UNSIGNED_BYTE,
                     bytes(pixel_data[:header.width * header.height]))

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
        from ..quake2.files import FS_LoadFile

        data, length = FS_LoadFile("pics/colormap.pcx")
        if data is None or length < 768 + 128:
            return None

        # Palette is last 768 bytes (256 colors * 3 bytes RGB)
        palette = data[length - 768:length]

        # Convert to OpenGL palette texture
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_1D, tex_id)

        glTexImage1D(GL_TEXTURE_1D, 0, GL_RGB,
                     256, 0,
                     GL_RGB, GL_UNSIGNED_BYTE,
                     palette)

        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_1D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        return tex_id

    except:
        return None


@TODO
def GL_SetTexturePalette(palette):
    pass


@TODO
def GL_EnableMultitexture(enable):
    pass


@TODO
def GL_SelectTexture(texture):
    pass


@TODO
def GL_TexEnv(mode):
    pass


@TODO
def GL_Bind(texnum):
    pass


@TODO
def GL_MBind(target, texnum):
    pass


@TODO
def GL_TextureMode(string):
    pass


@TODO
def GL_TextureAlphaMode(string):
    pass


@TODO
def GL_TextureSolidMode(string):
    pass


@TODO
def GL_ImageList_f():
    pass


@TODO
def Scrap_AllocBlock(w, h, x: Mutable, y: Mutable):
    pass


@TODO
def Scrap_Upload():
    pass


@TODO
def LoadPCX(filename, pic, palette, width: Mutable, height: Mutable):
    pass


@TODO
def LoadTGA(name, pic, width: Mutable, height: Mutable):
    pass


@TODO
def R_FloodFillSkin(skin, skinwidth, skinheight):
    pass


@TODO
def GL_ResampleTexture(_in, inwidth, inheight, out, outwidth, outheight):
    pass


@TODO
def GL_LightScaleTexture(_in, inwidth, inheight, only_game):
    pass


@TODO
def GL_MipMap(_in, width, height):
    pass


@TODO
def GL_BuildPalettedTexture(paleetted_texture, scaled, scaled_width, scald_height):
    pass


@TODO
def GL_Upload32(data, width, height, mipmap):
    pass


@TODO
def GL_Upload8(data, width, height, mipmap, is_sky):
    pass


@TODO
def GL_LoadPic(name, pic, width, height, _type, bits):
    pass


@TODO
def GL_LoadWal(name):
    pass


@TODO
def GL_FindImage(name, _type):
    pass


@TODO
def R_RegisterSkin(name):
    pass


@TODO
def GL_FreeUnusedImages():
    pass


@TODO
def Draw_GetPalette():
    pass


@TODO
def GL_InitImages():
    pass


@TODO
def GL_ShutdownImages():
    pass
