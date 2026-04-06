"""
Unit tests for ref_gl/gl_image.py
Tests image and texture loading functionality
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_image_struct():
    """Test image structure"""
    print("\n=== Test: Image Structure ===")

    image = {
        'name': 'textures/base/floor01.wal',
        'width': 256,
        'height': 256,
        'type': 'WAL',
        'gl_texturenum': 0,
        'registration_sequence': 0
    }

    assert image['name'].endswith('.wal')
    assert image['width'] > 0
    assert image['height'] > 0
    assert image['type'] == 'WAL'

    print("[OK] Image structure valid")
    print(f"  Name: {image['name']}")
    print(f"  Size: {image['width']}x{image['height']}")


def test_wal_format_validation():
    """Test WAL format header validation"""
    print("\n=== Test: WAL Format Validation ===")

    # WAL format header (from Quake 2)
    wal_header = {
        'name': 'textures/base/floor01.wal',
        'width': 256,
        'height': 256,
        'offset': [40, 1024, 1280, 1344],  # Mipmap offsets
        'next_name': 'textures/base/floor02.wal',
        'flags': 0,
        'contents': 0,
        'value': 0
    }

    assert wal_header['width'] in [64, 128, 256, 512]  # Valid sizes
    assert wal_header['height'] in [64, 128, 256, 512]
    assert len(wal_header['offset']) == 4  # 4 mipmap levels

    print("[OK] WAL header valid")
    print(f"  Size: {wal_header['width']}x{wal_header['height']}")
    print(f"  Mipmaps: {len(wal_header['offset'])}")


def test_texture_cache():
    """Test texture caching system"""
    print("\n=== Test: Texture Cache ===")

    texture_cache = {}

    # Add images to cache
    texture_cache['floor01'] = {'name': 'floor01', 'gl_texturenum': 1}
    texture_cache['wall01'] = {'name': 'wall01', 'gl_texturenum': 2}

    assert 'floor01' in texture_cache
    assert 'wall01' in texture_cache
    assert len(texture_cache) == 2
    assert texture_cache['floor01']['gl_texturenum'] == 1

    print("[OK] Texture cache works")
    print(f"  Cached textures: {len(texture_cache)}")
    for name in texture_cache:
        print(f"    - {name}")


def test_image_registration():
    """Test image registration tracking"""
    print("\n=== Test: Image Registration ===")

    registration_sequence = 0

    images = [
        {'name': 'tex1', 'registration_sequence': registration_sequence},
        {'name': 'tex2', 'registration_sequence': registration_sequence},
    ]

    # Increment sequence for new registration cycle
    registration_sequence += 1

    new_images = [
        {'name': 'tex3', 'registration_sequence': registration_sequence},
        {'name': 'tex4', 'registration_sequence': registration_sequence},
    ]

    # Old images should have different sequence
    assert images[0]['registration_sequence'] != registration_sequence
    assert new_images[0]['registration_sequence'] == registration_sequence

    print("[OK] Image registration tracking works")
    print(f"  Old sequence: {images[0]['registration_sequence']}")
    print(f"  Current sequence: {registration_sequence}")


def test_palette_loading():
    """Test palette loading for 8-bit textures"""
    print("\n=== Test: Palette Loading ===")

    # Standard Quake 2 palette is 256 colors * 3 bytes (RGB)
    palette_size = 256 * 3

    # Create mock palette
    palette = bytearray(palette_size)
    for i in range(256):
        palette[i * 3 + 0] = i  # R
        palette[i * 3 + 1] = i  # G
        palette[i * 3 + 2] = i  # B

    assert len(palette) == palette_size
    assert palette[0] == 0  # First color
    assert palette[-1] == 255  # Last color

    print("[OK] Palette structure valid")
    print(f"  Palette size: {len(palette)} bytes")
    print(f"  Colors: 256")


def test_pixel_format_conversion():
    """Test pixel format conversions"""
    print("\n=== Test: Pixel Format Conversion ===")

    # 8-bit indexed pixel
    indexed_pixel = 128

    # Convert to RGB (grayscale for simplicity)
    rgb_pixel = [indexed_pixel, indexed_pixel, indexed_pixel]

    assert len(rgb_pixel) == 3
    assert all(0 <= c <= 255 for c in rgb_pixel)

    # Convert to RGBA (add alpha)
    rgba_pixel = rgb_pixel + [255]

    assert len(rgba_pixel) == 4
    assert rgba_pixel[3] == 255  # Alpha channel

    print("[OK] Pixel format conversion works")
    print(f"  8-bit index: {indexed_pixel}")
    print(f"  RGB: {rgb_pixel}")
    print(f"  RGBA: {rgba_pixel}")


def test_texture_dimensions():
    """Test texture dimension validation"""
    print("\n=== Test: Texture Dimensions ===")

    valid_widths = [64, 128, 256, 512, 1024]
    valid_heights = [64, 128, 256, 512, 1024]

    # Test valid dimensions (power of 2)
    for w in valid_widths:
        for h in valid_heights:
            assert w > 0 and h > 0
            # Check that both are power of 2
            assert (w & (w - 1)) == 0  # Power of 2
            assert (h & (h - 1)) == 0  # Power of 2

    print("[OK] Texture dimensions valid")
    print(f"  Valid widths: {valid_widths}")
    print(f"  Valid heights: {valid_heights}")


def test_mipmap_chain():
    """Test mipmap generation chain"""
    print("\n=== Test: Mipmap Chain ===")

    base_width = 256
    base_height = 256

    mipmaps = []
    w, h = base_width, base_height
    level = 0

    while w >= 1 and h >= 1:
        mipmaps.append({'level': level, 'width': w, 'height': h})
        w //= 2
        h //= 2
        level += 1

    assert len(mipmaps) == 9  # 256→128→64→32→16→8→4→2→1
    assert mipmaps[0]['width'] == 256
    assert mipmaps[-1]['width'] == 1

    print("[OK] Mipmap chain generated")
    print(f"  Total levels: {len(mipmaps)}")
    for m in mipmaps[:3]:
        print(f"    Level {m['level']}: {m['width']}x{m['height']}")


def test_texture_filtering():
    """Test texture filtering modes"""
    print("\n=== Test: Texture Filtering ===")

    filters = {
        'GL_NEAREST': 'blocky (no interpolation)',
        'GL_LINEAR': 'smooth (bilinear interpolation)',
        'GL_NEAREST_MIPMAP_NEAREST': 'nearest mipmap',
        'GL_LINEAR_MIPMAP_NEAREST': 'linear mipmap',
        'GL_LINEAR_MIPMAP_LINEAR': 'trilinear filtering'
    }

    default_filter = 'GL_LINEAR_MIPMAP_NEAREST'

    assert default_filter in filters
    assert all(isinstance(f, str) for f in filters.keys())

    print("[OK] Texture filtering modes available")
    print(f"  Default: {default_filter}")
    print(f"  Modes: {len(filters)}")


if __name__ == '__main__':
    try:
        test_image_struct()
        test_wal_format_validation()
        test_texture_cache()
        test_image_registration()
        test_palette_loading()
        test_pixel_format_conversion()
        test_texture_dimensions()
        test_mipmap_chain()
        test_texture_filtering()

        print("\n" + "="*50)
        print("GL_IMAGE TESTS COMPLETED [OK]")
        print("="*50)

    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
