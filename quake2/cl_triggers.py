"""
cl_triggers.py - brush touch triggers and the targets they fire (g_trigger.c)

Like the movers in cl_movers, triggers are parsed from the loaded map's BSP
entity string and run on the client. A trigger_multiple / trigger_once is a
BSP submodel used purely as a volume: walking into it fires everything sharing
its "target" name.

UseTargets() is the dispatcher for the whole port: it fires the target entities
handled here (target_changelevel) and hands the name to cl_movers so doors open
too. Targets this port has no implementation for are simply ignored.
"""

import time

from .cl_monsters import parse_entities
from .cl_input import PLAYER_MINS, PLAYER_MAXS

TRIGGER_NOT_PLAYER = 2     # spawnflag: the volume ignores the player
TRIGGER_TRIGGERED = 4      # spawnflag: starts dormant until something uses it

DEFAULT_WAIT = 0.2         # SP_trigger_multiple's default retrigger delay
TOUCH_CLASSES = ('trigger_multiple', 'trigger_once')


class _TriggerState:
    entity_string = None
    triggers = []
    changelevels = {}      # targetname -> "map$spawnpoint"
    pending_level = None   # map string to load at the end of the frame


def _float(keys, name, default):
    try:
        return float(keys.get(name, default))
    except (TypeError, ValueError):
        return default


def _boxes_overlap(mins_a, maxs_a, mins_b, maxs_b):
    return not (mins_a[0] > maxs_b[0] or maxs_a[0] < mins_b[0] or
                mins_a[1] > maxs_b[1] or maxs_a[1] < mins_b[1] or
                mins_a[2] > maxs_b[2] or maxs_a[2] < mins_b[2])


def _spawn_from_entities(entities):
    from . import cmodel

    triggers = []
    changelevels = {}

    for keys in entities:
        classname = keys.get('classname', '')

        if classname == 'target_changelevel':
            targetname = keys.get('targetname', '')
            mapname = keys.get('map', '')
            if targetname and mapname:
                changelevels[targetname] = mapname
            continue

        if classname not in TOUCH_CLASSES:
            continue

        model = keys.get('model', '')
        if not model.startswith('*'):
            continue
        try:
            index = int(model[1:])
        except ValueError:
            continue
        if index <= 0 or index >= len(cmodel.models):
            continue

        spawnflags = int(_float(keys, 'spawnflags', 0.0))
        if spawnflags & TRIGGER_NOT_PLAYER:
            continue
        if spawnflags & TRIGGER_TRIGGERED:
            continue  # dormant until used, and nothing here can wake it yet

        submodel = cmodel.models[index]
        # trigger_once fires a single time; trigger_multiple repeats after "wait"
        once = classname == 'trigger_once'
        triggers.append({
            'mins': list(submodel['mins']),
            'maxs': list(submodel['maxs']),
            'target': keys.get('target', ''),
            'delay': _float(keys, 'delay', 0.0),
            'wait': -1.0 if once else _float(keys, 'wait', DEFAULT_WAIT),
            'fire_at': None,     # set while a "delay" is counting down
            'ready_at': 0.0,     # next time this volume may fire again
            'spent': False,
        })

    return triggers, changelevels


def _ensure_parsed():
    try:
        from . import cmodel
        estr = cmodel.entity_string
    except Exception:
        return
    if estr is _TriggerState.entity_string:
        return
    _TriggerState.entity_string = estr
    _TriggerState.triggers, _TriggerState.changelevels = _spawn_from_entities(
        parse_entities(estr or ""))
    _TriggerState.pending_level = None
    print(f"cl_triggers: spawned {len(_TriggerState.triggers)} touch triggers, "
          f"{len(_TriggerState.changelevels)} changelevels")


def UseTargets(name, now=None):
    """G_UseTargets: fire everything that answers to this targetname."""
    if not name:
        return
    if now is None:
        now = time.time()

    if name in _TriggerState.changelevels:
        # Queue it: the map cannot be swapped out from under the running frame
        _TriggerState.pending_level = _TriggerState.changelevels[name]

    try:
        from . import cl_movers
        cl_movers.UseTargets(name, now)
    except Exception as e:
        print(f"cl_triggers: target error for {name}: {e}")


def _clear_transient_state():
    """Drop shots, gibs and explosions left over from the level we are leaving."""
    try:
        from . import cl_weapon
        cl_weapon._WeaponState.bolts = []
        cl_weapon._WeaponState.explosions = []
        cl_weapon._WeaponState.wall_impacts = []
    except Exception:
        pass


def ChangeLevel(mapstring):
    """target_changelevel: load "base2" / "base2$base1" (map$spawnpoint)."""
    from . import cmodel, sv_main

    level, _, spawnpoint = str(mapstring).partition('$')
    level = level.strip().lstrip('*')
    if not level:
        return False

    print(f"cl_triggers: changing level to {level}"
          f"{' at ' + spawnpoint if spawnpoint else ''}")

    try:
        cmodel.CM_LoadMap(f"maps/{level}.bsp", False, None)
    except Exception as e:
        print(f"cl_triggers: could not load maps/{level}.bsp: {e}")
        return False

    _clear_transient_state()

    # cl_view watches mapname and reloads the world model from it
    sv_main.server.spawnpoint = spawnpoint
    sv_main.server.mapname = level
    sv_main.server.state = 2
    sv_main.server.time = 0.0

    _place_player()
    return True


def _place_player():
    """Drop the player on the new map's start before the frame is drawn.

    Leaving it to cl_view's own map-change check would render one frame from
    the old level's position first.
    """
    try:
        from . import cl_input, cl_view
        origin = cl_view._find_spawn_point()
        if origin:
            cl_view._ViewState.vieworg = list(origin)
            cl_view._ViewState.spawned = True
        else:
            cl_view._ViewState.spawned = False
        cl_input._State.velocity = [0.0, 0.0, 0.0]
        cl_input._State.on_ground = False
    except Exception as e:
        print(f"cl_triggers: could not place the player: {e}")


def _fire(trigger, now):
    trigger['fire_at'] = None
    UseTargets(trigger['target'], now)
    if trigger['wait'] > 0:
        trigger['ready_at'] = now + trigger['wait']
    else:
        trigger['spent'] = True   # trigger_once is gone after one use


def Update(frametime, player_origin, now=None):
    """Touch-test every trigger volume, then apply a queued level change."""
    if now is None:
        now = time.time()

    _ensure_parsed()

    player_mins = [player_origin[i] + PLAYER_MINS[i] for i in range(3)]
    player_maxs = [player_origin[i] + PLAYER_MAXS[i] for i in range(3)]

    for trigger in _TriggerState.triggers:
        if trigger['fire_at'] is not None:
            if now >= trigger['fire_at']:
                _fire(trigger, now)
            continue
        if trigger['spent'] or now < trigger['ready_at']:
            continue
        if not _boxes_overlap(player_mins, player_maxs,
                              trigger['mins'], trigger['maxs']):
            continue
        if trigger['delay'] > 0:
            trigger['fire_at'] = now + trigger['delay']
            continue
        _fire(trigger, now)

    pending = _TriggerState.pending_level
    if pending:
        _TriggerState.pending_level = None
        ChangeLevel(pending)
