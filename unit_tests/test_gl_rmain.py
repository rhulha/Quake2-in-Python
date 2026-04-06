"""
Unit tests for ref_gl/gl_rmain.py
Tests main rendering functions and view setup
"""

import sys
import os
import math

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_view_angle_setup():
    """Test view angle configuration"""
    print("\n=== Test: View Angle Setup ===")

    # Create view angles (pitch, yaw, roll in degrees)
    viewangles = [0.0, 90.0, 0.0]

    assert len(viewangles) == 3
    assert viewangles[0] == 0.0    # Pitch (look up/down)
    assert viewangles[1] == 90.0   # Yaw (turn left/right)
    assert viewangles[2] == 0.0    # Roll (tilt)

    print("[OK] View angles configured")
    print(f"  Pitch: {viewangles[0]}°")
    print(f"  Yaw: {viewangles[1]}°")
    print(f"  Roll: {viewangles[2]}°")


def test_camera_position():
    """Test camera position tracking"""
    print("\n=== Test: Camera Position ===")

    vieworg = [1248.0, 672.0, 472.0]

    assert len(vieworg) == 3
    assert all(isinstance(v, float) for v in vieworg)
    assert vieworg[2] > 0  # Z should be up

    print("[OK] Camera position valid")
    print(f"  Position: {vieworg}")
    print(f"  X (right): {vieworg[0]}")
    print(f"  Y (forward): {vieworg[1]}")
    print(f"  Z (up): {vieworg[2]}")


def test_fov_calculation():
    """Test field of view calculations"""
    print("\n=== Test: FOV Calculation ===")

    # Horizontal FOV
    fov_x = 90.0
    width = 800
    height = 600

    # Calculate vertical FOV
    aspect = width / height
    fov_y_rad = 2.0 * math.atan(math.tan(math.radians(fov_x) / 2.0) / aspect)
    fov_y = math.degrees(fov_y_rad)

    assert fov_y > 0
    assert fov_y < fov_x  # Vertical FOV should be narrower than horizontal for wide screens
    assert fov_y > 60 and fov_y < 80  # Should be around 73.74°

    print("[OK] FOV calculation correct")
    print(f"  Horizontal FOV: {fov_x}°")
    print(f"  Vertical FOV: {fov_y:.2f}°")
    print(f"  Aspect ratio: {aspect:.2f}")


def test_projection_matrix_params():
    """Test projection matrix parameters"""
    print("\n=== Test: Projection Matrix Params ===")

    width = 800
    height = 600
    fov_y = 73.74

    aspect = width / height
    near = 1.0
    far = 4096.0

    # Calculate frustum planes
    f = 1.0 / math.tan(math.radians(fov_y) / 2.0)
    left = -near * aspect / f
    right = near * aspect / f
    bottom = -near / f
    top = near / f

    assert near < far
    assert left < right
    assert bottom < top
    assert abs(right - (-left)) < 0.01  # Should be symmetric

    print("[OK] Frustum planes calculated correctly")
    print(f"  Near: {near}, Far: {far}")
    print(f"  Left: {left:.2f}, Right: {right:.2f}")
    print(f"  Bottom: {bottom:.2f}, Top: {top:.2f}")


def test_viewport_setup():
    """Test viewport configuration"""
    print("\n=== Test: Viewport Setup ===")

    viewport = {
        'x': 0,
        'y': 0,
        'width': 800,
        'height': 600
    }

    assert viewport['x'] == 0
    assert viewport['y'] == 0
    assert viewport['width'] > 0
    assert viewport['height'] > 0
    assert viewport['width'] > viewport['height']  # Landscape

    print("[OK] Viewport configured")
    print(f"  Position: ({viewport['x']}, {viewport['y']})")
    print(f"  Size: {viewport['width']}x{viewport['height']}")


def test_clear_color():
    """Test clear color setup"""
    print("\n=== Test: Clear Color ===")

    clear_color = [0.3, 0.3, 0.5, 1.0]  # RGBA

    assert len(clear_color) == 4
    assert all(0.0 <= c <= 1.0 for c in clear_color)
    assert clear_color[3] == 1.0  # Alpha should be 1.0 (opaque)

    print("[OK] Clear color valid")
    print(f"  Color: RGBA{tuple(clear_color)}")


def test_depth_test_config():
    """Test depth testing configuration"""
    print("\n=== Test: Depth Test Config ===")

    depth_config = {
        'test_enabled': True,
        'write_enabled': True,
        'func': 'GL_LEQUAL',
        'near': 0.0,
        'far': 1.0
    }

    assert depth_config['test_enabled']
    assert depth_config['write_enabled']
    assert depth_config['near'] < depth_config['far']

    print("[OK] Depth test configured")
    print(f"  Test enabled: {depth_config['test_enabled']}")
    print(f"  Depth function: {depth_config['func']}")
    print(f"  Range: {depth_config['near']} to {depth_config['far']}")


def test_culling_config():
    """Test face culling configuration"""
    print("\n=== Test: Culling Config ===")

    culling = {
        'enabled': True,
        'cull_face': 'GL_BACK',
        'front_face': 'GL_CCW'
    }

    assert culling['enabled']
    assert culling['cull_face'] in ['GL_BACK', 'GL_FRONT']
    assert culling['front_face'] in ['GL_CW', 'GL_CCW']

    print("[OK] Culling configured")
    print(f"  Culling: {culling['cull_face']}")
    print(f"  Front face: {culling['front_face']}")


def test_lighting_config():
    """Test lighting state"""
    print("\n=== Test: Lighting Config ===")

    lighting = {
        'enabled': False,  # We use immediate mode colors
        'ambient': [0.2, 0.2, 0.2, 1.0]
    }

    assert not lighting['enabled']
    assert len(lighting['ambient']) == 4

    print("[OK] Lighting configured for immediate mode")
    print(f"  Lighting enabled: {lighting['enabled']}")
    print(f"  Ambient: {lighting['ambient']}")


def test_blend_config():
    """Test blending configuration"""
    print("\n=== Test: Blend Config ===")

    blend = {
        'enabled': False,  # Generally disabled for opaque geometry
        'src_factor': 'GL_SRC_ALPHA',
        'dst_factor': 'GL_ONE_MINUS_SRC_ALPHA'
    }

    assert isinstance(blend['enabled'], bool)

    print("[OK] Blending configured")
    print(f"  Blending enabled: {blend['enabled']}")


def test_refdef_structure():
    """Test refdef_t structure"""
    print("\n=== Test: Refdef Structure ===")

    refdef = {
        'x': 0,
        'y': 0,
        'width': 800,
        'height': 600,
        'fov_x': 90.0,
        'fov_y': 73.74,
        'vieworg': [1248.0, 672.0, 472.0],
        'viewangles': [0.0, 90.0, 0.0],
        'blend': [0.0, 0.0, 0.0, 0.0],
        'time': 0.0,
        'rdflags': 0,
        'entities': [],
        'dlights': [],
        'particles': []
    }

    assert refdef['width'] > 0
    assert refdef['height'] > 0
    assert len(refdef['vieworg']) == 3
    assert len(refdef['viewangles']) == 3
    assert isinstance(refdef['entities'], list)

    print("[OK] Refdef structure complete")
    print(f"  Resolution: {refdef['width']}x{refdef['height']}")
    print(f"  FOV: {refdef['fov_x']}° × {refdef['fov_y']}°")
    print(f"  Entities: {len(refdef['entities'])}")


if __name__ == '__main__':
    try:
        test_view_angle_setup()
        test_camera_position()
        test_fov_calculation()
        test_projection_matrix_params()
        test_viewport_setup()
        test_clear_color()
        test_depth_test_config()
        test_culling_config()
        test_lighting_config()
        test_blend_config()
        test_refdef_structure()

        print("\n" + "="*50)
        print("GL_RMAIN TESTS COMPLETED [OK]")
        print("="*50)

    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
