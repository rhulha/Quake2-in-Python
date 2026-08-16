"""
cl_monsters.py - Client-side monster spawning, combat, and rendering
Parses the loaded map's BSP entity string for monster entities. Monsters
idle-animate, take damage from the player's weapons (DamageSegment), play
their death animation, and attack: they turn toward the player and fire
bolts when they have line of sight.
"""

import math
import random
import time

ANIM_FPS = 10.0
TURN_SPEED = 240.0          # degrees/sec monsters turn toward the player
SIGHT_RANGE = 1500.0
VIEWHEIGHT = 22.0
MOVE_SPEED = 120.0          # units/sec ground speed while chasing
STOP_RANGE = 160.0          # monsters hold position this close to the player
STEP_HEIGHT = 18.0          # max stair step they can climb
GROUND_SNAP = 64.0          # how far down to look for a floor after moving

GIB_HEALTH = -40.0          # at or below this, the kill gibs instead of a death anim
GIB_LIFETIME = 15.0
GIB_BOUNCE = 0.4            # velocity kept after a bounce
GIB_SOUND = "sound/misc/udeath.wav"
GIB_MODELS = [
    "models/objects/gibs/sm_meat/tris.md2",
    "models/objects/gibs/sm_meat/tris.md2",
    "models/objects/gibs/sm_meat/tris.md2",
    "models/objects/gibs/sm_meat/tris.md2",
    "models/objects/gibs/chest/tris.md2",
    "models/objects/gibs/head2/tris.md2",
]

MONSTER_BOLT_LIFETIME = 3.0
MONSTER_BOLT_DAMAGE = 10        # fallback damage for a bolt with no weapon data
HITSCAN_RANGE = 8192.0
MELEE_RANGE = 90.0             # melee monsters strike within this distance
MELEE_STOP_RANGE = 60.0       # ...and close to here before holding position
PLAYER_PAIN_SOUND = "sound/player/male/pain100_1.wav"
PLAYER_DEATH_SOUND = "sound/player/male/death1.wav"
ATTACK_INTERVAL = (1.2, 2.5)  # seconds between monster shots (randomized)

# Per-weapon fire definitions. Each monster fires its own weapon (matching the
# original m_*.c attack functions) instead of a generic blaster bolt. Projectile
# weapons spawn a travelling bolt; hitscan weapons trace instantly; melee strikes
# on contact. Models/sounds mirror the player weapons in cl_weapon.
MONSTER_WEAPONS = {
    'blaster': {
        'kind': 'projectile',
        'model': "models/objects/laser/tris.md2",
        'speed': 1000.0, 'damage': 8, 'gravity': False,
        'sound': "sound/weapons/blastf1a.wav",
    },
    'rocket': {
        'kind': 'projectile',
        'model': "models/objects/rocket/tris.md2",
        'speed': 500.0, 'damage': 30, 'gravity': False,
        'sound': "sound/weapons/rocklf1a.wav",
        'explode': True,
        'impact_model': "models/objects/r_explode/tris.md2",
        'impact_sound': "sound/weapons/rocklx1a.wav",
        'splash_radius': 120.0,
    },
    'grenade': {
        'kind': 'projectile',
        'model': "models/objects/grenade/tris.md2",
        'speed': 600.0, 'damage': 30, 'gravity': True, 'launch_up': 200.0,
        'sound': "sound/weapons/grenlf1a.wav",
        'explode': True,
        'impact_model': "models/objects/r_explode/tris.md2",
        'impact_sound': "sound/weapons/grenlx1a.wav",
        'splash_radius': 120.0,
    },
    'machinegun': {
        'kind': 'hitscan',
        'damage': 4, 'count': 3, 'spread': 300.0,
        'sound': "sound/weapons/machgf1b.wav",
    },
    'shotgun': {
        'kind': 'hitscan',
        'damage': 3, 'count': 6, 'spread': 600.0,
        'sound': "sound/weapons/shotgf1b.wav",
    },
    'railgun': {
        'kind': 'hitscan',
        'damage': 30, 'count': 1, 'spread': 0.0,
        'sound': "sound/weapons/railgf1a.wav",
    },
    'melee': {
        'kind': 'melee',
        'damage': 10, 'sound': None,
    },
}

# classname -> weapon type, from the original monster attack code. Monsters with
# no ranged attack in the original (berserker, mutant, ...) are melee.
MONSTER_WEAPON_BY_CLASS = {
    'monster_soldier_light': 'blaster',
    'monster_soldier': 'shotgun',
    'monster_soldier_ss': 'machinegun',
    'monster_infantry': 'machinegun',
    'monster_gunner': 'grenade',
    'monster_gladiator': 'railgun',
    'monster_chick': 'rocket',
    'monster_flyer': 'blaster',
    'monster_hover': 'blaster',
    'monster_floater': 'blaster',
    'monster_medic': 'blaster',
    'monster_makron': 'blaster',
    'monster_tank': 'rocket',
    'monster_tank_commander': 'rocket',
    'monster_supertank': 'rocket',
    'monster_boss2': 'rocket',
    'monster_jorg': 'machinegun',
    'monster_berserk': 'melee',
    'monster_brain': 'melee',
    'monster_mutant': 'melee',
    'monster_parasite': 'melee',
    'monster_insane': 'melee',
    'monster_flipper': 'melee',
}
DEFAULT_MONSTER_WEAPON = 'blaster'

# NOT_MEDIUM: entities flagged out of skill 1 are skipped, otherwise maps
# would spawn overlapping per-skill duplicates at the same spot.
SPAWNFLAG_NOT_MEDIUM = 512

# classname -> (model path, skin index), matching the original m_*.c files.
# Soldier and tank variants share one model and differ by skin.
MONSTERS = {
    'monster_berserk': ("models/monsters/berserk/tris.md2", 0),
    'monster_boss2': ("models/monsters/boss2/tris.md2", 0),
    'monster_brain': ("models/monsters/brain/tris.md2", 0),
    'monster_chick': ("models/monsters/bitch/tris.md2", 0),
    'monster_flipper': ("models/monsters/flipper/tris.md2", 0),
    'monster_floater': ("models/monsters/float/tris.md2", 0),
    'monster_flyer': ("models/monsters/flyer/tris.md2", 0),
    'monster_gladiator': ("models/monsters/gladiatr/tris.md2", 0),
    'monster_gunner': ("models/monsters/gunner/tris.md2", 0),
    'monster_hover': ("models/monsters/hover/tris.md2", 0),
    'monster_infantry': ("models/monsters/infantry/tris.md2", 0),
    'monster_insane': ("models/monsters/insane/tris.md2", 0),
    'monster_jorg': ("models/monsters/boss3/jorg/tris.md2", 0),
    'monster_makron': ("models/monsters/boss3/rider/tris.md2", 0),
    'monster_medic': ("models/monsters/medic/tris.md2", 0),
    'monster_mutant': ("models/monsters/mutant/tris.md2", 0),
    'monster_parasite': ("models/monsters/parasite/tris.md2", 0),
    'monster_soldier': ("models/monsters/soldier/tris.md2", 2),
    'monster_soldier_light': ("models/monsters/soldier/tris.md2", 0),
    'monster_soldier_ss': ("models/monsters/soldier/tris.md2", 4),
    'monster_supertank': ("models/monsters/boss1/tris.md2", 0),
    'monster_tank': ("models/monsters/tank/tris.md2", 0),
    'monster_tank_commander': ("models/monsters/tank/tris.md2", 2),
}

# Health values from the original g_*.c monster spawn functions.
HEALTH = {
    'monster_berserk': 240,
    'monster_boss2': 2000,
    'monster_brain': 300,
    'monster_chick': 175,
    'monster_flipper': 50,
    'monster_floater': 200,
    'monster_flyer': 50,
    'monster_gladiator': 400,
    'monster_gunner': 175,
    'monster_hover': 240,
    'monster_infantry': 100,
    'monster_insane': 100,
    'monster_jorg': 3000,
    'monster_makron': 3000,
    'monster_medic': 300,
    'monster_mutant': 300,
    'monster_parasite': 175,
    'monster_soldier': 30,
    'monster_soldier_light': 20,
    'monster_soldier_ss': 40,
    'monster_supertank': 1500,
    'monster_tank': 750,
    'monster_tank_commander': 1000,
}

# Bounding boxes (mins, maxs) for hit detection; default is the humanoid box.
DEFAULT_BOX = ([-16.0, -16.0, -24.0], [16.0, 16.0, 32.0])
BOXES = {
    'monster_gladiator': ([-32.0, -32.0, -24.0], [32.0, 32.0, 64.0]),
    'monster_mutant': ([-32.0, -32.0, -24.0], [32.0, 32.0, 48.0]),
    'monster_tank': ([-32.0, -32.0, -16.0], [32.0, 32.0, 72.0]),
    'monster_tank_commander': ([-32.0, -32.0, -16.0], [32.0, 32.0, 72.0]),
    'monster_supertank': ([-64.0, -64.0, 0.0], [64.0, 64.0, 112.0]),
    'monster_boss2': ([-56.0, -56.0, 0.0], [56.0, 56.0, 80.0]),
    'monster_jorg': ([-80.0, -80.0, 0.0], [80.0, 80.0, 140.0]),
    'monster_makron': ([-30.0, -30.0, 0.0], [30.0, 30.0, 90.0]),
}

PLAYER_BOX = ([-16.0, -16.0, -24.0], [16.0, 16.0, 32.0])


class _MonsterState:
    entity_string = None  # entity string the monsters were parsed from
    monsters = []
    models = {}           # path -> loaded model or None
    anim_ranges = {}      # (path, prefix) -> (first_frame, frame_count)
    bolts = []            # monster shots: {'origin', 'velocity', 'expire'}
    gibs = []             # flying chunks: {'origin', 'velocity', 'model', ...}


class PlayerState:
    health = 100
    respawn_requested = False


def parse_entities(entity_string):
    """Parse a BSP entity string into a list of key/value dicts."""
    entities = []
    i = 0
    while i < len(entity_string):
        start = entity_string.find('{', i)
        if start == -1:
            break
        end = entity_string.find('}', start)
        if end == -1:
            break
        block = entity_string[start + 1:end]
        i = end + 1

        keys = {}
        j = 0
        while j < len(block):
            q1 = block.find('"', j)
            if q1 == -1:
                break
            q2 = block.find('"', q1 + 1)
            q3 = block.find('"', q2 + 1)
            q4 = block.find('"', q3 + 1)
            if q4 == -1:
                break
            keys[block[q1 + 1:q2]] = block[q3 + 1:q4]
            j = q4 + 1
        if keys:
            entities.append(keys)
    return entities


def _spawn_from_entities(entities):
    monsters = []
    for keys in entities:
        classname = keys.get('classname', '')
        if classname not in MONSTERS:
            continue

        try:
            spawnflags = int(keys.get('spawnflags', 0))
        except ValueError:
            spawnflags = 0
        if spawnflags & SPAWNFLAG_NOT_MEDIUM:
            continue

        origin = [0.0, 0.0, 0.0]
        origin_str = keys.get('origin', '')
        parts = origin_str.split()
        if len(parts) == 3:
            try:
                origin = [float(p) for p in parts]
            except ValueError:
                pass

        try:
            yaw = float(keys.get('angle', 0))
        except ValueError:
            yaw = 0.0

        model_path, skin = MONSTERS[classname]
        mins, maxs = BOXES.get(classname, DEFAULT_BOX)
        monsters.append({
            'classname': classname,
            'origin': origin,
            'yaw': yaw,
            'model_path': model_path,
            'skin': skin,
            'weapon': MONSTER_WEAPON_BY_CLASS.get(classname, DEFAULT_MONSTER_WEAPON),
            'health': HEALTH.get(classname, 100),
            'mins': mins,
            'maxs': maxs,
            'state': 'alive',        # alive -> dying -> dead
            'death_start': None,
            'attack_start': None,
            'next_attack': None,     # set on first Update (reaction delay)
            'moving': False,
        })
    return monsters


def _get_model(path):
    if path not in _MonsterState.models:
        model = None
        try:
            from ref_gl import gl_model
            model = gl_model.Mod_ForName(path, False)
        except Exception as e:
            print(f"cl_monsters: model load error for {path}: {e}")
        _MonsterState.models[path] = model
    return _MonsterState.models[path]


def _anim_range(path, model, prefix):
    """First frame and length of the model's first frame sequence whose
    names start with *prefix* (e.g. 'stand', 'death', 'atta')."""
    key = (path, prefix)
    if key not in _MonsterState.anim_ranges:
        first, count = 0, 1
        try:
            frames = model.mesh_data['frames']
            matching = [i for i, f in enumerate(frames)
                        if f.name.lower().startswith(prefix)]
            if matching:
                first = matching[0]
                count = 1
                while count < len(matching) and matching[count] == first + count:
                    count += 1
        except Exception:
            pass
        _MonsterState.anim_ranges[key] = (first, count)
    return _MonsterState.anim_ranges[key]


def _stand_range(path, model):
    return _anim_range(path, model, 'stand')


def _segment_box_t(start, end, origin, mins, maxs):
    """Slab test: entry time t in [0,1] where segment hits the box, or None."""
    tmin, tmax = 0.0, 1.0
    for i in range(3):
        lo = origin[i] + mins[i]
        hi = origin[i] + maxs[i]
        d = end[i] - start[i]
        if abs(d) < 1e-9:
            if start[i] < lo or start[i] > hi:
                return None
        else:
            t1 = (lo - start[i]) / d
            t2 = (hi - start[i]) / d
            if t1 > t2:
                t1, t2 = t2, t1
            tmin = max(tmin, t1)
            tmax = min(tmax, t2)
            if tmin > tmax:
                return None
    return tmin


def _gib_monster(monster, now):
    """Explode the monster into flying gibs (overkill death)."""
    monster['state'] = 'gibbed'
    center = [monster['origin'][0], monster['origin'][1],
              monster['origin'][2] + monster['maxs'][2] * 0.5]
    for model in GIB_MODELS:
        _MonsterState.gibs.append({
            'origin': list(center),
            'velocity': [random.uniform(-200.0, 200.0),
                         random.uniform(-200.0, 200.0),
                         random.uniform(150.0, 400.0)],
            'model': model,
            'expire': now + GIB_LIFETIME,
            'spawn': now,
            'avelocity': [random.uniform(-400.0, 400.0),
                          random.uniform(-400.0, 400.0)],
            'resting': False,
        })
    _play_sound(GIB_SOUND)


def _apply_damage(monster, damage, now):
    monster['health'] -= damage
    if monster['health'] > 0:
        return
    if monster['health'] <= GIB_HEALTH:
        _gib_monster(monster, now)
        print(f"{monster['classname']} gibbed")
    else:
        monster['state'] = 'dying'
        monster['death_start'] = now
        print(f"{monster['classname']} killed")


def _update_gibs(frametime, now):
    from quake2.cl_weapon import GRAVITY
    alive = []
    for gib in _MonsterState.gibs:
        if now >= gib['expire']:
            continue
        if not gib['resting']:
            gib['velocity'][2] -= GRAVITY * frametime
            start = gib['origin']
            end = [start[i] + gib['velocity'][i] * frametime for i in range(3)]
            tr = _trace(start, end)
            if tr is not None and (tr.fraction < 1.0 or tr.startsolid):
                # Bounce off whatever was hit, mostly killing the energy
                endpos = getattr(tr, 'endpos', None)
                if endpos is not None and not tr.startsolid:
                    gib['origin'] = list(endpos)
                gib['velocity'] = [v * GIB_BOUNCE for v in gib['velocity']]
                gib['velocity'][2] = abs(gib['velocity'][2])
                if sum(v * v for v in gib['velocity']) < 900.0:  # < 30 u/s: rest
                    gib['velocity'] = [0.0, 0.0, 0.0]
                    gib['resting'] = True
            else:
                gib['origin'] = end
        alive.append(gib)
    _MonsterState.gibs = alive


def _gib_entities(now):
    entities = []
    for gib in _MonsterState.gibs:
        model = _get_model(gib['model'])
        if not model:
            continue
        t = now - gib['spawn']
        if gib['resting']:
            angles = [0.0, (gib['avelocity'][1] * 0.1) % 360.0, 0.0]
        else:
            angles = [(gib['avelocity'][0] * t) % 360.0,
                      (gib['avelocity'][1] * t) % 360.0, 0.0]
        entities.append({
            'model': model,
            'origin': list(gib['origin']),
            'angles': angles,
        })
    return entities


def DamageSegment(start, end, damage, now=None):
    """Damage the first live monster the segment start->end passes through.
    Returns (t, monster) of the hit, or None. Corpses don't block shots."""
    if now is None:
        now = time.time()

    best_t = None
    best_monster = None
    for monster in _MonsterState.monsters:
        if monster['state'] != 'alive':
            continue
        t = _segment_box_t(start, end, monster['origin'], monster['mins'], monster['maxs'])
        if t is not None and (best_t is None or t < best_t):
            best_t = t
            best_monster = monster

    if best_monster is None:
        return None

    _apply_damage(best_monster, damage, now)
    return best_t, best_monster


def SplashDamage(origin, damage, radius, now=None):
    """Explosion damage to all live monsters near origin, falling off linearly."""
    if now is None:
        now = time.time()
    for monster in _MonsterState.monsters:
        if monster['state'] != 'alive':
            continue
        d = math.sqrt(sum((monster['origin'][i] - origin[i]) ** 2 for i in range(3)))
        if d < radius:
            _apply_damage(monster, damage * (1.0 - d / radius), now)


def _trace(start, end):
    size = [-1.0, -1.0, -1.0], [1.0, 1.0, 1.0]
    return _box_trace(start, end, size[0], size[1])


def _box_trace(start, end, mins, maxs):
    try:
        from quake2.cmodel import CM_BoxTrace, MASK_SOLID, num_models
        if num_models > 0:
            tr = CM_BoxTrace(start, end, mins, maxs, 0, MASK_SOLID)
            from quake2 import cl_doors
            return cl_doors.ClipTrace(start, end, mins, maxs, tr, MASK_SOLID)
    except Exception:
        pass
    return None


def _walk_monster(monster, frametime):
    """Move the monster one frame along its facing yaw, with world collision,
    stair stepping, and ground snapping."""
    yaw = math.radians(monster['yaw'])
    step = MOVE_SPEED * frametime
    start = monster['origin']
    end = [start[0] + math.cos(yaw) * step, start[1] + math.sin(yaw) * step, start[2]]
    mins, maxs = monster['mins'], monster['maxs']

    tr = _box_trace(start, end, mins, maxs)
    if tr is None:
        pos = end
    elif tr.startsolid:
        return  # embedded somewhere; don't make it worse
    elif tr.fraction >= 1.0:
        pos = end
    else:
        # Blocked: try the same move lifted by a stair step
        up_start = [start[0], start[1], start[2] + STEP_HEIGHT]
        up_end = [end[0], end[1], end[2] + STEP_HEIGHT]
        tr2 = _box_trace(up_start, up_end, mins, maxs)
        if tr2 is not None and not tr2.startsolid and tr2.fraction >= 1.0:
            pos = up_end
        else:
            pos = list(getattr(tr, 'endpos', start) or start)

    # Snap onto the floor below (walks down stairs and slopes; leaves
    # airborne monsters like flyers alone when no floor is near)
    gtr = _box_trace(pos, [pos[0], pos[1], pos[2] - GROUND_SNAP], mins, maxs)
    if gtr is not None and not gtr.startsolid and gtr.fraction < 1.0:
        endpos = getattr(gtr, 'endpos', None)
        if endpos is not None:
            pos = [pos[0], pos[1], endpos[2] + 0.25]

    monster['origin'] = pos


def _visible(start, end):
    """Line of sight through the world between two points."""
    tr = _trace(start, end)
    if tr is None:
        return True
    return tr.fraction >= 1.0 and not tr.startsolid


def _play_sound(path):
    if not path:
        return
    try:
        from quake2 import cl_weapon
        cl_weapon._play_sound(path)
    except Exception:
        pass


def _damage_player(damage):
    PlayerState.health -= damage
    if PlayerState.health <= 0:
        print("You died! Respawning...")
        _play_sound(PLAYER_DEATH_SOUND)
        PlayerState.health = 100
        PlayerState.respawn_requested = True
    else:
        print(f"Player hit! health = {PlayerState.health}")
        _play_sound(PLAYER_PAIN_SOUND)


def _monster_eye(monster):
    return [monster['origin'][0], monster['origin'][1],
            monster['origin'][2] + monster['maxs'][2] * 0.7]


def _monster_weapon(monster):
    return MONSTER_WEAPONS.get(monster.get('weapon', DEFAULT_MONSTER_WEAPON),
                               MONSTER_WEAPONS[DEFAULT_MONSTER_WEAPON])


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0]]


def _perp_basis(forward):
    """Right/up vectors perpendicular to forward, for spreading hitscan shots."""
    up_world = [1.0, 0.0, 0.0] if abs(forward[2]) > 0.99 else [0.0, 0.0, 1.0]
    right = _cross(forward, up_world)
    length = math.sqrt(sum(c * c for c in right)) or 1.0
    right = [c / length for c in right]
    up = _cross(right, forward)
    return right, up


def _fire_hitscan(eye, forward, player_origin, weapon, now):
    """Trace instant shots (bullets/pellets/rail) toward the player."""
    right, up = _perp_basis(forward)
    spread = weapon.get('spread', 0.0)
    for _ in range(weapon.get('count', 1)):
        r = random.uniform(-1.0, 1.0) * spread
        u = random.uniform(-1.0, 1.0) * spread
        end = [eye[i] + forward[i] * HITSCAN_RANGE + right[i] * r + up[i] * u
               for i in range(3)]
        tr = _trace(eye, end)
        world_hit = tr is not None and (tr.fraction < 1.0 or tr.startsolid)
        seg_end = list(getattr(tr, 'endpos', end) or end) if world_hit else end
        if _segment_box_t(eye, seg_end, player_origin,
                          PLAYER_BOX[0], PLAYER_BOX[1]) is not None:
            _damage_player(weapon['damage'])


def _monster_attack(monster, eye, player_eye, player_origin, dist, now):
    """Fire the monster's specific weapon. Returns True if it attacked."""
    weapon = _monster_weapon(monster)
    kind = weapon['kind']

    direction = [player_eye[i] - eye[i] for i in range(3)]
    length = math.sqrt(sum(d * d for d in direction)) or 1.0
    forward = [d / length for d in direction]

    if kind == 'melee':
        if dist > MELEE_RANGE:
            return False
        _damage_player(weapon['damage'])
        _play_sound(weapon.get('sound'))
        return True

    if kind == 'hitscan':
        _fire_hitscan(eye, forward, player_origin, weapon, now)
        _play_sound(weapon.get('sound'))
        return True

    # projectile
    velocity = [forward[i] * weapon['speed'] for i in range(3)]
    velocity[2] += weapon.get('launch_up', 0.0)
    _MonsterState.bolts.append({
        'origin': [eye[i] + forward[i] * 24.0 for i in range(3)],
        'velocity': velocity,
        'expire': now + MONSTER_BOLT_LIFETIME,
        'model': weapon['model'],
        'damage': weapon['damage'],
        'gravity': weapon.get('gravity', False),
        'explode': weapon.get('explode', False),
        'impact_model': weapon.get('impact_model'),
        'impact_sound': weapon.get('impact_sound'),
        'splash_radius': weapon.get('splash_radius', 0.0),
    })
    _play_sound(weapon.get('sound'))
    return True


def _update_ai(frametime, player_eye, now):
    player_origin = [player_eye[0], player_eye[1], player_eye[2] - VIEWHEIGHT]
    for monster in _MonsterState.monsters:
        if monster['state'] != 'alive':
            continue

        eye = _monster_eye(monster)
        dx = player_eye[0] - eye[0]
        dy = player_eye[1] - eye[1]
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > SIGHT_RANGE:
            monster['moving'] = False
            continue
        if not _visible(eye, player_eye):
            monster['moving'] = False
            continue

        # Turn toward the player
        want_yaw = math.degrees(math.atan2(dy, dx))
        delta = (want_yaw - monster['yaw'] + 180.0) % 360.0 - 180.0
        max_turn = TURN_SPEED * frametime
        monster['yaw'] += max(-max_turn, min(max_turn, delta))

        # Chase: run toward the player until close enough to hold position.
        # Melee monsters close in further so they can reach striking range.
        stop_range = MELEE_STOP_RANGE if _monster_weapon(monster)['kind'] == 'melee' else STOP_RANGE
        if dist > stop_range and abs(delta) < 90.0:
            monster['moving'] = True
            _walk_monster(monster, frametime)
        else:
            monster['moving'] = False

        # Attack when roughly facing the player and the attack timer allows
        if monster['next_attack'] is None:
            monster['next_attack'] = now + random.uniform(0.5, 1.5)  # reaction time
        if now >= monster['next_attack'] and abs(delta) < 30.0:
            if _monster_attack(monster, eye, player_eye, player_origin, dist, now):
                monster['attack_start'] = now
                monster['next_attack'] = now + random.uniform(*ATTACK_INTERVAL)


def _explode_bolt(bolt, origin, player_origin, now):
    """Detonate an exploding monster projectile: splash the player, show FX."""
    radius = bolt.get('splash_radius', 0.0)
    if radius > 0.0:
        center = [player_origin[0], player_origin[1], player_origin[2] + 4.0]
        d = math.sqrt(sum((center[i] - origin[i]) ** 2 for i in range(3)))
        if d < radius:
            _damage_player(int(round(bolt['damage'] * (1.0 - d / radius))))
    try:
        from quake2 import cl_weapon
        cl_weapon.spawn_explosion(origin, bolt.get('impact_model'),
                                  bolt.get('impact_sound'), now)
    except Exception:
        pass


def _update_bolts(frametime, player_origin, now):
    from quake2.cl_weapon import GRAVITY
    alive = []
    for bolt in _MonsterState.bolts:
        damage = bolt.get('damage', MONSTER_BOLT_DAMAGE)
        if now >= bolt['expire']:
            if bolt.get('explode'):
                _explode_bolt(bolt, bolt['origin'], player_origin, now)
            continue
        if bolt.get('gravity'):
            bolt['velocity'][2] -= GRAVITY * frametime
        start = bolt['origin']
        end = [start[i] + bolt['velocity'][i] * frametime for i in range(3)]

        tr = _trace(start, end)
        world_hit = tr is not None and (tr.fraction < 1.0 or tr.startsolid)
        seg_end = list(getattr(tr, 'endpos', end) or end) if world_hit else end

        t = _segment_box_t(start, seg_end, player_origin, PLAYER_BOX[0], PLAYER_BOX[1])
        if t is not None:
            point = [start[i] + (seg_end[i] - start[i]) * t for i in range(3)]
            if bolt.get('explode'):
                _explode_bolt(bolt, point, player_origin, now)
            else:
                _damage_player(damage)
            continue
        if world_hit:
            if bolt.get('explode'):
                _explode_bolt(bolt, seg_end, player_origin, now)
            continue

        bolt['origin'] = end
        alive.append(bolt)
    _MonsterState.bolts = alive


def _monster_frame(monster, model, index, now):
    path = monster['model_path']

    if monster['state'] in ('dying', 'dead'):
        first, count = _anim_range(path, model, 'death')
        elapsed_frames = int((now - monster['death_start']) * ANIM_FPS)
        if elapsed_frames >= count:
            monster['state'] = 'dead'
            return first + count - 1
        return first + elapsed_frames

    if monster['attack_start'] is not None:
        first, count = _anim_range(path, model, 'atta')
        elapsed_frames = int((now - monster['attack_start']) * ANIM_FPS)
        if elapsed_frames < count:
            return first + elapsed_frames
        monster['attack_start'] = None

    if monster.get('moving'):
        first, count = _anim_range(path, model, 'run')
        if count <= 1:
            first, count = _anim_range(path, model, 'walk')
        if count > 1:
            return first + (int(now * ANIM_FPS) + index) % count

    first, count = _anim_range(path, model, 'stand')
    return first + (int(now * ANIM_FPS) + index) % count


def _ensure_parsed():
    try:
        from quake2 import cmodel
        estr = cmodel.entity_string
    except Exception:
        return
    if estr is _MonsterState.entity_string:
        return
    _MonsterState.entity_string = estr
    _MonsterState.monsters = _spawn_from_entities(parse_entities(estr or ""))
    _MonsterState.bolts = []
    _MonsterState.gibs = []
    PlayerState.health = 100
    print(f"cl_monsters: spawned {len(_MonsterState.monsters)} monsters")


def Update(frametime, player_origin, now=None):
    """Advance monster AI and shots one frame. Returns entity dicts to render."""
    if now is None:
        now = time.time()

    _ensure_parsed()

    player_eye = [player_origin[0], player_origin[1], player_origin[2] + VIEWHEIGHT]
    _update_ai(frametime, player_eye, now)
    _update_bolts(frametime, player_origin, now)
    _update_gibs(frametime, now)

    entities = _gib_entities(now)
    for index, monster in enumerate(_MonsterState.monsters):
        if monster['state'] == 'gibbed':
            continue
        model = _get_model(monster['model_path'])
        if not model:
            continue
        entities.append({
            'model': model,
            'origin': monster['origin'],
            'angles': [0.0, monster['yaw'], 0.0],
            'frame': _monster_frame(monster, model, index, now),
            'skinnum': monster['skin'],
        })

    from quake2.cl_weapon import _vector_to_angles
    for bolt in _MonsterState.bolts:
        model = _get_model(bolt.get('model', MONSTER_WEAPONS['blaster']['model']))
        if not model:
            continue
        entities.append({
            'model': model,
            'origin': list(bolt['origin']),
            'angles': _vector_to_angles(bolt['velocity']),
        })
    return entities
