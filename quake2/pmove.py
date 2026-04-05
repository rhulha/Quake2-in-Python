"""
pmove.py - Quake 2 player movement system
Handles gravity, acceleration, jumping, and collision-based movement
Used by both client (prediction) and server (authoritative)
"""

import math
from wrapper_qpy.decorators import TODO
from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), ["Com_Printf"])

# ===== Constants =====

PMOVE_DUCKED = 1
PMOVE_NORMAL = 0

JUMP_HEIGHT = 0.5

STEPSIZE = 18
SLOPE_NORMAL = 0.7
SLOPE_STEEP = 0.2

# ===== Player State =====

class pmove_t:
    def __init__(self):
        self.s = None                   # player state
        self.cmd = None                 # user input command
        self.snapinitial = False

        self.numtouch = 0
        self.touchents = []

        self.viewangles = [0, 0, 0]
        self.velocity = [0, 0, 0]
        self.origin = [0, 0, 0]

        self.waterlevel = 0             # 0=dry, 1=wading, 2=swimming
        self.watertype = 0              # CONTENTS_*

        self.groundentity = None
        self.groundsurface = None

        self.trace = None


# ===== Vector Utilities =====

def vec3_set(v, x, y, z):
    v[0] = x
    v[1] = y
    v[2] = z


def vec3_copy(src):
    return [src[0], src[1], src[2]]


def vec3_add(a, b):
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def vec3_subtract(a, b):
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def vec3_scale(v, s):
    return [v[0] * s, v[1] * s, v[2] * s]


def vec3_length(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def vec3_normalize(v):
    length = vec3_length(v)
    if length == 0:
        return [0, 0, 0]
    return [v[0] / length, v[1] / length, v[2] / length]


def vec3_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def DotProduct(a, b):
    return vec3_dot(a, b)


def Distance(a, b):
    return vec3_length(vec3_subtract(a, b))


# ===== Collision Functions =====

def PM_ClipVelocity(vel_in, normal, vel_out, overbounce=1.0):
    """
    Modify velocity based on collision with surface normal.
    Removes velocity component perpendicular to surface.
    """
    backoff = DotProduct(vel_in, normal) * overbounce

    for i in range(3):
        vel_out[i] = vel_in[i] - backoff * normal[i]


def PM_StepSlideMove_():
    """Try stepping over obstacles"""
    pass


def PM_StepSlideMove():
    """
    Each collision causes a full sliding step.
    This is a complex move that handles stairs and slopes.
    """
    global pm

    # Try moving without stepping
    start_o = vec3_copy(pm.origin)
    start_v = vec3_copy(pm.velocity)

    # Perform trace
    vel_length = vec3_length(pm.velocity)
    if vel_length == 0:
        return

    # Scale velocity by frame time (assumed to be in cmd)
    move = vec3_scale(pm.velocity, 0.001)  # Assume 1ms timestep for now

    # Simple collision: move and check
    # In full implementation, would do iterative collision checks
    pm.origin = vec3_add(pm.origin, move)


# ===== Friction and Acceleration =====

def PM_Friction(pm_state):
    """Apply friction to slow the player down"""
    speed = vec3_length(pm_state.velocity)

    if speed < 1.0:
        pm_state.velocity = [0, 0, 0]
        return

    # Calculate friction
    if pm_state.waterlevel >= 2:
        friction = 4.0  # Water friction
    elif pm_state.groundentity is not None:
        friction = 6.0  # Ground friction
    else:
        friction = 0.0  # Air - no friction

    if friction == 0:
        return

    # Apply friction: v = v * (1 - friction * dt)
    control = max(speed, 30.0)
    newspeed = speed - friction * control * 0.001  # 1ms timestep

    if newspeed < 0:
        newspeed = 0

    # Scale velocity
    scale = newspeed / speed
    pm_state.velocity = vec3_scale(pm_state.velocity, scale)


def PM_Accelerate(pm_state, wishdir, wishspeed, accel):
    """
    Apply acceleration in wish direction.
    Used for running, strafing, etc.
    """
    # Calculate current speed in wish direction
    currentspeed = vec3_dot(pm_state.velocity, wishdir)

    # Calculate speed to add
    addspeed = wishspeed - currentspeed
    if addspeed <= 0:
        return

    # Limit acceleration
    accelspeed = min(addspeed, accel * 0.001)  # 1ms timestep

    # Add acceleration
    for i in range(3):
        pm_state.velocity[i] += accelspeed * wishdir[i]


def PM_AirAccelerate(pm_state, wishdir, wishspeed, accel):
    """Apply acceleration while in air (more restrictive than ground)"""
    # Similar to PM_Accelerate but with lower cap
    wishspeed = min(wishspeed, 30.0)

    currentspeed = vec3_dot(pm_state.velocity, wishdir)
    addspeed = wishspeed - currentspeed

    if addspeed <= 0:
        return

    accelspeed = min(addspeed, accel * 0.001)

    for i in range(3):
        pm_state.velocity[i] += accelspeed * wishdir[i]


# ===== Movement Modes =====

def PM_AddCurrents(pm_state, wishvel):
    """Add water/slime currents to velocity"""
    # Check for current contents
    if pm_state.watertype == 0:
        return

    # TODO: Add current effects
    pass


def PM_WaterMove(pm_state):
    """Handle movement while in water"""
    # Calculate wish direction from player input
    wishvel = [0, 0, 0]

    if pm_state.cmd:
        wishvel[0] = pm_state.cmd.forwardmove
        wishvel[1] = pm_state.cmd.sidemove

    # Apply friction
    PM_Friction(pm_state)

    # Apply water acceleration
    PM_Accelerate(pm_state, vec3_normalize(wishvel), 70.0, 10.0)

    # Add gravity
    pm_state.velocity[2] -= 0.001 * 600.0  # 600 units/s^2 gravity

    # Limit falling speed
    if pm_state.velocity[2] < -200:
        pm_state.velocity[2] = -200


def PM_AirMove(pm_state):
    """Handle movement while in air"""
    if pm_state.cmd is None:
        return

    # Calculate forward and right vectors from angles
    yaw = pm_state.viewangles[1] * (math.pi / 180.0)
    forward = [math.cos(yaw), math.sin(yaw), 0]
    right = [-math.sin(yaw), math.cos(yaw), 0]

    # Build wish velocity
    fmove = pm_state.cmd.forwardmove
    smove = pm_state.cmd.sidemove

    wishvel = [
        forward[0] * fmove + right[0] * smove,
        forward[1] * fmove + right[1] * smove,
        0
    ]

    wishspeed = vec3_length(wishvel)
    if wishspeed > 0:
        wishvel = vec3_normalize(wishvel)

    # Cap air movement speed
    if wishspeed > 30:
        wishspeed = 30

    # Apply air acceleration (lower than ground)
    PM_AirAccelerate(pm_state, wishvel, wishspeed, 10.0)

    # Apply gravity
    pm_state.velocity[2] -= 0.001 * 800.0  # 800 units/s^2 gravity


def PM_CatagorizePosition(pm_state):
    """Determine if player is on ground, in water, etc."""
    # Check if on ground by tracing down
    # For now, assume always on ground
    pm_state.groundentity = True
    pm_state.waterlevel = 0


def PM_CheckJump(pm_state):
    """Handle jump when requested"""
    if pm_state.cmd is None:
        return False

    if not (pm_state.cmd.upmove > 0):
        return False

    # Can't jump if not on ground
    if pm_state.groundentity is None:
        return False

    # Jump: add upward velocity
    pm_state.velocity[2] = math.sqrt(2 * 800 * JUMP_HEIGHT)  # sqrt(2 * g * h)

    pm_state.groundentity = None

    return True


def PM_CheckSpecialMovement(pm_state):
    """Check for special moves like wallrunning (future feature)"""
    pass


def PM_FlyMove(pm_state, doclip=True):
    """
    Handle flying movement (for debugging and special modes).
    Only used when cheats enabled.
    """
    if pm_state.cmd is None:
        return

    # Similar to air move but with no gravity
    yaw = pm_state.viewangles[1] * (math.pi / 180.0)
    pitch = pm_state.viewangles[0] * (math.pi / 180.0)

    forward = [
        math.cos(pitch) * math.cos(yaw),
        math.cos(pitch) * math.sin(yaw),
        -math.sin(pitch)
    ]

    right = [-math.sin(yaw), math.cos(yaw), 0]

    up = [0, 0, 1]

    fmove = pm_state.cmd.forwardmove
    smove = pm_state.cmd.sidemove
    upmove = pm_state.cmd.upmove

    wishvel = [
        forward[0] * fmove + right[0] * smove + up[0] * upmove,
        forward[1] * fmove + right[1] * smove + up[1] * upmove,
        forward[2] * fmove + right[2] * smove + up[2] * upmove,
    ]

    wishspeed = vec3_length(wishvel)
    if wishspeed > 0:
        wishvel = vec3_normalize(wishvel)

    PM_Accelerate(pm_state, wishvel, wishspeed, 10.0)


def PM_CheckDuck(pm_state):
    """Check if player should be ducked"""
    # Check crouch key in cmd
    # TODO: Adjust player model bbox
    pass


def PM_DeadMove(pm_state):
    """Handle movement when dead"""
    # No movement when dead
    pm_state.velocity = [0, 0, 0]


def PM_GoodPosition(pm_state):
    """Check if current position is valid (not stuck in walls)"""
    # TODO: Perform collision checks
    return True


def PM_SnapPosition(pm_state):
    """Snap position to grid for network efficiency"""
    # TODO: Snap origin to 0.125 unit grid
    pass


def PM_InitialSnapPosition(pm_state):
    """Initial position snap for new player"""
    PM_SnapPosition(pm_state)


def PM_ClampAngles(pm_state):
    """Clamp view angles to valid range"""
    # Pitch: -89 to 89 degrees
    if pm_state.viewangles[0] > 89:
        pm_state.viewangles[0] = 89
    if pm_state.viewangles[0] < -89:
        pm_state.viewangles[0] = -89

    # Yaw: 0 to 360 degrees
    while pm_state.viewangles[1] < 0:
        pm_state.viewangles[1] += 360
    while pm_state.viewangles[1] > 360:
        pm_state.viewangles[1] -= 360

    # Roll: -50 to 50 degrees (usually 0)
    pm_state.viewangles[2] = 0


def Pmove(pmove):
    """
    Main player movement function.
    Called once per frame to update player position and velocity.
    """
    global pm

    pm = pmove

    # Clamp input angles
    PM_ClampAngles(pmove)

    # Categorize position (on ground, in water, etc.)
    PM_CatagorizePosition(pmove)

    # Check for jump
    if not PM_CheckJump(pmove):
        # Apply friction if no jump
        if pmove.waterlevel >= 2:
            PM_WaterMove(pmove)
        elif pmove.groundentity is not None:
            PM_Friction(pmove)
        else:
            # Air movement
            pass

    # Process input
    if pmove.waterlevel >= 2:
        PM_WaterMove(pmove)
    elif pmove.groundentity is not None:
        # Ground movement
        if pmove.cmd:
            # Calculate wish velocity
            yaw = pmove.viewangles[1] * (math.pi / 180.0)
            forward = [math.cos(yaw), math.sin(yaw), 0]
            right = [-math.sin(yaw), math.cos(yaw), 0]

            fmove = pmove.cmd.forwardmove
            smove = pmove.cmd.sidemove

            wishvel = [
                forward[0] * fmove + right[0] * smove,
                forward[1] * fmove + right[1] * smove,
                0
            ]

            wishspeed = vec3_length(wishvel)
            if wishspeed > 0:
                wishvel = vec3_normalize(wishvel)

            # Cap ground speed
            if wishspeed > 300:
                wishspeed = 300

            PM_Accelerate(pmove, wishvel, wishspeed, 20.0)

            # Handle stepping
            PM_StepSlideMove()
    else:
        # Air movement
        PM_AirMove(pmove)

    # Add gravity
    if pmove.waterlevel == 0:
        pmove.velocity[2] -= 0.001 * 800.0  # 800 units/s^2 gravity

    # Snap position to grid
    PM_SnapPosition(pmove)


# Global state
pm = None


# ===== Import after function definitions =====

from .common import Com_Printf
