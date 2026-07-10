"""
cl_monsters.py - Client-side monster spawning and rendering (single-player)
Parses the loaded map's BSP entity string for monster entities and returns
render entities for them each frame. Monsters idle-animate their "stand"
frame sequence; no AI yet.
"""

import time

ANIM_FPS = 10.0

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


class _MonsterState:
    entity_string = None  # entity string the monsters were parsed from
    monsters = []         # dicts: {'classname', 'origin', 'angles', 'model_path', 'skin'}
    models = {}           # path -> loaded model or None
    stand_ranges = {}     # path -> (first_frame, frame_count)


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
        monsters.append({
            'classname': classname,
            'origin': origin,
            'angles': [0.0, yaw, 0.0],
            'model_path': model_path,
            'skin': skin,
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


def _stand_range(path, model):
    """First frame and length of the model's 'stand' animation."""
    if path not in _MonsterState.stand_ranges:
        first, count = 0, 1
        try:
            frames = model.mesh_data['frames']
            stand = [i for i, f in enumerate(frames) if f.name.lower().startswith('stand')]
            if stand:
                first = stand[0]
                count = 1
                while count < len(stand) and stand[count] == first + count:
                    count += 1
        except Exception:
            pass
        _MonsterState.stand_ranges[path] = (first, count)
    return _MonsterState.stand_ranges[path]


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
    print(f"cl_monsters: spawned {len(_MonsterState.monsters)} monsters")


def GetEntities(now=None):
    """Render entities for all monsters on the current map."""
    if now is None:
        now = time.time()

    _ensure_parsed()

    entities = []
    for index, monster in enumerate(_MonsterState.monsters):
        model = _get_model(monster['model_path'])
        if not model:
            continue
        first, count = _stand_range(monster['model_path'], model)
        # index offset staggers the animation so monsters don't move in sync
        frame = first + (int(now * ANIM_FPS) + index) % count
        entities.append({
            'model': model,
            'origin': monster['origin'],
            'angles': monster['angles'],
            'frame': frame,
            'skinnum': monster['skin'],
        })
    return entities
