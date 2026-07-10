"""
cl_weapon.py - Client-side weapon handling (single-player)
All ten Quake 2 weapons: view model with fire animation, per-weapon fire
sound, and projectiles traced against the world where the original weapon
fires one. Update() is called once per frame from V_RenderView; number keys
switch weapons via SelectWeapon().
"""

import io
import math
import time

BUTTON_ATTACK = 1

RF_WEAPONMODEL = 4
RF_DEPTHHACK = 16

ANIM_FPS = 10.0
GRAVITY = 800.0
BOLT_LIFETIME = 3.0
MUZZLE_FORWARD = 24.0
MUZZLE_RIGHT = 8.0
MUZZLE_UP = -8.0

LASER_MODEL = "models/objects/laser/tris.md2"
ROCKET_MODEL = "models/objects/rocket/tris.md2"
GRENADE_MODEL = "models/objects/grenade/tris.md2"

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
        'projectile': {'model': LASER_MODEL, 'speed': 1000.0, 'gravity': False},
    },
    {
        'name': 'Shotgun',
        'model': "models/weapons/v_shotg/tris.md2",
        'sound': "sound/weapons/shotgf1b.wav",
        'fire_first': 8, 'fire_last': 18, 'idle': 19,
        'cooldown': 1.0,
        'projectile': None,
    },
    {
        'name': 'Super Shotgun',
        'model': "models/weapons/v_shotg2/tris.md2",
        'sound': "sound/weapons/sshotf1b.wav",
        'fire_first': 7, 'fire_last': 17, 'idle': 18,
        'cooldown': 1.1,
        'projectile': None,
    },
    {
        'name': 'Machinegun',
        'model': "models/weapons/v_machn/tris.md2",
        'sound': "sound/weapons/machgf1b.wav",
        'fire_first': 4, 'fire_last': 5, 'idle': 6,
        'cooldown': 0.1,
        'projectile': None,
    },
    {
        'name': 'Chaingun',
        'model': "models/weapons/v_chain/tris.md2",
        'sound': "sound/weapons/machgf3b.wav",
        'fire_first': 5, 'fire_last': 31, 'idle': 32,
        'cooldown': 0.1,
        'projectile': None,
    },
    {
        'name': 'Grenade Launcher',
        'model': "models/weapons/v_launch/tris.md2",
        'sound': "sound/weapons/grenlf1a.wav",
        'fire_first': 6, 'fire_last': 16, 'idle': 17,
        'cooldown': 1.1,
        'projectile': {'model': GRENADE_MODEL, 'speed': 600.0, 'gravity': True},
    },
    {
        'name': 'Rocket Launcher',
        'model': "models/weapons/v_rocket/tris.md2",
        'sound': "sound/weapons/rocklf1a.wav",
        'fire_first': 5, 'fire_last': 12, 'idle': 13,
        'cooldown': 0.8,
        'projectile': {'model': ROCKET_MODEL, 'speed': 650.0, 'gravity': False},
    },
    {
        'name': 'HyperBlaster',
        'model': "models/weapons/v_hyperb/tris.md2",
        'sound': "sound/weapons/hyprbf1a.wav",
        'fire_first': 6, 'fire_last': 20, 'idle': 21,
        'cooldown': 0.1,
        'projectile': {'model': LASER_MODEL, 'speed': 1000.0, 'gravity': False},
    },
    {
        'name': 'Railgun',
        'model': "models/weapons/v_rail/tris.md2",
        'sound': "sound/weapons/railgf1a.wav",
        'fire_first': 4, 'fire_last': 18, 'idle': 19,
        'cooldown': 1.5,
        'projectile': None,
    },
    {
        'name': 'BFG10K',
        'model': "models/weapons/v_bfg/tris.md2",
        'sound': "sound/weapons/bfg__f1y.wav",
        'fire_first': 9, 'fire_last': 32, 'idle': 33,
        'cooldown': 2.0,
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
            return CM_BoxTrace(start, end, size[0], size[1], 0, MASK_SOLID)
    except Exception:
        pass
    return None


def _fire(weapon, vieworg, viewangles, now):
    projectile = weapon['projectile']
    if projectile:
        forward, right, up = _angle_vectors(viewangles)
        origin = [
            vieworg[i] + forward[i] * MUZZLE_FORWARD + right[i] * MUZZLE_RIGHT + up[i] * MUZZLE_UP
            for i in range(3)
        ]
        _WeaponState.bolts.append({
            'origin': origin,
            'velocity': [forward[i] * projectile['speed'] for i in range(3)],
            'expire': now + BOLT_LIFETIME,
            'model': projectile['model'],
            'gravity': projectile['gravity'],
        })
    _WeaponState.last_fire_time = now
    _WeaponState.fire_anim_start = now
    _play_sound(weapon['sound'])


def _update_bolts(frametime, now):
    alive = []
    for bolt in _WeaponState.bolts:
        if now >= bolt['expire']:
            continue
        if bolt['gravity']:
            bolt['velocity'][2] -= GRAVITY * frametime
        start = bolt['origin']
        end = [start[i] + bolt['velocity'][i] * frametime for i in range(3)]
        tr = _trace(start, end)
        if tr is not None and (tr.fraction < 1.0 or tr.startsolid):
            continue  # hit the world - projectile is gone
        bolt['origin'] = end
        alive.append(bolt)
    _WeaponState.bolts = alive


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

    entities = []
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
