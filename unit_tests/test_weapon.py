"""Tests for client-side weapon logic (quake2/cl_weapon.py)."""

import math
import sys
from types import SimpleNamespace

from quake2 import cl_weapon
from quake2.cl_input import usercmd_t

BLASTER = cl_weapon.WEAPONS[0]


def _reset_state(monkeypatch, weapon_index=0):
    monkeypatch.setattr(cl_weapon._WeaponState, "current", weapon_index)
    monkeypatch.setattr(cl_weapon._WeaponState, "bolts", [])
    monkeypatch.setattr(cl_weapon._WeaponState, "explosions", [])
    monkeypatch.setattr(cl_weapon._WeaponState, "wall_impacts", [])
    monkeypatch.setattr(cl_weapon._WeaponState, "last_fire_time", -1000.0)
    monkeypatch.setattr(cl_weapon._WeaponState, "fire_anim_start", None)
    monkeypatch.setattr(cl_weapon, "_get_model", lambda _path: None)
    monkeypatch.setattr(cl_weapon, "_play_sound", lambda _path: None)
    monkeypatch.setattr(cl_weapon, "_trace", lambda _s, _e: None)


def _attack_cmd():
    cmd = usercmd_t()
    cmd.buttons = cl_weapon.BUTTON_ATTACK
    return cmd


def _update(frametime, now, cmd=None, angles=(0.0, 0.0, 0.0)):
    return cl_weapon.Update(frametime, [0.0, 0.0, 0.0], list(angles), cmd, now=now)


def test_development_audio_is_sixty_percent_quieter(monkeypatch):
    from quake2 import files

    class FakeSound:
        def __init__(self):
            self.volume = None
            self.played = False

        def set_volume(self, volume):
            self.volume = volume

        def play(self):
            self.played = True

    sound = FakeSound()
    mixer = SimpleNamespace(
        get_init=lambda: True,
        init=lambda: None,
        Sound=lambda **_kwargs: sound,
    )
    monkeypatch.setitem(sys.modules, "pygame", SimpleNamespace(mixer=mixer))
    monkeypatch.setattr(files, "FS_LoadFile", lambda _path: (b"wave-data", 9))
    monkeypatch.setattr(cl_weapon._WeaponState, "sounds", {})
    monkeypatch.setattr(cl_weapon._WeaponState, "mixer_ready", False)

    cl_weapon._play_sound("sound/test.wav")

    assert sound.volume == 0.4
    assert sound.played is True


def test_fire_spawns_bolt_along_view_direction(monkeypatch):
    _reset_state(monkeypatch)

    # frametime 0 so the bolt hasn't moved yet and the muzzle offset is checkable
    _update(0.0, 10.0, _attack_cmd())

    assert len(cl_weapon._WeaponState.bolts) == 1
    bolt = cl_weapon._WeaponState.bolts[0]
    # Looking down +X (yaw 0): velocity is straight forward
    assert bolt['velocity'][0] == BLASTER['projectile']['speed']
    assert abs(bolt['velocity'][2]) < 1e-9
    # Muzzle offset: forward 24, right 8 (right = -Y at yaw 0), up -8
    assert math.isclose(bolt['origin'][0], cl_weapon.MUZZLE_FORWARD)
    assert math.isclose(bolt['origin'][1], -cl_weapon.MUZZLE_RIGHT)
    assert math.isclose(bolt['origin'][2], cl_weapon.MUZZLE_UP)


def test_cooldown_blocks_rapid_fire(monkeypatch):
    _reset_state(monkeypatch)

    _update(0.016, 10.0, _attack_cmd())
    _update(0.016, 10.1, _attack_cmd())
    assert len(cl_weapon._WeaponState.bolts) == 1

    _update(0.016, 10.0 + BLASTER['cooldown'], _attack_cmd())
    assert len(cl_weapon._WeaponState.bolts) == 2


def test_bolt_moves_and_expires(monkeypatch):
    _reset_state(monkeypatch)

    _update(0.016, 10.0, _attack_cmd())
    start_x = cl_weapon._WeaponState.bolts[0]['origin'][0]

    _update(0.1, 10.1)
    speed = BLASTER['projectile']['speed']
    assert cl_weapon._WeaponState.bolts[0]['origin'][0] == start_x + speed * 0.1

    _update(0.016, 10.0 + cl_weapon.BOLT_LIFETIME + 0.1)
    assert cl_weapon._WeaponState.bolts == []


def test_bolt_removed_on_world_hit(monkeypatch):
    _reset_state(monkeypatch)

    class HitTrace:
        fraction = 0.5
        startsolid = False

    _update(0.016, 10.0, _attack_cmd())
    monkeypatch.setattr(cl_weapon, "_trace", lambda _s, _e: HitTrace())
    _update(0.016, 10.1)

    assert cl_weapon._WeaponState.bolts == []


def test_rocket_hit_spawns_animated_explosion(monkeypatch):
    _reset_state(monkeypatch, weapon_index=6)
    loaded_models = []
    monkeypatch.setattr(
        cl_weapon, "_get_model",
        lambda path: loaded_models.append(path) or path,
    )

    class HitTrace:
        fraction = 0.5
        startsolid = False
        endpos = [31.0, 4.0, 7.0]

    _update(0.0, 10.0, _attack_cmd())
    monkeypatch.setattr(cl_weapon, "_trace", lambda _s, _e: HitTrace())
    entities = _update(0.1, 10.1)

    assert cl_weapon._WeaponState.bolts == []
    assert len(cl_weapon._WeaponState.explosions) == 1
    explosion = next(e for e in entities if e['model'] == cl_weapon.ROCKET_EXPLOSION_MODEL)
    assert explosion['origin'] == HitTrace.endpos
    assert explosion['frame'] == 1
    assert explosion['oldframe'] == 0
    assert explosion['flags'] & cl_weapon.RF_FULLBRIGHT
    assert cl_weapon.ROCKET_EXPLOSION_MODEL in loaded_models


def test_grenade_bounces_without_exploding(monkeypatch):
    _reset_state(monkeypatch, weapon_index=5)
    played_sounds = []
    monkeypatch.setattr(cl_weapon, "_play_sound", played_sounds.append)

    class HitTrace:
        fraction = 0.25
        startsolid = False
        endpos = [18.0, -6.0, -12.0]
        plane = type("Plane", (), {"normal": [0.0, 0.0, 1.0]})()

    _update(0.0, 10.0, _attack_cmd())
    cl_weapon._WeaponState.bolts[0]['velocity'] = [100.0, 0.0, -200.0]
    monkeypatch.setattr(cl_weapon, "_trace", lambda _s, _e: HitTrace())
    _update(0.1, 10.1)

    assert len(cl_weapon._WeaponState.bolts) == 1
    grenade = cl_weapon._WeaponState.bolts[0]
    assert grenade['origin'] == HitTrace.endpos
    assert grenade['velocity'] == [100.0, 0.0, 140.0]
    assert cl_weapon._WeaponState.explosions == []
    assert played_sounds[-1] == cl_weapon.GRENADE_BOUNCE_SOUND


def test_grenade_fuse_spawns_animated_explosion(monkeypatch):
    _reset_state(monkeypatch, weapon_index=5)
    played_sounds = []
    monkeypatch.setattr(cl_weapon, "_get_model", lambda path: path)
    monkeypatch.setattr(cl_weapon, "_play_sound", played_sounds.append)

    _update(0.0, 10.0, _attack_cmd())
    grenade_origin = list(cl_weapon._WeaponState.bolts[0]['origin'])
    entities = _update(0.0, 10.0 + cl_weapon.GRENADE_FUSE)

    assert cl_weapon._WeaponState.bolts == []
    assert len(cl_weapon._WeaponState.explosions) == 1
    explosion = next(e for e in entities if e['model'] == cl_weapon.ROCKET_EXPLOSION_MODEL)
    assert explosion['origin'] == grenade_origin
    assert explosion['frame'] == 1
    assert explosion['flags'] & cl_weapon.RF_FULLBRIGHT
    assert played_sounds[-1] == cl_weapon.GRENADE_EXPLOSION_SOUND


def test_slow_grenade_rests_on_floor_until_fuse(monkeypatch):
    _reset_state(monkeypatch, weapon_index=5)
    trace_calls = []

    class HitTrace:
        fraction = 0.5
        startsolid = False
        endpos = [10.0, 20.0, 0.0]
        plane = type("Plane", (), {"normal": [0.0, 0.0, 1.0]})()

    _update(0.0, 10.0, _attack_cmd())
    grenade = cl_weapon._WeaponState.bolts[0]
    grenade['velocity'] = [20.0, 0.0, -20.0]
    monkeypatch.setattr(
        cl_weapon, "_trace",
        lambda _s, _e: trace_calls.append((_s, _e)) or HitTrace(),
    )

    _update(0.01, 10.1)
    assert grenade['grounded'] is True
    assert grenade['velocity'] == [0.0, 0.0, 0.0]
    assert len(trace_calls) == 1

    _update(0.1, 10.2)
    assert grenade['origin'] == HitTrace.endpos
    assert len(trace_calls) == 1


def test_blaster_hit_does_not_spawn_explosion(monkeypatch):
    _reset_state(monkeypatch)

    class HitTrace:
        fraction = 0.5
        startsolid = False
        endpos = [1.0, 2.0, 3.0]

    _update(0.0, 10.0, _attack_cmd())
    monkeypatch.setattr(cl_weapon, "_trace", lambda _s, _e: HitTrace())
    _update(0.1, 10.1)

    assert cl_weapon._WeaponState.explosions == []


def test_rocket_explosion_expires(monkeypatch):
    _reset_state(monkeypatch, weapon_index=6)
    monkeypatch.setattr(cl_weapon._WeaponState, "explosions", [{
        'origin': [1.0, 2.0, 3.0],
        'start': 10.0,
        'model': cl_weapon.ROCKET_EXPLOSION_MODEL,
    }])

    _update((cl_weapon.EXPLOSION_FRAMES - 1) / cl_weapon.EXPLOSION_FPS, 11.4)

    assert cl_weapon._WeaponState.explosions == []


def test_fire_animation_frames_then_idle(monkeypatch):
    _reset_state(monkeypatch)

    _update(0.016, 10.0, _attack_cmd())

    assert cl_weapon._gun_frame(BLASTER, 10.0) == BLASTER['fire_first']
    assert cl_weapon._gun_frame(BLASTER, 10.25) == BLASTER['fire_first'] + 2
    after = 10.0 + (BLASTER['fire_last'] - BLASTER['fire_first'] + 1) / cl_weapon.ANIM_FPS + 0.01
    assert cl_weapon._gun_frame(BLASTER, after) == BLASTER['idle']


def test_vector_to_angles_matches_engine_convention():
    # This engine: positive pitch = looking up
    pitch, yaw, roll = cl_weapon._vector_to_angles([0.0, 0.0, 1.0])
    assert math.isclose(pitch, 90.0)

    pitch, yaw, roll = cl_weapon._vector_to_angles([1.0, 1.0, 0.0])
    assert math.isclose(yaw, 45.0)
    assert pitch == 0.0


def test_fire_direction_matches_view_pitch(monkeypatch):
    _reset_state(monkeypatch)

    # Looking up 30 degrees: bolt must climb
    _update(0.0, 10.0, _attack_cmd(), angles=(30.0, 0.0, 0.0))
    bolt = cl_weapon._WeaponState.bolts[0]
    assert bolt['velocity'][2] > 0
    assert math.isclose(bolt['velocity'][2], 1000.0 * math.sin(math.radians(30.0)))

    # And _vector_to_angles round-trips back to the view pitch
    pitch, yaw, _roll = cl_weapon._vector_to_angles(bolt['velocity'])
    assert math.isclose(pitch, 30.0, abs_tol=1e-6)
    assert math.isclose(yaw, 0.0, abs_tol=1e-6)


def test_select_weapon_switches_and_ignores_invalid(monkeypatch):
    _reset_state(monkeypatch)

    cl_weapon.SelectWeapon(6)
    assert cl_weapon.WEAPONS[cl_weapon._WeaponState.current]['name'] == 'Rocket Launcher'

    cl_weapon.SelectWeapon(99)
    assert cl_weapon._WeaponState.current == 6
    cl_weapon.SelectWeapon(-1)
    assert cl_weapon._WeaponState.current == 6


def test_switching_cancels_fire_animation(monkeypatch):
    _reset_state(monkeypatch)

    _update(0.016, 10.0, _attack_cmd())
    assert cl_weapon._WeaponState.fire_anim_start is not None

    cl_weapon.SelectWeapon(1)
    assert cl_weapon._WeaponState.fire_anim_start is None


def test_hitscan_weapon_spawns_no_projectile(monkeypatch):
    _reset_state(monkeypatch, weapon_index=1)  # Shotgun

    _update(0.016, 10.0, _attack_cmd())
    assert cl_weapon._WeaponState.bolts == []
    # But it did fire (cooldown started, animation running)
    assert cl_weapon._WeaponState.last_fire_time == 10.0
    assert cl_weapon._WeaponState.fire_anim_start == 10.0


def test_shotgun_pellets_create_wall_smoke_and_flash(monkeypatch):
    _reset_state(monkeypatch, weapon_index=1)
    monkeypatch.setattr(cl_weapon.random, "uniform", lambda _a, _b: 0.0)
    monkeypatch.setattr(cl_weapon, "_damage_monsters_segment", lambda *_args: None)
    monkeypatch.setattr(cl_weapon, "_get_model", lambda path: path)

    class HitTrace:
        fraction = 0.5
        startsolid = False
        endpos = [128.0, 0.0, 22.0]
        plane = type("Plane", (), {"normal": [-1.0, 0.0, 0.0]})()

    trace_calls = []
    monkeypatch.setattr(
        cl_weapon, "_trace",
        lambda start, end: trace_calls.append((start, end)) or HitTrace(),
    )
    entities = _update(0.0, 10.0, _attack_cmd())

    assert len(trace_calls) == 12
    assert len(cl_weapon._WeaponState.wall_impacts) == 12
    assert sum(e['model'] == cl_weapon.SHOTGUN_SMOKE_MODEL for e in entities) == 12
    assert sum(e['model'] == cl_weapon.SHOTGUN_FLASH_MODEL for e in entities) == 12
    impact_entities = [
        e for e in entities
        if e['model'] in (cl_weapon.SHOTGUN_SMOKE_MODEL, cl_weapon.SHOTGUN_FLASH_MODEL)
    ]
    assert all(e['origin'] == HitTrace.endpos for e in impact_entities)


def test_super_shotgun_fires_two_ten_pellet_volleys(monkeypatch):
    _reset_state(monkeypatch, weapon_index=2)
    monkeypatch.setattr(cl_weapon.random, "uniform", lambda _a, _b: 0.0)
    monkeypatch.setattr(cl_weapon, "_damage_monsters_segment", lambda *_args: None)

    trace_ends = []
    monkeypatch.setattr(
        cl_weapon, "_trace",
        lambda _start, end: trace_ends.append(end) or None,
    )
    _update(0.0, 10.0, _attack_cmd())

    assert len(trace_ends) == 20
    assert all(end[1] < 0.0 for end in trace_ends[:10])
    assert all(end[1] > 0.0 for end in trace_ends[10:])
    assert cl_weapon._WeaponState.wall_impacts == []


def test_shotgun_wall_effect_expires(monkeypatch):
    _reset_state(monkeypatch, weapon_index=1)
    monkeypatch.setattr(cl_weapon._WeaponState, "wall_impacts", [{
        'origin': [1.0, 2.0, 3.0],
        'normal': [0.0, 0.0, 1.0],
        'start': 10.0,
    }])

    lifetime = (cl_weapon.SHOTGUN_SMOKE_FRAMES - 1) / cl_weapon.SHOTGUN_IMPACT_FPS
    _update(0.0, 10.0 + lifetime)

    assert cl_weapon._WeaponState.wall_impacts == []


def test_grenade_arcs_under_gravity(monkeypatch):
    _reset_state(monkeypatch, weapon_index=5)  # Grenade Launcher

    _update(0.0, 10.0, _attack_cmd())
    assert len(cl_weapon._WeaponState.bolts) == 1
    bolt = cl_weapon._WeaponState.bolts[0]
    assert bolt['gravity'] is True
    assert bolt['velocity'][2] == cl_weapon.GRENADE_LAUNCH_UP

    _update(0.1, 10.1)
    assert bolt['velocity'][2] == cl_weapon.GRENADE_LAUNCH_UP - cl_weapon.GRAVITY * 0.1


def test_all_weapon_definitions_are_complete():
    assert len(cl_weapon.WEAPONS) == 10
    for w in cl_weapon.WEAPONS:
        assert w['model'].startswith("models/weapons/v_")
        assert w['sound'].startswith("sound/weapons/")
        assert 0 < w['fire_first'] <= w['fire_last']
        assert w['idle'] == w['fire_last'] + 1
        assert w['cooldown'] > 0
        if w['projectile']:
            assert w['projectile']['speed'] > 0

def test_hitscan_fire_damages_monster(monkeypatch):
    from quake2 import cl_monsters
    _reset_state(monkeypatch, weapon_index=8)  # Railgun, damage 100

    entities = [{'classname': 'monster_soldier', 'origin': '300 0 0'}]
    soldier = cl_monsters._spawn_from_entities(entities)[0]
    monkeypatch.setattr(cl_monsters._MonsterState, "monsters", [soldier])

    monkeypatch.setattr(cl_monsters._MonsterState, "gibs", [])
    monkeypatch.setattr(cl_monsters, "_play_sound", lambda _p: None)

    _update(0.016, 10.0, _attack_cmd())

    assert soldier['health'] == 30 - 100
    assert soldier['state'] == 'gibbed'  # -70 is past GIB_HEALTH (-40)
    assert len(cl_monsters._MonsterState.gibs) == len(cl_monsters.GIB_MODELS)


def test_projectile_stops_on_monster_hit(monkeypatch):
    from quake2 import cl_monsters
    _reset_state(monkeypatch)  # Blaster, damage 15

    entities = [{'classname': 'monster_soldier', 'origin': '300 0 0'}]
    soldier = cl_monsters._spawn_from_entities(entities)[0]
    monkeypatch.setattr(cl_monsters._MonsterState, "monsters", [soldier])

    _update(0.0, 10.0, _attack_cmd())
    assert len(cl_weapon._WeaponState.bolts) == 1

    # One long frame flies the bolt through the monster's box
    _update(0.5, 10.5)

    assert cl_weapon._WeaponState.bolts == []
    assert soldier['health'] == 30 - 15
