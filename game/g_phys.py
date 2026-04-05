import math

from .reference_import import gi
from .global_vars import level
from shared.QEnums import movetype_t, solid_t, damage_t
from shared.QConstants import (MASK_SOLID, MASK_MONSTERSOLID, MASK_PLAYERSOLID,
                                CONTENTS_WATER, CONTENTS_LAVA, CONTENTS_SLIME,
                                MASK_WATER, EF_FLIES)

MAX_VELOCITY = 2000.0
STOP_EPSILON = 0.1
STEPSIZE     = 18.0


def _game():
    from .g_main import game
    return game


def SV_TestEntityPosition(ent):
    """Return a trace of ent at its current position; if stuck, return trace.startsolid."""
    mask = MASK_SOLID if ent.clipmask else MASK_SOLID
    if ent.clipmask:
        mask = ent.clipmask
    tr = gi.trace(ent.s.origin, ent.mins, ent.maxs, ent.s.origin, ent, mask)
    if tr.startsolid:
        return tr
    return None


def SV_CheckVelocity(ent):
    """Clamp velocity to MAX_VELOCITY."""
    for i in range(3):
        if ent.velocity[i] >  MAX_VELOCITY:
            ent.velocity[i] =  MAX_VELOCITY
        elif ent.velocity[i] < -MAX_VELOCITY:
            ent.velocity[i] = -MAX_VELOCITY


def SV_RunThink(ent):
    """Run ent.think if nextthink is due.  Returns False if entity was freed."""
    thinktime = ent.nextthink
    if thinktime <= 0:
        return True
    if thinktime > level.time + 0.001:
        return True
    ent.nextthink = 0
    if not ent.think:
        pass
    else:
        ent.think(ent)
    return True


def SV_Impact(e1, trace):
    """Call touch callbacks on collision."""
    e2 = trace.ent if trace and trace.ent else None
    if e1.touch and e1.solid != solid_t.SOLID_NOT:
        e1.touch(e1, e2, trace.plane if trace else None, trace.surface if trace else None)
    if e2 and e2.touch and e2.solid != solid_t.SOLID_NOT:
        e2.touch(e2, e1, None, None)


def ClipVelocity(in_vel, normal, out_vel, overbounce):
    """Reflect in_vel off plane normal → out_vel.  overbounce=1 stops, >1 bounces."""
    backoff = (in_vel[0]*normal[0] + in_vel[1]*normal[1] + in_vel[2]*normal[2]) * overbounce
    for i in range(3):
        change = normal[i] * backoff
        out_vel[i] = in_vel[i] - change
        if STOP_EPSILON > out_vel[i] > -STOP_EPSILON:
            out_vel[i] = 0.0


MAX_CLIP_PLANES = 5

def SV_FlyMove(ent, time, mask):
    """Iterative sliding movement — used by MOVETYPE_FLY/FLYMISSILE/TOSS.
    Returns an OR of touched-surface flags (not fully used here).
    """
    numbumps  = 4
    blocked   = 0
    original_velocity = list(ent.velocity)
    primal_velocity   = list(ent.velocity)
    time_left = time

    planes = []
    for _bumpcount in range(numbumps):
        if time_left <= 0:
            break

        end = [
            ent.s.origin[0] + time_left * ent.velocity[0],
            ent.s.origin[1] + time_left * ent.velocity[1],
            ent.s.origin[2] + time_left * ent.velocity[2],
        ]

        trace = gi.trace(ent.s.origin, ent.mins, ent.maxs, end, ent, mask)

        if trace.allsolid:
            ent.velocity[:] = [0, 0, 0]
            return 3

        if trace.fraction > 0:
            ent.s.origin[:] = list(trace.endpos)
            original_velocity = list(ent.velocity)
            planes = []

        if trace.fraction == 1:
            break

        if trace.plane.normal[2] > 0.7:
            blocked |= 1   # floor
        if not trace.plane.normal[2]:
            blocked |= 2   # step

        SV_Impact(ent, trace)
        if not ent.inuse:
            break

        time_left -= time_left * trace.fraction

        if len(planes) >= MAX_CLIP_PLANES:
            ent.velocity[:] = [0, 0, 0]
            return 3

        planes.append(list(trace.plane.normal))

        for i, plane in enumerate(planes):
            new_velocity = [0.0, 0.0, 0.0]
            ClipVelocity(ent.velocity, plane, new_velocity, 1)
            for j, other_plane in enumerate(planes):
                if j == i:
                    continue
                dot = new_velocity[0]*other_plane[0] + new_velocity[1]*other_plane[1] + new_velocity[2]*other_plane[2]
                if dot < 0:
                    break
            else:
                ent.velocity[:] = new_velocity
                break
        else:
            if len(planes) == 2:
                # shoot along crease
                d0 = planes[0]
                d1 = planes[1]
                crease = [
                    d0[1]*d1[2] - d0[2]*d1[1],
                    d0[2]*d1[0] - d0[0]*d1[2],
                    d0[0]*d1[1] - d0[1]*d1[0],
                ]
                d = crease[0]*ent.velocity[0] + crease[1]*ent.velocity[1] + crease[2]*ent.velocity[2]
                ent.velocity[:] = [crease[i]*d for i in range(3)]
            else:
                ent.velocity[:] = [0, 0, 0]
                return 3

        dot = ent.velocity[0]*primal_velocity[0] + ent.velocity[1]*primal_velocity[1] + ent.velocity[2]*primal_velocity[2]
        if dot <= 0:
            ent.velocity[:] = [0, 0, 0]
            return blocked

    return blocked


def SV_AddGravity(ent):
    """Apply gravity to ent.velocity."""
    sv_gravity = 800.0
    if gi.cvar:
        try:
            sv_gravity = float(gi.cvar('sv_gravity', '800', 0).value)
        except Exception:
            sv_gravity = 800.0
    ent.velocity[2] -= ent.gravity * sv_gravity * 0.1


def SV_PushEntity(ent, push):
    """Move ent by push vector; fire touch callbacks. Returns trace."""
    end = [
        ent.s.origin[0] + push[0],
        ent.s.origin[1] + push[1],
        ent.s.origin[2] + push[2],
    ]

    if ent.clipmask:
        mask = ent.clipmask
    else:
        mask = MASK_SOLID

    trace = gi.trace(ent.s.origin, ent.mins, ent.maxs, end, ent, mask)
    ent.s.origin[:] = list(trace.endpos)
    gi.linkentity(ent)

    if trace.fraction != 1.0:
        SV_Impact(ent, trace)
        if not ent.inuse:
            return trace

    return trace


def SV_Push(pusher, move, amove):
    """Move a PUSH/STOP entity and drag or block other entities.
    Returns True on success, False if blocked.
    """
    g = _game()

    # build rotation matrix for amove
    # (simplified: only handle yaw rotation)
    yaw_rad = math.radians(amove[1])
    cos_yaw = math.cos(yaw_rad)
    sin_yaw = math.sin(yaw_rad)

    # save pusher's original position
    old_origin = list(pusher.s.origin)
    old_angles = list(pusher.s.angles)

    pusher.s.origin[0] += move[0]
    pusher.s.origin[1] += move[1]
    pusher.s.origin[2] += move[2]
    pusher.s.angles[0] += amove[0]
    pusher.s.angles[1] += amove[1]
    pusher.s.angles[2] += amove[2]
    gi.linkentity(pusher)

    # find entities in the potentially-moved-to area
    pushed_list = []

    for e in g.entities:
        if e is None or not e.inuse:
            continue
        if e.movetype in (movetype_t.MOVETYPE_PUSH, movetype_t.MOVETYPE_STOP,
                          movetype_t.MOVETYPE_NONE, movetype_t.MOVETYPE_NOCLIP):
            continue
        if e is pusher:
            continue

        # check overlap
        if (e.absmin[0] >= pusher.absmax[0] or e.absmin[1] >= pusher.absmax[1] or
                e.absmin[2] >= pusher.absmax[2]):
            continue
        if (e.absmax[0] <= pusher.absmin[0] or e.absmax[1] <= pusher.absmin[1] or
                e.absmax[2] <= pusher.absmin[2]):
            continue

        # save old position
        ent_origin = list(e.s.origin)

        # move entity with the pusher
        e.s.origin[0] += move[0]
        e.s.origin[1] += move[1]
        e.s.origin[2] += move[2]

        # test if valid position
        block = SV_TestEntityPosition(e)
        if block is None:
            gi.linkentity(e)
            pushed_list.append((e, ent_origin))
            continue

        # blocked — for STOP movers, abort
        if pusher.movetype == movetype_t.MOVETYPE_STOP:
            # restore pusher
            pusher.s.origin[:] = old_origin
            pusher.s.angles[:] = old_angles
            gi.linkentity(pusher)
            # restore all already-moved entities
            for moved_e, moved_origin in pushed_list:
                moved_e.s.origin[:] = moved_origin
                gi.linkentity(moved_e)
            if pusher.blocked:
                pusher.blocked(pusher, e)
            return False

        # restore this entity's position
        e.s.origin[:] = ent_origin

    return True


def SV_Physics_Pusher(ent):
    """Physics for MOVETYPE_PUSH / MOVETYPE_STOP (platforms, doors)."""
    if ent.velocity[0] or ent.velocity[1] or ent.velocity[2] or \
       ent.avelocity[0] or ent.avelocity[1] or ent.avelocity[2]:
        move = [v * 0.1 for v in ent.velocity]
        amove = [v * 0.1 for v in ent.avelocity]
        SV_Push(ent, move, amove)

    SV_RunThink(ent)


def SV_Physics_None(ent):
    """No physics — just run think."""
    SV_RunThink(ent)


def SV_Physics_Noclip(ent):
    """Noclip movement — no collision."""
    if not SV_RunThink(ent):
        return
    ent.s.angles[0] += 0.1 * ent.avelocity[0]
    ent.s.angles[1] += 0.1 * ent.avelocity[1]
    ent.s.angles[2] += 0.1 * ent.avelocity[2]
    ent.s.origin[0] += 0.1 * ent.velocity[0]
    ent.s.origin[1] += 0.1 * ent.velocity[1]
    ent.s.origin[2] += 0.1 * ent.velocity[2]
    gi.linkentity(ent)


def SV_Physics_Toss(ent):
    """Physics for MOVETYPE_TOSS / MOVETYPE_BOUNCE / MOVETYPE_FLY / MOVETYPE_FLYMISSILE."""
    SV_RunThink(ent)
    if not ent.inuse:
        return

    if ent.velocity[2] > 0:
        ent.groundentity = None

    if ent.groundentity and not ent.groundentity.inuse:
        ent.groundentity = None

    if ent.movetype in (movetype_t.MOVETYPE_FLY, movetype_t.MOVETYPE_FLYMISSILE):
        SV_FlyMove(ent, 0.1, ent.clipmask if ent.clipmask else MASK_SOLID)
        gi.linkentity(ent)
        SV_ToTouchList(ent)
        return

    if ent.groundentity is None:
        SV_AddGravity(ent)

    SV_CheckVelocity(ent)

    move = [ent.velocity[i] * 0.1 for i in range(3)]
    trace = SV_PushEntity(ent, move)
    if not ent.inuse:
        return

    if trace.fraction < 1.0:
        if ent.movetype == movetype_t.MOVETYPE_BOUNCE:
            new_vel = [0.0, 0.0, 0.0]
            ClipVelocity(ent.velocity, trace.plane.normal, new_vel, 1.5)
            ent.velocity[:] = new_vel
        else:
            new_vel = [0.0, 0.0, 0.0]
            ClipVelocity(ent.velocity, trace.plane.normal, new_vel, 1.0)
            ent.velocity[:] = new_vel

        if trace.plane.normal[2] > 0.7:
            if ent.velocity[2] < 60 or ent.movetype != movetype_t.MOVETYPE_BOUNCE:
                ent.groundentity = trace.ent
                ent.groundentity_linkcount = trace.ent.linkcount if trace.ent else 0
                ent.velocity[:] = [0, 0, 0]
                ent.avelocity[:] = [0, 0, 0]

    if ent.inuse:
        SV_ToTouchList(ent)

    if ent.inuse:
        gi.linkentity(ent)


def SV_ToTouchList(ent):
    """Fire G_TouchTriggers and G_TouchSolids for ent."""
    from .g_utils import G_TouchTriggers, G_TouchSolids
    G_TouchTriggers(ent)
    if ent.inuse:
        G_TouchSolids(ent)


def SV_AddRotationalFriction(ent):
    """Apply friction to ent.avelocity."""
    ROTATIONAL_FRICTION_LEVEL = 200.0
    ROTATIONAL_SPEED         =   2.0
    ent.s.angles[0] += 0.1 * ent.avelocity[0]
    ent.s.angles[1] += 0.1 * ent.avelocity[1]
    ent.s.angles[2] += 0.1 * ent.avelocity[2]
    for i in range(3):
        if ent.avelocity[i] > 0:
            ent.avelocity[i] -= ROTATIONAL_FRICTION_LEVEL * 0.1
            if ent.avelocity[i] < 0:
                ent.avelocity[i] = 0
        elif ent.avelocity[i] < 0:
            ent.avelocity[i] += ROTATIONAL_FRICTION_LEVEL * 0.1
            if ent.avelocity[i] > 0:
                ent.avelocity[i] = 0


def SV_Physics_Step(ent):
    """Physics for MOVETYPE_STEP (monsters) — gravity + step-up."""
    SV_CheckVelocity(ent)

    if ent.groundentity and not ent.groundentity.inuse:
        ent.groundentity = None

    if ent.groundentity is None:
        SV_AddGravity(ent)

    if ent.avelocity[0] or ent.avelocity[1] or ent.avelocity[2]:
        SV_AddRotationalFriction(ent)

    if ent.velocity[0] or ent.velocity[1] or ent.velocity[2]:
        SV_CheckVelocity(ent)
        mask = ent.clipmask if ent.clipmask else MASK_MONSTERSOLID
        SV_FlyMove(ent, 0.1, mask)
        gi.linkentity(ent)
        from .g_utils import G_TouchTriggers
        G_TouchTriggers(ent)
        if not ent.inuse:
            return

    if not SV_RunThink(ent):
        return


def G_RunEntity(ent):
    """Dispatch entity to the appropriate physics routine."""
    mt = ent.movetype
    if mt == movetype_t.MOVETYPE_PUSH or mt == movetype_t.MOVETYPE_STOP:
        SV_Physics_Pusher(ent)
    elif mt == movetype_t.MOVETYPE_NONE:
        SV_Physics_None(ent)
    elif mt == movetype_t.MOVETYPE_NOCLIP:
        SV_Physics_Noclip(ent)
    elif mt in (movetype_t.MOVETYPE_STEP,):
        SV_Physics_Step(ent)
    elif mt in (movetype_t.MOVETYPE_TOSS, movetype_t.MOVETYPE_BOUNCE,
                movetype_t.MOVETYPE_FLY, movetype_t.MOVETYPE_FLYMISSILE):
        SV_Physics_Toss(ent)
    elif mt == movetype_t.MOVETYPE_WALK:
        SV_RunThink(ent)
    else:
        raise RuntimeError(f"G_RunEntity: bad movetype {mt}")
