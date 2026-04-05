import math

from .reference_import import gi


PITCH = 0
YAW = 1
ROLL = 2


def _game():
    from .g_main import game
    return game


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _angles_to_axes(angles):
    pitch = math.radians(angles[0])
    yaw = math.radians(angles[1])
    roll = math.radians(angles[2])

    sp, cp = math.sin(pitch), math.cos(pitch)
    sy, cy = math.sin(yaw), math.cos(yaw)
    sr, cr = math.sin(roll), math.cos(roll)

    forward = [cp * cy, cp * sy, -sp]
    right = [(-sr * sp * cy) + (-cr * -sy), (-sr * sp * sy) + (-cr * cy), -sr * cp]
    up = [(cr * sp * cy) + (-sr * -sy), (cr * sp * sy) + (-sr * cy), cr * cp]
    return forward, right, up


def SV_CalcRoll(angles, velocity, sv_rollangle=2.0, sv_rollspeed=200.0):
    _, right, _ = _angles_to_axes(angles)
    side = _dot(velocity, right)
    sign = -1 if side < 0 else 1
    side = abs(side)

    if side < sv_rollspeed:
        side = side * sv_rollangle / sv_rollspeed
    else:
        side = sv_rollangle
    return side * sign


def P_DamageFeedback(player):
    if not player or not player.client:
        return

    client = player.client
    client.ps.stats[0] = 0
    if client.damage_blood:
        client.ps.stats[0] |= 1
    if client.damage_armor and not (player.flags & 0x10):
        client.ps.stats[0] |= 2

    count = client.damage_blood + client.damage_armor + client.damage_parmor
    if count <= 0:
        return

    if count < 10:
        count = 10
    client.damage_alpha += count * 0.01
    if client.damage_alpha < 0.2:
        client.damage_alpha = 0.2
    if client.damage_alpha > 0.6:
        client.damage_alpha = 0.6

    real = max(1, client.damage_blood + client.damage_armor + client.damage_parmor)
    v = [0.0, 0.0, 0.0]
    if client.damage_parmor:
        f = client.damage_parmor / real
        v[0] += 0.0 * f
        v[1] += 1.0 * f
        v[2] += 0.0 * f
    if client.damage_armor:
        f = client.damage_armor / real
        v[0] += 1.0 * f
        v[1] += 1.0 * f
        v[2] += 1.0 * f
    if client.damage_blood:
        f = client.damage_blood / real
        v[0] += 1.0 * f
        v[1] += 0.0 * f
        v[2] += 0.0 * f
    client.damage_blend[:] = v

    kick = abs(client.damage_knockback)
    if kick and player.health > 0:
        kick = kick * 100 / player.health
        if kick < count * 0.5:
            kick = count * 0.5
        if kick > 50:
            kick = 50

        d = [
            client.damage_from[0] - player.s.origin[0],
            client.damage_from[1] - player.s.origin[1],
            client.damage_from[2] - player.s.origin[2],
        ]
        n = math.sqrt(_dot(d, d)) or 1.0
        d = [d[0] / n, d[1] / n, d[2] / n]
        fwd, right, _ = _angles_to_axes(player.client.ps.viewangles)
        side = _dot(d, right)
        client.v_dmg_roll = kick * side * 0.3
        side = -_dot(d, fwd)
        client.v_dmg_pitch = kick * side * 0.3
        client.v_dmg_time = _game().level.time + 0.5

    client.damage_blood = 0
    client.damage_armor = 0
    client.damage_parmor = 0
    client.damage_knockback = 0


def SV_CalcViewOffset(ent):
    client = ent.client
    angles = client.ps.kick_angles

    if ent.deadflag:
        angles[:] = [0.0, 0.0, 0.0]
        client.ps.viewangles[ROLL] = 40
        client.ps.viewangles[PITCH] = -15
        client.ps.viewangles[YAW] = client.killer_yaw
    else:
        angles[:] = list(client.kick_angles)

        ratio = (client.v_dmg_time - _game().level.time) / 0.5
        if ratio < 0:
            ratio = 0
            client.v_dmg_pitch = 0
            client.v_dmg_roll = 0
        angles[PITCH] += ratio * client.v_dmg_pitch
        angles[ROLL] += ratio * client.v_dmg_roll

        ratio = (client.fall_time - _game().level.time) / 0.3
        if ratio < 0:
            ratio = 0
        angles[PITCH] += ratio * client.fall_value

        forward, right, _ = _angles_to_axes(client.ps.viewangles)
        delta = _dot(ent.velocity, forward)
        angles[PITCH] += delta * 0.002
        delta = _dot(ent.velocity, right)
        angles[ROLL] += delta * 0.001

    v = [0.0, 0.0, 0.0]
    v[2] += ent.viewheight

    ratio = (client.fall_time - _game().level.time) / 0.3
    if ratio < 0:
        ratio = 0
    v[2] -= ratio * client.fall_value * 0.4

    speed = math.sqrt(ent.velocity[0] * ent.velocity[0] + ent.velocity[1] * ent.velocity[1])
    bob = math.sin(_game().level.time * 8.0) * speed * 0.001
    if bob > 6:
        bob = 6
    v[2] += bob

    v[0] += client.kick_origin[0]
    v[1] += client.kick_origin[1]
    v[2] += client.kick_origin[2]

    v[0] = max(-14, min(14, v[0]))
    v[1] = max(-14, min(14, v[1]))
    v[2] = max(-22, min(30, v[2]))

    client.ps.viewoffset[:] = v


def SV_CalcGunOffset(ent):
    client = ent.client
    speed = math.sqrt(ent.velocity[0] * ent.velocity[0] + ent.velocity[1] * ent.velocity[1])
    bobfracsin = math.sin(_game().level.time * 8.0)

    client.ps.gunangles[ROLL] = speed * bobfracsin * 0.005
    client.ps.gunangles[YAW] = speed * bobfracsin * 0.01
    if int(_game().level.framenum) & 1:
        client.ps.gunangles[ROLL] = -client.ps.gunangles[ROLL]
        client.ps.gunangles[YAW] = -client.ps.gunangles[YAW]
    client.ps.gunangles[PITCH] = speed * bobfracsin * 0.005

    for i in range(3):
        delta = client.oldviewangles[i] - client.ps.viewangles[i]
        if delta > 180:
            delta -= 360
        if delta < -180:
            delta += 360
        delta = max(-45, min(45, delta))
        if i == YAW:
            client.ps.gunangles[ROLL] += 0.1 * delta
        client.ps.gunangles[i] += 0.2 * delta

    client.ps.gunoffset[:] = [0.0, 0.0, 0.0]
    fwd, right, up = _angles_to_axes(client.ps.viewangles)
    gun_x = getattr(_game(), "gun_x", 0.0)
    gun_y = getattr(_game(), "gun_y", 0.0)
    gun_z = getattr(_game(), "gun_z", 0.0)
    for i in range(3):
        client.ps.gunoffset[i] += fwd[i] * gun_y
        client.ps.gunoffset[i] += right[i] * gun_x
        client.ps.gunoffset[i] += up[i] * (-gun_z)


def SV_AddBlend(r, g, b, a, v_blend):
    if a <= 0:
        return
    a2 = v_blend[3] + (1 - v_blend[3]) * a
    a3 = v_blend[3] / a2 if a2 else 0
    v_blend[0] = v_blend[0] * a3 + r * (1 - a3)
    v_blend[1] = v_blend[1] * a3 + g * (1 - a3)
    v_blend[2] = v_blend[2] * a3 + b * (1 - a3)
    v_blend[3] = a2


def SV_CalcBlend(ent):
    client = ent.client
    client.ps.blend[:] = [0.0, 0.0, 0.0, 0.0]

    if ent.deadflag:
        SV_AddBlend(0.4, 0.0, 0.0, 0.5, client.ps.blend)

    if client.damage_alpha > 0:
        SV_AddBlend(
            client.damage_blend[0],
            client.damage_blend[1],
            client.damage_blend[2],
            client.damage_alpha,
            client.ps.blend,
        )
        client.damage_alpha -= 0.06
        if client.damage_alpha < 0:
            client.damage_alpha = 0


def P_FallingDamage(ent):
    if not ent or not ent.client:
        return

    delta = ent.velocity[2] - ent.client.oldvelocity[2]
    delta = delta * delta * 0.0001
    if ent.waterlevel == 3:
        return
    if ent.waterlevel == 2:
        delta *= 0.25
    if ent.waterlevel == 1:
        delta *= 0.5
    if delta < 1:
        return

    ent.client.fall_value = min(40, delta * 0.5)
    ent.client.fall_time = _game().level.time + 0.3

    if delta > 15 and ent.health > 0:
        if delta >= 30:
            if gi.sound and gi.soundindex:
                gi.sound(ent, 1, gi.soundindex("player/land1.wav"), 1, 1, 0)
        damage = int((delta - 30) / 2)
        if damage > 0:
            from .g_combat import T_Damage
            T_Damage(ent, None, None, [0, 0, 1], ent.s.origin, [0, 0, 1], damage, 0, 0, 19)


def P_WorldEffects(ent):
    if ent.health <= 0:
        return

    breather = ent.client.breather_framenum > _game().level.framenum
    envirosuit = ent.client.enviro_framenum > _game().level.framenum

    if ent.waterlevel == 3:
        if not breather and not envirosuit:
            if ent.air_finished < _game().level.time:
                if ent.client.next_drown_time < _game().level.time and ent.health > 0:
                    ent.client.next_drown_time = _game().level.time + 1
                    ent.dmg += 2
                    if ent.dmg > 15:
                        ent.dmg = 15
                    from .g_combat import T_Damage
                    T_Damage(ent, None, None, [0, 0, 1], ent.s.origin, [0, 0, 1], ent.dmg, 0, 0, 14)
        else:
            ent.air_finished = _game().level.time + 10
            ent.dmg = 2
    else:
        ent.air_finished = _game().level.time + 12
        ent.dmg = 2


def G_SetClientEffects(ent):
    ent.s.effects = 0
    if ent.health <= 0:
        return
    if ent.powerarmor_time > _game().level.time:
        ent.s.effects |= 0x00000080
    if ent.client.quad_framenum > _game().level.framenum:
        ent.s.effects |= 0x00000008
    if ent.client.invincible_framenum > _game().level.framenum:
        ent.s.effects |= 0x00000010


def G_SetClientEvent(ent):
    ent.s.event = 0
    if ent.client and ent.client.fall_value > 0 and ent.groundentity:
        if ent.client.fall_value > 32:
            ent.s.event = 1
        elif ent.client.fall_value > 16:
            ent.s.event = 2


def G_SetClientSound(ent):
    if ent.waterlevel and ent.watertype & 0x20:
        ent.client.ps.rdflags |= 1
    else:
        ent.client.ps.rdflags &= ~1


def G_SetClientFrame(ent):
    if ent.s.modelindex != 255:
        return

    client = ent.client
    if client.anim_priority == 0:
        if client.ps.pmove.pm_flags & 1:
            ent.s.frame = 135
            client.anim_end = 138
        elif ent.velocity[0] or ent.velocity[1]:
            ent.s.frame = 40
            client.anim_end = 45
        else:
            ent.s.frame = 0
            client.anim_end = 39

    if ent.s.frame < client.anim_end:
        ent.s.frame += 1
    else:
        client.anim_priority = 0


def ClientEndServerFrame(ent):
    if not ent or not ent.client:
        return

    ent.client.ps.pmove.origin[:] = [int(ent.s.origin[i] * 8) for i in range(3)]
    ent.client.ps.pmove.velocity[:] = [int(ent.velocity[i] * 8) for i in range(3)]

    if _game().intermissiontime:
        ent.client.ps.blend[:] = [0.0, 0.0, 0.0, 0.0]
        ent.client.ps.fov = 90
        return

    forward, right, up = _angles_to_axes(ent.client.v_angle)
    _ = (forward, right, up)

    P_WorldEffects(ent)
    P_FallingDamage(ent)
    P_DamageFeedback(ent)
    SV_CalcViewOffset(ent)
    SV_CalcGunOffset(ent)
    SV_CalcBlend(ent)

    if ent.client.resp.spectator:
        G_SetClientEvent(ent)
    else:
        G_SetClientEffects(ent)
        G_SetClientEvent(ent)
        G_SetClientSound(ent)
        G_SetClientFrame(ent)

    ent.client.oldvelocity[:] = list(ent.velocity)
    ent.client.oldviewangles[:] = list(ent.client.ps.viewangles)
    ent.client.kick_origin[:] = [0.0, 0.0, 0.0]
    ent.client.kick_angles[:] = [0.0, 0.0, 0.0]
