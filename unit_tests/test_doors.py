"""Regression tests for func_door movers (quake2/cl_doors.py), against base1."""

import os
import sys

import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)

from quake2 import cl_doors, cl_input, cmodel
from quake2.files import FS_InitFilesystem

# base1's upward-sliding door (BSP submodel *19) and a spot in front of it
DOOR_INDEX = 19
APPROACH = [-1250.0, 1630.0, -23.0]     # outside the door's trigger volume
IN_TRIGGER = [-1165.0, 1630.0, -23.0]   # inside it
FRAME = 1.0 / 30.0


@pytest.fixture(scope="module")
def base1():
    try:
        FS_InitFilesystem()
    except Exception:
        pass
    cmodel.CM_LoadMap("maps/base1.bsp", False, None)
    assert cmodel.num_models > 0, "base1.bsp did not load"
    cl_doors._DoorState.entity_string = None
    cl_doors._ensure_parsed()
    return cl_doors._DoorState


@pytest.fixture
def door(base1, monkeypatch):
    """The map's door 19, reset to closed, with audio disabled."""
    monkeypatch.setattr(cl_doors, "_play_sound", lambda _path: None)
    entry = next(d for d in base1.doors if d['index'] == DOOR_INDEX)
    entry['frac'] = 0.0
    entry['state'] = 'bottom'
    entry['close_at'] = None
    cl_doors._update_offset(entry)
    for team in base1.teams:
        team['debounce'] = 0.0
    return entry


def test_door_parsed_from_entity_string(base1):
    """base1's four func_doors are picked up with their travel distances."""
    indices = sorted(d['index'] for d in base1.doors)
    assert indices == [19, 31, 32, 33]

    door19 = next(d for d in base1.doors if d['index'] == 19)
    assert door19['open'] == [0.0, 0.0, 120.0]  # "angle" "-1" slides straight up
    assert door19['triggered'] is False

    pair = [d for d in base1.doors if d['index'] in (32, 33)]
    assert all(d['team'] == '1' for d in pair)
    assert [t['auto'] for t in base1.teams if len(t['doors']) == 2] == [True]


def test_closed_door_blocks_a_trace(door):
    """A closed door is solid even though its brushes are not in the world hull."""
    y = (door['mins'][1] + door['maxs'][1]) * 0.5
    z = door['mins'][2] + 30.0
    start = [door['mins'][0] - 60.0, y, z]
    end = [door['maxs'][0] + 60.0, y, z]

    world = cmodel.CM_BoxTrace(start, end, cl_input.PLAYER_MINS, cl_input.PLAYER_MAXS,
                               0, cmodel.MASK_PLAYERSOLID)
    assert world.fraction == 1.0, "world hull alone should not contain the door"

    clipped = cl_doors.ClipTrace(start, end, cl_input.PLAYER_MINS, cl_input.PLAYER_MAXS,
                                 world, cmodel.MASK_PLAYERSOLID)
    assert clipped.fraction < 1.0


def test_open_door_lets_a_trace_through(door):
    """Once raised, the same trace runs clear."""
    door['frac'] = 1.0
    cl_doors._update_offset(door)

    y = (door['mins'][1] + door['maxs'][1]) * 0.5
    z = door['mins'][2] + 30.0
    start = [door['mins'][0] - 60.0, y, z]
    end = [door['maxs'][0] + 60.0, y, z]

    world = cmodel.CM_BoxTrace(start, end, cl_input.PLAYER_MINS, cl_input.PLAYER_MAXS,
                               0, cmodel.MASK_PLAYERSOLID)
    clipped = cl_doors.ClipTrace(start, end, cl_input.PLAYER_MINS, cl_input.PLAYER_MAXS,
                                 world, cmodel.MASK_PLAYERSOLID)
    assert clipped.fraction == 1.0


def test_door_opens_on_approach_and_closes_after_the_wait(door):
    """Full cycle: bottom -> up -> top, then closes once the player leaves."""
    now = 0.0
    cl_doors.Update(FRAME, APPROACH, now=now)
    assert door['state'] == 'bottom'

    for _ in range(60):  # two seconds standing in the trigger
        now += FRAME
        cl_doors.Update(FRAME, IN_TRIGGER, now=now)
    assert door['state'] == 'top'
    assert door['offset'] == [0.0, 0.0, 120.0]

    for _ in range(180):  # six seconds away: 3s wait plus the ride down
        now += FRAME
        cl_doors.Update(FRAME, APPROACH, now=now)
    assert door['state'] == 'bottom'
    assert door['offset'] == [0.0, 0.0, 0.0]


def test_closing_door_reverses_off_the_player(door):
    """door_blocked: a closing door backs off instead of crushing."""
    door['frac'] = 1.0
    door['state'] = 'down'
    cl_doors._update_offset(door)

    # Stand where the door's brush lands as it comes down
    under = [(door['mins'][0] + door['maxs'][0]) * 0.5,
             (door['mins'][1] + door['maxs'][1]) * 0.5,
             door['mins'][2] + 24.0]

    now = 0.0
    for _ in range(30):
        now += FRAME
        cl_doors.Update(FRAME, under, now=now)

    assert door['state'] in ('up', 'top')  # reversed, and possibly back at the top
    assert door['frac'] > 0.5, "the door should not have closed onto the player"


def test_triggered_door_stays_shut_without_its_trigger(base1, monkeypatch):
    """Door 31 waits on a func_button, so proximity must not open it."""
    monkeypatch.setattr(cl_doors, "_play_sound", lambda _path: None)
    door31 = next(d for d in base1.doors if d['index'] == 31)
    door31['frac'] = 0.0
    door31['state'] = 'bottom'

    centre = [(door31['mins'][0] + door31['maxs'][0]) * 0.5,
              (door31['mins'][1] + door31['maxs'][1]) * 0.5,
              door31['mins'][2] + 24.0]

    now = 0.0
    for _ in range(60):
        now += FRAME
        cl_doors.Update(FRAME, centre, now=now)

    assert door31['state'] == 'bottom'
    assert door31['frac'] == 0.0
