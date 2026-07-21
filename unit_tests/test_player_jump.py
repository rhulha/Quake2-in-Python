"""Regression tests for the client-side player jump arc."""

from quake2 import cl_input


def test_jump_starts_from_ground_and_respects_jump_hold(monkeypatch):
    """Space applies one jump impulse and does not bunny-hop while held."""
    monkeypatch.setattr(cl_input, "_trace", lambda _start, _end: None)
    monkeypatch.setattr(cl_input._State, "velocity", [0.0, 0.0, 0.0])
    monkeypatch.setattr(cl_input._State, "on_ground", True)
    monkeypatch.setattr(cl_input._State, "jump_held", False)
    monkeypatch.setattr(cl_input._State, "jump_buffer", 0.0)
    monkeypatch.setattr(cl_input._State, "jump_requested", False)
    monkeypatch.setattr(cl_input._State, "jump_available", True)
    monkeypatch.setattr(cl_input._State, "viewangles", [0.0, 0.0, 0.0])

    cmd = cl_input.usercmd_t()
    cmd.upmove = cl_input.cl_upspeed

    position = cl_input.CL_ApplyMovement(cmd, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], 0.016)
    first_vertical_velocity = cl_input._State.velocity[2]

    assert cl_input._State.jump_held is True
    assert first_vertical_velocity == cl_input.JUMP_SPEED
    assert position[2] > 0.0
    assert cl_input._State.on_ground is False

    cl_input.CL_ApplyMovement(cmd, position, [0.0, 0.0, 0.0], 0.016)
    assert cl_input._State.velocity[2] == first_vertical_velocity - cl_input.GRAVITY * 0.016


def test_jump_can_be_triggered_again_after_release(monkeypatch):
    monkeypatch.setattr(cl_input, "_trace", lambda _start, _end: None)
    monkeypatch.setattr(cl_input._State, "velocity", [0.0, 0.0, 0.0])
    monkeypatch.setattr(cl_input._State, "on_ground", True)
    monkeypatch.setattr(cl_input._State, "jump_held", False)
    monkeypatch.setattr(cl_input._State, "jump_buffer", 0.0)
    monkeypatch.setattr(cl_input._State, "jump_requested", False)
    monkeypatch.setattr(cl_input._State, "jump_available", True)
    monkeypatch.setattr(cl_input._State, "viewangles", [0.0, 0.0, 0.0])

    jump = cl_input.usercmd_t()
    jump.upmove = cl_input.cl_upspeed
    position = cl_input.CL_ApplyMovement(jump, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], 0.016)

    release = cl_input.usercmd_t()
    position = cl_input.CL_ApplyMovement(release, position, [0.0, 0.0, 0.0], 0.016)
    assert cl_input._State.jump_held is False

    cl_input._State.on_ground = True
    cl_input.CL_ApplyMovement(jump, position, [0.0, 0.0, 0.0], 0.016)
    assert cl_input._State.jump_held is True
    assert cl_input._State.velocity[2] == cl_input.JUMP_SPEED


def test_active_client_frame_reuses_movement_command(monkeypatch):
    """The render pass must not consume a second, empty input command."""
    from quake2 import cl_main, cl_view

    command = cl_input.usercmd_t()
    command.upmove = cl_input.cl_upspeed
    captured = {}

    monkeypatch.setattr(cl_main, "CL_SendCommand", lambda: command)
    monkeypatch.setattr(cl_main, "CL_CheckForResend", lambda: None)
    monkeypatch.setattr(cl_main, "CL_ReadPackets", lambda: None)

    def fake_render(**kwargs):
        captured["movement_cmd"] = kwargs["movement_cmd"]

    monkeypatch.setattr(cl_view, "V_RenderView", fake_render)
    monkeypatch.setattr(cl_main.cls, "paused", False)
    monkeypatch.setattr(cl_main.cls, "demorecording", False)

    cl_main.CL_Frame(16)

    assert captured["movement_cmd"] is command


def test_jump_tap_works_when_ground_state_is_stale(monkeypatch):
    """A Space tap must not be lost before the floor trace updates state."""
    monkeypatch.setattr(cl_input, "_trace", lambda _start, _end: None)
    monkeypatch.setattr(cl_input, "_has_ground_below", lambda _position: True)
    monkeypatch.setattr(cl_input._State, "velocity", [0.0, 0.0, 0.0])
    monkeypatch.setattr(cl_input._State, "on_ground", False)
    monkeypatch.setattr(cl_input._State, "jump_held", False)
    monkeypatch.setattr(cl_input._State, "jump_buffer", 0.0)
    monkeypatch.setattr(cl_input._State, "jump_requested", False)
    monkeypatch.setattr(cl_input._State, "jump_available", True)
    monkeypatch.setattr(cl_input._State, "viewangles", [0.0, 0.0, 0.0])

    jump = cl_input.usercmd_t()
    jump.upmove = cl_input.cl_upspeed

    position = cl_input.CL_ApplyMovement(jump, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], 0.016)

    assert position[2] > 0.0
    assert cl_input._State.velocity[2] == cl_input.JUMP_SPEED
    assert cl_input._State.jump_buffer == 0.0


def test_space_event_starts_a_jump_even_if_the_command_is_empty(monkeypatch):
    """The local key event must survive command-generation timing."""
    import pygame

    monkeypatch.setattr(cl_input, "_trace", lambda _start, _end: None)
    monkeypatch.setattr(cl_input, "_has_ground_below", lambda _position: True)
    monkeypatch.setattr(cl_input._State, "velocity", [0.0, 0.0, 0.0])
    monkeypatch.setattr(cl_input._State, "on_ground", False)
    monkeypatch.setattr(cl_input._State, "jump_held", False)
    monkeypatch.setattr(cl_input._State, "jump_buffer", 0.0)
    monkeypatch.setattr(cl_input._State, "jump_requested", False)
    monkeypatch.setattr(cl_input._State, "jump_available", True)
    monkeypatch.setattr(cl_input._State, "viewangles", [0.0, 0.0, 0.0])

    cl_input.KeyUp(cl_input.in_up)
    cl_input._handle_keydown(pygame.K_SPACE)
    position = cl_input.CL_ApplyMovement(
        cl_input.usercmd_t(), [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], 0.016
    )
    cl_input._handle_keyup(pygame.K_SPACE)

    assert position[2] > 0.0
    assert cl_input._State.velocity[2] == cl_input.JUMP_SPEED
    assert cl_input._State.jump_requested is False


def test_polled_space_key_requests_jump_when_no_keydown_event_arrives(monkeypatch):
    """OpenGL window input still works if only keyboard state is available."""
    import pygame

    class PressedKeys:
        def __getitem__(self, key):
            return key == pygame.K_SPACE

    monkeypatch.setattr(cl_input.pygame.event, "get", lambda: [])
    monkeypatch.setattr(cl_input.pygame.key, "get_pressed", lambda: PressedKeys())
    monkeypatch.setattr(cl_input._State, "jump_requested", False)
    monkeypatch.setattr(cl_input._State, "last_screenshot_time", cl_input.time.time())

    assert cl_input.IN_Frame() is True
    assert cl_input._State.jump_requested is True
