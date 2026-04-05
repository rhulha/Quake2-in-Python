import math
import random as _random

from .reference_import import gi
from .global_vars import level
from shared.QEnums import movetype_t, solid_t


STATE_TOP = 0
STATE_BOTTOM = 1
STATE_UP = 2
STATE_DOWN = 3

DOOR_START_OPEN = 1
DOOR_REVERSE = 2
DOOR_CRUSHER = 4
DOOR_NOMONSTER = 8
DOOR_TOGGLE = 32
DOOR_X_AXIS = 64
DOOR_Y_AXIS = 128



def _sound(ent, chan, idx, vol=1.0, atten=3.0):
    if gi.sound and idx:
        gi.sound(ent, chan, idx, vol, atten, 0)



def Move_Done(ent):
    ent.velocity[:] = [0.0, 0.0, 0.0]
    if ent.moveinfo.endfunc:
        ent.moveinfo.endfunc(ent)



def Move_Final(ent):
    if ent.moveinfo.remaining_distance == 0:
        Move_Done(ent)
        return

    for i in range(3):
        ent.velocity[i] = ent.moveinfo.dir[i] * ent.moveinfo.remaining_distance / 0.1
    ent.think = Move_Done
    ent.nextthink = level.time + 0.1



def Move_Begin(ent):
    if (ent.moveinfo.speed * 0.1) >= ent.moveinfo.remaining_distance:
        Move_Final(ent)
        return

    for i in range(3):
        ent.velocity[i] = ent.moveinfo.dir[i] * ent.moveinfo.speed

    frames = math.floor((ent.moveinfo.remaining_distance / ent.moveinfo.speed) / 0.1)
    ent.moveinfo.remaining_distance -= frames * ent.moveinfo.speed * 0.1
    ent.nextthink = level.time + (frames * 0.1)
    ent.think = Move_Final



def Move_Calc(ent, dest, func):
    ent.velocity[:] = [0.0, 0.0, 0.0]
    delta = [dest[i] - ent.s.origin[i] for i in range(3)]
    dist = math.sqrt(delta[0] * delta[0] + delta[1] * delta[1] + delta[2] * delta[2])
    if dist > 0:
        ent.moveinfo.dir[:] = [delta[i] / dist for i in range(3)]
    else:
        ent.moveinfo.dir[:] = [0.0, 0.0, 0.0]
    ent.moveinfo.remaining_distance = dist
    ent.moveinfo.endfunc = func

    if ent.moveinfo.speed == ent.moveinfo.accel and ent.moveinfo.speed == ent.moveinfo.decel:
        Move_Begin(ent)
    else:
        ent.moveinfo.current_speed = 0
        ent.think = Think_AccelMove
        ent.nextthink = level.time + 0.1



def AngleMove_Done(ent):
    ent.avelocity[:] = [0.0, 0.0, 0.0]
    if ent.moveinfo.endfunc:
        ent.moveinfo.endfunc(ent)



def AngleMove_Final(ent):
    if ent.moveinfo.state == STATE_UP:
        move = [ent.moveinfo.end_angles[i] - ent.s.angles[i] for i in range(3)]
    else:
        move = [ent.moveinfo.start_angles[i] - ent.s.angles[i] for i in range(3)]

    if move[0] == 0 and move[1] == 0 and move[2] == 0:
        AngleMove_Done(ent)
        return

    for i in range(3):
        ent.avelocity[i] = move[i] / 0.1
    ent.think = AngleMove_Done
    ent.nextthink = level.time + 0.1



def AngleMove_Begin(ent):
    if ent.moveinfo.state == STATE_UP:
        destdelta = [ent.moveinfo.end_angles[i] - ent.s.angles[i] for i in range(3)]
    else:
        destdelta = [ent.moveinfo.start_angles[i] - ent.s.angles[i] for i in range(3)]

    length = math.sqrt(destdelta[0] * destdelta[0] + destdelta[1] * destdelta[1] + destdelta[2] * destdelta[2])
    traveltime = length / ent.moveinfo.speed if ent.moveinfo.speed else 0

    if traveltime < 0.1:
        AngleMove_Final(ent)
        return

    frames = math.floor(traveltime / 0.1)
    for i in range(3):
        ent.avelocity[i] = destdelta[i] / traveltime
    ent.nextthink = level.time + frames * 0.1
    ent.think = AngleMove_Final



def AngleMove_Calc(ent, func):
    ent.avelocity[:] = [0.0, 0.0, 0.0]
    ent.moveinfo.endfunc = func
    AngleMove_Begin(ent)



def _accel_distance(target, rate):
    return target * ((target / rate) + 1) / 2 if rate else 0



def plat_CalcAcceleratedMove(moveinfo):
    moveinfo.move_speed = moveinfo.speed

    if moveinfo.remaining_distance < moveinfo.accel:
        moveinfo.current_speed = moveinfo.remaining_distance
        return

    accel_dist = _accel_distance(moveinfo.speed, moveinfo.accel)
    decel_dist = _accel_distance(moveinfo.speed, moveinfo.decel)

    if (moveinfo.remaining_distance - accel_dist - decel_dist) < 0:
        f = (moveinfo.accel + moveinfo.decel) / (moveinfo.accel * moveinfo.decel)
        moveinfo.move_speed = (-2 + math.sqrt(4 - 4 * f * (-2 * moveinfo.remaining_distance))) / (2 * f)
        decel_dist = _accel_distance(moveinfo.move_speed, moveinfo.decel)

    moveinfo.decel_distance = decel_dist



def plat_Accelerate(moveinfo):
    if moveinfo.remaining_distance <= moveinfo.decel_distance:
        if moveinfo.remaining_distance < moveinfo.decel:
            moveinfo.current_speed = moveinfo.remaining_distance
            return
        if moveinfo.current_speed > moveinfo.decel:
            moveinfo.current_speed -= moveinfo.decel
            return

    if moveinfo.current_speed == moveinfo.move_speed:
        return

    newspeed = moveinfo.current_speed + moveinfo.accel
    if newspeed < moveinfo.move_speed:
        moveinfo.current_speed = newspeed
        return

    newspeed = moveinfo.move_speed
    p1_distance = moveinfo.remaining_distance - moveinfo.decel_distance
    p2_distance = moveinfo.move_speed * (1 - (moveinfo.current_speed + newspeed) / (2 * moveinfo.move_speed))

    if p1_distance < p2_distance:
        distance = p1_distance / p2_distance
        moveinfo.current_speed = moveinfo.current_speed + distance * (newspeed - moveinfo.current_speed)
    else:
        moveinfo.current_speed = newspeed



def Think_AccelMove(ent):
    moveinfo = ent.moveinfo

    if moveinfo.current_speed == 0:
        plat_CalcAcceleratedMove(moveinfo)

    plat_Accelerate(moveinfo)

    if (moveinfo.remaining_distance <= moveinfo.current_speed):
        Move_Final(ent)
        return

    for i in range(3):
        ent.velocity[i] = moveinfo.dir[i] * moveinfo.current_speed

    moveinfo.remaining_distance -= moveinfo.current_speed
    ent.nextthink = level.time + 0.1



def plat_hit_top(ent):
    if ent.moveinfo.sound_end:
        _sound(ent, 1, ent.moveinfo.sound_end)
    ent.moveinfo.state = STATE_TOP
    ent.think = plat_go_down
    ent.nextthink = level.time + 3



def plat_hit_bottom(ent):
    if ent.moveinfo.sound_end:
        _sound(ent, 1, ent.moveinfo.sound_end)
    ent.moveinfo.state = STATE_BOTTOM



def plat_go_down(ent):
    if ent.moveinfo.sound_start:
        _sound(ent, 1, ent.moveinfo.sound_start)
    ent.moveinfo.state = STATE_DOWN
    Move_Calc(ent, ent.moveinfo.end_origin, plat_hit_bottom)



def plat_go_up(ent):
    if ent.moveinfo.sound_start:
        _sound(ent, 1, ent.moveinfo.sound_start)
    ent.moveinfo.state = STATE_UP
    Move_Calc(ent, ent.moveinfo.start_origin, plat_hit_top)



def plat_blocked(_self, other):
    from .g_combat import T_Damage
    T_Damage(other, _self, _self, [0, 0, 0], other.s.origin, [0, 0, 0], _self.dmg, 1, 0, 12)



def Use_Plat(ent, other, activator):
    if ent.think:
        return
    plat_go_down(ent)



def Touch_Plat_Center(ent, other, plane, surg):
    if not other.client:
        return
    if other.health <= 0:
        return
    if ent.enemy.moveinfo.state == STATE_BOTTOM:
        plat_go_up(ent.enemy)



def plat_spawn_inside_trigger(ent):
    from .g_utils import G_Spawn
    trigger = G_Spawn()
    trigger.touch = Touch_Plat_Center
    trigger.movetype = movetype_t.MOVETYPE_NONE
    trigger.solid = solid_t.SOLID_TRIGGER
    trigger.enemy = ent

    tmin = list(ent.mins)
    tmax = list(ent.maxs)
    tmin[0] += 25
    tmin[1] += 25
    tmax[0] -= 25
    tmax[1] -= 25
    tmax[2] = tmin[2] + 8

    trigger.s.origin[:] = list(ent.s.origin)
    trigger.mins[:] = tmin
    trigger.maxs[:] = tmax
    gi.linkentity(trigger)



def SP_func_plat(ent):
    if not ent.speed:
        ent.speed = 20
    if not ent.accel:
        ent.accel = 5
    if not ent.decel:
        ent.decel = 5
    if not ent.dmg:
        ent.dmg = 2

    ent.movetype = movetype_t.MOVETYPE_PUSH
    ent.solid = solid_t.SOLID_BSP
    if gi.setmodel:
        gi.setmodel(ent, ent.model)

    ent.blocked = plat_blocked

    ent.moveinfo.start_origin[:] = list(ent.s.origin)
    ent.moveinfo.start_angles[:] = list(ent.s.angles)
    ent.moveinfo.speed = ent.speed
    ent.moveinfo.accel = ent.accel
    ent.moveinfo.decel = ent.decel
    ent.moveinfo.wait = ent.wait

    lip = ent.lip if ent.lip else 8
    height = ent.maxs[2] - ent.mins[2] - lip
    ent.moveinfo.end_origin[:] = [ent.s.origin[0], ent.s.origin[1], ent.s.origin[2] - height]
    ent.moveinfo.end_angles[:] = list(ent.s.angles)

    ent.use = Use_Plat

    if gi.soundindex:
        ent.moveinfo.sound_start = gi.soundindex("plats/pt1_strt.wav")
        ent.moveinfo.sound_middle = gi.soundindex("plats/pt1_mid.wav")
        ent.moveinfo.sound_end = gi.soundindex("plats/pt1_end.wav")

    plat_spawn_inside_trigger(ent)
    gi.linkentity(ent)



def rotating_blocked(_self, other):
    from .g_combat import T_Damage
    T_Damage(other, _self, _self, [0, 0, 0], other.s.origin, [0, 0, 0], _self.dmg, 1, 0, 12)



def rotating_touch(_self, other, plane, surf):
    if not other.takedamage:
        return
    from .g_combat import T_Damage
    T_Damage(other, _self, _self, [0, 0, 0], other.s.origin, [0, 0, 0], _self.dmg, 1, 0, 12)



def rotating_use(_self, other, activator):
    if _self.avelocity[0] or _self.avelocity[1] or _self.avelocity[2]:
        _self.avelocity[:] = [0, 0, 0]
        _self.touch = None
        return

    _self.avelocity[:] = [_self.movedir[0] * _self.speed,
                          _self.movedir[1] * _self.speed,
                          _self.movedir[2] * _self.speed]
    if _self.spawnflags & 16:
        _self.touch = rotating_touch



def SP_func_rotating(ent):
    from .g_utils import G_SetMovedir

    if ent.spawnflags & 4:
        ent.movedir[:] = [0, 0, 1]
    else:
        G_SetMovedir(ent.s.angles, ent.movedir)

    if not ent.speed:
        ent.speed = 100
    if not ent.dmg:
        ent.dmg = 2

    ent.movetype = movetype_t.MOVETYPE_PUSH
    ent.solid = solid_t.SOLID_BSP
    ent.use = rotating_use
    ent.blocked = rotating_blocked

    if gi.setmodel:
        gi.setmodel(ent, ent.model)
    gi.linkentity(ent)



def button_done(_self):
    _self.moveinfo.state = STATE_BOTTOM



def button_return(_self):
    _self.moveinfo.state = STATE_DOWN
    Move_Calc(_self, _self.moveinfo.start_origin, button_done)



def button_wait(_self):
    _self.moveinfo.state = STATE_TOP
    from .g_utils import G_UseTargets
    G_UseTargets(_self, _self.activator)
    _self.think = button_return
    _self.nextthink = level.time + _self.moveinfo.wait



def button_fire(_self):
    if _self.moveinfo.state == STATE_UP or _self.moveinfo.state == STATE_TOP:
        return

    _self.moveinfo.state = STATE_UP
    Move_Calc(_self, _self.moveinfo.end_origin, button_wait)



def button_use(_self, other, activator):
    _self.activator = activator
    button_fire(_self)



def button_touch(_self, other, plane, surf):
    if not other.client:
        return
    _self.activator = other
    button_fire(_self)



def button_killed(_self, inflictor, attacker, damage, point):
    _self.activator = attacker
    _self.health = _self.max_health
    _self.takedamage = 0
    button_fire(_self)



def SP_func_button(ent):
    from .g_utils import G_SetMovedir

    if not ent.speed:
        ent.speed = 40
    if not ent.accel:
        ent.accel = ent.speed
    if not ent.decel:
        ent.decel = ent.speed
    if not ent.wait:
        ent.wait = 3

    G_SetMovedir(ent.s.angles, ent.movedir)

    ent.movetype = movetype_t.MOVETYPE_STOP
    ent.solid = solid_t.SOLID_BSP
    if gi.setmodel:
        gi.setmodel(ent, ent.model)

    ent.use = button_use

    ent.moveinfo.start_origin[:] = list(ent.s.origin)
    ent.moveinfo.start_angles[:] = list(ent.s.angles)
    dist = abs(ent.movedir[0] * ent.size[0] + ent.movedir[1] * ent.size[1] + ent.movedir[2] * ent.size[2])
    ent.moveinfo.end_origin[:] = [ent.s.origin[i] + ent.movedir[i] * (dist - ent.lip) for i in range(3)]
    ent.moveinfo.end_angles[:] = list(ent.s.angles)
    ent.moveinfo.state = STATE_BOTTOM
    ent.moveinfo.speed = ent.speed
    ent.moveinfo.accel = ent.accel
    ent.moveinfo.decel = ent.decel
    ent.moveinfo.wait = ent.wait

    if ent.health:
        ent.max_health = ent.health
        ent.die = button_killed
        ent.takedamage = 1
    elif not ent.targetname:
        ent.touch = button_touch

    gi.linkentity(ent)



def door_use_areaportals(_self, open):
    if _self.target_ent and _self.target_ent.style and gi.SetAreaPortalState:
        gi.SetAreaPortalState(_self.target_ent.style, open)



def door_hit_top(_self):
    _self.moveinfo.state = STATE_TOP
    if not (_self.spawnflags & DOOR_TOGGLE):
        _self.think = door_go_down
        _self.nextthink = level.time + _self.moveinfo.wait



def door_hit_bottom(_self):
    _self.moveinfo.state = STATE_BOTTOM
    door_use_areaportals(_self, False)



def door_go_down(_self):
    if _self.max_health:
        _self.takedamage = 1
        _self.health = _self.max_health

    _self.moveinfo.state = STATE_DOWN
    Move_Calc(_self, _self.moveinfo.start_origin, door_hit_bottom)



def door_go_up(_self, activator):
    if _self.moveinfo.state == STATE_UP:
        return

    if _self.moveinfo.state == STATE_TOP:
        if _self.moveinfo.wait >= 0:
            _self.nextthink = level.time + _self.moveinfo.wait
        return

    if activator:
        _self.activator = activator

    _self.moveinfo.state = STATE_UP
    Move_Calc(_self, _self.moveinfo.end_origin, door_hit_top)
    door_use_areaportals(_self, True)



def door_use(_self, other, activator):
    if _self.flags & 0x00000400:
        return

    if _self.spawnflags & DOOR_TOGGLE:
        if _self.moveinfo.state == STATE_UP or _self.moveinfo.state == STATE_TOP:
            door_go_down(_self)
        else:
            door_go_up(_self, activator)
        return

    door_go_up(_self, activator)



def Touch_DoorTrigger(_self, other, plane, surf):
    if not other.client:
        return

    if other.health <= 0:
        return

    if _self.owner.moveinfo.state != STATE_UP:
        door_use(_self.owner, other, other)



def Think_CalcMoveSpeed(_self):
    return



def Think_SpawnDoorTrigger(ent):
    from .g_utils import G_Spawn

    if ent.flags & 0x00000400:
        return

    mins = list(ent.absmin)
    maxs = list(ent.absmax)

    trigger = G_Spawn()
    trigger.movetype = movetype_t.MOVETYPE_NONE
    trigger.solid = solid_t.SOLID_TRIGGER
    trigger.owner = ent
    trigger.touch = Touch_DoorTrigger
    trigger.mins[:] = [mins[0] - 60, mins[1] - 60, mins[2]]
    trigger.maxs[:] = [maxs[0] + 60, maxs[1] + 60, maxs[2]]
    gi.linkentity(trigger)



def door_blocked(_self, other):
    from .g_combat import T_Damage

    if not other.takedamage:
        return

    T_Damage(other, _self, _self, [0, 0, 0], other.s.origin, [0, 0, 0], _self.dmg, 1, 0, 12)

    if _self.spawnflags & DOOR_CRUSHER:
        return

    if _self.moveinfo.state == STATE_DOWN:
        door_go_up(_self, _self.activator)
    else:
        door_go_down(_self)



def door_killed(_self, inflictor, attacker, damage, point):
    _self.health = _self.max_health
    _self.takedamage = 0
    door_use(_self, attacker, attacker)



def door_touch(_self, other, plane, surf):
    if not other.client:
        return
    if level.time < _self.touch_debounce_time:
        return
    _self.touch_debounce_time = level.time + 5.0
    if _self.message and gi.centerprintf:
        gi.centerprintf(other, _self.message)



def SP_func_door(ent):
    from .g_utils import G_SetMovedir

    G_SetMovedir(ent.s.angles, ent.movedir)

    if not ent.speed:
        ent.speed = 100
    if not ent.accel:
        ent.accel = ent.speed
    if not ent.decel:
        ent.decel = ent.speed
    if not ent.wait:
        ent.wait = 3
    if not ent.dmg:
        ent.dmg = 2

    ent.movetype = movetype_t.MOVETYPE_PUSH
    ent.solid = solid_t.SOLID_BSP
    if gi.setmodel:
        gi.setmodel(ent, ent.model)

    ent.blocked = door_blocked

    ent.moveinfo.start_origin[:] = list(ent.s.origin)
    ent.moveinfo.start_angles[:] = list(ent.s.angles)
    dist = abs(ent.movedir[0] * ent.size[0] + ent.movedir[1] * ent.size[1] + ent.movedir[2] * ent.size[2])
    ent.moveinfo.end_origin[:] = [ent.s.origin[i] + ent.movedir[i] * (dist - ent.lip) for i in range(3)]
    ent.moveinfo.end_angles[:] = list(ent.s.angles)
    ent.moveinfo.state = STATE_BOTTOM
    ent.moveinfo.speed = ent.speed
    ent.moveinfo.accel = ent.accel
    ent.moveinfo.decel = ent.decel
    ent.moveinfo.wait = ent.wait

    if ent.spawnflags & DOOR_START_OPEN:
        ent.s.origin[:] = list(ent.moveinfo.end_origin)
        ent.moveinfo.end_origin[:] = list(ent.moveinfo.start_origin)
        ent.moveinfo.start_origin[:] = list(ent.s.origin)

    if ent.health:
        ent.max_health = ent.health
        ent.die = door_killed
        ent.takedamage = 1

    if ent.targetname:
        ent.use = door_use
    else:
        ent.think = Think_SpawnDoorTrigger
        ent.nextthink = level.time + 0.1

    if ent.message:
        ent.touch = door_touch

    gi.linkentity(ent)



def SP_func_door_rotating(ent):
    if not ent.speed:
        ent.speed = 100
    if not ent.dmg:
        ent.dmg = 2

    ent.movetype = movetype_t.MOVETYPE_PUSH
    ent.solid = solid_t.SOLID_BSP
    if gi.setmodel:
        gi.setmodel(ent, ent.model)

    if ent.spawnflags & DOOR_X_AXIS:
        ent.movedir[:] = [1, 0, 0]
    elif ent.spawnflags & DOOR_Y_AXIS:
        ent.movedir[:] = [0, 1, 0]
    else:
        ent.movedir[:] = [0, 0, 1]

    ent.moveinfo.speed = ent.speed
    ent.moveinfo.state = STATE_BOTTOM
    ent.moveinfo.start_angles[:] = list(ent.s.angles)

    angle = ent.distance if ent.distance else 90
    ent.moveinfo.end_angles[:] = [ent.s.angles[i] + ent.movedir[i] * angle for i in range(3)]

    ent.blocked = door_blocked

    if ent.targetname:
        ent.use = door_use
    else:
        ent.think = Think_SpawnDoorTrigger
        ent.nextthink = level.time + 0.1

    gi.linkentity(ent)



def SP_func_water(_self):
    SP_func_door(_self)



def train_blocked(_self, other):
    if level.time < _self.touch_debounce_time:
        return
    _self.touch_debounce_time = level.time + 0.5
    from .g_combat import T_Damage
    T_Damage(other, _self, _self, [0, 0, 0], other.s.origin, [0, 0, 0], _self.dmg, 1, 0, 12)



def train_wait(_self):
    if _self.target_ent and _self.target_ent.pathtarget:
        from .g_utils import G_UseTargets
        save = _self.target_ent.target
        _self.target_ent.target = _self.target_ent.pathtarget
        G_UseTargets(_self.target_ent, _self.activator)
        _self.target_ent.target = save

    if _self.moveinfo.wait > 0:
        _self.nextthink = level.time + _self.moveinfo.wait
        _self.think = train_next
    elif _self.spawnflags & 1:
        _self.nextthink = 0
    else:
        train_next(_self)



def train_next(_self):
    from .g_utils import G_Find

    if not _self.target:
        return

    ent = G_Find(None, 'targetname', _self.target)
    if not ent:
        return

    _self.target = ent.target
    _self.target_ent = ent

    dest = [ent.s.origin[i] - _self.mins[i] for i in range(3)]
    _self.moveinfo.state = STATE_TOP
    Move_Calc(_self, dest, train_wait)



def train_resume(_self):
    train_next(_self)



def func_train_find(_self):
    from .g_utils import G_Find

    target = G_Find(None, 'targetname', _self.target)
    if not target:
        return

    _self.s.origin[:] = [target.s.origin[i] - _self.mins[i] for i in range(3)]
    _self.target = target.target
    gi.linkentity(_self)

    if not _self.targetname:
        _self.spawnflags |= 1

    if _self.spawnflags & 1:
        _self.nextthink = level.time + 0.1
        _self.think = train_next



def train_use(_self, other, activator):
    _self.activator = activator

    if _self.spawnflags & 1:
        _self.spawnflags &= ~1
        if not (_self.velocity[0] or _self.velocity[1] or _self.velocity[2]):
            train_resume(_self)
    else:
        _self.spawnflags |= 1
        _self.velocity[:] = [0, 0, 0]
        _self.nextthink = 0



def SP_func_train(_self):
    if not _self.speed:
        _self.speed = 100
    if _self.dmg is None:
        _self.dmg = 2

    _self.movetype = movetype_t.MOVETYPE_PUSH
    _self.solid = solid_t.SOLID_BSP
    if gi.setmodel:
        gi.setmodel(_self, _self.model)

    _self.blocked = train_blocked
    _self.use = train_use
    _self.think = func_train_find
    _self.nextthink = level.time + 0.1
    _self.moveinfo.speed = _self.speed
    _self.moveinfo.accel = _self.accel if _self.accel else _self.speed
    _self.moveinfo.decel = _self.decel if _self.decel else _self.speed
    _self.moveinfo.wait = _self.wait

    gi.linkentity(_self)



def trigger_elevator_use(_self, other, activator):
    if _self.movetarget:
        return
    if not _self.target:
        return

    _self.movetarget = _self.goalentity
    _self.goalentity = _self.movetarget

    if _self.goalentity and _self.goalentity.pathtarget:
        _self.goalentity.target = _self.goalentity.pathtarget

    train_resume(_self.movetarget)



def trigger_elevator_init(_self):
    from .g_utils import G_Find

    _self.movetarget = G_Find(None, 'targetname', _self.target)
    if not _self.movetarget:
        return

    _self.use = trigger_elevator_use
    _self.svflags = 0x00000004



def SP_trigger_elevator(_self):
    if not _self.target:
        return

    _self.think = trigger_elevator_init
    _self.nextthink = level.time + 0.1



def func_timer_think(_self):
    from .g_utils import G_UseTargets

    G_UseTargets(_self, _self.activator)

    if _self.wait:
        _self.nextthink = level.time + _self.wait + _self.random * (_random.random() * 2.0 - 1.0)



def func_timer_use(_self, other, activator):
    _self.activator = activator

    if _self.nextthink:
        _self.nextthink = 0
    else:
        if _self.delay:
            _self.nextthink = level.time + _self.delay
        else:
            func_timer_think(_self)



def SP_func_timer(_self):
    if _self.wait is None:
        _self.wait = 1.0
    if _self.random is None:
        _self.random = 0.0

    if _self.random >= _self.wait and _self.wait > 0:
        _self.random = _self.wait - 0.1

    _self.use = func_timer_use
    _self.svflags = 0x00000004

    if _self.spawnflags & 1:
        _self.nextthink = level.time + 1.0 + _self.st.pausetime + _self.delay + _self.wait + _self.random * (_random.random() * 2.0 - 1.0)
        _self.activator = _self
        _self.think = func_timer_think



def func_conveyor_use(_self, other, activator):
    if _self.spawnflags & 1:
        _self.spawnflags &= ~1
        _self.speed = 0
    else:
        _self.spawnflags |= 1
        _self.speed = _self.count



def SP_func_conveyor(_self):
    if not _self.speed:
        _self.speed = 100

    if _self.spawnflags & 1:
        _self.count = _self.speed
    else:
        _self.count = _self.speed
        _self.speed = 0

    if gi.setmodel:
        gi.setmodel(_self, _self.model)

    _self.movetype = movetype_t.MOVETYPE_PUSH
    _self.solid = solid_t.SOLID_BSP
    _self.use = func_conveyor_use

    gi.linkentity(_self)



def door_secret_use(_self, other, activator):
    if _self.moveinfo.state != STATE_BOTTOM:
        return

    _self.moveinfo.state = STATE_UP

    if _self.spawnflags & 1:
        Move_Calc(_self, _self.moveinfo.end_origin, door_secret_move1)
    else:
        Move_Calc(_self, _self.moveinfo.end2_origin, door_secret_move1)



def door_secret_move1(_self):
    _self.nextthink = level.time + 1.0
    _self.think = door_secret_move2



def door_secret_move2(_self):
    if _self.spawnflags & 1:
        Move_Calc(_self, _self.moveinfo.end2_origin, door_secret_move3)
    else:
        Move_Calc(_self, _self.moveinfo.end_origin, door_secret_move3)



def door_secret_move3(_self):
    _self.nextthink = level.time + _self.wait
    _self.think = door_secret_move4



def door_secret_move4(_self):
    if _self.spawnflags & 1:
        Move_Calc(_self, _self.moveinfo.end_origin, door_secret_move5)
    else:
        Move_Calc(_self, _self.moveinfo.end2_origin, door_secret_move5)



def door_secret_move5(_self):
    _self.nextthink = level.time + 1.0
    _self.think = door_secret_move6



def door_secret_move6(_self):
    Move_Calc(_self, _self.moveinfo.start_origin, door_secret_done)



def door_secret_done(_self):
    if not (_self.spawnflags & 1):
        _self.moveinfo.state = STATE_BOTTOM
    else:
        _self.moveinfo.state = STATE_TOP



def door_secret_blocked(_self, other):
    from .g_combat import T_Damage
    T_Damage(other, _self, _self, [0, 0, 0], other.s.origin, [0, 0, 0], _self.dmg, 1, 0, 12)



def door_secret_die(_self, inflictor, attacker, damage, point):
    _self.takedamage = 0
    door_secret_use(_self, inflictor, attacker)



def SP_func_door_secret(ent):
    from .g_utils import G_SetMovedir

    if not ent.dmg:
        ent.dmg = 2
    if not ent.wait:
        ent.wait = 5
    if not ent.speed:
        ent.speed = 50

    ent.movetype = movetype_t.MOVETYPE_PUSH
    ent.solid = solid_t.SOLID_BSP
    if gi.setmodel:
        gi.setmodel(ent, ent.model)

    ent.blocked = door_secret_blocked
    ent.use = door_secret_use
    if not (ent.targetname or ent.health):
        ent.health = 1

    if ent.health:
        ent.max_health = ent.health
        ent.die = door_secret_die
        ent.takedamage = 1

    G_SetMovedir(ent.s.angles, ent.movedir)

    ent.moveinfo.start_origin[:] = list(ent.s.origin)
    ent.moveinfo.start_angles[:] = list(ent.s.angles)
    width = abs(ent.movedir[0] * ent.size[0] + ent.movedir[1] * ent.size[1] + ent.movedir[2] * ent.size[2])
    ent.moveinfo.end_origin[:] = [ent.s.origin[i] + ent.movedir[i] * width for i in range(3)]

    if ent.spawnflags & 1:
        side = [ent.movedir[1], -ent.movedir[0], 0]
    else:
        side = [-ent.movedir[1], ent.movedir[0], 0]

    width2 = abs(side[0] * ent.size[0] + side[1] * ent.size[1] + side[2] * ent.size[2])
    ent.moveinfo.end2_origin[:] = [ent.moveinfo.end_origin[i] + side[i] * width2 for i in range(3)]

    ent.moveinfo.state = STATE_BOTTOM
    ent.moveinfo.speed = ent.speed

    gi.linkentity(ent)



def use_killbox(_self, other, activator):
    from .g_utils import KillBox
    KillBox(_self)



def SP_func_killbox(ent):
    if gi.setmodel:
        gi.setmodel(ent, ent.model)
    ent.use = use_killbox
    ent.movetype = movetype_t.MOVETYPE_NONE
    ent.solid = solid_t.SOLID_BSP
    gi.linkentity(ent)
