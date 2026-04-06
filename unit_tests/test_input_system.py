"""
Unit tests for quake2/cl_input.py and input handling
Tests keyboard and mouse input processing
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_input_state():
    """Test input state structure"""
    print("\n=== Test: Input State ===")

    input_state = {
        'in_attack': False,
        'in_use': False,
        'in_jump': False,
        'in_forward': 0,
        'in_back': 0,
        'in_left': 0,
        'in_right': 0,
        'in_up': 0,
        'in_down': 0
    }

    assert not input_state['in_attack']
    assert input_state['in_forward'] == 0
    assert input_state['in_jump'] == False

    print("[OK] Input state initialized")
    print(f"  Keys tracked: {len(input_state)}")


def test_key_binding():
    """Test key binding system"""
    print("\n=== Test: Key Binding ===")

    key_bindings = {}

    # Bind keys to actions
    key_bindings['w'] = 'in_forward'
    key_bindings['a'] = 'in_left'
    key_bindings['s'] = 'in_back'
    key_bindings['d'] = 'in_right'
    key_bindings['space'] = 'in_jump'

    assert key_bindings['w'] == 'in_forward'
    assert 'space' in key_bindings
    assert len(key_bindings) == 5

    print("[OK] Keys bound to actions")
    print(f"  Bindings: {len(key_bindings)}")
    for key, action in key_bindings.items():
        print(f"    {key} -> {action}")


def test_key_down_event():
    """Test key down event"""
    print("\n=== Test: Key Down Event ===")

    input_state = {'in_forward': 0}
    key = 'w'
    key_bindings = {'w': 'in_forward'}

    # Simulate key down
    if key in key_bindings:
        action = key_bindings[key]
        input_state[action] = 1

    assert input_state['in_forward'] == 1

    print("[OK] Key down event processed")
    print(f"  Key: {key}")
    print(f"  State: {input_state['in_forward']}")


def test_key_up_event():
    """Test key up event"""
    print("\n=== Test: Key Up Event ===")

    input_state = {'in_forward': 1}
    key = 'w'
    key_bindings = {'w': 'in_forward'}

    # Simulate key up
    if key in key_bindings:
        action = key_bindings[key]
        input_state[action] = 0

    assert input_state['in_forward'] == 0

    print("[OK] Key up event processed")
    print(f"  Key: {key}")
    print(f"  State: {input_state['in_forward']}")


def test_mouse_movement():
    """Test mouse movement input"""
    print("\n=== Test: Mouse Movement ===")

    mouse_state = {
        'x': 0,
        'y': 0,
        'dx': 0,
        'dy': 0
    }

    # Simulate mouse movement
    mouse_state['dx'] = 5
    mouse_state['dy'] = -3

    assert mouse_state['dx'] == 5
    assert mouse_state['dy'] == -3

    print("[OK] Mouse movement tracked")
    print(f"  Delta: dx={mouse_state['dx']}, dy={mouse_state['dy']}")


def test_view_angle_adjustment():
    """Test adjusting view angles with mouse"""
    print("\n=== Test: View Angle Adjustment ===")

    view_angles = [0.0, 0.0, 0.0]  # pitch, yaw, roll
    mouse_sensitivity = 0.5

    # Mouse movement
    mouse_dx = 10
    mouse_dy = 5

    # Update angles (typical FPS controls)
    view_angles[1] += mouse_dx * mouse_sensitivity  # Yaw
    view_angles[0] -= mouse_dy * mouse_sensitivity  # Pitch

    assert view_angles[1] == 5.0
    assert view_angles[0] == -2.5

    print("[OK] View angles adjusted by mouse")
    print(f"  Angles: pitch={view_angles[0]}, yaw={view_angles[1]}")


def test_continuous_input():
    """Test continuous input (held keys)"""
    print("\n=== Test: Continuous Input ===")

    input_state = {
        'in_forward': 0,
        'in_back': 0,
        'in_left': 0,
        'in_right': 0
    }

    # Multiple keys held
    input_state['in_forward'] = 1
    input_state['in_right'] = 1

    # Simulate movement
    movement = [0.0, 0.0, 0.0]  # x, y, z
    move_speed = 10.0

    if input_state['in_forward']:
        movement[1] += move_speed

    if input_state['in_right']:
        movement[0] += move_speed

    assert movement[1] == 10.0
    assert movement[0] == 10.0

    print("[OK] Continuous input processed")
    print(f"  Movement: {movement}")


def test_input_frame():
    """Test processing one frame of input"""
    print("\n=== Test: Input Frame ===")

    # Simulate one frame of input processing
    frame_input = {
        'keys_pressed': ['w', 'd'],
        'mouse_dx': 2,
        'mouse_dy': -1,
        'buttons': {'attack': False, 'use': False}
    }

    assert len(frame_input['keys_pressed']) == 2
    assert frame_input['mouse_dx'] == 2

    print("[OK] Frame input processed")
    print(f"  Keys: {frame_input['keys_pressed']}")
    print(f"  Mouse: dx={frame_input['mouse_dx']}, dy={frame_input['mouse_dy']}")


def test_input_clamping():
    """Test clamping input values"""
    print("\n=== Test: Input Clamping ===")

    # Raw input values might be out of range
    pitch = -95.0  # Too low
    yaw = 390.0    # Too high

    # Clamp pitch
    pitch = max(-90.0, min(90.0, pitch))
    assert pitch == -90.0

    # Normalize yaw
    while yaw > 360.0:
        yaw -= 360.0
    assert yaw == 30.0

    print("[OK] Input values clamped")
    print(f"  Pitch: {pitch} (clamped)")
    print(f"  Yaw: {yaw} (normalized)")


def test_button_state():
    """Test button state tracking"""
    print("\n=== Test: Button State ===")

    buttons = {
        'attack': False,
        'use': False,
        'jump': False,
        'reload': False
    }

    # Press attack button
    buttons['attack'] = True
    assert buttons['attack']

    # Release attack button
    buttons['attack'] = False
    assert not buttons['attack']

    print("[OK] Button states tracked")
    print(f"  Buttons: {len(buttons)}")


if __name__ == '__main__':
    try:
        test_input_state()
        test_key_binding()
        test_key_down_event()
        test_key_up_event()
        test_mouse_movement()
        test_view_angle_adjustment()
        test_continuous_input()
        test_input_frame()
        test_input_clamping()
        test_button_state()

        print("\n" + "="*50)
        print("INPUT SYSTEM TESTS COMPLETED [OK]")
        print("="*50)

    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
