"""
cl_doors.py - func_door movers, ported from the original g_func.c

This engine simulates the world on the client (see cl_monsters/cl_weapon), so
doors are parsed straight out of the loaded map's BSP entity string. A door is
a BSP submodel ("*32"): it renders through gl_rsurf's per-submodel batches at
the displacement published by SubmodelOffsets(), and ClipTrace() clips traces
against its current position so a closed door is a solid wall.

Doors without a targetname open by themselves when the player enters the
trigger volume around them (Think_SpawnDoorTrigger in the original). Doors with
a targetname wait for a trigger and stay shut until buttons/triggers exist.
"""

import math
import time

from .cl_monsters import parse_entities
from .cl_input import PLAYER_MINS, PLAYER_MAXS

DOOR_START_OPEN = 1
DOOR_TOGGLE = 32

DEFAULT_SPEED = 100.0
DEFAULT_WAIT = 3.0
DEFAULT_LIP = 8.0

TRIGGER_EXPAND = 60.0      # trigger volume grows this far in x/y around the door
TRIGGER_DEBOUNCE = 1.0     # seconds between retriggers while standing in it
BLOCKED_DEBOUNCE = 0.5     # min seconds between reverse sounds when obstructed

SOUND_START = "sound/doors/dr1_strt.wav"
SOUND_END = "sound/doors/dr1_end.wav"


class _DoorState:
    entity_string = None   # entity string the doors were parsed from
    doors = []
    teams = []
    sounds = {}
    mixer_ready = False


def _play_sound(path):
    try:
        import io
        import pygame
        if not _DoorState.mixer_ready:
            _DoorState.mixer_ready = True
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        if path not in _DoorState.sounds:
            sound = None
            from quake2.files import FS_LoadFile
            from quake2.cl_weapon import DEVELOPMENT_AUDIO_VOLUME
            data, length = FS_LoadFile(path)
            if data:
                sound = pygame.mixer.Sound(file=io.BytesIO(bytes(data)))
                sound.set_volume(DEVELOPMENT_AUDIO_VOLUME)
            _DoorState.sounds[path] = sound
        if _DoorState.sounds[path]:
            _DoorState.sounds[path].play()
    except Exception as e:
        print(f"cl_doors: sound error for {path}: {e}")
        _DoorState.sounds[path] = None


def _float(keys, name, default):
    try:
        value = float(keys.get(name, default))
    except (TypeError, ValueError):
        return default
    return value


def _movedir(keys):
    """G_SetMovedir: "angle" -1 means up, -2 down, anything else is a yaw."""
    angle = _float(keys, 'angle', 0.0)
    if angle == -1.0:
        return [0.0, 0.0, 1.0]
    if angle == -2.0:
        return [0.0, 0.0, -1.0]
    yaw = math.radians(angle)
    return [math.cos(yaw), math.sin(yaw), 0.0]


def _boxes_overlap(mins_a, maxs_a, mins_b, maxs_b):
    return not (mins_a[0] > maxs_b[0] or maxs_a[0] < mins_b[0] or
                mins_a[1] > maxs_b[1] or maxs_a[1] < mins_b[1] or
                mins_a[2] > maxs_b[2] or maxs_a[2] < mins_b[2])


def _door_box(door):
    offset = door['offset']
    mins = [door['mins'][i] + offset[i] for i in range(3)]
    maxs = [door['maxs'][i] + offset[i] for i in range(3)]
    return mins, maxs


def _player_box(origin):
    mins = [origin[i] + PLAYER_MINS[i] for i in range(3)]
    maxs = [origin[i] + PLAYER_MAXS[i] for i in range(3)]
    return mins, maxs


def _update_offset(door):
    frac = door['frac']
    door['offset'] = [door['closed'][i] + (door['open'][i] - door['closed'][i]) * frac
                      for i in range(3)]


def _spawn_from_entities(entities):
    from . import cmodel

    doors = []
    for keys in entities:
        if keys.get('classname') != 'func_door':
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

        submodel = cmodel.models[index]
        mins = list(submodel['mins'])
        maxs = list(submodel['maxs'])
        size = [maxs[i] - mins[i] for i in range(3)]

        movedir = _movedir(keys)
        lip = _float(keys, 'lip', DEFAULT_LIP)
        distance = abs(movedir[0] * size[0] + movedir[1] * size[1] +
                       movedir[2] * size[2]) - lip
        if distance <= 0.0:
            continue  # degenerate; leave it standing as static geometry

        speed = _float(keys, 'speed', DEFAULT_SPEED) or DEFAULT_SPEED
        wait = _float(keys, 'wait', DEFAULT_WAIT)
        spawnflags = int(_float(keys, 'spawnflags', 0.0))

        travel = [movedir[i] * distance for i in range(3)]
        if spawnflags & DOOR_START_OPEN:
            # The original swaps start/end: the door spawns where it would have
            # opened to, and "opening" carries it back to the brush position.
            closed, opened = travel, [0.0, 0.0, 0.0]
        else:
            closed, opened = [0.0, 0.0, 0.0], travel

        door = {
            'index': index,
            'mins': mins,
            'maxs': maxs,
            'closed': closed,
            'open': opened,
            'frac': 0.0,                    # 0 = closed, 1 = open
            'frac_speed': speed / distance,
            'state': 'bottom',              # bottom -> up -> top -> down
            'wait': wait,
            'toggle': bool(spawnflags & DOOR_TOGGLE),
            'close_at': None,
            'blocked_until': 0.0,
            'team': keys.get('team', ''),
            'triggered': bool(keys.get('targetname')) or bool(keys.get('health')),
            'offset': [0.0, 0.0, 0.0],
        }
        _update_offset(door)
        doors.append(door)

    return doors


def _build_teams(doors):
    """Group doors sharing a "team" key; each team gets one trigger volume."""
    teams = []
    by_name = {}
    for door in doors:
        name = door['team']
        if name and name in by_name:
            by_name[name]['doors'].append(door)
            continue
        team = {'doors': [door], 'debounce': 0.0}
        if name:
            by_name[name] = team
        teams.append(team)

    for team in teams:
        # Doors that wait on a trigger never grow a proximity trigger
        team['auto'] = not any(door['triggered'] for door in team['doors'])

        # Only the first door of a pair is audible, as in the original
        for position, door in enumerate(team['doors']):
            door['audible'] = position == 0

        mins = [min(door['mins'][i] + door['offset'][i] for door in team['doors'])
                for i in range(3)]
        maxs = [max(door['maxs'][i] + door['offset'][i] for door in team['doors'])
                for i in range(3)]
        team['trigger_mins'] = [mins[0] - TRIGGER_EXPAND, mins[1] - TRIGGER_EXPAND, mins[2]]
        team['trigger_maxs'] = [maxs[0] + TRIGGER_EXPAND, maxs[1] + TRIGGER_EXPAND, maxs[2]]

    return teams


def _ensure_parsed():
    try:
        from . import cmodel
        estr = cmodel.entity_string
    except Exception:
        return
    if estr is _DoorState.entity_string:
        return
    _DoorState.entity_string = estr
    _DoorState.doors = _spawn_from_entities(parse_entities(estr or ""))
    _DoorState.teams = _build_teams(_DoorState.doors)
    print(f"cl_doors: spawned {len(_DoorState.doors)} doors")


def _open_team(team, now):
    """door_use: raise every door of the team, or hold an open one open."""
    started = False
    for door in team['doors']:
        if door['state'] == 'up':
            continue
        if door['state'] == 'top':
            # Already open and someone is still standing there: restart the wait
            if door['wait'] >= 0 and not door['toggle']:
                door['close_at'] = now + door['wait']
            continue
        door['state'] = 'up'
        door['close_at'] = None
        started = True
    if started:
        _play_sound(SOUND_START)


def _reverse(door, now):
    """door_blocked: a non-crusher door backs off whatever obstructs it."""
    door['state'] = 'up' if door['state'] == 'down' else 'down'
    door['close_at'] = None
    if now >= door['blocked_until']:
        door['blocked_until'] = now + BLOCKED_DEBOUNCE
        if door['audible']:
            _play_sound(SOUND_START)


def _move_door(door, frametime, now, player_mins, player_maxs):
    state = door['state']

    if state == 'top':
        if door['close_at'] is not None and now >= door['close_at']:
            door['state'] = 'down'
            door['close_at'] = None
            if door['audible']:
                _play_sound(SOUND_START)
        return
    if state == 'bottom':
        return

    previous = door['frac']
    if state == 'up':
        door['frac'] = min(1.0, previous + door['frac_speed'] * frametime)
    else:
        door['frac'] = max(0.0, previous - door['frac_speed'] * frametime)
    _update_offset(door)

    door_mins, door_maxs = _door_box(door)
    if _boxes_overlap(player_mins, player_maxs, door_mins, door_maxs):
        door['frac'] = previous
        _update_offset(door)
        _reverse(door, now)
        return

    if door['frac'] >= 1.0:
        door['state'] = 'top'
        if door['wait'] >= 0 and not door['toggle']:
            door['close_at'] = now + door['wait']
        if door['audible']:
            _play_sound(SOUND_END)
    elif door['frac'] <= 0.0:
        door['state'] = 'bottom'
        if door['audible']:
            _play_sound(SOUND_END)


def Update(frametime, player_origin, now=None):
    """Advance every door one frame."""
    if now is None:
        now = time.time()

    _ensure_parsed()
    if not _DoorState.doors:
        return

    player_mins, player_maxs = _player_box(player_origin)

    for team in _DoorState.teams:
        if not team['auto']:
            continue
        if now < team['debounce']:
            continue
        if _boxes_overlap(player_mins, player_maxs,
                          team['trigger_mins'], team['trigger_maxs']):
            team['debounce'] = now + TRIGGER_DEBOUNCE
            _open_team(team, now)

    for door in _DoorState.doors:
        _move_door(door, frametime, now, player_mins, player_maxs)


def SubmodelOffsets():
    """{submodel index: displacement} for the renderer."""
    return {door['index']: door['offset'] for door in _DoorState.doors}


def _segment_may_hit(start, end, mins, maxs, box_mins, box_maxs):
    """Cheap reject: does the swept box's bounding box touch the door's?"""
    for i in range(3):
        lo = min(start[i], end[i]) + mins[i]
        hi = max(start[i], end[i]) + maxs[i]
        if lo > box_maxs[i] or hi < box_mins[i]:
            return False
    return True


def ClipTrace(start, end, mins, maxs, trace_obj, mask=None):
    """Clip a world trace against the doors at their current positions.

    Returns whichever result stops first; door brushes live in their own BSP
    submodel hulls, so a world trace alone passes straight through them.
    """
    if not _DoorState.doors:
        return trace_obj

    from .cmodel import CM_TransformedBoxTrace, MASK_PLAYERSOLID

    if mask is None:
        mask = MASK_PLAYERSOLID

    best = trace_obj
    for door in _DoorState.doors:
        door_mins, door_maxs = _door_box(door)
        if not _segment_may_hit(start, end, mins, maxs, door_mins, door_maxs):
            continue

        tr = CM_TransformedBoxTrace(start, end, mins, maxs, door['index'], mask,
                                    door['offset'], [0.0, 0.0, 0.0])
        if best is None:
            best = tr
            continue

        if tr.fraction < best.fraction:
            startsolid = best.startsolid or tr.startsolid
            allsolid = best.allsolid or tr.allsolid
            best = tr
            best.startsolid = startsolid
            best.allsolid = allsolid
        else:
            best.startsolid = best.startsolid or tr.startsolid
            best.allsolid = best.allsolid or tr.allsolid

    return best
