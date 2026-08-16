"""Regression tests for the func_door / func_button movers (quake2/cl_movers.py).

Everything here runs against the real base1.bsp.
"""

import os
import sys

import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)

from quake2 import cl_movers, cl_input, cmodel
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
    cl_movers._MoverState.entity_string = None
    cl_movers._ensure_parsed()
    return cl_movers._MoverState


@pytest.fixture
def door(base1, monkeypatch):
    """The map's door 19, reset to closed, with audio disabled."""
    monkeypatch.setattr(cl_movers, "_play_sound", lambda _path: None)
    entry = next(d for d in base1.doors if d['index'] == DOOR_INDEX)
    entry['frac'] = 0.0
    entry['state'] = 'bottom'
    entry['close_at'] = None
    cl_movers._update_offset(entry)
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

    clipped = cl_movers.ClipTrace(start, end, cl_input.PLAYER_MINS, cl_input.PLAYER_MAXS,
                                 world, cmodel.MASK_PLAYERSOLID)
    assert clipped.fraction < 1.0


def test_open_door_lets_a_trace_through(door):
    """Once raised, the same trace runs clear."""
    door['frac'] = 1.0
    cl_movers._update_offset(door)

    y = (door['mins'][1] + door['maxs'][1]) * 0.5
    z = door['mins'][2] + 30.0
    start = [door['mins'][0] - 60.0, y, z]
    end = [door['maxs'][0] + 60.0, y, z]

    world = cmodel.CM_BoxTrace(start, end, cl_input.PLAYER_MINS, cl_input.PLAYER_MAXS,
                               0, cmodel.MASK_PLAYERSOLID)
    clipped = cl_movers.ClipTrace(start, end, cl_input.PLAYER_MINS, cl_input.PLAYER_MAXS,
                                 world, cmodel.MASK_PLAYERSOLID)
    assert clipped.fraction == 1.0


def test_door_opens_on_approach_and_closes_after_the_wait(door):
    """Full cycle: bottom -> up -> top, then closes once the player leaves."""
    now = 0.0
    cl_movers.Update(FRAME, APPROACH, now=now)
    assert door['state'] == 'bottom'

    for _ in range(60):  # two seconds standing in the trigger
        now += FRAME
        cl_movers.Update(FRAME, IN_TRIGGER, now=now)
    assert door['state'] == 'top'
    assert door['offset'] == [0.0, 0.0, 120.0]

    for _ in range(180):  # six seconds away: 3s wait plus the ride down
        now += FRAME
        cl_movers.Update(FRAME, APPROACH, now=now)
    assert door['state'] == 'bottom'
    assert door['offset'] == [0.0, 0.0, 0.0]


def test_closing_door_reverses_off_the_player(door):
    """door_blocked: a closing door backs off instead of crushing."""
    door['frac'] = 1.0
    door['state'] = 'down'
    cl_movers._update_offset(door)

    # Stand where the door's brush lands as it comes down
    under = [(door['mins'][0] + door['maxs'][0]) * 0.5,
             (door['mins'][1] + door['maxs'][1]) * 0.5,
             door['mins'][2] + 24.0]

    now = 0.0
    for _ in range(30):
        now += FRAME
        cl_movers.Update(FRAME, under, now=now)

    assert door['state'] in ('up', 'top')  # reversed, and possibly back at the top
    assert door['frac'] > 0.5, "the door should not have closed onto the player"


def test_triggered_door_stays_shut_without_its_trigger(base1, monkeypatch):
    """Door 31 waits on a func_button, so proximity must not open it."""
    monkeypatch.setattr(cl_movers, "_play_sound", lambda _path: None)
    door31 = next(d for d in base1.doors if d['index'] == 31)
    door31['frac'] = 0.0
    door31['state'] = 'bottom'

    centre = [(door31['mins'][0] + door31['maxs'][0]) * 0.5,
              (door31['mins'][1] + door31['maxs'][1]) * 0.5,
              door31['mins'][2] + 24.0]

    now = 0.0
    for _ in range(60):
        now += FRAME
        cl_movers.Update(FRAME, centre, now=now)

    assert door31['state'] == 'bottom'
    assert door31['frac'] == 0.0


# --- func_button -----------------------------------------------------------

TOUCH_BUTTON = 34    # base1's wall switch, targets door 31
SHOOT_BUTTON = 13    # base1's floor plate, "health" "1" so only shots press it


@pytest.fixture
def buttons(base1, monkeypatch):
    """Both base1 buttons and door 31, reset to their spawn state."""
    monkeypatch.setattr(cl_movers, "_play_sound", lambda _path: None)
    for mover in base1.movers:
        mover['frac'] = 0.0
        mover['state'] = 'bottom'
        mover['close_at'] = None
        cl_movers._update_offset(mover)
    return {b['index']: b for b in base1.buttons}


def test_buttons_parsed_from_entity_string(buttons):
    """A wall switch you walk into, and a plate you have to shoot."""
    assert sorted(buttons) == [SHOOT_BUTTON, TOUCH_BUTTON]

    switch = buttons[TOUCH_BUTTON]
    assert switch['touchable'] is True
    assert switch['target'] == 't4'
    # 9-unit thick brush, 4-unit lip, "angle" "180" -> 5 units into the wall
    assert switch['open'] == pytest.approx([-5.0, 0.0, 0.0])

    plate = buttons[SHOOT_BUTTON]
    assert plate['touchable'] is False   # "health" makes it shoot-only
    assert plate['health'] == 1.0


def test_walking_into_a_button_opens_the_door_it_targets(base1, buttons):
    """base1's switch is the only way through door 31."""
    switch = buttons[TOUCH_BUTTON]
    door31 = next(d for d in base1.doors if d['index'] == 31)

    against_it = [switch['maxs'][0] + 17.0,
                  (switch['mins'][1] + switch['maxs'][1]) * 0.5,
                  switch['mins'][2] + 10.0]

    now = 0.0
    door_states = set()
    for _ in range(30):  # one second stood against the switch
        now += FRAME
        cl_movers.Update(FRAME, against_it, now=now)
        door_states.add(door31['state'])

    assert switch['state'] in ('top', 'down')   # pressed all the way in
    assert 'up' in door_states                  # and the door it targets was used
    assert door31['frac'] > 0.0


def test_button_out_of_reach_does_nothing(base1, buttons):
    """Standing near, but not against, the switch leaves it alone."""
    switch = buttons[TOUCH_BUTTON]
    door31 = next(d for d in base1.doors if d['index'] == 31)

    nearby = [switch['maxs'][0] + 48.0,
              (switch['mins'][1] + switch['maxs'][1]) * 0.5,
              switch['mins'][2] + 10.0]

    now = 0.0
    for _ in range(30):
        now += FRAME
        cl_movers.Update(FRAME, nearby, now=now)

    assert switch['state'] == 'bottom'
    assert door31['state'] == 'bottom'


def test_shooting_a_button_presses_it(buttons):
    """A shot trace that lands on a shootable button fires it once."""
    plate = buttons[SHOOT_BUTTON]
    centre_y = (plate['mins'][1] + plate['maxs'][1]) * 0.5
    centre_z = (plate['mins'][2] + plate['maxs'][2]) * 0.5
    start = [plate['maxs'][0] + 64.0, centre_y, centre_z]   # the plate is recessed,
    end = [plate['mins'][0] - 1.0, centre_y, centre_z]      # so shoot it side-on
    shot = [-1.0, -1.0, -1.0], [1.0, 1.0, 1.0]

    world = cmodel.CM_BoxTrace(start, end, shot[0], shot[1], 0, cmodel.MASK_SOLID)
    tr = cl_movers.ClipTrace(start, end, shot[0], shot[1], world, cmodel.MASK_SOLID)

    assert getattr(tr, '_mover', None) is plate, "the trace should name what it hit"
    assert cl_movers.Damage(tr, 10, now=0.0) is True
    assert plate['state'] == 'up'

    # button_killed stops taking damage, so a second hit changes nothing
    assert cl_movers.Damage(tr, 10, now=0.0) is False


def test_pressed_button_returns_after_its_wait(base1, buttons):
    """The switch pops back out; "wait" "-1" plates stay in."""
    switch = buttons[TOUCH_BUTTON]
    against_it = [switch['maxs'][0] + 17.0,
                  (switch['mins'][1] + switch['maxs'][1]) * 0.5,
                  switch['mins'][2] + 10.0]
    away = [switch['maxs'][0] + 96.0, against_it[1], against_it[2]]

    now = 0.0
    for _ in range(15):
        now += FRAME
        cl_movers.Update(FRAME, against_it, now=now)
    assert switch['state'] in ('up', 'top')

    for _ in range(180):  # six seconds clear of it: 3s wait plus the ride back
        now += FRAME
        cl_movers.Update(FRAME, away, now=now)

    assert switch['state'] == 'bottom'
    assert switch['frac'] == 0.0
