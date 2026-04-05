import struct
import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import moderngl

# Constants
MAX_GLTEXTURES = 1024
TEXNUM_LIGHTMAPS = 1024
TEXNUM_SCRAPS = 1152
TEXNUM_IMAGES = 1153

@dataclass
class Image:
    """Texture object metadata and GL binding."""
    name: str
    type: str  # 'skin', 'sprite', 'wall', 'pic', 'sky'
    width: int
    height: int
    upload_width: int
    upload_height: int
    registration_sequence: int = 0
    texnum: int = 0  # GL texture binding
    sl: float = 0.0  # UV coords in atlas
    tl: float = 0.0
    sh: float = 1.0
    th: float = 1.0
    scrap: bool = False
    has_alpha: bool = False
    paletted: bool = False
    texture: Optional[moderngl.Texture] = None

class ImageManager:
    """Texture cache and image loading system."""

    def __init__(self, ctx: moderngl.Context):
        self.ctx = ctx
        self.gltextures: Dict[str, Image] = {}
        self.registration_sequence = 1
        self.d_8to24table = np.zeros(256, dtype=np.uint32)
        self.scrap_dirty = False

    def load_pcx(self, filepath: str) -> Tuple[np.ndarray, np.ndarray, int, int]:
        """Load PCX file (8-bit paletted). Returns (pixels, palette, width, height)."""
        with open(filepath, 'rb') as f:
            data = f.read()

        if len(data) < 128:
            raise ValueError("PCX file too short")

        # Parse header
        header = struct.unpack('<BBBBHHHHHHBBBB48s', data[:68])
        manufacturer, version, encoding, bits_per_pixel = header[0:4]
        xmin, ymin, xmax, ymax = header[4:8]
        width = xmax - xmin + 1
        height = ymax - ymin + 1
        palette_type = header[12]

        if manufacturer != 10 or version != 5 or encoding != 1:
            raise ValueError("Invalid PCX file")

        # Decode RLE image data
        pixels = bytearray()
        pos = 128
        while len(pixels) < width * height and pos < len(data):
            byte = data[pos]
            pos += 1
            if (byte & 0xC0) == 0xC0:
                count = byte & 0x3F
                byte = data[pos]
                pos += 1
                pixels.extend([byte] * count)
            else:
                pixels.append(byte)

        # Extract palette (last 768 bytes)
        palette = np.zeros(256, dtype=np.uint32)
        if len(data) >= 768:
            pal_data = data[-768:]
            for i in range(256):
                r = pal_data[i*3]
                g = pal_data[i*3 + 1]
                b = pal_data[i*3 + 2]
                palette[i] = (255 << 24) | (b << 16) | (g << 8) | r

        return np.array(pixels, dtype=np.uint8).reshape(height, width), palette, width, height

    def load_tga(self, filepath: str) -> Tuple[np.ndarray, int, int]:
        """Load TGA file (24-bit or 32-bit RGB/RGBA). Returns (pixels_rgba, width, height)."""
        with open(filepath, 'rb') as f:
            data = f.read()

        if len(data) < 18:
            raise ValueError("TGA file too short")

        # Parse header
        id_len, colormap_type, image_type = struct.unpack('<BBB', data[0:3])
        width, height = struct.unpack('<HH', data[12:16])
        bits_per_pixel = data[16]
        img_descriptor = data[17]

        if image_type not in (2, 10):
            raise ValueError("Only uncompressed (2) and RLE (10) TGA supported")

        if bits_per_pixel not in (24, 32):
            raise ValueError("Only 24-bit and 32-bit TGA supported")

        pixel_size = bits_per_pixel // 8
        expected_size = width * height * pixel_size
        image_data = data[18 + id_len:]

        if image_type == 2:
            # Uncompressed
            pixels = np.frombuffer(image_data[:expected_size], dtype=np.uint8)
        else:
            # RLE compressed
            pixels = bytearray()
            pos = 0
            while len(pixels) < expected_size and pos < len(image_data):
                byte = image_data[pos]
                pos += 1
                if byte & 0x80:
                    count = (byte & 0x7F) + 1
                    chunk = image_data[pos:pos + pixel_size]
                    pos += pixel_size
                    for _ in range(count):
                        pixels.extend(chunk)
                else:
                    count = byte + 1
                    chunk_size = count * pixel_size
                    pixels.extend(image_data[pos:pos + chunk_size])
                    pos += chunk_size
            pixels = np.array(pixels, dtype=np.uint8)

        # Reshape and convert BGR(A) to RGBA
        pixels = pixels.reshape(height, width, pixel_size)
        if pixel_size == 3:
            # BGR to RGB, add alpha
            rgba = np.zeros((height, width, 4), dtype=np.uint8)
            rgba[..., 0] = pixels[..., 2]
            rgba[..., 1] = pixels[..., 1]
            rgba[..., 2] = pixels[..., 0]
            rgba[..., 3] = 255
            pixels = rgba
        else:
            # BGRA to RGBA
            pixels_rgba = np.zeros_like(pixels)
            pixels_rgba[..., 0] = pixels[..., 2]
            pixels_rgba[..., 1] = pixels[..., 1]
            pixels_rgba[..., 2] = pixels[..., 0]
            pixels_rgba[..., 3] = pixels[..., 3]
            pixels = pixels_rgba

        return pixels, width, height

    def load_wal(self, filepath: str, palette: np.ndarray) -> Tuple[np.ndarray, int, int]:
        """Load WAL file (Quake 2 miptex). Returns (pixels, width, height)."""
        with open(filepath, 'rb') as f:
            data = f.read()

        if len(data) < 40:
            raise ValueError("WAL file too short")

        # Parse header: name(32), width, height, offsets(4*4)
        name_bytes = data[0:32]
        width, height = struct.unpack('<II', data[32:40])
        offsets = struct.unpack('<IIII', data[40:56])

        if len(data) < offsets[0] + width * height:
            raise ValueError("WAL file incomplete")

        # Load base (first) mip level
        mip_data = data[offsets[0]:offsets[0] + width * height]
        pixels = np.array(list(mip_data), dtype=np.uint8).reshape(height, width)

        return pixels, width, height

    def upload_8bit(self, pixels: np.ndarray, palette: np.ndarray, width: int, height: int) -> moderngl.Texture:
        """Convert 8-bit paletted to RGBA and upload to GPU."""
        rgba = np.zeros((height, width, 4), dtype=np.uint8)
        for i in range(height):
            for j in range(width):
                pal_idx = pixels[i, j]
                color = palette[pal_idx]
                rgba[i, j, 0] = (color >> 0) & 0xFF
                rgba[i, j, 1] = (color >> 8) & 0xFF
                rgba[i, j, 2] = (color >> 16) & 0xFF
                rgba[i, j, 3] = 255

        return self.ctx.texture((width, height), 4, rgba.astype(np.uint8))

    def upload_32bit(self, pixels: np.ndarray, width: int, height: int) -> moderngl.Texture:
        """Upload 32-bit RGBA directly to GPU."""
        return self.ctx.texture((width, height), 4, pixels.astype(np.uint8))

    def find_image(self, name: str, image_type: str = 'wall') -> Image:
        """Load or retrieve cached image."""
        if name in self.gltextures:
            img = self.gltextures[name]
            img.registration_sequence = self.registration_sequence
            return img

        # Attempt to load from disk
        try:
            if name.endswith('.pcx'):
                pixels, palette, w, h = self.load_pcx(name)
                self.d_8to24table = palette
                texture = self.upload_8bit(pixels, palette, w, h)
            elif name.endswith('.tga'):
                pixels, w, h = self.load_tga(name)
                texture = self.upload_32bit(pixels, w, h)
            elif name.endswith('.wal'):
                pixels, w, h = self.load_wal(name, self.d_8to24table)
                texture = self.upload_8bit(pixels, self.d_8to24table, w, h)
            else:
                # Fallback: try .pcx, .tga, .wal in sequence
                for ext in ['.pcx', '.tga', '.wal']:
                    try:
                        return self.find_image(name + ext, image_type)
                    except FileNotFoundError:
                        pass
                # Return error texture
                return self._make_error_texture(name)

            img = Image(
                name=name,
                type=image_type,
                width=w,
                height=h,
                upload_width=w,
                upload_height=h,
                registration_sequence=self.registration_sequence,
                texnum=TEXNUM_IMAGES,
                texture=texture,
            )
            self.gltextures[name] = img
            return img

        except Exception as e:
            print(f"Failed to load image {name}: {e}")
            return self._make_error_texture(name)

    def _make_error_texture(self, name: str) -> Image:
        """Create a checkerboard error texture."""
        pixels = np.zeros((32, 32, 4), dtype=np.uint8)
        for i in range(32):
            for j in range(32):
                if (i // 4 + j // 4) % 2 == 0:
                    pixels[i, j] = [255, 0, 255, 255]
                else:
                    pixels[i, j] = [0, 0, 0, 255]

        texture = self.ctx.texture((32, 32), 4, pixels)
        img = Image(
            name=name,
            type='pic',
            width=32,
            height=32,
            upload_width=32,
            upload_height=32,
            texture=texture,
        )
        self.gltextures[name] = img
        return img

    def free_unused_images(self):
        """Remove cached images not used in current registration."""
        to_delete = []
        for name, img in self.gltextures.items():
            if img.registration_sequence != self.registration_sequence:
                to_delete.append(name)

        for name in to_delete:
            img = self.gltextures[name]
            if img.texture:
                img.texture.release()
            del self.gltextures[name]

    def begin_registration(self):
        """Start a new registration cycle."""
        self.registration_sequence += 1

    def end_registration(self):
        """End registration cycle and clean up unused textures."""
        self.free_unused_images()
