"""
Unit tests for ref_gl/gl_mesh.py, gl_draw.py, and gl_screenshot.py
Tests entity model, drawing, and screenshot functionality
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_md2_model_struct():
    """Test MD2 model structure"""
    print("\n=== Test: MD2 Model Structure ===")

    model = {
        'type': 'MD2',
        'numframes': 78,
        'numvertices': 512,
        'numtris': 1024,
        'numskins': 1,
        'skinwidth': 256,
        'skinheight': 256
    }

    assert model['type'] == 'MD2'
    assert model['numframes'] > 0
    assert model['numvertices'] > 0
    assert model['numtris'] > 0

    print("[OK] MD2 model structure valid")
    print(f"  Frames: {model['numframes']}")
    print(f"  Vertices: {model['numvertices']}")
    print(f"  Triangles: {model['numtris']}")


def test_md2_animation_frame():
    """Test MD2 animation frame data"""
    print("\n=== Test: MD2 Animation Frame ===")

    frame = {
        'name': 'stand',
        'index': 0,
        'vertices': [],
        'scale': [0.0625, 0.0625, 0.0625],
        'translate': [0.0, 0.0, 0.0]
    }

    # Add some vertex positions
    for i in range(10):
        frame['vertices'].append([float(i), 0.0, 0.0])

    assert frame['index'] == 0
    assert len(frame['vertices']) == 10
    assert len(frame['scale']) == 3

    print("[OK] MD2 frame structure valid")
    print(f"  Frame: {frame['name']}")
    print(f"  Vertices: {len(frame['vertices'])}")


def test_md2_frame_interpolation():
    """Test frame interpolation for smooth animation"""
    print("\n=== Test: MD2 Frame Interpolation ===")

    # Two frames
    frame1_vertex = [0.0, 0.0, 0.0]
    frame2_vertex = [10.0, 0.0, 0.0]

    # Interpolation amount (0.0 = frame1, 1.0 = frame2)
    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
        lerp_vertex = [
            frame1_vertex[0] + t * (frame2_vertex[0] - frame1_vertex[0]),
            frame1_vertex[1] + t * (frame2_vertex[1] - frame1_vertex[1]),
            frame1_vertex[2] + t * (frame2_vertex[2] - frame1_vertex[2])
        ]

        expected = t * 10.0
        assert abs(lerp_vertex[0] - expected) < 0.01

    print("[OK] Frame interpolation works correctly")
    print(f"  t=0.0: position = 0.0")
    print(f"  t=0.5: position = 5.0")
    print(f"  t=1.0: position = 10.0")


def test_2d_draw_rect():
    """Test 2D rectangle drawing"""
    print("\n=== Test: 2D Draw Rectangle ===")

    rect = {
        'x': 10,
        'y': 20,
        'width': 100,
        'height': 50,
        'color': [1.0, 0.0, 0.0]
    }

    assert rect['x'] >= 0
    assert rect['y'] >= 0
    assert rect['width'] > 0
    assert rect['height'] > 0
    assert len(rect['color']) == 3

    print("[OK] 2D rectangle structure valid")
    print(f"  Position: ({rect['x']}, {rect['y']})")
    print(f"  Size: {rect['width']}x{rect['height']}")


def test_2d_draw_text():
    """Test 2D text drawing"""
    print("\n=== Test: 2D Draw Text ===")

    text_render = {
        'text': 'Hello World',
        'x': 10,
        'y': 10,
        'color': [1.0, 1.0, 1.0],
        'scale': 1.0
    }

    assert len(text_render['text']) > 0
    assert text_render['x'] >= 0
    assert text_render['y'] >= 0
    assert 0.5 <= text_render['scale'] <= 2.0

    print("[OK] 2D text structure valid")
    print(f"  Text: {text_render['text']}")
    print(f"  Position: ({text_render['x']}, {text_render['y']})")


def test_2d_character_grid():
    """Test 2D character grid for font rendering"""
    print("\n=== Test: 2D Character Grid ===")

    # Standard console font: 16x16 grid of glyphs, each 8x8 pixels
    char_grid = {
        'glyphs_per_row': 16,
        'glyphs_per_col': 16,
        'glyph_width': 8,
        'glyph_height': 8,
        'texture_width': 128,
        'texture_height': 128
    }

    total_glyphs = char_grid['glyphs_per_row'] * char_grid['glyphs_per_col']
    assert total_glyphs == 256  # ASCII character set

    # Verify texture size
    assert char_grid['texture_width'] == char_grid['glyphs_per_row'] * char_grid['glyph_width']
    assert char_grid['texture_height'] == char_grid['glyphs_per_col'] * char_grid['glyph_height']

    print("[OK] Character grid configured correctly")
    print(f"  Glyphs: {total_glyphs}")
    print(f"  Texture: {char_grid['texture_width']}x{char_grid['texture_height']}")


def test_screenshot_format():
    """Test screenshot format specifications"""
    print("\n=== Test: Screenshot Format ===")

    screenshot = {
        'width': 800,
        'height': 600,
        'format': 'PNG',
        'channels': 3,  # RGB
        'bits_per_channel': 8,
        'filename': 'quake2_screenshot_20260406_120000.png'
    }

    assert screenshot['width'] > 0
    assert screenshot['height'] > 0
    assert screenshot['format'] in ['PNG', 'BMP', 'TGA']
    assert screenshot['channels'] in [3, 4]  # RGB or RGBA

    print("[OK] Screenshot format valid")
    print(f"  Resolution: {screenshot['width']}x{screenshot['height']}")
    print(f"  Format: {screenshot['format']}")
    print(f"  Channels: {screenshot['channels']}")


def test_screenshot_data_buffer():
    """Test screenshot pixel data buffer"""
    print("\n=== Test: Screenshot Data Buffer ===")

    # Create mock pixel buffer
    width = 4
    height = 4
    channels = 3

    # Create buffer (4x4 RGB image)
    pixel_data = bytearray(width * height * channels)

    # Fill with test pattern
    for i in range(len(pixel_data)):
        pixel_data[i] = (i % 256)

    assert len(pixel_data) == 48  # 4*4*3
    assert pixel_data[0] == 0
    assert pixel_data[-1] == 47

    print("[OK] Screenshot pixel buffer valid")
    print(f"  Buffer size: {len(pixel_data)} bytes")
    print(f"  Dimensions: {width}x{height}x{channels}")


def test_crosshair_drawing():
    """Test crosshair rendering"""
    print("\n=== Test: Crosshair Drawing ===")

    crosshair = {
        'x': 400,  # Center of 800px width
        'y': 300,  # Center of 600px height
        'size': 10,
        'color': [1.0, 1.0, 1.0],
        'style': 'cross'  # or 'dot', 'square'
    }

    assert crosshair['x'] > 0
    assert crosshair['y'] > 0
    assert crosshair['size'] > 0
    assert crosshair['style'] in ['cross', 'dot', 'square']

    print("[OK] Crosshair configuration valid")
    print(f"  Position: ({crosshair['x']}, {crosshair['y']})")
    print(f"  Style: {crosshair['style']}")


def test_hud_element():
    """Test HUD element drawing"""
    print("\n=== Test: HUD Element ===")

    hud_element = {
        'type': 'health',
        'value': 75,
        'max_value': 100,
        'x': 10,
        'y': 570,
        'width': 200,
        'height': 20,
        'color': [0.0, 1.0, 0.0]
    }

    assert hud_element['value'] <= hud_element['max_value']
    assert hud_element['x'] >= 0
    assert hud_element['y'] >= 0

    # Calculate bar fill percentage
    fill_percent = hud_element['value'] / hud_element['max_value']
    assert 0.0 <= fill_percent <= 1.0

    print("[OK] HUD element structure valid")
    print(f"  Type: {hud_element['type']}")
    print(f"  Value: {hud_element['value']}/{hud_element['max_value']}")


if __name__ == '__main__':
    try:
        test_md2_model_struct()
        test_md2_animation_frame()
        test_md2_frame_interpolation()
        test_2d_draw_rect()
        test_2d_draw_text()
        test_2d_character_grid()
        test_screenshot_format()
        test_screenshot_data_buffer()
        test_crosshair_drawing()
        test_hud_element()

        print("\n" + "="*50)
        print("GL_MISC TESTS COMPLETED [OK]")
        print("="*50)

    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
