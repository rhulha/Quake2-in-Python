import math
import random as _random

from .reference_import import gi
from .global_vars import level
from shared.QEnums import damage_t, temp_event_t, multicast_t, solid_t
from shared.QConstants import (MASK_SOLID, MASK_SHOT,
                                CONTENTS_SOLID, EF_GIB,
                                PRINT_HIGH, RF_SHELL_RED)

MOD_UNKNOWN      = 0
MOD_BLASTER      = 1
MOD_SHOTGUN      = 2
MOD_SSHOTGUN     = 3
MOD_MACHINEGUN   = 4
MOD_CHAINGUN     = 5
MOD_GRENADE      = 6
MOD_G_SPLASH     = 7
MOD_ROCKET       = 8
MOD_R_SPLASH     = 9
MOD_HYPERBLASTER = 10
MOD_RAILGUN      = 11
MOD_BFG_LASER    = 12
MOD_BFG_BLAST    = 13
MOD_BFG_EFFECT   = 14
MOD_HANDGRENADE  = 15
MOD_HG_SPLASH    = 16
MOD_WATER        = 17
MOD_SLIME        = 18
MOD_LAVA         = 19
MOD_CRUSH        = 20
MOD_TELEFRAG     = 21
MOD_FALLING      = 22
MOD_SUICIDE      = 23
MOD_HELD_GRENADE = 24
MOD_EXPLOSIVE    = 25
MOD_BARREL       = 26
MOD_BOMB         = 27
MOD_EXIT         = 28
MOD_SPLASH       = 29
MOD_TARGET_LASER = 30
MOD_TRIGGER_HURT = 31
MOD_HIT          = 32
MOD_TARGET_BLASTER = 33
MOD_FRIENDLY_FIRE = 0x8000000

# Damage flags
DAMAGE_RADIUS     = 0x00000001
DAMAGE_NO_ARMOR   = 0x00000002
DAMAGE_ENERGY     = 0x00000004
DAMAGE_NO_KNOCKBACK = 0x00000008
DAMAGE_BULLET     = 0x00000010
DAMAGE_NO_PROTECTION = 0x00000020

GIB_ORGANIC  = 0
GIB_METALLIC = 1


def _game():
    from .g_main import game
    return game


def CanDamage(targ, inflictor):
    """Check if targ can be damaged by inflictor (line-of-sight check)."""
    if targ is inflictor:
        return True

    # Try a direct trace from inflictor to target
    dest = list(targ.s.origin)
    tr = gi.trace(inflictor.s.origin, None, None, dest, inflictor, MASK_SOLID)
    if tr.fraction == 1.0:
        return True

    # Try a variety of offsets
    origin = inflictor.s.origin
    for offset in [
        [targ.mins[0], targ.mins[1], targ.mins[2]],
        [targ.maxs[0], targ.mins[1], targ.mins[2]],
        [targ.mins[0], targ.maxs[1], targ.mins[2]],
        [targ.maxs[0], targ.maxs[1], targ.mins[2]],
        [targ.mins[0], targ.mins[1], targ.maxs[2]],
        [targ.maxs[0], targ.mins[1], targ.maxs[2]],
        [targ.mins[0], targ.maxs[1], targ.maxs[2]],
        [targ.maxs[0], targ.maxs[1], targ.maxs[2]],
    ]:
        dest = [
            targ.s.origin[0] + offset[0],
            targ.s.origin[1] + offset[1],
            targ.s.origin[2] + offset[2],
        ]
        tr = gi.trace(origin, None, None, dest, inflictor, MASK_SOLID)
        if tr.fraction == 1.0:
            return True

    return False


def Killed(targ, inflictor, attacker, damage, point):
    """Handle entity death."""
    if targ.health < -999:
        targ.health = -999

    targ.enemy = attacker

    if targ.svflags & 0x01:  # SVF_MONSTER
        if targ.deadflag == 0:
            targ.deadflag = 1  # DEAD_DYING
        if targ.monsterinfo and targ.monsterinfo.currentmove:
            pass  # let monster's die callback handle it
        else:
            if targ.die:
                targ.die(targ, inflictor, attacker, damage, point)
        return

    if targ.die:
        targ.die(targ, inflictor, attacker, damage, point)


def SpawnDamage(_type, origin, normal, damage):
    """Spawn a temp entity at impact point."""
    if gi.WriteByte and gi.WritePosition and gi.WriteDir and gi.multicast:
        gi.WriteByte(26)  # svc_temp_entity
        gi.WriteByte(_type)
        gi.WritePosition(origin)
        gi.WriteDir(normal)
        gi.multicast(origin, multicast_t.MULTICAST_PVS)


def CheckPowerArmor(ent, point, normal, damage, dflags):
    """Check for power armor protection. Returns remaining damage."""
    if not ent.client:
        return damage
    if dflags & DAMAGE_NO_ARMOR:
        return damage

    # Power armor cell drain — simplified
    power_armor_type = 0  # no power armour by default
    if hasattr(ent.client, 'pers'):
        pass  # could check inventory

    return damage


def CheckArmor(ent, point, normal, damage, te_sparks, dflags):
    """Check for body armor. Returns damage that bleeds through."""
    if not ent.client:
        return damage
    if dflags & DAMAGE_NO_ARMOR:
        return damage

    client = ent.client
    if not hasattr(client, 'pers'):
        return damage

    # Find best armor
    index = 0
    armor_val = 0

    # jacket armor
    if hasattr(client.pers, 'inventory') and len(client.pers.inventory) > 2:
        index = 2  # ITEM_ARMOR_JACKET in real game
        armor_val = client.pers.inventory[index] if client.pers.inventory[index] > 0 else 0

    if armor_val <= 0:
        return damage

    # normal protection = 0.6, full = 0.8
    protection = 0.6
    save = int(math.ceil(protection * damage))
    if save >= armor_val:
        save = armor_val

    client.pers.inventory[index] -= save
    SpawnDamage(te_sparks, point, normal, save)

    return damage - save


def M_ReactToDamage(targ, attacker):
    """Monster reacts to being damaged — may switch attack target."""
    if not (targ.svflags & 0x01):  # not a monster
        return
    if not attacker.client and not (attacker.svflags & 0x01):
        return
    if attacker is targ:
        return

    if attacker is targ.enemy:
        return

    targ.enemy = attacker
    from .g_ai import FoundTarget
    FoundTarget(targ)


def CheckTeamDamage(targ, attacker):
    """Check if friendly fire. Returns True if damage should be skipped."""
    return False


def T_Damage(targ, inflictor, attacker, _dir, point, normal, damage, knockback, dflags, _mod):
    """Apply damage to an entity."""
    if not targ.takedamage or targ.takedamage == damage_t.DAMAGE_NO.value:
        return

    # check team damage
    if CheckTeamDamage(targ, attacker):
        return

    client = targ.client

    # power armor
    damage = CheckPowerArmor(targ, point, normal, damage, dflags)

    # armor
    if client:
        if dflags & DAMAGE_NO_ARMOR:
            pass
        else:
            asave = CheckArmor(targ, point, normal, damage, 12, dflags)  # TE_SPARKS
            damage -= asave

    if damage <= 0:
        return

    # knockback
    if knockback and not (dflags & DAMAGE_NO_KNOCKBACK):
        if targ.mass > 0:
            kscale = 1600.0 / targ.mass
        else:
            kscale = 1600.0
        if _dir and (abs(_dir[0]) + abs(_dir[1]) + abs(_dir[2])) > 0:
            targ.velocity[0] += _dir[0] * knockback * kscale * 0.1
            targ.velocity[1] += _dir[1] * knockback * kscale * 0.1
            targ.velocity[2] += _dir[2] * knockback * kscale * 0.1

    take = damage
    save = 0

    SpawnDamage(1, point, normal, take)  # TE_BLOOD

    targ.health -= take

    if targ.health <= 0:
        if targ.svflags & 0x01:
            targ.flags |= 0x400  # FL_NO_KNOCKBACK for dead monsters
        Killed(targ, inflictor, attacker, take, point)
        return

    if targ.svflags & 0x01:
        M_ReactToDamage(targ, attacker)
    if targ.pain:
        targ.pain(targ, attacker, knockback, take)


def T_RadiusDamage(inflictor, attacker, damage, ignore, radius, _mod):
    """Apply splash damage to all entities within radius."""
    from .g_utils import findradius
    elist = findradius(inflictor.s.origin, radius)

    for ent in elist:
        if ent is ignore:
            continue
        if not ent.takedamage or ent.takedamage == damage_t.DAMAGE_NO.value:
            continue
        if not CanDamage(ent, inflictor):
            continue

        # scale damage by distance
        org = inflictor.s.origin
        eorg = [
            ent.s.origin[0] + (ent.mins[0] + ent.maxs[0]) * 0.5,
            ent.s.origin[1] + (ent.mins[1] + ent.maxs[1]) * 0.5,
            ent.s.origin[2] + (ent.mins[2] + ent.maxs[2]) * 0.5,
        ]
        diff = [eorg[i] - org[i] for i in range(3)]
        dist = math.sqrt(diff[0]**2 + diff[1]**2 + diff[2]**2)
        pts = damage - 0.5 * dist
        if pts <= 0:
            continue

        # direction for knockback
        length = dist if dist > 0 else 1.0
        _dir = [d / length for d in diff]

        T_Damage(ent, inflictor, attacker, _dir, ent.s.origin, _dir,
                 int(pts), int(pts), DAMAGE_RADIUS, _mod)
