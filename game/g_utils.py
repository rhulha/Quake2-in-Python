import math
import random as _random

from .reference_import import gi
from .global_vars import level
from shared.QClasses import edict_t
from shared.QConstants import AREA_TRIGGERS, AREA_SOLID, MASK_ALL, MAX_EDICTS
from shared.QEnums import solid_t, damage_t


def G_ProjectSource(point, distance, forward, right, result):
    result[0] = point[0] + forward[0] * distance[0] + right[0] * distance[1]
    result[1] = point[1] + forward[1] * distance[0] + right[1] * distance[1]
    result[2] = point[2] + forward[2] * distance[0] + right[2] * distance[1] + distance[2]


def _game():
    """Late-import game state to avoid circular imports."""
    from .g_main import game
    return game


def G_Find(from_ent, fieldname, match):
    """Find first entity after from_ent where entity.fieldname == match.
    Pass None for from_ent to start from the beginning.
    Returns matching entity or None.
    """
    g = _game()
    start = 0 if from_ent is None else (from_ent.index + 1)
    for i in range(start, len(g.entities)):
        e = g.entities[i]
        if e is None or not e.inuse:
            continue
        val = getattr(e, fieldname, None)
        if val == match:
            return e
    return None


def findradius(org, rad):
    """Return list of entities within radius rad of org."""
    g = _game()
    result = []
    rad2 = rad * rad
    for e in g.entities:
        if e is None or not e.inuse:
            continue
        if e.solid == solid_t.SOLID_NOT:
            continue
        eorg = [
            org[0] - (e.s.origin[0] + (e.mins[0] + e.maxs[0]) * 0.5),
            org[1] - (e.s.origin[1] + (e.mins[1] + e.maxs[1]) * 0.5),
            org[2] - (e.s.origin[2] + (e.mins[2] + e.maxs[2]) * 0.5),
        ]
        dist2 = eorg[0]*eorg[0] + eorg[1]*eorg[1] + eorg[2]*eorg[2]
        if dist2 <= rad2:
            result.append(e)
    return result


def G_PickTarget(targetname):
    """Return a random entity that has the given targetname."""
    if not targetname:
        return None
    num_choices = 0
    choices = []
    ent = None
    while True:
        ent = G_Find(ent, 'targetname', targetname)
        if ent is None:
            break
        choices.append(ent)
        num_choices += 1
    if num_choices == 0:
        return None
    return _random.choice(choices)


def Think_Delay(ent):
    """Think function: fire targets after a delay."""
    G_UseTargets(ent, ent.activator)
    G_FreeEdict(ent)


def G_UseTargets(ent, activator):
    """Trigger all entities whose targetname matches ent.target.
    Also kills any entity with ent.killtarget, and prints ent.message.
    """
    if ent.killtarget:
        t = None
        while True:
            t = G_Find(t, 'targetname', ent.killtarget)
            if t is None:
                break
            G_FreeEdict(t)

    if not ent.target:
        return

    t = None
    while True:
        t = G_Find(t, 'targetname', ent.target)
        if t is None:
            break
        if t is ent:
            continue
        if t.use:
            t.use(t, ent, activator)


def tv(v):
    """Format a vector as a string (for debug prints)."""
    return '(%g %g %g)' % (v[0], v[1], v[2])


def vtos(v):
    return tv(v)


_VEC_UP    = [0, -1, 0]
_VEC_DOWN  = [0, -2, 0]
_MOVEDIR_UP   = [0, 0, 1]
_MOVEDIR_DOWN = [0, 0, -1]

def G_SetMovedir(angles, movedir):
    """Compute movedir from angles.  Special cases: angle -1 → up, -2 → down."""
    if angles == _VEC_UP or angles[1] == -1:
        movedir[:] = _MOVEDIR_UP
    elif angles == _VEC_DOWN or angles[1] == -2:
        movedir[:] = _MOVEDIR_DOWN
    else:
        from .q_shared import AngleVectors
        AngleVectors(angles, movedir, None, None)
    angles[:] = [0, 0, 0]


def vectoyaw(vec):
    """Return the yaw angle in degrees for direction vector vec."""
    if vec[1] == 0 and vec[0] == 0:
        return 0.0
    yaw = math.degrees(math.atan2(vec[1], vec[0]))
    if yaw < 0:
        yaw += 360
    return yaw


def vectoangles(value, angles):
    """Convert a direction vector to pitch/yaw/roll angles (degrees)."""
    if value[1] == 0 and value[0] == 0:
        yaw = 0.0
        pitch = 90.0 if value[2] > 0 else 270.0
    else:
        yaw = math.degrees(math.atan2(value[1], value[0]))
        if yaw < 0:
            yaw += 360
        forward = math.sqrt(value[0]*value[0] + value[1]*value[1])
        pitch = math.degrees(math.atan2(value[2], forward))
        if pitch < 0:
            pitch += 360
    angles[0] = pitch
    angles[1] = yaw
    angles[2] = 0


def G_CopyString(s):
    """Return a copy of string s (trivial in Python)."""
    return str(s) if s is not None else ""


def G_InitEdict(e):
    """Reset an edict slot to clean state, preserving its index."""
    idx = e.index
    e.__init__()
    e.index = idx
    e.inuse = True
    e.s.number = idx


def G_Spawn():
    """Allocate a new entity from the pool.  Returns the edict_t.
    Reuses dead slots; expands the pool up to MAX_EDICTS.
    """
    g = _game()
    # Slots 0..maxclients are reserved (world + players)
    start = g.maxclients + 1
    for i in range(start, len(g.entities)):
        e = g.entities[i]
        if e is None:
            e = edict_t()
            e.index = i
            g.entities[i] = e
            G_InitEdict(e)
            return e
        if not e.inuse and (level.time - e.freetime) > 0.5:
            G_InitEdict(e)
            return e

    if len(g.entities) >= MAX_EDICTS:
        raise RuntimeError("G_Spawn: no free edicts")

    e = edict_t()
    e.index = len(g.entities)
    g.entities.append(e)
    G_InitEdict(e)
    return e


def G_FreeEdict(ed):
    """Mark an entity as free so it can be recycled."""
    if gi.unlinkentity:
        gi.unlinkentity(ed)
    ed.inuse = False
    ed.classname = "freed"
    ed.freetime = level.time


def G_TouchTriggers(ent):
    """Check ent against all SOLID_TRIGGER entities and fire their touch callbacks."""
    if not gi.BoxEdicts:
        return
    if not ent.inuse:
        return

    touch_list = gi.BoxEdicts(ent.absmin, ent.absmax, [], 128, AREA_TRIGGERS)
    for hit in touch_list:
        if hit is ent:
            continue
        if not hit.inuse:
            continue
        if hit.touch:
            hit.touch(hit, ent, None, None)


def G_TouchSolids(ent):
    """Check ent against all SOLID_BBOX/BSP entities and fire touch callbacks."""
    if not gi.BoxEdicts:
        return
    if not ent.inuse:
        return

    touch_list = gi.BoxEdicts(ent.absmin, ent.absmax, [], 128, AREA_SOLID)
    for hit in touch_list:
        if hit is ent:
            continue
        if not hit.inuse:
            continue
        if hit.touch:
            hit.touch(hit, ent, None, None)
        if not ent.inuse:
            break


def KillBox(ent):
    """Kill everything in the entity's bounding box (used for teleports)."""
    from .g_combat import T_Damage
    from shared.QEnums import damage_t as _dt
    while True:
        if not gi.BoxEdicts:
            break
        touch_list = gi.BoxEdicts(ent.absmin, ent.absmax, [], 128, AREA_SOLID)
        found = False
        for hit in touch_list:
            if hit is ent:
                continue
            if hit.takedamage == _dt.DAMAGE_NO.value:
                continue
            T_Damage(hit, ent, ent, [0,0,0], hit.s.origin, [0,0,0],
                     100000, 1, 0x8, 12)  # MOD_TELEFRAG
            found = True
        if not found:
            break
