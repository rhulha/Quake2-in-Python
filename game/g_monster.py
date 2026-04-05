import math
import random as _random

from .reference_import import gi
from .global_vars import level
from shared.QEnums import movetype_t, solid_t, damage_t, temp_event_t, multicast_t
from shared.QConstants import (MASK_MONSTERSOLID, MASK_SHOT, MASK_WATER,
                                CONTENTS_WATER, CONTENTS_LAVA, CONTENTS_SLIME,
                                EF_FLIES, EF_GIB, SVF_MONSTER, SVF_DEADMONSTER,
                                PRINT_HIGH)

SVF_MONSTER    = 0x00000001
SVF_DEADMONSTER= 0x00000010
FL_FLY         = 0x00000004
FL_SWIM        = 0x00000008
FL_NO_KNOCKBACK= 0x00000400
FL_NOTARGET    = 0x00000008

DEAD_NO        = 0
DEAD_DYING     = 1
DEAD_DEAD      = 2
DEAD_RESPAWNABLE = 3

DAMAGE_AIM = 2

MONSTER_THINK_TIME = 0.1


def _game():
    from .g_main import game
    return game


def monster_fire_bullet(self, start, _dir, damage, kick, hspread, vspread, flashtype):
    from .g_weapon import fire_bullet
    fire_bullet(self, start, _dir, damage, kick, hspread, vspread, 4)  # MOD_MACHINEGUN
    if gi.WriteByte and gi.WritePosition and gi.WriteDir and gi.multicast:
        gi.WriteByte(1)   # svc_muzzleflash2
        gi.WriteShort(self.s.number)
        gi.WriteByte(flashtype)
        gi.multicast(start, multicast_t.MULTICAST_PVS)


def monster_fire_shotgun(self, start, aimdir, damage, kick, hspread, vspread, count, flashtype):
    from .g_weapon import fire_shotgun
    fire_shotgun(self, start, aimdir, damage, kick, hspread, vspread, count, 3)  # MOD_SHOTGUN
    if gi.WriteByte and gi.multicast:
        gi.WriteByte(1)
        gi.WriteShort(self.s.number)
        gi.WriteByte(flashtype)
        gi.multicast(start, multicast_t.MULTICAST_PVS)


def monster_fire_blaster(self, start, _dir, damage, speed, flashtype, effect):
    from .g_weapon import fire_blaster
    fire_blaster(self, start, _dir, damage, speed, effect, False)
    if gi.WriteByte and gi.multicast:
        gi.WriteByte(1)
        gi.WriteShort(self.s.number)
        gi.WriteByte(flashtype)
        gi.multicast(start, multicast_t.MULTICAST_PVS)


def monster_fire_grenade(self, start, aimdir, damage, speed, flashtype):
    from .g_weapon import fire_grenade
    fire_grenade(self, start, aimdir, damage, speed, 2.5, 2.5)
    if gi.WriteByte and gi.multicast:
        gi.WriteByte(1)
        gi.WriteShort(self.s.number)
        gi.WriteByte(flashtype)
        gi.multicast(start, multicast_t.MULTICAST_PVS)


def monster_fire_rocket(self, start, _dir, damage, speed, flashtype):
    from .g_weapon import fire_rocket
    fire_rocket(self, start, _dir, damage, speed, damage + 40, damage * 0.5)
    if gi.WriteByte and gi.multicast:
        gi.WriteByte(1)
        gi.WriteShort(self.s.number)
        gi.WriteByte(flashtype)
        gi.multicast(start, multicast_t.MULTICAST_PVS)


def monster_fire_railgun(self, start, aimdir, damage, kick, flashtype):
    from .g_weapon import fire_rail
    fire_rail(self, start, aimdir, damage, kick)
    if gi.WriteByte and gi.multicast:
        gi.WriteByte(1)
        gi.WriteShort(self.s.number)
        gi.WriteByte(flashtype)
        gi.multicast(start, multicast_t.MULTICAST_PVS)


def monster_fire_bfg(self, start, aimdir, damage, speed, kick, damage_radius, flashtype):
    from .g_weapon import fire_bfg
    fire_bfg(self, start, aimdir, damage, speed, damage_radius)
    if gi.WriteByte and gi.multicast:
        gi.WriteByte(1)
        gi.WriteShort(self.s.number)
        gi.WriteByte(flashtype)
        gi.multicast(start, multicast_t.MULTICAST_PVS)


def M_FliesOff(self):
    """Remove the flies-on-corpse effect."""
    self.s.effects &= ~EF_FLIES
    self.s.sound = 0


def M_FliesOn(self):
    """Start the flies-on-corpse visual/audio effect."""
    if self.waterlevel:
        return
    self.s.effects |= EF_FLIES
    if gi.soundindex:
        self.s.sound = gi.soundindex("infantry/insect1.wav")


def M_FlyCheck(self):
    """Schedule flies effect for recently dead monster."""
    if self.waterlevel:
        return
    if _random.random() > 0.5:
        self.think = M_FliesOn
        self.nextthink = level.time + 15 + _random.uniform(0, 15)


def AttackFinished(self, time):
    self.monsterinfo.attack_finished = level.time + time


def M_CheckGround(self):
    """Check if monster is on the ground; set/clear groundentity."""
    if self.flags & (FL_FLY | FL_SWIM):
        return

    if self.velocity[2] > 100:
        self.groundentity = None
        return

    point = [
        self.s.origin[0],
        self.s.origin[1],
        self.s.origin[2] - 0.25,
    ]
    tr = gi.trace(self.s.origin, self.mins, self.maxs, point, self, MASK_MONSTERSOLID)
    if tr.plane.normal[2] < 0.7 and not tr.startsolid:
        self.groundentity = None
        return

    if not tr.startsolid and not tr.allsolid:
        self.s.origin[:] = list(tr.endpos)
        self.groundentity = tr.ent
        self.groundentity_linkcount = tr.ent.linkcount if tr.ent else 0
        self.velocity[2] = 0


def M_CatagorizePosition(self):
    """Determine watertype and waterlevel."""
    point = [
        self.s.origin[0],
        self.s.origin[1],
        self.s.origin[2] + self.mins[2] + 1,
    ]
    cont = gi.pointcontents(point) if gi.pointcontents else 0
    if not (cont & MASK_WATER):
        self.waterlevel = 0
        self.watertype = 0
        return

    self.watertype = cont
    self.waterlevel = 1

    point[2] = self.s.origin[2] + (self.mins[2] + self.maxs[2]) * 0.5
    cont = gi.pointcontents(point) if gi.pointcontents else 0
    if not (cont & MASK_WATER):
        return
    self.waterlevel = 2

    point[2] = self.s.origin[2] + self.maxs[2] + 8
    cont = gi.pointcontents(point) if gi.pointcontents else 0
    if cont & MASK_WATER:
        self.waterlevel = 3


def M_WorldEffects(self):
    """Apply water/lava/slime damage and handle drowning."""
    dmg = 0
    if self.health > 0:
        if not (self.flags & FL_SWIM):
            if self.waterlevel > 2:
                # drowning: only non-swimmers drown
                pass
        if self.waterlevel:
            if self.watertype & CONTENTS_LAVA:
                if not (self.flags & FL_SWIM):
                    dmg = 10 * self.waterlevel
            elif self.watertype & CONTENTS_SLIME:
                dmg = 4 * self.waterlevel

    if dmg:
        from .g_combat import T_Damage
        T_Damage(self, _game().entities[0], _game().entities[0],
                 [0,0,0], self.s.origin, [0,0,0], dmg, 0, 8, MOD_WATER)

    from .g_phys import SV_AddGravity


MOD_WATER = 17


def M_droptofloor(self):
    """Drop monster to the floor."""
    self.s.origin[2] += 1

    end = list(self.s.origin)
    end[2] -= 256

    tr = gi.trace(self.s.origin, self.mins, self.maxs, end, self, MASK_MONSTERSOLID)
    if tr.fraction == 1.0 or tr.allsolid:
        return

    self.s.origin[:] = list(tr.endpos)
    gi.linkentity(self)
    M_CheckGround(self)
    M_CatagorizePosition(self)


def M_SetEffects(self):
    """Set entity effects bits for quad/pent/etc."""
    self.s.effects &= ~(0x08000 | 0x10000)  # EF_QUAD | EF_PENT
    if self.monsterinfo.power_armor_type == 1:
        self.s.effects |= 0x00000200  # EF_POWERSCREEN
    elif self.monsterinfo.power_armor_type == 2:
        if level.framenum & 8:
            self.s.effects |= 0x0100  # EF_COLOR_SHELL
            self.s.renderfx |= 0x400  # RF_SHELL_GREEN


def M_MoveFrame(self):
    """Advance monster animation frame and call frame function."""
    move = self.monsterinfo.currentmove
    if not move:
        return

    self.nextthink = level.time + MONSTER_THINK_TIME

    if self.monsterinfo.nextframe and move.firstframe <= self.monsterinfo.nextframe <= move.lastframe:
        self.s.frame = self.monsterinfo.nextframe
        self.monsterinfo.nextframe = 0
    else:
        if self.s.frame == move.lastframe:
            if move.endfunc:
                move.endfunc(self)
                if not self.inuse:
                    return
                if self.monsterinfo.currentmove != move:
                    # endfunc changed the move
                    M_MoveFrame(self)
                    return
            self.s.frame = move.firstframe
        else:
            self.s.frame += 1

    if move.frame and len(move.frame) > 0:
        frame_index = self.s.frame - move.firstframe
        if 0 <= frame_index < len(move.frame):
            frame = move.frame[frame_index]
            if frame.aifunc:
                frame.aifunc(self, frame.dist)
            if self.inuse and frame.thinkfunc:
                frame.thinkfunc(self)


def monster_think(self):
    """Monster think — advance frame and handle AI."""
    M_MoveFrame(self)
    if not self.inuse:
        return
    M_WorldEffects(self)
    if not self.inuse:
        return
    M_SetEffects(self)
    M_CatagorizePosition(self)
    M_CheckGround(self)
    gi.linkentity(self)


def monster_use(self, other, activator):
    """Monster use callback — release from waiting state."""
    if self.enemy:
        return
    if self.health <= 0:
        return
    if activator and activator.flags & FL_NOTARGET:
        return
    if not activator or not (activator.client or (activator.svflags & SVF_MONSTER)):
        return

    self.enemy = activator
    from .g_ai import FoundTarget
    FoundTarget(self)


def monster_triggered_spawn(self):
    """Actually spawn the monster (delayed by trigger)."""
    self.s.origin[2] += 1
    M_droptofloor(self)

    if self.enemy and self.enemy.inuse and self.enemy.health > 0:
        pass
    else:
        self.enemy = None

    monster_start_go(self)
    if self.enemy and self.enemy.inuse:
        from .g_ai import FoundTarget
        FoundTarget(self)


def monster_triggered_spawn_use(self, other, activator):
    """Use callback to trigger a delayed monster spawn."""
    self.svflags &= ~SVF_NOCLIENT  # make visible
    self.use = None
    if activator and activator.client:
        self.enemy = activator
    self.think = monster_triggered_spawn
    self.nextthink = level.time + 0.2


def monster_death_use(self):
    """After monster dies, trigger its targets."""
    self.flags &= ~(FL_FLY | FL_SWIM)
    self.monsterinfo.aiflags &= ~(0x04 | 0x08)  # AI_STAND_GROUND | AI_TEMP_STAND_GROUND
    if self.item:
        from .g_items import Drop_Item
        Drop_Item(self, self.item)
        self.item = None
    if self.deathtarget:
        self.target = self.deathtarget
    if self.target:
        from .g_utils import G_UseTargets
        G_UseTargets(self, self.attacker)


SVF_NOCLIENT = 0x00000004

def monster_start(self):
    """Initialize a monster at spawn time."""
    if self.spawnflags & 4:  # MONSTER_TRIGGER_SPAWN
        self.svflags |= SVF_NOCLIENT
        self.solid = solid_t.SOLID_NOT
        self.use = monster_triggered_spawn_use
        return False

    if not self.health:
        self.health = self.max_health = 100

    self.svflags |= SVF_MONSTER
    self.s.renderfx |= 0x04  # RF_FRAMELERP
    self.takedamage = DAMAGE_AIM
    self.air_finished = level.time + 12
    self.use = monster_use
    self.max_health = self.health
    self.clipmask = MASK_MONSTERSOLID
    self.deadflag = DEAD_NO
    self.svflags &= ~SVF_DEADMONSTER

    if not self.monsterinfo:
        from shared.QClasses import monsterinfo_t
        self.monsterinfo = monsterinfo_t()

    level.total_monsters += 1
    return True


def monster_start_go(self):
    """Finish monster setup after spawning."""
    if self.health <= 0:
        return

    if not self.yaw_speed:
        self.yaw_speed = 20

    if not self.viewheight:
        self.viewheight = 25

    if self.monsterinfo.stand:
        self.monsterinfo.stand(self)

    self.think = monster_think
    self.nextthink = level.time + _random.uniform(0, MONSTER_THINK_TIME)


def walkmonster_start_go(self):
    from .m_move import M_CheckBottom
    if not (self.spawnflags & 2) and gi.pointcontents:
        M_droptofloor(self)
        if not self.groundentity:
            pass
    monster_start_go(self)


def walkmonster_start(self):
    self.think = walkmonster_start_go
    self.nextthink = level.time + _random.uniform(0, MONSTER_THINK_TIME)
    if monster_start(self):
        pass


def flymonster_start_go(self):
    self.flags |= FL_FLY
    if not (self.spawnflags & 2):
        M_droptofloor(self)
    monster_start_go(self)


def flymonster_start(self):
    self.movetype = movetype_t.MOVETYPE_STEP
    self.think = flymonster_start_go
    self.nextthink = level.time + _random.uniform(0, MONSTER_THINK_TIME)
    monster_start(self)


def swimmonster_start_go(self):
    self.flags |= FL_SWIM
    self.waterlevel = 3
    monster_start_go(self)


def swimmonster_start(self):
    self.movetype = movetype_t.MOVETYPE_STEP
    self.think = swimmonster_start_go
    self.nextthink = level.time + _random.uniform(0, MONSTER_THINK_TIME)
    monster_start(self)
