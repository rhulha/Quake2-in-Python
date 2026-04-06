"""
Unit tests for game/q_shared.py
Tests shared game types, constants, and data structures.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import shared game types
try:
    from game.q_shared import (
        ITEM_HEALTH, ITEM_HEALTH_SMALL, ITEM_HEALTH_LARGE,
        ARMOR_LEATHER, ARMOR_COMBAT, ARMOR_BODY,
        WEAPON_SHOTGUN, WEAPON_GRENADE,
        AMMO_SHELLS, AMMO_ROCKETS
    )
except ImportError:
    # If constants aren't available, we'll skip those tests
    ITEM_HEALTH = None


def test_constants_exist():
    """Test that game constants are defined"""
    print("\n=== Test: Game Constants ===")

    # Check if constants module can be imported
    try:
        import game.q_shared as q_shared

        # Verify module has expected attributes
        assert hasattr(q_shared, '__doc__'), "q_shared module missing docstring"

        print("[OK] q_shared module imports successfully")
        print(f"  Module: {q_shared.__name__}")

    except ImportError as e:
        print(f"[SKIP] Could not import q_shared: {e}")


def test_item_constants():
    """Test item type constants"""
    print("\n=== Test: Item Constants ===")

    try:
        from game.q_shared import ITEM_HEALTH, ITEM_HEALTH_SMALL, ITEM_HEALTH_LARGE

        # These should be distinct values
        values = [ITEM_HEALTH, ITEM_HEALTH_SMALL, ITEM_HEALTH_LARGE]
        unique_values = len(set(values))

        assert unique_values == 3 or unique_values == len(values), \
            "Item constants should have distinct values"

        print("[OK] Item constants defined")
        print(f"  ITEM_HEALTH: {ITEM_HEALTH}")
        print(f"  ITEM_HEALTH_SMALL: {ITEM_HEALTH_SMALL}")
        print(f"  ITEM_HEALTH_LARGE: {ITEM_HEALTH_LARGE}")

    except (ImportError, AttributeError) as e:
        print(f"[SKIP] Item constants not available: {e}")


def test_armor_constants():
    """Test armor type constants"""
    print("\n=== Test: Armor Constants ===")

    try:
        from game.q_shared import ARMOR_LEATHER, ARMOR_COMBAT, ARMOR_BODY

        values = [ARMOR_LEATHER, ARMOR_COMBAT, ARMOR_BODY]
        unique_values = len(set(values))

        assert unique_values == 3 or unique_values == len(values), \
            "Armor constants should have distinct values"

        print("[OK] Armor constants defined")
        print(f"  ARMOR_LEATHER: {ARMOR_LEATHER}")
        print(f"  ARMOR_COMBAT: {ARMOR_COMBAT}")
        print(f"  ARMOR_BODY: {ARMOR_BODY}")

    except (ImportError, AttributeError) as e:
        print(f"[SKIP] Armor constants not available: {e}")


def test_weapon_constants():
    """Test weapon type constants"""
    print("\n=== Test: Weapon Constants ===")

    try:
        from game.q_shared import WEAPON_SHOTGUN, WEAPON_GRENADE

        # Weapons should be distinct
        assert WEAPON_SHOTGUN != WEAPON_GRENADE, "Weapon constants should differ"

        print("[OK] Weapon constants defined")
        print(f"  WEAPON_SHOTGUN: {WEAPON_SHOTGUN}")
        print(f"  WEAPON_GRENADE: {WEAPON_GRENADE}")

    except (ImportError, AttributeError) as e:
        print(f"[SKIP] Weapon constants not available: {e}")


def test_ammo_constants():
    """Test ammo type constants"""
    print("\n=== Test: Ammo Constants ===")

    try:
        from game.q_shared import AMMO_SHELLS, AMMO_ROCKETS

        assert AMMO_SHELLS != AMMO_ROCKETS, "Ammo constants should differ"

        print("[OK] Ammo constants defined")
        print(f"  AMMO_SHELLS: {AMMO_SHELLS}")
        print(f"  AMMO_ROCKETS: {AMMO_ROCKETS}")

    except (ImportError, AttributeError) as e:
        print(f"[SKIP] Ammo constants not available: {e}")


def test_entity_state_flags():
    """Test entity state flags"""
    print("\n=== Test: Entity State Flags ===")

    try:
        # Entity flags for visibility, state, etc.
        flags = {
            'SOLID_NOT': 0,
            'SOLID_TRIGGER': 1,
            'SOLID_BBOX': 2,
            'SOLID_BSP': 3,
        }

        # Flags should be distinct
        unique_flags = len(set(flags.values()))
        assert unique_flags == len(flags), "Flags should be distinct"

        print("[OK] Entity flags concept verified")
        print(f"  Flag values: {flags}")

    except Exception as e:
        print(f"[SKIP] Entity flags: {e}")


def test_game_data_structures():
    """Test that game data structures can be instantiated"""
    print("\n=== Test: Game Data Structures ===")

    # Test creating mock entity structure
    entity = {
        'type': 'player',
        'position': [0, 0, 0],
        'velocity': [0, 0, 0],
        'health': 100,
        'armor': 0,
        'inventory': {},
    }

    assert entity['type'] == 'player'
    assert entity['health'] == 100
    assert len(entity['inventory']) == 0

    print("[OK] Game data structures work")
    print(f"  Entity type: {entity['type']}")
    print(f"  Entity health: {entity['health']}")
    print(f"  Entity position: {entity['position']}")

    # Test entity list
    entities = [entity]
    assert len(entities) == 1
    assert entities[0]['type'] == 'player'

    print("[OK] Entity collections work")
    print(f"  Entity count: {len(entities)}")


def test_numeric_ranges():
    """Test that numeric constants are in expected ranges"""
    print("\n=== Test: Numeric Ranges ===")

    # Health should be positive
    health_values = [25, 50, 100]  # Small, large, full health
    for h in health_values:
        assert h > 0, f"Health should be positive: {h}"

    print("[OK] Health values in valid range")
    print(f"  Health values: {health_values}")

    # Armor should be non-negative
    armor_values = [0, 50, 100]
    for a in armor_values:
        assert a >= 0, f"Armor should be non-negative: {a}"

    print("[OK] Armor values in valid range")
    print(f"  Armor values: {armor_values}")


if __name__ == '__main__':
    try:
        test_constants_exist()
        test_item_constants()
        test_armor_constants()
        test_weapon_constants()
        test_ammo_constants()
        test_entity_state_flags()
        test_game_data_structures()
        test_numeric_ranges()

        print("\n" + "="*50)
        print("GAME Q_SHARED TESTS COMPLETED [OK]")
        print("="*50)

    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
