"""
cl_weapon.py - Client-side weapon handling (single-player)
All ten Quake 2 weapons: view model with fire animation, per-weapon fire
sound, and projectiles traced against the world where the original weapon
fires one. Update() is called once per frame from V_RenderView; number keys
switch weapons via SelectWeapon().
"""

import io
import math
import random
import time

BUTTON_ATTACK = 1

# Temporary master level for the client-side audio path during development.
# 0.4 means 60% quieter than the source volume.
DEVELOPMENT_AUDIO_VOLUME = 0.4

RF_WEAPONMODEL = 4
RF_FULLBRIGHT = 8
RF_DEPTHHACK = 16
RF_TRANSLUCENT = 32

ANIM_FPS = 10.0
GRAVITY = 800.0
BOLT_LIFETIME = 3.0
GRENADE_FUSE = 2.5
GRENADE_LAUNCH_UP = 200.0
GRENADE_OVERBOUNCE = 1.5
MUZZLE_FORWARD = 24.0
MUZZLE_RIGHT = 8.0
MUZZLE_UP = -8.0
HITSCAN_RANGE = 8192.0
SPLASH_RADIUS = 120.0

LASER_MODEL = "models/objects/laser/tris.md2"
ROCKET_MODEL = "models/objects/rocket/tris.md2"
GRENADE_MODEL = "models/objects/grenade/tris.md2"
ROCKET_EXPLOSION_MODEL = "models/objects/r_explode/tris.md2"
ROCKET_EXPLOSION_SOUND = "sound/weapons/rocklx1a.wav"
GRENADE_EXPLOSION_SOUND = "sound/weapons/grenlx1a.wav"
GRENADE_BOUNCE_SOUND = "sound/weapons/grenlb1b.wav"
EXPLOSION_FPS = 10.0
EXPLOSION_FRAMES = 15
SHOTGUN_SMOKE_MODEL = "models/objects/smoke/tris.md2"
SHOTGUN_FLASH_MODEL = "models/objects/flash/tris.md2"
SHOTGUN_IMPACT_FPS = 10.0
SHOTGUN_SMOKE_FRAMES = 4
SHOTGUN_FLASH_FRAMES = 2

# Fire animation frame ranges match the Weapon_Generic() calls in the
# original p_weapon.c; idle is the first frame after the fire sequence.
# Cooldowns are the original per-shot fire rates.
WEAPONS = [
    {
        'name': 'Blaster',
        'model': "models/weapons/v_blast/tris.md2",
        'sound': "sound/weapons/blastf1a.wav",
        'fire_first': 5, 'fire_last': 8, 'idle': 9,
        'cooldown': 0.4,
        'damage': 15,
        'projectile': {'model': LASER_MODEL, 'speed': 1000.0, 'gravity': False},
    },
    {
        'name': 'Shotgun',
        'model': "models/weapons/v_shotg/tris.md2",
        'sound': "sound/weapons/shotgf1b.wav",
        'fire_first': 8, 'fire_last': 18, 'idle': 19,
        'cooldown': 1.0,
        'damage': 48,
        'shotgun': {
            'pellet_damage': 4, 'hspread': 500.0, 'vspread': 500.0,
            'volleys': [(0.0, 12)],
        },
        'projectile': None,
    },
    {
        'name': 'Super Shotgun',
        'model': "models/weapons/v_shotg2/tris.md2",
        'sound': "sound/weapons/sshotf1b.wav",
        'fire_first': 7, 'fire_last': 17, 'idle': 18,
        'cooldown': 1.1,
        'damage': 120,
        'shotgun': {
            'pellet_damage': 6, 'hspread': 1000.0, 'vspread': 500.0,
            'volleys': [(-5.0, 10), (5.0, 10)],
        },
        'projectile': None,
    },
    {
        'name': 'Machinegun',
        'model': "models/weapons/v_machn/tris.md2",
        'sound': "sound/weapons/machgf1b.wav",
        'fire_first': 4, 'fire_last': 5, 'idle': 6,
        'cooldown': 0.1,
        'damage': 8,
        'projectile': None,
    },
    {
        'name': 'Chaingun',
        'model': "models/weapons/v_chain/tris.md2",
        'sound': "sound/weapons/machgf3b.wav",
        'fire_first': 5, 'fire_last': 31, 'idle': 32,
        'cooldown': 0.1,
        'damage': 8,
        'projectile': None,
    },
    {
        'name': 'Grenade Launcher',
        'model': "models/weapons/v_launch/tris.md2",
        'sound': "sound/weapons/grenlf1a.wav",
        'fire_first': 6, 'fire_last': 16, 'idle': 17,
        'cooldown': 1.1,
        'damage': 120,
        'projectile': {
            'model': GRENADE_MODEL, 'speed': 600.0, 'gravity': True,
            'launch_up': GRENADE_LAUNCH_UP,
            'fuse': GRENADE_FUSE,
            'bounce': True,
            'bounce_sound': GRENADE_BOUNCE_SOUND,
            'explode_on_expire': True,
            'impact_model': ROCKET_EXPLOSION_MODEL,
            'impact_sound': GRENADE_EXPLOSION_SOUND,
        },
    },
    {
        'name': 'Rocket Launcher',
        'model': "models/weapons/v_rocket/tris.md2",
        'sound': "sound/weapons/rocklf1a.wav",
        'fire_first': 5, 'fire_last': 12, 'idle': 13,
        'cooldown': 0.8,
        'damage': 120,
        'projectile': {
            'model': ROCKET_MODEL, 'speed': 650.0, 'gravity': False,
            'impact_model': ROCKET_EXPLOSION_MODEL,
            'impact_sound': ROCKET_EXPLOSION_SOUND,
        },
    },
    {
        'name': 'HyperBlaster',
        'model': "models/weapons/v_hyperb/tris.md2",
        'sound': "sound/weapons/hyprbf1a.wav",
        'fire_first': 6, 'fire_last': 20, 'idle': 21,
        'cooldown': 0.1,
        'damage': 15,
        'projectile': {'model': LASER_MODEL, 'speed': 1000.0, 'gravity': False},
    },
    {
        'name': 'Railgun',
        'model': "models/weapons/v_rail/tris.md2",
        'sound': "sound/weapons/railgf1a.wav",
        'fire_first': 4, 'fire_last': 18, 'idle': 19,
        'cooldown': 1.5,
        'damage': 100,
        'projectile': None,
    },
    {
        'name': 'BFG10K',
        'model': "models/weapons/v_bfg/tris.md2",
        'sound': "sound/weapons/bfg__f1y.wav",
        'fire_first': 9, 'fire_last': 32, 'idle': 33,
        'cooldown': 2.0,
        'damage': 200,
        'projectile': {'model': LASER_MODEL, 'speed': 400.0, 'gravity': False},
    },
]


class _WeaponState:
    current = 0
    models = {}   # path -> loaded model or None
    sounds = {}   # path -> pygame Sound or None
    mixer_ready = False
    last_fire_time = -1000.0
    fire_anim_start = None
    bolts = []  # dicts: {'origin', 'velocity', 'expire', 'model', 'gravity'}
    explosions = []  # dicts: {'origin', 'start', 'model'}
    wall_impacts = []  # shotgun pellet smoke/flash effects


def SelectWeapon(index):
    """Switch to weapon by list index (0 = Blaster ... 9 = BFG10K)."""
    if not 0 <= index < len(WEAPONS):
        return
    if index == _WeaponState.current:
        return
    _WeaponState.current = index
    _WeaponState.fire_anim_start = None
    print(f"Weapon: {WEAPONS[index]['name']}")


def _get_model(path):
    if path not in _WeaponState.models:
        model = None
        try:
            from ref_gl import gl_model
            model = gl_model.Mod_ForName(path, False)
        except Exception as e:
            print(f"cl_weapon: model load error for {path}: {e}")
        _WeaponState.models[path] = model
    return _WeaponState.models[path]


def _play_sound(path):
    try:
        import pygame
        if not _WeaponState.mixer_ready:
            _WeaponState.mixer_ready = True
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        if path not in _WeaponState.sounds:
            sound = None
            from quake2.files import FS_LoadFile
            data, length = FS_LoadFile(path)
            if data:
                sound = pygame.mixer.Sound(file=io.BytesIO(bytes(data)))
                sound.set_volume(DEVELOPMENT_AUDIO_VOLUME)
            _WeaponState.sounds[path] = sound
        if _WeaponState.sounds[path]:
            _WeaponState.sounds[path].play()
    except Exception as e:
        print(f"cl_weapon: sound error for {path}: {e}")
        _WeaponState.sounds[path] = None


def _angle_vectors(viewangles):
    """AngleVectors for roll=0: returns (forward, right, up).

    This engine's pitch sign is mirrored from the original Quake 2:
    positive pitch looks UP (see _make_view_matrix in gl_rmain / mouse
    handling in cl_input), so forward.z is +sin(pitch), not -sin(pitch).
    """
    pitch = math.radians(viewangles[0])
    yaw = math.radians(viewangles[1])
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    forward = [cp * cy, cp * sy, sp]
    right = [sy, -cy, 0.0]
    up = [-sp * cy, -sp * sy, cp]
    return forward, right, up


def _vector_to_angles(v):
    """Inverse of _angle_vectors: [pitch, yaw, 0] for a direction vector
    (positive pitch = up, matching this engine's convention)."""
    horiz = math.sqrt(v[0] * v[0] + v[1] * v[1])
    yaw = math.degrees(math.atan2(v[1], v[0]))
    pitch = math.degrees(math.atan2(v[2], horiz))
    return [pitch, yaw, 0.0]


def _trace(start, end):
    try:
        from quake2.cmodel import CM_BoxTrace, MASK_SOLID, num_models
        if num_models > 0:
            size = [-1.0, -1.0, -1.0], [1.0, 1.0, 1.0]
            tr = CM_BoxTrace(start, end, size[0], size[1], 0, MASK_SOLID)
            from quake2 import cl_doors
            return cl_doors.ClipTrace(start, end, size[0], size[1], tr, MASK_SOLID)
    except Exception:
        pass
    return None


def _damage_monsters_segment(start, end, damage, now):
    """Hit test a shot segment against live monsters; returns (t, monster)."""
    try:
        from quake2 import cl_monsters
        return cl_monsters.DamageSegment(start, end, damage, now)
    except Exception:
        return None


def _splash_damage_monsters(origin, damage, now):
    try:
        from quake2 import cl_monsters
        cl_monsters.SplashDamage(origin, damage, SPLASH_RADIUS, now)
    except Exception:
        pass


def _fire_hitscan(weapon, vieworg, viewangles, now):
    forward, _right, _up = _angle_vectors(viewangles)
    start = list(vieworg)
    end = [vieworg[i] + forward[i] * HITSCAN_RANGE for i in range(3)]
    tr = _trace(start, end)
    if tr is not None and (tr.fraction < 1.0 or tr.startsolid):
        end = _trace_impact_position(tr, start, end)
    _damage_monsters_segment(start, end, weapon['damage'], now)


def _spawn_shotgun_wall_impact(origin, normal, now):
    _WeaponState.wall_impacts.append({
        'origin': list(origin),
        'normal': list(normal),
        'start': now,
    })


def _fire_shotgun(weapon, vieworg, viewangles, now):
    """Trace Quake II-style pellet volleys and create effects on wall hits."""
    shotgun = weapon['shotgun']
    start = list(vieworg)
    for yaw_offset, count in shotgun['volleys']:
        pellet_angles = list(viewangles)
        pellet_angles[1] += yaw_offset
        forward, right, up = _angle_vectors(pellet_angles)
        for _ in range(count):
            r = random.uniform(-1.0, 1.0) * shotgun['hspread']
            u = random.uniform(-1.0, 1.0) * shotgun['vspread']
            end = [
                start[i] + forward[i] * HITSCAN_RANGE + right[i] * r + up[i] * u
                for i in range(3)
            ]
            tr = _trace(start, end)
            world_hit = tr is not None and (tr.fraction < 1.0 or tr.startsolid)
            segment_end = _trace_impact_position(tr, start, end) if world_hit else end

            monster_hit = _damage_monsters_segment(
                start, segment_end, shotgun['pellet_damage'], now
            )
            if monster_hit is not None or not world_hit:
                continue

            plane = getattr(tr, 'plane', None)
            normal = getattr(plane, 'normal', [0.0, 0.0, 1.0])
            _spawn_shotgun_wall_impact(segment_end, normal, now)


def _fire(weapon, vieworg, viewangles, now):
    projectile = weapon['projectile']
    if projectile:
        forward, right, up = _angle_vectors(viewangles)
        origin = [
            vieworg[i] + forward[i] * MUZZLE_FORWARD + right[i] * MUZZLE_RIGHT + up[i] * MUZZLE_UP
            for i in range(3)
        ]
        velocity = [
            forward[i] * projectile['speed'] + up[i] * projectile.get('launch_up', 0.0)
            for i in range(3)
        ]
        _WeaponState.bolts.append({
            'origin': origin,
            'velocity': velocity,
            'expire': now + projectile.get('fuse', BOLT_LIFETIME),
            'model': projectile['model'],
            'gravity': projectile['gravity'],
            'damage': weapon['damage'],
            'grounded': False,
            'bounce': projectile.get('bounce', False),
            'bounce_sound': projectile.get('bounce_sound'),
            'explode_on_expire': projectile.get('explode_on_expire', False),
            'impact_model': projectile.get('impact_model'),
            'impact_sound': projectile.get('impact_sound'),
        })
    elif weapon.get('shotgun'):
        _fire_shotgun(weapon, vieworg, viewangles, now)
    else:
        _fire_hitscan(weapon, vieworg, viewangles, now)
    _WeaponState.last_fire_time = now
    _WeaponState.fire_anim_start = now
    _play_sound(weapon['sound'])


def spawn_explosion(origin, model=ROCKET_EXPLOSION_MODEL, sound=ROCKET_EXPLOSION_SOUND, now=None):
    """Add an animated explosion effect at origin (used by monster projectiles).

    Reuses the same explosion render path as the player's rockets."""
    if now is None:
        now = time.time()
    _WeaponState.explosions.append({
        'origin': list(origin),
        'start': now,
        'model': model or ROCKET_EXPLOSION_MODEL,
    })
    if sound:
        _play_sound(sound)


def _spawn_projectile_explosion(bolt, origin, now):
    if not bolt['impact_model']:
        return
    _splash_damage_monsters(origin, bolt['damage'], now)
    _WeaponState.explosions.append({
        'origin': list(origin),
        'start': now,
        'model': bolt['impact_model'],
    })
    if bolt['impact_sound']:
        _play_sound(bolt['impact_sound'])


def _trace_impact_position(tr, start, end):
    impact = getattr(tr, 'endpos', None)
    if impact is not None:
        return list(impact)
    fraction = max(0.0, min(1.0, float(tr.fraction)))
    return [start[i] + (end[i] - start[i]) * fraction for i in range(3)]


def _bounce_projectile(bolt, normal):
    """Reflect velocity using Quake II's MOVETYPE_BOUNCE overbounce."""
    backoff = sum(bolt['velocity'][i] * normal[i] for i in range(3)) * GRENADE_OVERBOUNCE
    for i in range(3):
        velocity = bolt['velocity'][i] - normal[i] * backoff
        bolt['velocity'][i] = 0.0 if -0.1 < velocity < 0.1 else velocity

    # Quake II rests a slowly bouncing grenade on upward-facing ground.
    if normal[2] > 0.7 and bolt['velocity'][2] < 60.0:
        bolt['velocity'][:] = [0.0, 0.0, 0.0]
        bolt['grounded'] = True


def _update_bolts(frametime, now):
    alive = []
    for bolt in _WeaponState.bolts:
        if now >= bolt['expire']:
            if bolt['explode_on_expire']:
                _spawn_projectile_explosion(bolt, bolt['origin'], now)
            continue
        if bolt['grounded']:
            alive.append(bolt)
            continue
        if bolt['gravity']:
            bolt['velocity'][2] -= GRAVITY * frametime
        start = bolt['origin']
        end = [start[i] + bolt['velocity'][i] * frametime for i in range(3)]
        tr = _trace(start, end)
        world_hit = tr is not None and (tr.fraction < 1.0 or tr.startsolid)

        # Monster hit on the world-clipped segment takes priority (it is closer)
        seg_end = _trace_impact_position(tr, start, end) if world_hit else end
        monster_hit = _damage_monsters_segment(start, seg_end, bolt['damage'], now)
        if monster_hit is not None:
            t, _monster = monster_hit
            point = [start[i] + (seg_end[i] - start[i]) * t for i in range(3)]
            _spawn_projectile_explosion(bolt, point, now)
            continue

        if world_hit:
            impact = seg_end
            if bolt['bounce']:
                plane = getattr(tr, 'plane', None)
                normal = list(getattr(plane, 'normal', [0.0, 0.0, 1.0]))
                bolt['origin'] = impact
                _bounce_projectile(bolt, normal)
                if bolt['bounce_sound']:
                    _play_sound(bolt['bounce_sound'])
                alive.append(bolt)
                continue
            _spawn_projectile_explosion(bolt, impact, now)
            continue  # hit the world - projectile is gone
        bolt['origin'] = end
        alive.append(bolt)
    _WeaponState.bolts = alive


def _explosion_entities(now):
    """Advance rocket explosions and return their animated render entities."""
    alive = []
    entities = []
    lifetime = (EXPLOSION_FRAMES - 1) / EXPLOSION_FPS
    for explosion in _WeaponState.explosions:
        elapsed = max(0.0, now - explosion['start'])
        if elapsed >= lifetime:
            continue

        frame_time = elapsed * EXPLOSION_FPS
        oldframe = int(frame_time)
        frame = min(oldframe + 1, EXPLOSION_FRAMES - 1)
        frame_fraction = frame_time - oldframe
        skinnum = oldframe >> 1 if oldframe < 10 else (5 if oldframe < 13 else 6)
        flags = RF_FULLBRIGHT
        if oldframe >= 10:
            flags |= RF_TRANSLUCENT

        model = _get_model(explosion['model'])
        if model:
            entities.append({
                'model': model,
                'origin': list(explosion['origin']),
                'angles': [0.0, 0.0, 0.0],
                'frame': frame,
                'oldframe': oldframe,
                'backlerp': 1.0 - frame_fraction,
                'skinnum': skinnum,
                'alpha': (16.0 - oldframe) / 16.0,
                'flags': flags,
            })
        alive.append(explosion)
    _WeaponState.explosions = alive
    return entities


def _shotgun_impact_entities(now):
    """Animate the smoke and flash models used by the original TE_SHOTGUN."""
    alive = []
    entities = []
    smoke_model = _get_model(SHOTGUN_SMOKE_MODEL)
    flash_model = _get_model(SHOTGUN_FLASH_MODEL)
    lifetime = (SHOTGUN_SMOKE_FRAMES - 1) / SHOTGUN_IMPACT_FPS

    for impact in _WeaponState.wall_impacts:
        elapsed = max(0.0, now - impact['start'])
        if elapsed >= lifetime:
            continue

        frame_time = elapsed * SHOTGUN_IMPACT_FPS
        oldframe = int(frame_time)
        fraction = frame_time - oldframe

        if smoke_model:
            smoke_frame = min(oldframe + 1, SHOTGUN_SMOKE_FRAMES - 1)
            entities.append({
                'model': smoke_model,
                'origin': list(impact['origin']),
                'angles': [0.0, 0.0, 0.0],
                'frame': smoke_frame,
                'oldframe': min(oldframe, SHOTGUN_SMOKE_FRAMES - 1),
                'backlerp': 1.0 - fraction,
                'alpha': max(0.0, 1.0 - frame_time / (SHOTGUN_SMOKE_FRAMES - 1)),
                'flags': RF_TRANSLUCENT,
            })

        if flash_model and frame_time < SHOTGUN_FLASH_FRAMES - 1:
            flash_oldframe = int(frame_time)
            entities.append({
                'model': flash_model,
                'origin': list(impact['origin']),
                'angles': [0.0, 0.0, 0.0],
                'frame': min(flash_oldframe + 1, SHOTGUN_FLASH_FRAMES - 1),
                'oldframe': flash_oldframe,
                'backlerp': 1.0 - fraction,
                'flags': RF_FULLBRIGHT,
            })

        alive.append(impact)

    _WeaponState.wall_impacts = alive
    return entities


def _gun_frame(weapon, now):
    start = _WeaponState.fire_anim_start
    if start is not None:
        frame = weapon['fire_first'] + int((now - start) * ANIM_FPS)
        if frame <= weapon['fire_last']:
            return frame
        _WeaponState.fire_anim_start = None
    return weapon['idle']


def Update(frametime, vieworg, viewangles, cmd, now=None):
    """Advance weapon state one frame. Returns entity dicts to render."""
    if now is None:
        now = time.time()

    weapon = WEAPONS[_WeaponState.current]

    attack = cmd is not None and (cmd.buttons & BUTTON_ATTACK)
    if attack and now - _WeaponState.last_fire_time >= weapon['cooldown']:
        _fire(weapon, vieworg, viewangles, now)

    _update_bolts(frametime, now)

    entities = _explosion_entities(now)
    entities.extend(_shotgun_impact_entities(now))
    for bolt in _WeaponState.bolts:
        model = _get_model(bolt['model'])
        if model:
            entities.append({
                'model': model,
                'origin': list(bolt['origin']),
                'angles': _vector_to_angles(bolt['velocity']),
            })

    gun_model = _get_model(weapon['model'])
    if gun_model:
        entities.append({
            'model': gun_model,
            'origin': list(vieworg),
            'angles': list(viewangles),
            'frame': _gun_frame(weapon, now),
            'flags': RF_WEAPONMODEL | RF_DEPTHHACK,
        })
    return entities
