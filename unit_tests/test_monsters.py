"""Tests for client-side monster spawning (quake2/cl_monsters.py)."""

from quake2 import cl_monsters

SAMPLE_ENTITY_STRING = '''
{
"classname" "worldspawn"
"message" "Test Map"
}
{
"classname" "monster_soldier"
"origin" "100 200 24"
"angle" "90"
}
{
"classname" "monster_infantry"
"origin" "-50 0 24"
"angle" "180"
"spawnflags" "512"
}
{
"classname" "monster_tank_commander"
"origin" "300 300 32"
}
{
"classname" "info_player_start"
"origin" "0 0 24"
}
'''


def test_parse_entities_reads_all_blocks():
    entities = cl_monsters.parse_entities(SAMPLE_ENTITY_STRING)
    assert len(entities) == 5
    assert entities[0]['classname'] == 'worldspawn'
    assert entities[1]['origin'] == '100 200 24'


def test_spawn_monsters_at_map_locations():
    entities = cl_monsters.parse_entities(SAMPLE_ENTITY_STRING)
    monsters = cl_monsters._spawn_from_entities(entities)

    # infantry has NOT_MEDIUM spawnflag and is skipped; non-monsters ignored
    assert [m['classname'] for m in monsters] == ['monster_soldier', 'monster_tank_commander']

    soldier = monsters[0]
    assert soldier['origin'] == [100.0, 200.0, 24.0]
    assert soldier['yaw'] == 90.0
    assert soldier['model_path'] == "models/monsters/soldier/tris.md2"
    assert soldier['skin'] == 2
    assert soldier['health'] == 30
    assert soldier['state'] == 'alive'

    commander = monsters[1]
    assert commander['origin'] == [300.0, 300.0, 32.0]
    assert commander['yaw'] == 0.0
    assert commander['model_path'] == "models/monsters/tank/tris.md2"
    assert commander['skin'] == 2
    assert commander['health'] == 1000
    assert commander['maxs'][2] == 72.0


def test_all_monster_definitions_are_complete():
    assert len(cl_monsters.MONSTERS) == 23
    for classname, (model_path, skin) in cl_monsters.MONSTERS.items():
        assert classname.startswith('monster_')
        assert model_path.startswith("models/monsters/")
        assert model_path.endswith("tris.md2")
        assert skin >= 0


def test_stand_range_finds_consecutive_stand_frames():
    class Frame:
        def __init__(self, name):
            self.name = name

    class Model:
        mesh_data = {'frames': [Frame('attak101'), Frame('stand01'), Frame('stand02'),
                                Frame('stand03'), Frame('walk01'), Frame('stand99')]}

    cl_monsters._MonsterState.stand_ranges = {}
    first, count = cl_monsters._stand_range("test/model", Model())
    assert first == 1
    assert count == 3


def test_stand_range_defaults_to_frame_zero():
    class Frame:
        def __init__(self, name):
            self.name = name

    class Model:
        mesh_data = {'frames': [Frame('attak101'), Frame('walk01')]}

    cl_monsters._MonsterState.stand_ranges = {}
    first, count = cl_monsters._stand_range("test/model2", Model())
    assert first == 0
    assert count == 1

def _make_monster(classname='monster_soldier', origin=(0.0, 0.0, 0.0)):
    entities = [{'classname': classname, 'origin': ' '.join(str(c) for c in origin)}]
    return cl_monsters._spawn_from_entities(entities)[0]


def test_damage_segment_hits_and_kills(monkeypatch):
    soldier = _make_monster(origin=(100.0, 0.0, 0.0))
    monkeypatch.setattr(cl_monsters._MonsterState, "monsters", [soldier])

    # Shot passing left of the monster misses
    assert cl_monsters.DamageSegment([0.0, 50.0, 0.0], [200.0, 50.0, 0.0], 15, now=5.0) is None
    assert soldier['health'] == 30

    # Direct hit damages
    hit = cl_monsters.DamageSegment([0.0, 0.0, 0.0], [200.0, 0.0, 0.0], 15, now=5.0)
    assert hit is not None
    t, monster = hit
    assert monster is soldier
    assert 0.4 < t < 0.5  # box front face at x=84 of a 200-unit shot
    assert soldier['health'] == 15
    assert soldier['state'] == 'alive'

    # Second hit kills and starts the death animation
    cl_monsters.DamageSegment([0.0, 0.0, 0.0], [200.0, 0.0, 0.0], 15, now=6.0)
    assert soldier['state'] == 'dying'
    assert soldier['death_start'] == 6.0

    # Corpses don't block shots
    assert cl_monsters.DamageSegment([0.0, 0.0, 0.0], [200.0, 0.0, 0.0], 15, now=7.0) is None


def test_splash_damage_falls_off_with_distance(monkeypatch):
    near = _make_monster(origin=(50.0, 0.0, 0.0))
    far = _make_monster(origin=(500.0, 0.0, 0.0))
    monkeypatch.setattr(cl_monsters._MonsterState, "monsters", [near, far])

    cl_monsters.SplashDamage([0.0, 0.0, 0.0], 120, 120.0, now=5.0)

    assert near['health'] < 30       # 120 * (1 - 50/120) = 70 damage -> dead
    assert near['state'] == 'dying'
    assert far['health'] == 30       # out of radius


def test_death_animation_plays_then_holds_last_frame(monkeypatch):
    class Frame:
        def __init__(self, name):
            self.name = name

    class Model:
        mesh_data = {'frames': [Frame('stand01'), Frame('death101'),
                                Frame('death102'), Frame('death103')]}

    soldier = _make_monster()
    soldier['state'] = 'dying'
    soldier['death_start'] = 10.0
    cl_monsters._MonsterState.anim_ranges = {}

    model = Model()
    assert cl_monsters._monster_frame(soldier, model, 0, 10.0) == 1
    assert cl_monsters._monster_frame(soldier, model, 0, 10.25) == 3
    # Past the end: corpse holds the last death frame
    assert cl_monsters._monster_frame(soldier, model, 0, 12.0) == 3
    assert soldier['state'] == 'dead'


def test_projectile_monster_fires_its_own_bolt(monkeypatch):
    # A blaster monster (soldier_light) spawns a travelling bolt with its model
    flyer = _make_monster(classname='monster_soldier_light', origin=(200.0, 0.0, 0.0))
    flyer['yaw'] = 180.0  # already facing the player at the origin
    flyer['next_attack'] = 0.0
    monkeypatch.setattr(cl_monsters._MonsterState, "monsters", [flyer])
    monkeypatch.setattr(cl_monsters._MonsterState, "bolts", [])
    monkeypatch.setattr(cl_monsters, "_visible", lambda _s, _e: True)
    monkeypatch.setattr(cl_monsters, "_play_sound", lambda _p: None)

    cl_monsters._update_ai(0.016, [0.0, 0.0, 22.0], now=10.0)

    assert len(cl_monsters._MonsterState.bolts) == 1
    bolt = cl_monsters._MonsterState.bolts[0]
    assert bolt['velocity'][0] < 0  # flying toward the player (-x)
    assert bolt['model'] == cl_monsters.MONSTER_WEAPONS['blaster']['model']
    assert bolt['damage'] == cl_monsters.MONSTER_WEAPONS['blaster']['damage']
    assert flyer['attack_start'] == 10.0
    assert flyer['next_attack'] > 10.0


def test_each_monster_uses_its_own_weapon():
    # Weapon assignment matches the original monster attack code
    def weapon_of(classname):
        return cl_monsters._spawn_from_entities(
            [{'classname': classname, 'origin': '0 0 0'}])[0]['weapon']

    assert weapon_of('monster_soldier') == 'shotgun'
    assert weapon_of('monster_soldier_ss') == 'machinegun'
    assert weapon_of('monster_gladiator') == 'railgun'
    assert weapon_of('monster_chick') == 'rocket'
    assert weapon_of('monster_gunner') == 'grenade'
    assert weapon_of('monster_berserk') == 'melee'
    # Every weapon type referenced by a monster is defined
    for classname in cl_monsters.MONSTERS:
        weapon = cl_monsters.MONSTER_WEAPON_BY_CLASS.get(
            classname, cl_monsters.DEFAULT_MONSTER_WEAPON)
        assert weapon in cl_monsters.MONSTER_WEAPONS


def test_hitscan_monster_damages_aligned_player(monkeypatch):
    # A shotgun soldier's instant pellets hit a player directly in front
    soldier = _make_monster(classname='monster_soldier', origin=(120.0, 0.0, 0.0))
    soldier['yaw'] = 180.0
    soldier['next_attack'] = 0.0
    monkeypatch.setattr(cl_monsters._MonsterState, "monsters", [soldier])
    monkeypatch.setattr(cl_monsters._MonsterState, "bolts", [])
    monkeypatch.setattr(cl_monsters, "_visible", lambda _s, _e: True)
    monkeypatch.setattr(cl_monsters, "_trace", lambda _s, _e: None)  # no wall
    monkeypatch.setattr(cl_monsters, "_play_sound", lambda _p: None)
    monkeypatch.setattr(cl_monsters.PlayerState, "health", 100)

    cl_monsters._update_ai(0.016, [0.0, 0.0, 22.0], now=10.0)

    assert cl_monsters._MonsterState.bolts == []   # hitscan, no projectile
    assert cl_monsters.PlayerState.health < 100    # pellets landed


def test_melee_monster_strikes_at_close_range(monkeypatch):
    close = _make_monster(classname='monster_berserk', origin=(40.0, 0.0, 0.0))
    close['yaw'] = 180.0
    close['next_attack'] = 0.0
    monkeypatch.setattr(cl_monsters._MonsterState, "monsters", [close])
    monkeypatch.setattr(cl_monsters._MonsterState, "bolts", [])
    monkeypatch.setattr(cl_monsters, "_visible", lambda _s, _e: True)
    monkeypatch.setattr(cl_monsters, "_box_trace", lambda _s, _e, _mi, _ma: None)
    monkeypatch.setattr(cl_monsters, "_play_sound", lambda _p: None)
    monkeypatch.setattr(cl_monsters.PlayerState, "health", 100)

    cl_monsters._update_ai(0.1, [0.0, 0.0, 22.0], now=10.0)

    assert cl_monsters._MonsterState.bolts == []  # melee: no projectile
    assert cl_monsters.PlayerState.health == 100 - cl_monsters.MONSTER_WEAPONS['melee']['damage']


def test_melee_monster_out_of_range_does_not_strike(monkeypatch):
    far = _make_monster(classname='monster_berserk', origin=(400.0, 0.0, 0.0))
    far['yaw'] = 180.0
    far['next_attack'] = 0.0
    monkeypatch.setattr(cl_monsters._MonsterState, "monsters", [far])
    monkeypatch.setattr(cl_monsters._MonsterState, "bolts", [])
    monkeypatch.setattr(cl_monsters, "_visible", lambda _s, _e: True)
    monkeypatch.setattr(cl_monsters, "_box_trace", lambda _s, _e, _mi, _ma: None)
    monkeypatch.setattr(cl_monsters, "_play_sound", lambda _p: None)
    monkeypatch.setattr(cl_monsters.PlayerState, "health", 100)

    cl_monsters._update_ai(0.1, [0.0, 0.0, 22.0], now=10.0)

    assert cl_monsters.PlayerState.health == 100  # too far to melee


def test_monster_holds_fire_without_line_of_sight(monkeypatch):
    soldier = _make_monster(origin=(200.0, 0.0, 0.0))
    soldier['next_attack'] = 0.0
    monkeypatch.setattr(cl_monsters._MonsterState, "monsters", [soldier])
    monkeypatch.setattr(cl_monsters._MonsterState, "bolts", [])
    monkeypatch.setattr(cl_monsters, "_visible", lambda _s, _e: False)

    cl_monsters._update_ai(0.016, [0.0, 0.0, 22.0], now=10.0)

    assert cl_monsters._MonsterState.bolts == []


def test_monster_bolt_damages_player_and_respawns(monkeypatch):
    monkeypatch.setattr(cl_monsters._MonsterState, "monsters", [])
    monkeypatch.setattr(cl_monsters, "_trace", lambda _s, _e: None)
    monkeypatch.setattr(cl_monsters, "_play_sound", lambda _p: None)
    monkeypatch.setattr(cl_monsters.PlayerState, "health", 100)
    monkeypatch.setattr(cl_monsters.PlayerState, "respawn_requested", False)

    # Bolt heading into the player box at the origin
    monkeypatch.setattr(cl_monsters._MonsterState, "bolts", [{
        'origin': [40.0, 0.0, 0.0],
        'velocity': [-600.0, 0.0, 0.0],
        'expire': 99.0,
    }])
    cl_monsters._update_bolts(0.1, [0.0, 0.0, 0.0], now=10.0)

    assert cl_monsters.PlayerState.health == 100 - cl_monsters.MONSTER_BOLT_DAMAGE
    assert cl_monsters._MonsterState.bolts == []

    # Enough hits kill and request a respawn
    monkeypatch.setattr(cl_monsters.PlayerState, "health", cl_monsters.MONSTER_BOLT_DAMAGE)
    monkeypatch.setattr(cl_monsters._MonsterState, "bolts", [{
        'origin': [40.0, 0.0, 0.0],
        'velocity': [-600.0, 0.0, 0.0],
        'expire': 99.0,
    }])
    cl_monsters._update_bolts(0.1, [0.0, 0.0, 0.0], now=10.0)

    assert cl_monsters.PlayerState.respawn_requested is True
    assert cl_monsters.PlayerState.health == 100


def test_exploding_bolt_splashes_player_and_shows_effect(monkeypatch):
    from quake2 import cl_weapon
    monkeypatch.setattr(cl_monsters._MonsterState, "monsters", [])
    monkeypatch.setattr(cl_monsters, "_trace", lambda _s, _e: None)  # no wall
    monkeypatch.setattr(cl_monsters, "_play_sound", lambda _p: None)
    monkeypatch.setattr(cl_monsters.PlayerState, "health", 100)

    effects = []
    monkeypatch.setattr(cl_weapon, "spawn_explosion",
                        lambda origin, model=None, sound=None, now=None: effects.append(origin))

    rocket = dict(cl_monsters.MONSTER_WEAPONS['rocket'])
    # Rocket heading straight into the player box at the origin
    monkeypatch.setattr(cl_monsters._MonsterState, "bolts", [{
        'origin': [40.0, 0.0, 0.0],
        'velocity': [-500.0, 0.0, 0.0],
        'expire': 99.0,
        'model': rocket['model'], 'damage': rocket['damage'], 'gravity': False,
        'explode': True, 'impact_model': rocket['impact_model'],
        'impact_sound': rocket['impact_sound'], 'splash_radius': rocket['splash_radius'],
    }])
    cl_monsters._update_bolts(0.1, [0.0, 0.0, 0.0], now=10.0)

    assert cl_monsters.PlayerState.health < 100  # splash damage applied
    assert len(effects) == 1                     # explosion effect spawned
    assert cl_monsters._MonsterState.bolts == []  # rocket consumed


def test_monster_chases_distant_player(monkeypatch):
    soldier = _make_monster(origin=(400.0, 0.0, 0.0))
    soldier['yaw'] = 180.0  # facing the player at the origin
    soldier['next_attack'] = 99999.0
    monkeypatch.setattr(cl_monsters._MonsterState, "monsters", [soldier])
    monkeypatch.setattr(cl_monsters, "_visible", lambda _s, _e: True)
    monkeypatch.setattr(cl_monsters, "_box_trace", lambda _s, _e, _mi, _ma: None)

    cl_monsters._update_ai(0.1, [0.0, 0.0, 22.0], now=10.0)

    assert soldier['moving'] is True
    assert soldier['origin'][0] == 400.0 - cl_monsters.MOVE_SPEED * 0.1


def test_monster_holds_position_in_firing_range(monkeypatch):
    soldier = _make_monster(origin=(100.0, 0.0, 0.0))  # inside STOP_RANGE
    soldier['yaw'] = 180.0
    soldier['next_attack'] = 99999.0
    monkeypatch.setattr(cl_monsters._MonsterState, "monsters", [soldier])
    monkeypatch.setattr(cl_monsters, "_visible", lambda _s, _e: True)
    monkeypatch.setattr(cl_monsters, "_box_trace", lambda _s, _e, _mi, _ma: None)

    cl_monsters._update_ai(0.1, [0.0, 0.0, 22.0], now=10.0)

    assert soldier['moving'] is False
    assert soldier['origin'] == [100.0, 0.0, 0.0]


def test_walk_blocked_by_wall_does_not_pass_through(monkeypatch):
    soldier = _make_monster(origin=(400.0, 0.0, 0.0))
    soldier['yaw'] = 180.0

    class Blocked:
        fraction = 0.0
        startsolid = False
        endpos = [400.0, 0.0, 0.0]

    # Both the direct and the stepped-up move are blocked
    monkeypatch.setattr(cl_monsters, "_box_trace",
                        lambda _s, _e, _mi, _ma: Blocked())

    cl_monsters._walk_monster(soldier, 0.1)

    assert soldier['origin'][0] == 400.0


def test_walk_steps_up_stairs(monkeypatch):
    soldier = _make_monster(origin=(400.0, 0.0, 0.0))
    soldier['yaw'] = 180.0

    class Blocked:
        fraction = 0.0
        startsolid = False
        endpos = [400.0, 0.0, 0.0]

    class Clear:
        fraction = 1.0
        startsolid = False

    calls = []

    def fake_trace(start, _end, _mi, _ma):
        calls.append(list(start))
        if len(calls) == 1:
            return Blocked()  # direct move hits the step
        if len(calls) == 2:
            return Clear()    # lifted move is clear
        return None           # no floor found below (keep lifted height)

    monkeypatch.setattr(cl_monsters, "_box_trace", fake_trace)

    cl_monsters._walk_monster(soldier, 0.1)

    assert soldier['origin'][0] == 400.0 - cl_monsters.MOVE_SPEED * 0.1
    assert soldier['origin'][2] == cl_monsters.STEP_HEIGHT


def test_running_monster_uses_run_animation(monkeypatch):
    class Frame:
        def __init__(self, name):
            self.name = name

    class Model:
        mesh_data = {'frames': [Frame('stand01'), Frame('stand02'),
                                Frame('run01'), Frame('run02'), Frame('run03')]}

    soldier = _make_monster()
    soldier['moving'] = True
    cl_monsters._MonsterState.anim_ranges = {}

    frame = cl_monsters._monster_frame(soldier, Model(), 0, 10.0)
    assert 2 <= frame <= 4  # inside the run01..run03 range


def test_overkill_gibs_instead_of_death_animation(monkeypatch):
    soldier = _make_monster(origin=(100.0, 0.0, 0.0))  # 30 hp
    monkeypatch.setattr(cl_monsters._MonsterState, "monsters", [soldier])
    monkeypatch.setattr(cl_monsters._MonsterState, "gibs", [])
    monkeypatch.setattr(cl_monsters, "_play_sound", lambda _p: None)

    # Railgun-class hit: 30 - 100 = -70, past GIB_HEALTH (-40)
    cl_monsters.DamageSegment([0.0, 0.0, 0.0], [200.0, 0.0, 0.0], 100, now=5.0)

    assert soldier['state'] == 'gibbed'
    assert len(cl_monsters._MonsterState.gibs) == len(cl_monsters.GIB_MODELS)
    for gib in cl_monsters._MonsterState.gibs:
        assert gib['velocity'][2] > 0  # launched upward
        assert gib['expire'] == 5.0 + cl_monsters.GIB_LIFETIME


def test_normal_kill_still_plays_death_animation(monkeypatch):
    soldier = _make_monster(origin=(100.0, 0.0, 0.0))  # 30 hp
    monkeypatch.setattr(cl_monsters._MonsterState, "monsters", [soldier])
    monkeypatch.setattr(cl_monsters._MonsterState, "gibs", [])
    monkeypatch.setattr(cl_monsters, "_play_sound", lambda _p: None)

    # 30 - 40 = -10: dead but above the gib threshold
    cl_monsters.DamageSegment([0.0, 0.0, 0.0], [200.0, 0.0, 0.0], 40, now=5.0)

    assert soldier['state'] == 'dying'
    assert cl_monsters._MonsterState.gibs == []


def test_gibs_fall_bounce_and_expire(monkeypatch):
    monkeypatch.setattr(cl_monsters, "_trace", lambda _s, _e: None)
    gib = {
        'origin': [0.0, 0.0, 100.0],
        'velocity': [50.0, 0.0, 0.0],
        'model': cl_monsters.GIB_MODELS[0],
        'expire': 20.0,
        'spawn': 5.0,
        'avelocity': [100.0, 100.0],
        'resting': False,
    }
    monkeypatch.setattr(cl_monsters._MonsterState, "gibs", [gib])

    cl_monsters._update_gibs(0.1, now=5.1)
    assert gib['velocity'][2] < 0  # gravity pulls it down
    assert gib['origin'][0] > 0.0

    # Floor hit: bounce keeps a fraction of the speed, then rests when slow
    class Floor:
        fraction = 0.5
        startsolid = False
        endpos = [1.0, 0.0, 24.0]

    gib['velocity'] = [10.0, 0.0, -50.0]
    monkeypatch.setattr(cl_monsters, "_trace", lambda _s, _e: Floor())
    for _ in range(10):  # each bounce sheds energy until the gib rests
        cl_monsters._update_gibs(0.1, now=5.2)
        if gib['resting']:
            break
    assert gib['resting'] is True
    assert gib['velocity'] == [0.0, 0.0, 0.0]

    # Expiry removes it
    cl_monsters._update_gibs(0.1, now=25.0)
    assert cl_monsters._MonsterState.gibs == []


def test_gibbed_monster_is_not_rendered(monkeypatch):
    soldier = _make_monster(origin=(100.0, 0.0, 0.0))
    soldier['state'] = 'gibbed'
    monkeypatch.setattr(cl_monsters._MonsterState, "monsters", [soldier])
    monkeypatch.setattr(cl_monsters._MonsterState, "gibs", [])
    monkeypatch.setattr(cl_monsters._MonsterState, "bolts", [])
    monkeypatch.setattr(cl_monsters, "_get_model", lambda _p: None)

    entities = cl_monsters.Update(0.016, [0.0, 0.0, 0.0], now=10.0)

    assert entities == []
