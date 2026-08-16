"""
cl_movers.py - func_door and func_button brush movers, ported from g_func.c

This engine simulates the world on the client (see cl_monsters/cl_weapon), so
movers are parsed straight out of the loaded map's BSP entity string. A mover
is a BSP submodel ("*32"): it renders through gl_rsurf's per-submodel batches
at the displacement published by SubmodelOffsets(), and ClipTrace() clips
traces against its current position so a closed door is a solid wall.

Doors without a targetname open by themselves when the player enters the
trigger volume around them (Think_SpawnDoorTrigger in the original). Doors with
a targetname wait to be fired by a button. Buttons press in when the player
walks into them, or when a shot hits them if the mapper gave them health.
"""

import math
import time

from .cl_monsters import parse_entities
from .cl_input import PLAYER_MINS, PLAYER_MAXS

DOOR_START_OPEN = 1
DOOR_TOGGLE = 32

DOOR_SPEED = 100.0
DOOR_LIP = 8.0
BUTTON_SPEED = 40.0
BUTTON_LIP = 4.0
DEFAULT_WAIT = 3.0

TRIGGER_EXPAND = 60.0      # trigger volume grows this far in x/y around a door
TRIGGER_DEBOUNCE = 1.0     # seconds between retriggers while standing in it
BLOCKED_DEBOUNCE = 0.5     # min seconds between reverse sounds when obstructed
TOUCH_MARGIN = 2.0         # collision parks the player just off the brush face

SOUND_DOOR_START = "sound/doors/dr1_strt.wav"
SOUND_DOOR_END = "sound/doors/dr1_end.wav"
SOUND_BUTTON = "sound/switches/butn2.wav"


class _MoverState:
    entity_string = None   # entity string the movers were parsed from
    movers = []            # doors + buttons, everything holding a submodel
    doors = []
    buttons = []
    teams = []
    sounds = {}
    mixer_ready = False


def _play_sound(path):
    try:
        import io
        import pygame
        if not _MoverState.mixer_ready:
            _MoverState.mixer_ready = True
            if not pygame.mixer.get_init():
                pygame.mixer.init()
        if path not in _MoverState.sounds:
            sound = None
            from quake2.files import FS_LoadFile
            from quake2.cl_weapon import DEVELOPMENT_AUDIO_VOLUME
            data, length = FS_LoadFile(path)
            if data:
                sound = pygame.mixer.Sound(file=io.BytesIO(bytes(data)))
                sound.set_volume(DEVELOPMENT_AUDIO_VOLUME)
            _MoverState.sounds[path] = sound
        if _MoverState.sounds[path]:
            _MoverState.sounds[path].play()
    except Exception as e:
        print(f"cl_movers: sound error for {path}: {e}")
        _MoverState.sounds[path] = None


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


def _mover_box(mover, margin=0.0):
    offset = mover['offset']
    mins = [mover['mins'][i] + offset[i] - margin for i in range(3)]
    maxs = [mover['maxs'][i] + offset[i] + margin for i in range(3)]
    return mins, maxs


def _player_box(origin):
    mins = [origin[i] + PLAYER_MINS[i] for i in range(3)]
    maxs = [origin[i] + PLAYER_MAXS[i] for i in range(3)]
    return mins, maxs


def _player_inside(mover, player_origin, player_mins, player_maxs):
    """SV_TestEntityPosition: is the player box stuck in this mover's brushes?

    The bounding box of a big door covers far more than its geometry, so the
    cheap box test only decides when it is worth asking the brush hull.
    """
    mover_mins, mover_maxs = _mover_box(mover)
    if not _boxes_overlap(player_mins, player_maxs, mover_mins, mover_maxs):
        return False

    from .cmodel import CM_TransformedBoxTrace, MASK_PLAYERSOLID
    tr = CM_TransformedBoxTrace(player_origin, player_origin, PLAYER_MINS, PLAYER_MAXS,
                                mover['index'], MASK_PLAYERSOLID,
                                mover['offset'], [0.0, 0.0, 0.0])
    return bool(tr.startsolid or tr.allsolid)


def _update_offset(mover):
    frac = mover['frac']
    mover['offset'] = [mover['closed'][i] + (mover['open'][i] - mover['closed'][i]) * frac
                       for i in range(3)]


def _make_mover(keys, kind, default_speed, default_lip):
    """Shared func_door / func_button spawn: submodel, travel and speed."""
    from . import cmodel

    model = keys.get('model', '')
    if not model.startswith('*'):
        return None
    try:
        index = int(model[1:])
    except ValueError:
        return None
    if index <= 0 or index >= len(cmodel.models):
        return None

    submodel = cmodel.models[index]
    mins = list(submodel['mins'])
    maxs = list(submodel['maxs'])
    size = [maxs[i] - mins[i] for i in range(3)]

    movedir = _movedir(keys)
    lip = _float(keys, 'lip', default_lip)
    distance = (abs(movedir[0]) * size[0] + abs(movedir[1]) * size[1] +
                abs(movedir[2]) * size[2]) - lip
    if distance <= 0.0:
        return None  # degenerate; leave it standing as static geometry

    speed = _float(keys, 'speed', default_speed) or default_speed
    spawnflags = int(_float(keys, 'spawnflags', 0.0))
    travel = [movedir[i] * distance for i in range(3)]

    if spawnflags & DOOR_START_OPEN:
        # The original swaps start/end: the mover spawns where it would have
        # opened to, and "opening" carries it back to the brush position.
        closed, opened = travel, [0.0, 0.0, 0.0]
    else:
        closed, opened = [0.0, 0.0, 0.0], travel

    mover = {
        'kind': kind,
        'index': index,
        'mins': mins,
        'maxs': maxs,
        'closed': closed,
        'open': opened,
        'frac': 0.0,                    # 0 = closed/out, 1 = open/pressed
        'frac_speed': speed / distance,
        'state': 'bottom',              # bottom -> up -> top -> down
        'wait': _float(keys, 'wait', DEFAULT_WAIT),
        'spawnflags': spawnflags,
        'close_at': None,
        'audible': True,
        'offset': [0.0, 0.0, 0.0],
    }
    _update_offset(mover)
    return mover


def _spawn_from_entities(entities):
    doors = []
    buttons = []

    for keys in entities:
        classname = keys.get('classname', '')

        if classname == 'func_door':
            door = _make_mover(keys, 'door', DOOR_SPEED, DOOR_LIP)
            if door is None:
                continue
            door.update({
                'toggle': bool(door['spawnflags'] & DOOR_TOGGLE),
                'blocked_until': 0.0,
                'team': keys.get('team', ''),
                'targetname': keys.get('targetname', ''),
                'triggered': bool(keys.get('targetname')) or bool(keys.get('health')),
            })
            doors.append(door)

        elif classname == 'func_button':
            button = _make_mover(keys, 'button', BUTTON_SPEED, BUTTON_LIP)
            if button is None:
                continue
            button.update({
                'target': keys.get('target', ''),
                'health': _float(keys, 'health', 0.0),
                # Shootable buttons and trigger-fired ones ignore being walked into
                'touchable': not keys.get('health') and not keys.get('targetname'),
            })
            buttons.append(button)

    return doors, buttons


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
    if estr is _MoverState.entity_string:
        return
    _MoverState.entity_string = estr
    doors, buttons = _spawn_from_entities(parse_entities(estr or ""))
    _MoverState.doors = doors
    _MoverState.buttons = buttons
    _MoverState.movers = doors + buttons
    _MoverState.teams = _build_teams(doors)
    print(f"cl_movers: spawned {len(doors)} doors, {len(buttons)} buttons")


def _use_team(team, now):
    """door_use: raise every door of the team, or hold an open one open."""
    started = False
    for door in team['doors']:
        if door['toggle'] and door['state'] in ('up', 'top'):
            door['state'] = 'down'
            door['close_at'] = None
            started = True
            continue
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
        _play_sound(SOUND_DOOR_START)


def _fire_targets(name, now):
    """G_UseTargets, narrowed to the doors this port knows how to move."""
    if not name:
        return
    for team in _MoverState.teams:
        if any(door['targetname'] == name for door in team['doors']):
            _use_team(team, now)


def _press_button(button, now):
    """button_fire: sink the button in unless it is already down."""
    if button['state'] in ('up', 'top'):
        return
    button['state'] = 'up'
    button['close_at'] = None
    _play_sound(SOUND_BUTTON)


def _reverse(door, now):
    """door_blocked: a non-crusher door backs off whatever obstructs it."""
    door['state'] = 'up' if door['state'] == 'down' else 'down'
    door['close_at'] = None
    if now >= door['blocked_until']:
        door['blocked_until'] = now + BLOCKED_DEBOUNCE
        if door['audible']:
            _play_sound(SOUND_DOOR_START)


def _advance(mover, frametime):
    """Slide the mover one frame along its travel; returns the previous frac."""
    previous = mover['frac']
    if mover['state'] == 'up':
        mover['frac'] = min(1.0, previous + mover['frac_speed'] * frametime)
    else:
        mover['frac'] = max(0.0, previous - mover['frac_speed'] * frametime)
    _update_offset(mover)
    return previous


def _move_door(door, frametime, now, player_origin, player_mins, player_maxs):
    state = door['state']

    if state == 'top':
        if door['close_at'] is not None and now >= door['close_at']:
            door['state'] = 'down'
            door['close_at'] = None
            if door['audible']:
                _play_sound(SOUND_DOOR_START)
        return
    if state == 'bottom':
        return

    previous = _advance(door, frametime)

    if _player_inside(door, player_origin, player_mins, player_maxs):
        door['frac'] = previous
        _update_offset(door)
        _reverse(door, now)
        return

    if door['frac'] >= 1.0:
        door['state'] = 'top'
        if door['wait'] >= 0 and not door['toggle']:
            door['close_at'] = now + door['wait']
        if door['audible']:
            _play_sound(SOUND_DOOR_END)
    elif door['frac'] <= 0.0:
        door['state'] = 'bottom'
        if door['audible']:
            _play_sound(SOUND_DOOR_END)


def _move_button(button, frametime, now, player_mins, player_maxs):
    state = button['state']

    if state == 'bottom':
        if button['touchable']:
            touch_mins, touch_maxs = _mover_box(button, TOUCH_MARGIN)
            if _boxes_overlap(player_mins, player_maxs, touch_mins, touch_maxs):
                _press_button(button, now)
        return

    if state == 'top':
        # wait -1 leaves the button held in, as in the original
        if button['close_at'] is not None and now >= button['close_at']:
            button['state'] = 'down'
            button['close_at'] = None
        return

    _advance(button, frametime)

    if button['frac'] >= 1.0:
        # button_wait: fully pressed, so fire whatever it targets
        button['state'] = 'top'
        if button['wait'] >= 0:
            button['close_at'] = now + button['wait']
        _fire_targets(button['target'], now)
    elif button['frac'] <= 0.0:
        button['state'] = 'bottom'


def Update(frametime, player_origin, now=None):
    """Advance every door and button one frame."""
    if now is None:
        now = time.time()

    _ensure_parsed()
    if not _MoverState.movers:
        return

    player_mins, player_maxs = _player_box(player_origin)

    for team in _MoverState.teams:
        if not team['auto']:
            continue
        if now < team['debounce']:
            continue
        if _boxes_overlap(player_mins, player_maxs,
                          team['trigger_mins'], team['trigger_maxs']):
            team['debounce'] = now + TRIGGER_DEBOUNCE
            _use_team(team, now)

    for door in _MoverState.doors:
        _move_door(door, frametime, now, player_origin, player_mins, player_maxs)
    for button in _MoverState.buttons:
        _move_button(button, frametime, now, player_mins, player_maxs)


def SubmodelOffsets():
    """{submodel index: displacement} for the renderer."""
    return {mover['index']: mover['offset'] for mover in _MoverState.movers}


def Damage(trace_obj, damage, now=None):
    """button_killed: a shot that lands on a shootable button presses it."""
    mover = getattr(trace_obj, '_mover', None) if trace_obj is not None else None
    if not mover or mover['kind'] != 'button' or damage <= 0:
        return False
    if not mover['health']:
        return False
    mover['health'] = 0.0  # the original stops taking damage once triggered
    _press_button(mover, now if now is not None else time.time())
    return True


def _segment_may_hit(start, end, mins, maxs, box_mins, box_maxs):
    """Cheap reject: does the swept box's bounding box touch the mover's?"""
    for i in range(3):
        lo = min(start[i], end[i]) + mins[i]
        hi = max(start[i], end[i]) + maxs[i]
        if lo > box_maxs[i] or hi < box_mins[i]:
            return False
    return True


def ClipTrace(start, end, mins, maxs, trace_obj, mask=None):
    """Clip a world trace against the movers at their current positions.

    Returns whichever result stops first; mover brushes live in their own BSP
    submodel hulls, so a world trace alone passes straight through them. The
    winning mover is tagged on the trace for Damage().
    """
    if not _MoverState.movers:
        return trace_obj

    from .cmodel import CM_TransformedBoxTrace, MASK_PLAYERSOLID

    if mask is None:
        mask = MASK_PLAYERSOLID

    best = trace_obj
    for mover in _MoverState.movers:
        mover_mins, mover_maxs = _mover_box(mover)
        if not _segment_may_hit(start, end, mins, maxs, mover_mins, mover_maxs):
            continue

        tr = CM_TransformedBoxTrace(start, end, mins, maxs, mover['index'], mask,
                                    mover['offset'], [0.0, 0.0, 0.0])
        if tr.fraction < 1.0 or tr.startsolid:
            tr._mover = mover

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
