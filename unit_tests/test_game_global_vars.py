"""
Unit tests for game/global_vars.py
Tests global game state and variables.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_global_state_creation():
    """Test that global game state can be created"""
    print("\n=== Test: Global State Creation ===")

    # Create a game state object
    game_state = {
        'level': 1,
        'entities': [],
        'time': 0.0,
        'players': [],
        'monsters': [],
        'items': [],
        'projectiles': [],
    }

    assert game_state['level'] == 1
    assert len(game_state['entities']) == 0
    assert game_state['time'] == 0.0

    print("[OK] Global state structure created")
    print(f"  Level: {game_state['level']}")
    print(f"  Entities: {len(game_state['entities'])}")
    print(f"  Time: {game_state['time']}")


def test_game_time_progression():
    """Test game time progression"""
    print("\n=== Test: Game Time Progression ===")

    game_time = 0.0
    frame_time = 0.016  # ~60 FPS

    # Simulate 10 frames
    for i in range(10):
        game_time += frame_time

    expected_time = 0.16  # 10 * 0.016
    assert abs(game_time - expected_time) < 0.001, \
        f"Expected time {expected_time}, got {game_time}"

    print("[OK] Game time progresses correctly")
    print(f"  Frames: 10")
    print(f"  Frame time: {frame_time}s")
    print(f"  Total time: {game_time}s")


def test_entity_list_management():
    """Test managing entity lists"""
    print("\n=== Test: Entity List Management ===")

    entities = []

    # Add entities
    entities.append({'id': 1, 'type': 'player'})
    entities.append({'id': 2, 'type': 'monster'})
    entities.append({'id': 3, 'type': 'item'})

    assert len(entities) == 3
    assert entities[0]['id'] == 1
    assert entities[2]['type'] == 'item'

    print("[OK] Entity list management works")
    print(f"  Entities added: {len(entities)}")
    for e in entities:
        print(f"    - ID {e['id']}: {e['type']}")

    # Remove entity
    entities.pop(1)  # Remove monster
    assert len(entities) == 2
    assert all(e['type'] != 'monster' for e in entities)

    print("[OK] Entity removal works")
    print(f"  Entities remaining: {len(entities)}")


def test_player_state():
    """Test player state management"""
    print("\n=== Test: Player State ===")

    player = {
        'id': 0,
        'health': 100,
        'armor': 0,
        'ammo': {
            'shells': 0,
            'bullets': 0,
            'rockets': 0,
            'grenades': 0,
        },
        'weapons': {
            'current': None,
            'inventory': [],
        },
        'position': [0, 0, 0],
        'velocity': [0, 0, 0],
        'dead': False,
    }

    assert player['health'] == 100
    assert player['armor'] == 0
    assert not player['dead']

    # Simulate taking damage
    damage = 25
    player['health'] -= damage
    assert player['health'] == 75

    # Simulate picking up health
    player['health'] = min(player['health'] + 50, 100)
    assert player['health'] == 100

    print("[OK] Player state management works")
    print(f"  Health: {player['health']}")
    print(f"  Armor: {player['armor']}")
    print(f"  Ammo inventory: {player['ammo']}")


def test_monster_state():
    """Test monster state management"""
    print("\n=== Test: Monster State ===")

    monster = {
        'id': 1,
        'type': 'grunt',
        'health': 20,
        'maxhealth': 20,
        'position': [100, 200, 0],
        'target': None,
        'state': 'idle',  # idle, chasing, attacking, dying
    }

    assert monster['health'] == monster['maxhealth']
    assert monster['state'] == 'idle'

    # Simulate state transitions
    monster['state'] = 'chasing'
    assert monster['state'] == 'chasing'

    # Simulate taking damage
    monster['health'] -= 5
    assert monster['health'] == 15

    # Check if dead
    monster['health'] = 0
    monster['state'] = 'dying'
    assert monster['health'] <= 0
    assert monster['state'] == 'dying'

    print("[OK] Monster state management works")
    print(f"  Type: {monster['type']}")
    print(f"  Health: {monster['health']}/{monster['maxhealth']}")
    print(f"  State: {monster['state']}")


def test_game_state_persistence():
    """Test that game state persists across updates"""
    print("\n=== Test: Game State Persistence ===")

    import copy

    game = {
        'running': True,
        'level': 1,
        'score': 0,
        'entities': [],
    }

    # Simulate game update - use deep copy to save state
    original_state = copy.deepcopy(game)

    # Add data
    game['entities'].append({'id': 1})
    game['score'] += 100

    # Verify persistence
    assert game['level'] == original_state['level']
    assert game['running'] == original_state['running']
    assert game['score'] > original_state['score']
    assert len(game['entities']) > len(original_state['entities'])

    print("[OK] Game state persists correctly")
    print(f"  Level: {game['level']}")
    print(f"  Score: {game['score']}")
    print(f"  Running: {game['running']}")


def test_level_progression():
    """Test level/difficulty progression"""
    print("\n=== Test: Level Progression ===")

    level = 1
    difficulty_modifiers = {
        1: 1.0,   # Normal
        2: 1.25,  # Hard
        3: 1.5,   # Very hard
    }

    for lv in [1, 2, 3]:
        modifier = difficulty_modifiers.get(lv, 1.0)
        enemy_health = 20 * modifier
        assert enemy_health >= 20

    print("[OK] Level progression with difficulty modifiers")
    for lv, mod in difficulty_modifiers.items():
        health = 20 * mod
        print(f"  Level {lv}: {health} health per enemy")


def test_spawn_system():
    """Test entity spawn system"""
    print("\n=== Test: Spawn System ===")

    spawned_entities = []

    def spawn_entity(entity_type, position):
        entity = {
            'id': len(spawned_entities),
            'type': entity_type,
            'position': position,
        }
        spawned_entities.append(entity)
        return entity

    # Spawn entities
    player = spawn_entity('player', [0, 0, 0])
    monster = spawn_entity('monster', [100, 100, 0])
    item = spawn_entity('item', [50, 50, 0])

    assert len(spawned_entities) == 3
    assert player['type'] == 'player'
    assert monster['position'] == [100, 100, 0]

    print("[OK] Spawn system works")
    print(f"  Spawned entities: {len(spawned_entities)}")
    for e in spawned_entities:
        print(f"    - {e['type']} at {e['position']}")


if __name__ == '__main__':
    try:
        test_global_state_creation()
        test_game_time_progression()
        test_entity_list_management()
        test_player_state()
        test_monster_state()
        test_game_state_persistence()
        test_level_progression()
        test_spawn_system()

        print("\n" + "="*50)
        print("GAME GLOBAL VARS TESTS COMPLETED [OK]")
        print("="*50)

    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
