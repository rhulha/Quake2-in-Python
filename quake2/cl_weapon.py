"""
cl_weapon.py - Client-side weapon handling (single-player)
Blaster: view model with fire animation, projectile bolts traced against the
world, and fire sound. Update() is called once per frame from V_RenderView.
"""

import io
import math
import time

BUTTON_ATTACK = 1

RF_WEAPONMODEL = 4
RF_DEPTHHACK = 16

GUN_MODEL = "models/weapons/v_blast/tris.md2"
BOLT_MODEL = "models/objects/laser/tris.md2"
FIRE_SOUND = "sound/weapons/blastf1a.wav"

# v_blast frame layout (matches original p_weapon.c Weapon_Blaster):
# 0-4 activate, 5-8 fire ("pow01".."pow04"), 9-52 idle
FRAME_FIRE_FIRST = 5
FRAME_FIRE_LAST = 8
FRAME_IDLE = 9
ANIM_FPS = 10.0

FIRE_COOLDOWN = (FRAME_FIRE_LAST - FRAME_FIRE_FIRST + 1) / ANIM_FPS
BOLT_SPEED = 1000.0
BOLT_LIFETIME = 3.0
MUZZLE_FORWARD = 24.0
MUZZLE_RIGHT = 8.0
MUZZLE_UP = -8.0


class _WeaponState:
    gun_model = None
    bolt_model = None
    models_loaded = False
    fire_sound = None
    sound_loaded = False
    last_fire_time = -1000.0
    fire_anim_start = None
    bolts = []  # dicts: {'origin', 'velocity', 'expire'}


def _load_models():
    if _WeaponState.models_loaded:
        return
    _WeaponState.models_loaded = True
    try:
        from ref_gl import gl_model
        _WeaponState.gun_model = gl_model.Mod_ForName(GUN_MODEL, False)
        _WeaponState.bolt_model = gl_model.Mod_ForName(BOLT_MODEL, False)
    except Exception as e:
        print(f"cl_weapon: model load error: {e}")


def _play_fire_sound():
    try:
        import pygame
        if not _WeaponState.sound_loaded:
            _WeaponState.sound_loaded = True
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            from quake2.files import FS_LoadFile
            data, length = FS_LoadFile(FIRE_SOUND)
            if data:
                _WeaponState.fire_sound = pygame.mixer.Sound(file=io.BytesIO(bytes(data)))
        if _WeaponState.fire_sound:
            _WeaponState.fire_sound.play()
    except Exception as e:
        print(f"cl_weapon: sound error: {e}")
        _WeaponState.fire_sound = None


def _angle_vectors(viewangles):
    """Quake 2 AngleVectors for roll=0: returns (forward, right, up)."""
    pitch = math.radians(viewangles[0])
    yaw = math.radians(viewangles[1])
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    forward = [cp * cy, cp * sy, -sp]
    right = [sy, -cy, 0.0]
    up = [sp * cy, sp * sy, cp]
    return forward, right, up


def _vector_to_angles(v):
    """Quake 2 vectoangles: [pitch, yaw, 0] for a direction vector."""
    horiz = math.sqrt(v[0] * v[0] + v[1] * v[1])
    yaw = math.degrees(math.atan2(v[1], v[0]))
    pitch = -math.degrees(math.atan2(v[2], horiz))
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


def _fire(vieworg, viewangles, now):
    forward, right, up = _angle_vectors(viewangles)
    origin = [
        vieworg[i] + forward[i] * MUZZLE_FORWARD + right[i] * MUZZLE_RIGHT + up[i] * MUZZLE_UP
        for i in range(3)
    ]
    _WeaponState.bolts.append({
        'origin': origin,
        'velocity': [forward[i] * BOLT_SPEED for i in range(3)],
        'expire': now + BOLT_LIFETIME,
    })
    _WeaponState.last_fire_time = now
    _WeaponState.fire_anim_start = now
    _play_fire_sound()


def _update_bolts(frametime, now):
    alive = []
    for bolt in _WeaponState.bolts:
        if now >= bolt['expire']:
            continue
        start = bolt['origin']
        end = [start[i] + bolt['velocity'][i] * frametime for i in range(3)]
        tr = _trace(start, end)
        if tr is not None and (tr.fraction < 1.0 or tr.startsolid):
            continue  # hit the world - bolt is gone
        bolt['origin'] = end
        alive.append(bolt)
    _WeaponState.bolts = alive


def _gun_frame(now):
    start = _WeaponState.fire_anim_start
    if start is not None:
        frame = FRAME_FIRE_FIRST + int((now - start) * ANIM_FPS)
        if frame <= FRAME_FIRE_LAST:
            return frame
        _WeaponState.fire_anim_start = None
    return FRAME_IDLE


def Update(frametime, vieworg, viewangles, cmd, now=None):
    """Advance weapon state one frame. Returns entity dicts to render."""
    if now is None:
        now = time.time()

    _load_models()

    attack = cmd is not None and (cmd.buttons & BUTTON_ATTACK)
    if attack and now - _WeaponState.last_fire_time >= FIRE_COOLDOWN:
        _fire(vieworg, viewangles, now)

    _update_bolts(frametime, now)

    entities = []
    if _WeaponState.bolt_model:
        for bolt in _WeaponState.bolts:
            entities.append({
                'model': _WeaponState.bolt_model,
                'origin': list(bolt['origin']),
                'angles': _vector_to_angles(bolt['velocity']),
            })
    if _WeaponState.gun_model:
        entities.append({
            'model': _WeaponState.gun_model,
            'origin': list(vieworg),
            'angles': list(viewangles),
            'frame': _gun_frame(now),
            'flags': RF_WEAPONMODEL | RF_DEPTHHACK,
        })
    return entities
