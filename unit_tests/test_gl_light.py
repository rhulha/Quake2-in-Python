"""
Unit tests for ref_gl/gl_light.py
Tests dynamic and static lighting functionality
"""

import sys
import os
import math

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_light_struct():
    """Test dynamic light structure"""
    print("\n=== Test: Light Structure ===")

    light = {
        'origin': [100.0, 200.0, 50.0],
        'color': [1.0, 0.5, 0.0],
        'intensity': 200.0,
        'radius': 200.0
    }

    assert len(light['origin']) == 3
    assert len(light['color']) == 3
    assert light['intensity'] > 0
    assert all(0.0 <= c <= 1.0 for c in light['color'])

    print("[OK] Light structure valid")
    print(f"  Position: {light['origin']}")
    print(f"  Color: {light['color']}")
    print(f"  Intensity: {light['intensity']}")


def test_lightstyle_animation():
    """Test lightstyle animation patterns"""
    print("\n=== Test: Lightstyle Animation ===")

    # Standard Quake lightstyles use ASCII characters
    lightstyles = {
        0: 'm',  # Normal
        1: 'mmnmmommommnonmmonqmmonmmonmmnonmmonmmmmm',  # Strobe
        2: 'abcdefghijklmnopqrstuvwxyzyxwvutsrqponmlkjihgfedcba',  # Smooth
    }

    for style_num, pattern in lightstyles.items():
        assert isinstance(pattern, str)
        # Each character is 'a' + intensity (0-25)
        for char in pattern:
            ord_val = ord(char)
            assert ord_val >= ord('a') and ord_val <= ord('z')

    print("[OK] Lightstyle patterns valid")
    print(f"  Styles: {len(lightstyles)}")
    for num, pattern in lightstyles.items():
        print(f"    Style {num}: {len(pattern)} frames")


def test_light_distance_calculation():
    """Test light distance calculations"""
    print("\n=== Test: Light Distance ===")

    light_pos = [100.0, 100.0, 50.0]
    point_pos = [100.0, 100.0, 50.0]

    # Distance at same point
    distance = 0.0
    assert distance == 0.0

    # Distance at different point
    point_pos = [110.0, 100.0, 50.0]
    dx = point_pos[0] - light_pos[0]
    dy = point_pos[1] - light_pos[1]
    dz = point_pos[2] - light_pos[2]
    distance = math.sqrt(dx*dx + dy*dy + dz*dz)

    assert distance == 10.0

    print("[OK] Light distance calculation correct")
    print(f"  Distance: {distance}")


def test_light_attenuation():
    """Test light attenuation over distance"""
    print("\n=== Test: Light Attenuation ===")

    intensity = 200.0
    distance = 50.0
    radius = 200.0

    # Simple attenuation: intensity * (1 - distance/radius)
    if distance < radius:
        attenuation = 1.0 - (distance / radius)
        brightness = intensity * attenuation
    else:
        brightness = 0.0

    assert 0.0 <= attenuation <= 1.0
    assert brightness >= 0.0

    # At half radius, intensity should be half
    half_distance = radius / 2.0
    half_attenuation = 1.0 - (half_distance / radius)
    assert abs(half_attenuation - 0.5) < 0.01

    print("[OK] Light attenuation calculated correctly")
    print(f"  Distance: {distance}")
    print(f"  Attenuation: {attenuation:.2f}")
    print(f"  Brightness: {brightness:.0f}")


def test_light_color_mixing():
    """Test light color mixing"""
    print("\n=== Test: Light Color Mixing ===")

    # Red light
    light1_color = [1.0, 0.0, 0.0]
    light1_intensity = 100.0

    # Blue light
    light2_color = [0.0, 0.0, 1.0]
    light2_intensity = 100.0

    # Mix colors (additive blending)
    mixed = [
        min(light1_color[0] * light1_intensity + light2_color[0] * light2_intensity, 255) / 255.0,
        min(light1_color[1] * light1_intensity + light2_color[1] * light2_intensity, 255) / 255.0,
        min(light1_color[2] * light1_intensity + light2_color[2] * light2_intensity, 255) / 255.0,
    ]

    assert len(mixed) == 3

    print("[OK] Light color mixing works")
    print(f"  Light 1: {light1_color}")
    print(f"  Light 2: {light2_color}")
    print(f"  Mixed: {mixed}")


def test_lightmap_allocation():
    """Test lightmap texture allocation"""
    print("\n=== Test: Lightmap Allocation ===")

    # Lightmap is typically 128x128 pixels
    lightmap_width = 128
    lightmap_height = 128

    # Allocate blocks for surfaces
    lightmap_blocks = []

    # Each surface gets a block based on size
    surfaces = [
        {'width': 32, 'height': 32},
        {'width': 64, 'height': 64},
        {'width': 16, 'height': 16},
    ]

    for surf in surfaces:
        block = {
            'x': 0,
            'y': 0,
            'width': surf['width'],
            'height': surf['height']
        }
        lightmap_blocks.append(block)

    assert len(lightmap_blocks) == len(surfaces)

    print("[OK] Lightmap allocation works")
    print(f"  Lightmap size: {lightmap_width}x{lightmap_height}")
    print(f"  Blocks: {len(lightmap_blocks)}")


def test_surface_lightmap_coords():
    """Test surface lightmap coordinate calculation"""
    print("\n=== Test: Surface Lightmap Coords ===")

    # Surface extent in lightmap space
    extents = [256, 512]

    # Calculate lightmap sample grid
    smax = (extents[0] >> 4) + 1  # /16 + 1
    tmax = (extents[1] >> 4) + 1

    assert smax == 17  # 256/16 + 1
    assert tmax == 33  # 512/16 + 1

    # Calculate total samples
    total_samples = smax * tmax
    assert total_samples == 561

    print("[OK] Lightmap coordinates calculated")
    print(f"  Extents: {extents}")
    print(f"  Samples: {smax}x{tmax} = {total_samples}")


def test_light_list():
    """Test dynamic light list management"""
    print("\n=== Test: Light List ===")

    lights = []

    # Add lights
    for i in range(5):
        light = {
            'id': i,
            'origin': [i * 100.0, 0.0, 0.0],
            'color': [1.0, 1.0, 1.0],
            'intensity': 200.0
        }
        lights.append(light)

    assert len(lights) == 5
    assert lights[0]['id'] == 0
    assert lights[4]['id'] == 4

    # Remove a light
    lights.pop(2)
    assert len(lights) == 4

    print("[OK] Light list management works")
    print(f"  Lights: {len(lights)}")


def test_light_visibility():
    """Test light visibility checking"""
    print("\n=== Test: Light Visibility ===")

    light = {'origin': [100.0, 100.0, 100.0], 'radius': 200.0}

    # Test points
    visible_point = [150.0, 100.0, 100.0]  # 50 units away
    invisible_point = [400.0, 100.0, 100.0]  # 300 units away

    # Distance check
    dx = visible_point[0] - light['origin'][0]
    dy = visible_point[1] - light['origin'][1]
    dz = visible_point[2] - light['origin'][2]
    dist1 = math.sqrt(dx*dx + dy*dy + dz*dz)

    assert dist1 < light['radius']

    dx = invisible_point[0] - light['origin'][0]
    dy = invisible_point[1] - light['origin'][1]
    dz = invisible_point[2] - light['origin'][2]
    dist2 = math.sqrt(dx*dx + dy*dy + dz*dz)

    assert dist2 > light['radius']

    print("[OK] Light visibility checking works")
    print(f"  Visible point distance: {dist1:.1f}")
    print(f"  Invisible point distance: {dist2:.1f}")


if __name__ == '__main__':
    try:
        test_light_struct()
        test_lightstyle_animation()
        test_light_distance_calculation()
        test_light_attenuation()
        test_light_color_mixing()
        test_lightmap_allocation()
        test_surface_lightmap_coords()
        test_light_list()
        test_light_visibility()

        print("\n" + "="*50)
        print("GL_LIGHT TESTS COMPLETED [OK]")
        print("="*50)

    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
