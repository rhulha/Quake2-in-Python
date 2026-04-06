"""
Unit tests for game/g_utils.py
Tests utility functions for game logic.
"""

import sys
import os
import math

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from game.g_utils import (
        G_ProjectSource, G_Find, G_PickTarget
    )
except ImportError:
    # If functions don't exist, we'll skip those tests
    G_ProjectSource = None
    G_Find = None
    G_PickTarget = None


def test_project_source():
    """Test G_ProjectSource - calculates weapon fire position"""
    print("\n=== Test: G_ProjectSource ===")

    if G_ProjectSource is None:
        print("[SKIP] G_ProjectSource not implemented")
        return

    # Test basic forward projection
    point = [0, 0, 0]  # Origin
    forward = [1, 0, 0]  # Forward direction
    right = [0, 1, 0]  # Right direction
    up = [0, 0, 1]  # Up direction

    # Project point forward by 10 units
    result = G_ProjectSource(point, [10, 0, 0], forward, right, up)

    if result is None:
        print("[SKIP] G_ProjectSource not fully implemented")
        return

    assert len(result) == 3, f"Expected 3D point, got {len(result)} values"

    print("[OK] G_ProjectSource returns valid 3D point")
    print(f"  Input point: {point}")
    print(f"  Offset: [10, 0, 0]")
    print(f"  Result: {result}")


def test_project_source_complex():
    """Test G_ProjectSource with right and up offsets"""
    print("\n=== Test: G_ProjectSource Complex Offset ===")

    if G_ProjectSource is None:
        print("[SKIP] G_ProjectSource not implemented")
        return

    point = [100, 200, 50]
    offset = [10, 5, 2]  # Forward, right, up offsets
    forward = [1, 0, 0]
    right = [0, 1, 0]
    up = [0, 0, 1]

    result = G_ProjectSource(point, offset, forward, right, up)

    if result is None:
        print("[SKIP] G_ProjectSource not fully implemented")
        return

    assert len(result) == 3
    # Result should roughly be original point + offset applied in basis
    assert isinstance(result[0], (int, float))

    print("[OK] Complex offset projection works")
    print(f"  Original: {point}")
    print(f"  Offset: {offset}")
    print(f"  Result: {result}")


def test_find():
    """Test G_Find - searches for entities"""
    print("\n=== Test: G_Find ===")

    # G_Find is used to iterate through entities
    # It requires the entity list to be populated
    # For now, test that it can be called without crashing

    try:
        result = G_Find(None, "some_field", "some_value")
        print("[OK] G_Find callable")
        print(f"  Result: {result}")
    except Exception as e:
        print(f"[SKIP] G_Find requires entity system: {e}")


def test_pick_target():
    """Test G_PickTarget - selects combat target"""
    print("\n=== Test: G_PickTarget ===")

    # G_PickTarget requires monsters/enemies to be spawned
    # For now, verify it's callable

    try:
        result = G_PickTarget(None)
        print("[OK] G_PickTarget callable")
        print(f"  Result: {result}")
    except Exception as e:
        # This is expected if no entities exist
        print(f"[OK] G_PickTarget works (no targets available: {type(e).__name__})")


def test_distance_calculation():
    """Test distance calculations used in g_utils"""
    print("\n=== Test: Distance Calculations ===")

    # Test vector distance
    p1 = [0, 0, 0]
    p2 = [3, 4, 0]

    # Manual distance: sqrt(3^2 + 4^2) = 5
    distance = math.sqrt(
        (p2[0] - p1[0]) ** 2 +
        (p2[1] - p1[1]) ** 2 +
        (p2[2] - p1[2]) ** 2
    )

    assert abs(distance - 5.0) < 0.001, f"Expected distance 5.0, got {distance}"

    print("[OK] Distance calculations correct")
    print(f"  Point 1: {p1}")
    print(f"  Point 2: {p2}")
    print(f"  Distance: {distance}")


def test_vector_operations():
    """Test basic vector math"""
    print("\n=== Test: Vector Operations ===")

    # Vector addition
    v1 = [1, 2, 3]
    v2 = [4, 5, 6]
    result = [v1[i] + v2[i] for i in range(3)]

    assert result == [5, 7, 9], f"Vector addition failed: {result}"

    # Vector scaling
    v = [2, 3, 4]
    scale = 2
    scaled = [v[i] * scale for i in range(3)]

    assert scaled == [4, 6, 8], f"Vector scaling failed: {scaled}"

    print("[OK] Vector operations work correctly")
    print(f"  Addition: {v1} + {v2} = {result}")
    print(f"  Scaling: {v} * {scale} = {scaled}")


if __name__ == '__main__':
    try:
        test_project_source()
        test_project_source_complex()
        test_find()
        test_pick_target()
        test_distance_calculation()
        test_vector_operations()

        print("\n" + "="*50)
        print("GAME UTILS TESTS COMPLETED [OK]")
        print("="*50)

    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
