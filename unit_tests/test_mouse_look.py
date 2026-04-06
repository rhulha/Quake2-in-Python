"""Unit tests for mouse-look behavior."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quake2 import cl_input
from quake2 import cl_view


def setup_function(_func):
    cl_input._State.viewangles = [0.0, 0.0, 0.0]
    cl_input._State.key_dest_game = True
    cl_input.cl_mouse_sensitivity = 0.2
    cl_input.cl_mouse_invert = False


def test_mouse_motion_updates_yaw_and_pitch():
    cl_input._handle_mousemotion((10, -5))
    # yaw decreases with positive mouse x
    assert cl_input._State.viewangles[cl_input.YAW] == pytest.approx(358.0)
    # negative mouse y looks up (increases pitch with current mapping)
    assert cl_input._State.viewangles[cl_input.PITCH] == pytest.approx(1.0)


def test_mouse_pitch_is_clamped():
    cl_input._State.viewangles[cl_input.PITCH] = 88.0
    cl_input._handle_mousemotion((0, -20))
    assert cl_input._State.viewangles[cl_input.PITCH] == 89.0

    cl_input._State.viewangles[cl_input.PITCH] = -88.0
    cl_input._handle_mousemotion((0, 20))
    assert cl_input._State.viewangles[cl_input.PITCH] == -89.0


def test_mouse_invert_switches_pitch_direction():
    cl_input.cl_mouse_invert = True
    cl_input._handle_mousemotion((0, 10))
    assert cl_input._State.viewangles[cl_input.PITCH] == pytest.approx(2.0)


def test_mouse_motion_ignored_when_not_in_game():
    cl_input._State.key_dest_game = False
    cl_input._handle_mousemotion((20, 20))
    assert cl_input._State.viewangles == [0.0, 0.0, 0.0]


def test_view_render_uses_local_input_angles(monkeypatch):
    cl_input._State.viewangles = [11.0, 22.0, 33.0]
    cl_view._ViewState.prepared = True
    cl_view._ViewState.entities = []
    cl_view._ViewState.dlights = []
    cl_view._ViewState.particles = []

    # Prevent heavy renderer startup and rendering side effects.
    monkeypatch.setattr(cl_view, "CL_PrepRefresh", lambda: None)

    class _FakeServer:
        edicts = []
        mapname = ""

    import quake2.sv_main as sv_main
    monkeypatch.setattr(sv_main, "server", _FakeServer())

    import ref_gl.gl_rmain as gl_rmain
    monkeypatch.setattr(gl_rmain, "R_RenderFrame", lambda refdef: True)

    refdef = cl_view.V_RenderView()
    assert refdef.viewangles == [11.0, 22.0, 33.0]
