"""Regression tests for touch triggers and level exits (quake2/cl_triggers.py).

Everything here runs against the real base1.bsp, whose exit trigger fires a
target_changelevel to "base2$base1".
"""

import os
import sys

import pytest

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
os.chdir(project_root)

from quake2 import cl_movers, cl_triggers, cl_view, cmodel, sv_main
from quake2.files import FS_InitFilesystem

EXIT_TARGET = 't37'      # base1's trigger_multiple by the exit
DOOR_TARGET = 't4'       # door 31, normally opened by the wall switch
FRAME = 1.0 / 30.0


def _load_base1():
    cmodel.CM_LoadMap("maps/base1.bsp", False, None)
    sv_main.server.mapname = "base1"
    sv_main.server.spawnpoint = ""
    for module in (cl_triggers, cl_movers):
        module._ensure_parsed()


@pytest.fixture
def base1(monkeypatch):
    """base1 loaded and freshly parsed; the map is restored afterwards."""
    try:
        FS_InitFilesystem()
    except Exception:
        pass
    monkeypatch.setattr(cl_movers, "_play_sound", lambda _path: None)
    cl_triggers._TriggerState.entity_string = None
    cl_movers._MoverState.entity_string = None
    _load_base1()
    assert cmodel.num_models > 0, "base1.bsp did not load"
    yield cl_triggers._TriggerState
    # Other modules keep global map state, so leave base1 loaded behind us
    cl_triggers._TriggerState.entity_string = None
    cl_movers._MoverState.entity_string = None
    _load_base1()


def _exit_trigger(state):
    return next(t for t in state.triggers if t['target'] == EXIT_TARGET)


def _inside(trigger):
    return [(trigger['mins'][0] + trigger['maxs'][0]) * 0.5,
            (trigger['mins'][1] + trigger['maxs'][1]) * 0.5,
            trigger['mins'][2] + 24.0]


def test_touch_triggers_and_changelevel_parsed(base1):
    """Every brush trigger in base1 spawns, and the exit knows its map."""
    assert len(base1.triggers) == 22
    assert base1.changelevels == {EXIT_TARGET: 'base2$base1'}

    exit_trigger = _exit_trigger(base1)
    assert exit_trigger['wait'] == pytest.approx(0.2)   # trigger_multiple
    assert any(t['wait'] == -1.0 for t in base1.triggers)  # trigger_once


def test_walking_into_the_exit_loads_the_next_level(base1):
    """The whole point: touching the exit brush takes you to base2."""
    exit_trigger = _exit_trigger(base1)

    cl_triggers.Update(FRAME, _inside(exit_trigger), now=1.0)

    assert sv_main.server.mapname == 'base2'
    assert sv_main.server.spawnpoint == 'base1'
    # base2 has a plain start at x=832 and the base1 landmark at x=848
    assert cl_view._ViewState.vieworg == [848.0, 2292.0, -224.0]


def test_exit_only_fires_when_the_player_is_in_it(base1):
    """Standing outside the brush must not end the level."""
    exit_trigger = _exit_trigger(base1)
    outside = list(_inside(exit_trigger))
    outside[1] = exit_trigger['mins'][1] - 200.0

    cl_triggers.Update(FRAME, outside, now=1.0)

    assert sv_main.server.mapname == 'base1'


def test_trigger_once_fires_a_single_time(base1, monkeypatch):
    """trigger_once is spent after one touch; trigger_multiple comes back."""
    fired = []
    monkeypatch.setattr(cl_triggers, "UseTargets",
                        lambda name, now=None: fired.append((name, now)))

    once = next(t for t in base1.triggers if t['wait'] == -1.0 and t['target'])
    multiple = _exit_trigger(base1)

    now = 1.0
    for _ in range(10):   # a third of a second stood on both
        now += FRAME
        cl_triggers.Update(FRAME, _inside(once), now=now)
        cl_triggers.Update(FRAME, _inside(multiple), now=now)

    assert [name for name, _ in fired].count(once['target']) == 1
    assert [name for name, _ in fired].count(multiple['target']) > 1


def test_targets_are_dispatched_to_doors(base1):
    """A fired targetname reaches cl_movers, not just the trigger's own targets."""
    door31 = next(d for d in cl_movers._MoverState.doors if d['targetname'] == DOOR_TARGET)
    assert door31['state'] == 'bottom'

    cl_triggers.UseTargets(DOOR_TARGET, now=1.0)

    assert door31['state'] == 'up'
