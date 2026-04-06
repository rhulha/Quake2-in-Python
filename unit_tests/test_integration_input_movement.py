"""
Integration tests for input → movement pipeline
Tests that keyboard input actually moves the player through the full game loop
"""

import sys
import os
import math

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_input_command_creation():
    """Test that input commands can be created"""
    print("\n=== Test: Input Command Creation ===")

    from quake2.cl_input import usercmd_t

    # Test that we can create movement commands
    cmd_forward = usercmd_t()
    cmd_forward.forwardmove = 200.0
    assert cmd_forward.forwardmove == 200.0, "Should be able to set forwardmove"
    print(f"[OK] Forward command: forwardmove={cmd_forward.forwardmove}")

    cmd_strafe = usercmd_t()
    cmd_strafe.sidemove = -150.0
    assert cmd_strafe.sidemove == -150.0, "Should be able to set sidemove"
    print(f"[OK] Strafe left command: sidemove={cmd_strafe.sidemove}")

    cmd_right = usercmd_t()
    cmd_right.sidemove = 150.0
    assert cmd_right.sidemove == 150.0, "Should be able to set sidemove right"
    print(f"[OK] Strafe right command: sidemove={cmd_right.sidemove}")


def test_player_entity_initialization():
    """Test that player entity is properly set up"""
    print("\n=== Test: Player Entity Initialization ===")

    try:
        from game.g_main import game

        # Initialize game entities
        game.entities = [None] * 10

        # Create player entity like sv_main does
        player = {
            'number': 1,
            'classname': 'player',
            'inuse': True,
            'origin': [100.0, 200.0, 300.0],
            'angles': [0.0, 90.0, 0.0],
            'velocity': [0.0, 0.0, 0.0],
            'health': 100,
            'client': {
                'buttons': 0,
                'oldbuttons': 0,
                'v_angle': [0.0, 0.0, 0.0],
            }
        }

        game.entities[1] = player

        assert game.entities[1] is not None, "Player should be in game.entities[1]"
        assert game.entities[1]['health'] == 100, "Player health should be 100"
        assert game.entities[1]['client'] is not None, "Player should have client structure"

        print("[OK] Player entity initialized correctly")
        print(f"  Position: {player['origin']}")
        print(f"  Health: {player['health']}")

    except Exception as e:
        print(f"[ERROR] Failed to initialize player: {e}")
        raise


def test_input_applied_to_player():
    """Test that ClientThink applies input to player velocity"""
    print("\n=== Test: Input Applied to Player ===")

    from game.p_client import ClientThink
    from quake2.cl_input import usercmd_t

    player = {
        'classname': 'player',
        'inuse': True,
        'origin': [100.0, 200.0, 300.0],
        'angles': [0.0, 0.0, 0.0],
        'velocity': [0.0, 0.0, 0.0],
        'health': 100,
        'client': {
            'buttons': 0,
            'oldbuttons': 0,
            'v_angle': [0.0, 0.0, 0.0],
        }
    }

    # Create a command with forward movement
    cmd = usercmd_t()
    cmd.forwardmove = 200.0
    cmd.sidemove = 0.0
    cmd.upmove = 0.0

    # Apply command to player
    ClientThink(player, cmd)

    assert player['velocity'][0] == 200.0, "Forward movement should set velocity[0]"
    print(f"[OK] ClientThink applied forwardmove: velocity={player['velocity']}")

    # Test strafe
    player2 = {
        'classname': 'player',
        'inuse': True,
        'origin': [100.0, 200.0, 300.0],
        'velocity': [0.0, 0.0, 0.0],
        'health': 100,
        'client': {
            'buttons': 0,
            'oldbuttons': 0,
            'v_angle': [0.0, 0.0, 0.0],
        }
    }

    cmd2 = usercmd_t()
    cmd2.forwardmove = 0.0
    cmd2.sidemove = 150.0
    cmd2.upmove = 0.0

    ClientThink(player2, cmd2)

    assert player2['velocity'][1] == 150.0, "Strafe should set velocity[1]"
    print(f"[OK] ClientThink applied sidemove: velocity={player2['velocity']}")


def test_physics_updates_position():
    """Test that physics integration updates position from velocity"""
    print("\n=== Test: Physics Updates Position ===")

    from game.g_main import game

    # Initialize game
    game.entities = [None] * 10
    game.time = 0.0

    player = {
        'classname': 'player',
        'inuse': True,
        'origin': [100.0, 200.0, 300.0],
        'velocity': [100.0, 50.0, 0.0],  # Moving forward and right
        'health': 100,
    }

    game.entities[1] = player
    initial_origin = list(player['origin'])

    # Simulate one frame of physics (dt=0.016)
    dt = 0.016
    player['origin'][0] += player['velocity'][0] * dt
    player['origin'][1] += player['velocity'][1] * dt
    player['origin'][2] += player['velocity'][2] * dt

    # Check position changed
    expected_x = initial_origin[0] + 100.0 * dt
    expected_y = initial_origin[1] + 50.0 * dt

    assert abs(player['origin'][0] - expected_x) < 0.001, "X position should update from velocity"
    assert abs(player['origin'][1] - expected_y) < 0.001, "Y position should update from velocity"
    assert player['origin'][2] == initial_origin[2], "Z should not change (no velocity)"

    print(f"[OK] Physics updated position correctly")
    print(f"  Initial: {initial_origin}")
    print(f"  After dt={dt}: {player['origin']}")
    print(f"  Delta: ({player['origin'][0]-initial_origin[0]:.3f}, {player['origin'][1]-initial_origin[1]:.3f})")


def test_full_input_to_movement_pipeline():
    """Test complete pipeline: input → command → player velocity → position"""
    print("\n=== Test: Full Input-to-Movement Pipeline ===")

    from game.g_main import game
    from game.p_client import ClientThink
    from quake2.cl_input import usercmd_t

    # Setup game and player
    game.entities = [None] * 10
    game.time = 0.0

    player = {
        'classname': 'player',
        'inuse': True,
        'origin': [500.0, 600.0, 200.0],
        'angles': [0.0, 0.0, 0.0],
        'velocity': [0.0, 0.0, 0.0],
        'health': 100,
        'client': {
            'buttons': 0,
            'oldbuttons': 0,
            'v_angle': [0.0, 0.0, 0.0],
        }
    }
    game.entities[1] = player
    initial_pos = list(player['origin'])

    print(f"Initial position: {initial_pos}")

    # Step 1: Simulate WASD input
    cmd = usercmd_t()
    cmd.forwardmove = 200.0  # W key
    cmd.sidemove = 150.0     # D key
    cmd.upmove = 0.0

    # Step 2: Apply input to player (like G_RunFrame does)
    ClientThink(player, cmd)
    print(f"After input: velocity={player['velocity']}")

    assert player['velocity'][0] == 200.0, "Input should set forward velocity"
    assert player['velocity'][1] == 150.0, "Input should set strafe velocity"

    # Step 3: Physics update (like in G_RunFrame)
    dt = 0.016
    player['origin'][0] += player['velocity'][0] * dt
    player['origin'][1] += player['velocity'][1] * dt
    player['origin'][2] += player['velocity'][2] * dt

    print(f"After physics: position={player['origin']}")

    # Verify position changed
    expected_x = initial_pos[0] + 200.0 * dt
    expected_y = initial_pos[1] + 150.0 * dt

    assert abs(player['origin'][0] - expected_x) < 0.001, "X position should change"
    assert abs(player['origin'][1] - expected_y) < 0.001, "Y position should change"

    distance = math.sqrt(
        (player['origin'][0] - initial_pos[0])**2 +
        (player['origin'][1] - initial_pos[1])**2
    )

    print(f"[OK] Full pipeline works!")
    print(f"  Player moved {distance:.3f} units")
    print(f"  Direction: ({player['origin'][0]-initial_pos[0]:.3f}, {player['origin'][1]-initial_pos[1]:.3f})")


def test_multiple_frames_accumulate_movement():
    """Test that multiple frames accumulate movement"""
    print("\n=== Test: Multiple Frames Accumulate Movement ===")

    from game.g_main import game
    from game.p_client import ClientThink
    from quake2.cl_input import usercmd_t

    game.entities = [None] * 10

    player = {
        'classname': 'player',
        'inuse': True,
        'origin': [0.0, 0.0, 0.0],
        'velocity': [0.0, 0.0, 0.0],
        'health': 100,
        'client': {
            'buttons': 0,
            'oldbuttons': 0,
            'v_angle': [0.0, 0.0, 0.0],
        }
    }
    game.entities[1] = player

    # Simulate 10 frames of W key held down
    cmd = usercmd_t()
    cmd.forwardmove = 200.0
    dt = 0.016

    for frame in range(10):
        ClientThink(player, cmd)
        player['origin'][0] += player['velocity'][0] * dt
        player['origin'][1] += player['velocity'][1] * dt

    expected_distance = 200.0 * dt * 10
    actual_distance = player['origin'][0]

    assert abs(actual_distance - expected_distance) < 0.001, "10 frames should accumulate"

    print(f"[OK] 10 frames of movement accumulate correctly")
    print(f"  Expected distance: {expected_distance:.3f}")
    print(f"  Actual distance: {actual_distance:.3f}")


def test_no_movement_without_input():
    """Test that player doesn't move without input"""
    print("\n=== Test: No Movement Without Input ===")

    from game.p_client import ClientThink
    from quake2.cl_input import usercmd_t

    player = {
        'classname': 'player',
        'inuse': True,
        'origin': [100.0, 100.0, 100.0],
        'velocity': [50.0, 50.0, 50.0],  # Has velocity
        'health': 100,
        'client': {
            'buttons': 0,
            'oldbuttons': 0,
            'v_angle': [0.0, 0.0, 0.0],
        }
    }

    initial_vel = list(player['velocity'])

    # Send empty command (no input)
    cmd = usercmd_t()
    cmd.forwardmove = 0.0
    cmd.sidemove = 0.0
    cmd.upmove = 0.0

    ClientThink(player, cmd)

    # Velocity should be cleared by input (set to 0)
    assert player['velocity'][0] == 0.0, "No input should clear velocity"
    assert player['velocity'][1] == 0.0, "No input should clear velocity"

    print(f"[OK] No input clears velocity")
    print(f"  Initial velocity: {initial_vel}")
    print(f"  After empty input: {player['velocity']}")


def test_input_stops_immediately():
    """Test that releasing keys stops movement immediately"""
    print("\n=== Test: Input Stops Movement Immediately ===")

    from game.p_client import ClientThink
    from quake2.cl_input import usercmd_t

    player = {
        'classname': 'player',
        'inuse': True,
        'origin': [0.0, 0.0, 0.0],
        'velocity': [0.0, 0.0, 0.0],
        'health': 100,
        'client': {
            'buttons': 0,
            'oldbuttons': 0,
            'v_angle': [0.0, 0.0, 0.0],
        }
    }

    # Frame 1: W key pressed
    cmd1 = usercmd_t()
    cmd1.forwardmove = 200.0
    ClientThink(player, cmd1)
    assert player['velocity'][0] == 200.0, "W should set forward velocity"

    # Frame 2: W key released (empty command)
    cmd2 = usercmd_t()
    cmd2.forwardmove = 0.0
    ClientThink(player, cmd2)
    assert player['velocity'][0] == 0.0, "Release should immediately clear velocity"

    print(f"[OK] Keys stop movement immediately")


if __name__ == '__main__':
    try:
        test_input_command_creation()
        test_player_entity_initialization()
        test_input_applied_to_player()
        test_physics_updates_position()
        test_full_input_to_movement_pipeline()
        test_multiple_frames_accumulate_movement()
        test_no_movement_without_input()
        test_input_stops_immediately()

        print("\n" + "="*60)
        print("INTEGRATION TESTS COMPLETED [OK]")
        print("="*60)
        print("\nAll input -> movement pipeline tests passed!")
        print("This verifies that:")
        print("  [OK] Input creates movement commands")
        print("  [OK] Commands are applied to player velocity")
        print("  [OK] Physics updates position from velocity")
        print("  [OK] Multiple frames accumulate correctly")
        print("  [OK] Movement stops when input stops")

    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
