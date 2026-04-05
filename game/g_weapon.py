import math
import random as _random

from .reference_import import gi
from .global_vars import level
from shared.QEnums import movetype_t, solid_t, damage_t, temp_event_t, multicast_t
from shared.QConstants import (MASK_SHOT, MASK_SOLID, EF_ROCKET, EF_BLASTER,
                                EF_GRENADE, EF_BFG, EF_HYPERBLASTER,
                                CONTENTS_SOLID)

MOD_BLASTER      = 1
MOD_SHOTGUN      = 2
MOD_SSHOTGUN     = 3
MOD_MACHINEGUN   = 4
MOD_GRENADE      = 6
MOD_G_SPLASH     = 7
MOD_ROCKET       = 8
MOD_R_SPLASH     = 9
MOD_HYPERBLASTER = 10
MOD_RAILGUN      = 11
MOD_BFG_BLAST    = 13
MOD_BFG_EFFECT   = 14
MOD_HIT          = 32

DAMAGE_BULLET     = 0x00000010
DAMAGE_RADIUS     = 0x00000001


def _game():
    from .g_main import game
    return game


def check_dodge(self, start, _dir, speed):
    """Give nearby monsters a chance to dodge an incoming attack."""
    from .g_utils import findradius
    for ent in findradius(start, 256):
        if ent is self:
            continue
        if not ent.inuse:
            continue
        if not (ent.svflags & 0x01):  # SVF_MONSTER
            continue
        if ent.health <= 0:
            continue
        if not ent.monsterinfo or not ent.monsterinfo.dodge:
            continue
        ent.monsterinfo.dodge(ent, self, _dir, speed)


def fire_hit(self, aim, damage, kick):
    """Melee attack — trace forward, damage on hit. Returns True on hit."""
    from .q_shared import AngleVectors
    forward = [0.0, 0.0, 0.0]
    right   = [0.0, 0.0, 0.0]
    up      = [0.0, 0.0, 0.0]
    AngleVectors(self.s.angles, forward, right, up)

    center = [
        self.s.origin[0] + (self.mins[0] + self.maxs[0]) * 0.5,
        self.s.origin[1] + (self.mins[1] + self.maxs[1]) * 0.5,
        self.s.origin[2] + (self.mins[2] + self.maxs[2]) * 0.5,
    ]
    start = [
        center[0] + forward[0] * aim[0] + right[0] * aim[1] + up[0] * aim[2],
        center[1] + forward[1] * aim[0] + right[1] * aim[1] + up[1] * aim[2],
        center[2] + forward[2] * aim[0] + right[2] * aim[1] + up[2] * aim[2],
    ]
    end = [
        start[0] + forward[0] * 2,
        start[1] + forward[1] * 2,
        start[2] + forward[2] * 2,
    ]

    tr = gi.trace(start, None, None, end, self, MASK_SHOT)
    if tr.fraction < 1.0 and tr.ent and tr.ent.takedamage:
        from .g_combat import T_Damage
        T_Damage(tr.ent, self, self, forward, tr.endpos, tr.plane.normal,
                 damage, kick, 0, MOD_HIT)
        return True
    return False


def fire_lead(self, start, aimdir, damage, kick, te_impact, hspread, vspread, mod):
    """Single hitscan bullet — trace from start along aimdir."""
    from .q_shared import AngleVectors
    from .g_utils import vectoangles

    angles = [0.0, 0.0, 0.0]
    vectoangles(aimdir, angles)

    forward = [0.0, 0.0, 0.0]
    right   = [0.0, 0.0, 0.0]
    up      = [0.0, 0.0, 0.0]
    AngleVectors(angles, forward, right, up)

    spread_x = (_random.random() * 2 - 1) * hspread
    spread_y = (_random.random() * 2 - 1) * vspread
    end = [
        start[0] + forward[0] * 8192 + right[0] * spread_x + up[0] * spread_y,
        start[1] + forward[1] * 8192 + right[1] * spread_x + up[1] * spread_y,
        start[2] + forward[2] * 8192 + right[2] * spread_x + up[2] * spread_y,
    ]

    tr = gi.trace(start, None, None, end, self, MASK_SHOT)
    if tr.fraction < 1.0:
        if tr.ent and tr.ent.takedamage:
            from .g_combat import T_Damage
            T_Damage(tr.ent, self, self, aimdir, tr.endpos, tr.plane.normal,
                     damage, kick, DAMAGE_BULLET, mod)
        else:
            if gi.WriteByte and gi.WritePosition and gi.WriteDir and gi.multicast:
                gi.WriteByte(26)  # svc_temp_entity
                gi.WriteByte(te_impact)
                gi.WritePosition(tr.endpos)
                gi.WriteDir(tr.plane.normal)
                gi.multicast(tr.endpos, multicast_t.MULTICAST_PVS)


def fire_bullet(self, start, aimdir, damage, kick, hspread, vspread, mod):
    """Single bullet — calls fire_lead with bullet damage flags."""
    fire_lead(self, start, aimdir, damage, kick, 14, hspread, vspread, mod)


def fire_shotgun(self, start, aimdir, damage, kick, hspread, vspread, count, mod):
    """Multi-pellet shotgun blast."""
    for _ in range(count):
        fire_lead(self, start, aimdir, damage, kick, 4, hspread, vspread, mod)


def blaster_touch(self, other, plane, surf):
    """Blaster bolt impact — explode and remove."""
    from .g_combat import T_Damage, SpawnDamage
    mod = MOD_HYPERBLASTER if self.s.effects & EF_HYPERBLASTER else MOD_BLASTER

    if other is self.owner:
        return

    if surf and surf.flags & 0x80:  # SURF_SKY
        from .g_utils import G_FreeEdict
        G_FreeEdict(self)
        return

    if other.takedamage:
        from .g_combat import T_Damage
        norm = plane.normal if plane else [0, 0, 1]
        T_Damage(other, self, self.owner, self.velocity, self.s.origin, norm,
                 self.dmg, 1, 8, mod)  # DAMAGE_ENERGY
    else:
        SpawnDamage(2, self.s.origin, plane.normal if plane else [0, 0, 1], self.dmg)

    from .g_utils import G_FreeEdict
    G_FreeEdict(self)


def fire_blaster(self, start, _dir, damage, speed, effect, hyper):
    """Spawn a blaster bolt projectile."""
    from .g_utils import G_Spawn
    bolt = G_Spawn()
    bolt.s.origin[:] = list(start)
    bolt.s.angles[1] = math.degrees(math.atan2(_dir[1], _dir[0]))

    bolt.movetype = movetype_t.MOVETYPE_FLYMISSILE
    bolt.clipmask = MASK_SHOT
    bolt.solid = solid_t.SOLID_BBOX
    bolt.s.effects |= effect
    bolt.s.modelindex = gi.modelindex("models/objects/laser/tris.md2") if gi.modelindex else 0
    bolt.owner = self
    bolt.touch = blaster_touch
    bolt.nextthink = level.time + 8000 / speed if speed > 0 else level.time + 8
    bolt.think = lambda e: _G_FreeEdict_safe(e)
    bolt.dmg = damage
    bolt.classname = "bolt"

    length = math.sqrt(_dir[0]**2 + _dir[1]**2 + _dir[2]**2)
    if length > 0:
        bolt.velocity[:] = [_dir[i] / length * speed for i in range(3)]
    gi.linkentity(bolt)


def _G_FreeEdict_safe(e):
    from .g_utils import G_FreeEdict
    G_FreeEdict(e)


def Grenade_Explode(self):
    """Grenade detonation."""
    if self.enemy:
        from .g_combat import T_Damage
        diff = [
            self.s.origin[i] - self.enemy.s.origin[i]
            for i in range(3)
        ]
        d = math.sqrt(sum(x*x for x in diff)) - 32
        if d < 0:
            d = 0
        pts = self.dmg - 0.5 * d
        if pts > 0:
            norm = [x / (math.sqrt(sum(y*y for y in diff)) or 1) for x in diff]
            T_Damage(self.enemy, self, self.owner, [0,0,0],
                     self.s.origin, norm, int(pts), int(pts), 0x01, MOD_G_SPLASH)

    from .g_combat import T_RadiusDamage
    T_RadiusDamage(self, self.owner, self.dmg_radius, self.enemy, self.dmg_radius, MOD_G_SPLASH)

    if gi.WriteByte and gi.WritePosition and gi.multicast:
        origin_save = list(self.s.origin)
        gi.WriteByte(26)
        gi.WriteByte(temp_event_t.TE_GRENADE_EXPLOSION.value)
        gi.WritePosition(origin_save)
        gi.multicast(origin_save, multicast_t.MULTICAST_PHS)

    from .g_utils import G_FreeEdict
    G_FreeEdict(self)


def Grenade_Touch(self, other, plane, surf):
    """Grenade bounce/stick."""
    if other is self.owner:
        return
    if surf and surf.flags & 0x80:
        from .g_utils import G_FreeEdict
        G_FreeEdict(self)
        return
    if not other.takedamage:
        if gi.sound and self.s.sound:
            gi.sound(self, 0, self.s.sound, 1, 1, 0)
        return
    self.enemy = other
    Grenade_Explode(self)


def fire_grenade(self, start, aimdir, damage, speed, timer, damage_radius):
    """Launch a hand grenade."""
    from .g_utils import G_Spawn
    grenade = G_Spawn()
    grenade.s.origin[:] = list(start)
    length = math.sqrt(sum(x*x for x in aimdir)) or 1
    grenade.velocity[:] = [aimdir[i] / length * speed for i in range(3)]
    grenade.velocity[2] += 200 + _random.uniform(-25, 25)
    grenade.avelocity[:] = [300, 0, 0]
    grenade.movetype = movetype_t.MOVETYPE_BOUNCE
    grenade.clipmask = MASK_SHOT
    grenade.solid = solid_t.SOLID_BBOX
    grenade.s.effects |= EF_GRENADE
    grenade.owner = self
    grenade.touch = Grenade_Touch
    grenade.nextthink = level.time + timer
    grenade.think = Grenade_Explode
    grenade.dmg = damage
    grenade.dmg_radius = damage_radius
    grenade.classname = "grenade"
    grenade.mass = 400
    gi.linkentity(grenade)


def fire_grenade2(self, start, aimdir, damage, speed, timer, damage_radius):
    """Launch a grenade-launcher grenade (less arc)."""
    from .g_utils import G_Spawn
    grenade = G_Spawn()
    grenade.s.origin[:] = list(start)
    length = math.sqrt(sum(x*x for x in aimdir)) or 1
    grenade.velocity[:] = [aimdir[i] / length * speed for i in range(3)]
    grenade.avelocity[:] = [300, 0, 0]
    grenade.movetype = movetype_t.MOVETYPE_BOUNCE
    grenade.clipmask = MASK_SHOT
    grenade.solid = solid_t.SOLID_BBOX
    grenade.s.effects |= EF_GRENADE
    grenade.owner = self
    grenade.touch = Grenade_Touch
    grenade.nextthink = level.time + timer
    grenade.think = Grenade_Explode
    grenade.dmg = damage
    grenade.dmg_radius = damage_radius
    grenade.classname = "hgrenade"
    grenade.mass = 400
    gi.linkentity(grenade)


def rocket_touch(self, other, plane, surf):
    """Rocket impact."""
    if other is self.owner:
        return
    if surf and surf.flags & 0x80:
        from .g_utils import G_FreeEdict
        G_FreeEdict(self)
        return

    if other.takedamage:
        from .g_combat import T_Damage
        norm = plane.normal if plane else [0, 0, 1]
        T_Damage(other, self, self.owner, self.velocity, self.s.origin, norm,
                 self.dmg, 0, 0, MOD_ROCKET)

    from .g_combat import T_RadiusDamage
    T_RadiusDamage(self, self.owner, self.radius_dmg, other, self.dmg_radius, MOD_R_SPLASH)

    if gi.WriteByte and gi.WritePosition and gi.multicast:
        origin_save = list(self.s.origin)
        gi.WriteByte(26)
        gi.WriteByte(temp_event_t.TE_ROCKET_EXPLOSION.value)
        gi.WritePosition(origin_save)
        gi.multicast(origin_save, multicast_t.MULTICAST_PHS)

    from .g_utils import G_FreeEdict
    G_FreeEdict(self)


def fire_rocket(self, start, _dir, damage, speed, damage_radius, radius_damage):
    """Launch a rocket."""
    from .g_utils import G_Spawn
    rocket = G_Spawn()
    rocket.s.origin[:] = list(start)
    rocket.s.angles[1] = math.degrees(math.atan2(_dir[1], _dir[0]))
    length = math.sqrt(sum(x*x for x in _dir)) or 1
    rocket.velocity[:] = [_dir[i] / length * speed for i in range(3)]
    rocket.movetype = movetype_t.MOVETYPE_FLYMISSILE
    rocket.clipmask = MASK_SHOT
    rocket.solid = solid_t.SOLID_BBOX
    rocket.s.effects |= EF_ROCKET
    rocket.s.modelindex = gi.modelindex("models/objects/rocket/tris.md2") if gi.modelindex else 0
    if gi.soundindex:
        rocket.s.sound = gi.soundindex("weapons/rockfly.wav")
    rocket.owner = self
    rocket.touch = rocket_touch
    rocket.nextthink = level.time + 8000 / speed if speed > 0 else level.time + 8
    rocket.think = _G_FreeEdict_safe
    rocket.dmg = damage
    rocket.radius_dmg = radius_damage
    rocket.dmg_radius = damage_radius
    rocket.classname = "rocket"
    rocket.mass = 200
    gi.linkentity(rocket)


def fire_rail(self, start, aimdir, damage, kick):
    """Hit-scan rail shot — instant trace. Spawns rail trail."""
    length = math.sqrt(sum(x*x for x in aimdir)) or 1
    norm = [aimdir[i] / length for i in range(3)]
    end = [start[i] + norm[i] * 8192 for i in range(3)]

    passent = self
    while True:
        tr = gi.trace(start, None, None, end, passent, MASK_SHOT)
        if tr.ent and tr.ent.takedamage:
            from .g_combat import T_Damage
            T_Damage(tr.ent, self, self, aimdir, tr.endpos, tr.plane.normal,
                     damage, kick, 0, MOD_RAILGUN)
        if tr.fraction == 1.0:
            break
        passent = tr.ent
        if not passent:
            break

    if gi.WriteByte and gi.WritePosition and gi.WriteDir and gi.multicast:
        gi.WriteByte(26)
        gi.WriteByte(temp_event_t.TE_RAILTRAIL.value)
        gi.WritePosition(start)
        gi.WritePosition(tr.endpos)
        gi.multicast(self.s.origin, multicast_t.MULTICAST_PHS)


def bfg_explode(self):
    """BFG secondary explosion — damages everything in radius."""
    if self.timestamp <= level.time:
        from .g_utils import G_FreeEdict
        G_FreeEdict(self)
        return

    from .g_utils import findradius
    from .g_combat import T_Damage, CanDamage
    for ent in findradius(self.s.origin, self.dmg_radius):
        if not ent.takedamage:
            continue
        if ent is self.owner:
            continue
        if not CanDamage(ent, self):
            continue
        diff = [ent.s.origin[i] - self.s.origin[i] for i in range(3)]
        d = math.sqrt(sum(x*x for x in diff)) or 1
        norm = [x / d for x in diff]
        T_Damage(ent, self, self.owner, [0,0,0], ent.s.origin, norm,
                 self.dmg, 0, DAMAGE_RADIUS, MOD_BFG_EFFECT)

    self.nextthink = level.time + 0.1
    self.think = bfg_explode


DAMAGE_RADIUS = 0x00000001


def bfg_touch(self, other, plane, surf):
    """BFG projectile hits something."""
    if other is self.owner:
        return
    if surf and surf.flags & 0x80:
        from .g_utils import G_FreeEdict
        G_FreeEdict(self)
        return

    if gi.WriteByte and gi.WritePosition and gi.multicast:
        origin_save = list(self.s.origin)
        gi.WriteByte(26)
        gi.WriteByte(temp_event_t.TE_BFG_BIGEXPLOSION.value)
        gi.WritePosition(origin_save)
        gi.multicast(origin_save, multicast_t.MULTICAST_PVS)

    if other.takedamage:
        from .g_combat import T_Damage
        norm = plane.normal if plane else [0, 0, 1]
        T_Damage(other, self, self.owner, self.velocity, self.s.origin, norm,
                 200, 0, 0, MOD_BFG_BLAST)

    from .g_combat import T_RadiusDamage
    T_RadiusDamage(self, self.owner, self.radius_dmg, other, self.dmg_radius, MOD_BFG_BLAST)

    from .g_utils import G_Spawn, G_FreeEdict
    explosion = G_Spawn()
    explosion.s.origin[:] = list(self.s.origin)
    explosion.movetype = movetype_t.MOVETYPE_NONE
    explosion.solid = solid_t.SOLID_NOT
    explosion.s.renderfx |= 0x08  # RF_FULLBRIGHT
    explosion.owner = self.owner
    explosion.dmg = self.dmg // 10
    explosion.dmg_radius = self.dmg_radius
    explosion.radius_dmg = self.radius_dmg
    explosion.timestamp = level.time + 1.0
    explosion.think = bfg_explode
    explosion.nextthink = level.time + 0.1
    explosion.classname = "bfg explosion"
    gi.linkentity(explosion)

    G_FreeEdict(self)


def bfg_think(self):
    """BFG in-flight: shoot laser beams at nearby enemies."""
    from .g_utils import findradius
    from .g_combat import T_Damage, CanDamage
    for ent in findradius(self.s.origin, 256):
        if ent is self.owner:
            continue
        if not ent.takedamage:
            continue
        if not CanDamage(ent, self):
            continue
        if gi.WriteByte and gi.WritePosition and gi.multicast:
            gi.WriteByte(26)
            gi.WriteByte(temp_event_t.TE_BFG_LASER.value)
            gi.WritePosition(self.s.origin)
            gi.WritePosition(ent.s.origin)
            gi.multicast(self.s.origin, multicast_t.MULTICAST_PVS)
        T_Damage(ent, self, self.owner, [0,0,0], ent.s.origin, [0,0,0],
                 5, 0, 0, MOD_BFG_LASER)

    self.nextthink = level.time + 0.1


def fire_bfg(self, start, _dir, damage, speed, damage_radius):
    """Launch the BFG ball."""
    from .g_utils import G_Spawn
    bfg = G_Spawn()
    bfg.s.origin[:] = list(start)
    bfg.s.angles[1] = math.degrees(math.atan2(_dir[1], _dir[0]))
    length = math.sqrt(sum(x*x for x in _dir)) or 1
    bfg.velocity[:] = [_dir[i] / length * speed for i in range(3)]
    bfg.movetype = movetype_t.MOVETYPE_FLYMISSILE
    bfg.clipmask = MASK_SHOT
    bfg.solid = solid_t.SOLID_BBOX
    bfg.s.effects |= EF_BFG
    bfg.s.modelindex = gi.modelindex("models/objects/laser/tris.md2") if gi.modelindex else 0
    bfg.owner = self
    bfg.touch = bfg_touch
    bfg.nextthink = level.time + 8000 / speed if speed > 0 else level.time + 8
    bfg.think = bfg_think
    bfg.radius_dmg = damage
    bfg.dmg_radius = damage_radius
    bfg.dmg = damage // 10
    bfg.classname = "bfg"
    bfg.mass = 200
    gi.linkentity(bfg)
