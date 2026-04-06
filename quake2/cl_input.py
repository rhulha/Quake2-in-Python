import time
from dataclasses import dataclass, field


@dataclass
class kbutton_t:
    down: list = field(default_factory=lambda: [0, 0])
    downtime: int = 0
    msec: int = 0
    state: int = 0


@dataclass
class usercmd_t:
    angles: list = field(default_factory=lambda: [0, 0, 0])
    forwardmove: float = 0.0
    sidemove: float = 0.0
    upmove: float = 0.0
    buttons: int = 0
    msec: int = 0
    impulse: int = 0
    lightlevel: int = 0


BUTTON_ATTACK = 1
BUTTON_USE = 2
BUTTON_ANY = 128

PITCH = 0
YAW = 1


def _now_msec():
    return int(time.time() * 1000)


class _State:
    viewangles = [0.0, 0.0, 0.0]
    frame_player_delta_angles = [0, 0, 0]
    frametime = 0.016
    key_dest_game = True
    anykeydown = False
    lightlevel = 0
    last_screenshot_time = 0
    screenshot_interval = 5.0  # Screenshot every 5 seconds


in_klook = kbutton_t()
in_left = kbutton_t()
in_right = kbutton_t()
in_forward = kbutton_t()
in_back = kbutton_t()
in_lookup = kbutton_t()
in_lookdown = kbutton_t()
in_moveleft = kbutton_t()
in_moveright = kbutton_t()
in_strafe = kbutton_t()
in_speed = kbutton_t()
in_use = kbutton_t()
in_attack = kbutton_t()
in_up = kbutton_t()
in_down = kbutton_t()

in_impulse = 0

cl_upspeed = 200.0
cl_forwardspeed = 200.0
cl_sidespeed = 200.0
cl_yawspeed = 140.0
cl_pitchspeed = 150.0
cl_run = 0.0
cl_anglespeedkey = 1.5
cl_mouse_sensitivity = 0.2
cl_mouse_invert = False

sys_frame_time = _now_msec()
frame_msec = 16
old_sys_frame_time = sys_frame_time


def KeyDown(b, key=-1, timestamp=None):
    if key == b.down[0] or key == b.down[1]:
        return

    if not b.down[0]:
        b.down[0] = key
    elif not b.down[1]:
        b.down[1] = key
    else:
        return

    if b.state & 1:
        return

    b.downtime = int(timestamp if timestamp is not None else (_now_msec() - 100))
    b.state |= 1 | 2


def KeyUp(b, key=-1, timestamp=None):
    if key == -1:
        b.down[0] = b.down[1] = 0
        b.state = 4
        return

    if b.down[0] == key:
        b.down[0] = 0
    elif b.down[1] == key:
        b.down[1] = 0
    else:
        return

    if b.down[0] or b.down[1]:
        return
    if not (b.state & 1):
        return

    uptime = int(timestamp if timestamp is not None else _now_msec())
    b.msec += max(1, uptime - b.downtime)
    b.state &= ~1
    b.state |= 4


def CL_KeyState(key):
    global frame_msec, sys_frame_time

    key.state &= 1
    msec = key.msec
    key.msec = 0

    if key.state:
        msec += sys_frame_time - key.downtime
        key.downtime = sys_frame_time

    if frame_msec <= 0:
        return 0.0
    val = float(msec) / float(frame_msec)
    if val < 0:
        return 0.0
    if val > 1:
        return 1.0
    return val


def CL_AdjustAngles():
    speed = _State.frametime * cl_anglespeedkey if (in_speed.state & 1) else _State.frametime

    if not (in_strafe.state & 1):
        _State.viewangles[YAW] -= speed * cl_yawspeed * CL_KeyState(in_right)
        _State.viewangles[YAW] += speed * cl_yawspeed * CL_KeyState(in_left)

    if in_klook.state & 1:
        _State.viewangles[PITCH] -= speed * cl_pitchspeed * CL_KeyState(in_forward)
        _State.viewangles[PITCH] += speed * cl_pitchspeed * CL_KeyState(in_back)

    _State.viewangles[PITCH] -= speed * cl_pitchspeed * CL_KeyState(in_lookup)
    _State.viewangles[PITCH] += speed * cl_pitchspeed * CL_KeyState(in_lookdown)


def CL_BaseMove(cmd):
    CL_AdjustAngles()

    cmd.angles[:] = list(_State.viewangles)

    if in_strafe.state & 1:
        cmd.sidemove += cl_sidespeed * CL_KeyState(in_right)
        cmd.sidemove -= cl_sidespeed * CL_KeyState(in_left)

    cmd.sidemove += cl_sidespeed * CL_KeyState(in_moveright)
    cmd.sidemove -= cl_sidespeed * CL_KeyState(in_moveleft)

    cmd.upmove += cl_upspeed * CL_KeyState(in_up)
    cmd.upmove -= cl_upspeed * CL_KeyState(in_down)

    if not (in_klook.state & 1):
        cmd.forwardmove += cl_forwardspeed * CL_KeyState(in_forward)
        cmd.forwardmove -= cl_forwardspeed * CL_KeyState(in_back)

    if (bool(in_speed.state & 1)) ^ bool(int(cl_run)):
        cmd.forwardmove *= 2
        cmd.sidemove *= 2
        cmd.upmove *= 2


def CL_ClampPitch():
    pitch = _State.frame_player_delta_angles[PITCH]
    if pitch > 180:
        pitch -= 360
    if _State.viewangles[PITCH] + pitch > 89:
        _State.viewangles[PITCH] = 89 - pitch
    if _State.viewangles[PITCH] + pitch < -89:
        _State.viewangles[PITCH] = -89 - pitch


def _angle2short(a):
    return int(a * 65536.0 / 360.0) & 65535


def CL_FinishMove(cmd):
    global in_impulse

    if in_attack.state & 3:
        cmd.buttons |= BUTTON_ATTACK
    in_attack.state &= ~2

    if in_use.state & 3:
        cmd.buttons |= BUTTON_USE
    in_use.state &= ~2

    if _State.anykeydown and _State.key_dest_game:
        cmd.buttons |= BUTTON_ANY

    ms = int(_State.frametime * 1000)
    if ms > 250:
        ms = 100
    cmd.msec = ms

    CL_ClampPitch()
    for i in range(3):
        cmd.angles[i] = _angle2short(_State.viewangles[i])

    cmd.impulse = in_impulse
    in_impulse = 0
    cmd.lightlevel = int(_State.lightlevel)


def CL_CreateCmd():
    global frame_msec, old_sys_frame_time, sys_frame_time

    sys_frame_time = _now_msec()
    frame_msec = sys_frame_time - old_sys_frame_time
    if frame_msec < 1:
        frame_msec = 1
    if frame_msec > 200:
        frame_msec = 200

    cmd = usercmd_t()
    CL_BaseMove(cmd)
    CL_FinishMove(cmd)
    old_sys_frame_time = sys_frame_time
    return cmd


def IN_CenterView():
    _State.viewangles[PITCH] = -float(_State.frame_player_delta_angles[PITCH])


def CL_InitInput():
    return True


def CL_SendCmd():
    cmd = CL_CreateCmd()
    try:
        from . import cl_main
        if hasattr(cl_main, "CL_SendCommandToServer"):
            cl_main.CL_SendCommandToServer(cmd)
    except Exception:
        pass
    return cmd


# ===== Pygame Event Handling =====

def IN_Frame():
    """Process input events from pygame"""
    try:
        import pygame

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.KEYDOWN:
                _handle_keydown(event.key)

            elif event.type == pygame.KEYUP:
                _handle_keyup(event.key)

            elif event.type == pygame.MOUSEMOTION:
                _handle_mousemotion(event.rel)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                _handle_mousebuttondown(event.button)

            elif event.type == pygame.MOUSEBUTTONUP:
                _handle_mousebuttonup(event.button)

        # Periodic screenshot
        current_time = time.time()
        if current_time - _State.last_screenshot_time >= _State.screenshot_interval:
            try:
                from ref_gl.gl_screenshot import take_screenshot
                surface = pygame.display.get_surface()
                if surface:
                    w, h = surface.get_size()
                    take_screenshot(w, h)
                    _State.last_screenshot_time = current_time
                    print(f"Auto-screenshot saved")
            except:
                pass

        return True

    except Exception as e:
        return True


def _handle_keydown(key):
    """Handle key down event"""
    # WASD movement
    if key == pygame.K_w:
        KeyDown(in_forward)
    elif key == pygame.K_s:
        KeyDown(in_back)
    elif key == pygame.K_a:
        KeyDown(in_moveleft)
    elif key == pygame.K_d:
        KeyDown(in_moveright)

    # Arrow keys
    elif key == pygame.K_UP:
        KeyDown(in_lookup)
    elif key == pygame.K_DOWN:
        KeyDown(in_lookdown)
    elif key == pygame.K_LEFT:
        KeyDown(in_left)
    elif key == pygame.K_RIGHT:
        KeyDown(in_right)

    # Space - jump/up
    elif key == pygame.K_SPACE:
        KeyDown(in_up)

    # Ctrl - crouch/down
    elif key == pygame.K_LCTRL or key == pygame.K_RCTRL:
        KeyDown(in_down)

    # Shift - run
    elif key == pygame.K_LSHIFT or key == pygame.K_RSHIFT:
        KeyDown(in_speed)

    # E - use
    elif key == pygame.K_e:
        KeyDown(in_use)

    # Mouse button (attack)
    elif key == pygame.K_LMETA:
        KeyDown(in_attack)

    # ESC - menu (set key_dest_game)
    elif key == pygame.K_ESCAPE:
        _State.key_dest_game = False

    # F12 - screenshot
    elif key == pygame.K_F12:
        try:
            from ref_gl.gl_screenshot import take_screenshot
            # Get current window size from pygame
            import pygame
            surface = pygame.display.get_surface()
            if surface:
                w, h = surface.get_size()
                take_screenshot(w, h)
        except:
            pass


def _handle_keyup(key):
    """Handle key up event"""
    if key == pygame.K_w:
        KeyUp(in_forward)
    elif key == pygame.K_s:
        KeyUp(in_back)
    elif key == pygame.K_a:
        KeyUp(in_moveleft)
    elif key == pygame.K_d:
        KeyUp(in_moveright)

    elif key == pygame.K_UP:
        KeyUp(in_lookup)
    elif key == pygame.K_DOWN:
        KeyUp(in_lookdown)
    elif key == pygame.K_LEFT:
        KeyUp(in_left)
    elif key == pygame.K_RIGHT:
        KeyUp(in_right)

    elif key == pygame.K_SPACE:
        KeyUp(in_up)

    elif key == pygame.K_LCTRL or key == pygame.K_RCTRL:
        KeyUp(in_down)

    elif key == pygame.K_LSHIFT or key == pygame.K_RSHIFT:
        KeyUp(in_speed)

    elif key == pygame.K_e:
        KeyUp(in_use)

    elif key == pygame.K_LMETA:
        KeyUp(in_attack)


def _handle_mousemotion(rel):
    """Handle mouse motion for look"""
    if _State.key_dest_game:
        # Apply mouse deltas directly to local view angles.
        mouse_x, mouse_y = rel

        _State.viewangles[YAW] -= float(mouse_x) * cl_mouse_sensitivity
        pitch_delta = float(mouse_y) * cl_mouse_sensitivity
        _State.viewangles[PITCH] -= pitch_delta if cl_mouse_invert else pitch_delta

        # Keep angles in sensible ranges.
        if _State.viewangles[PITCH] > 89.0:
            _State.viewangles[PITCH] = 89.0
        if _State.viewangles[PITCH] < -89.0:
            _State.viewangles[PITCH] = -89.0

        while _State.viewangles[YAW] < 0.0:
            _State.viewangles[YAW] += 360.0
        while _State.viewangles[YAW] >= 360.0:
            _State.viewangles[YAW] -= 360.0


def _handle_mousebuttondown(button):
    """Handle mouse button press"""
    if button == 1:  # Left mouse - attack
        KeyDown(in_attack)
    elif button == 3:  # Right mouse - use
        KeyDown(in_use)


def _handle_mousebuttonup(button):
    """Handle mouse button release"""
    if button == 1:
        KeyUp(in_attack)
    elif button == 3:
        KeyUp(in_use)
