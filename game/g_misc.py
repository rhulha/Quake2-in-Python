import math
import random

from .reference_import import gi
from .global_vars import level
from shared.QEnums import movetype_t, solid_t


GIB_ORGANIC  = 0
GIB_METALLIC = 1


def Use_Areaportal(ent, other, activator):
    ent.count ^= 1
    if gi.SetAreaPortalState:
        gi.SetAreaPortalState(ent.style, bool(ent.count))


def SP_func_areaportal(ent):
    ent.use   = Use_Areaportal
    ent.count = 0


def VelocityForDamage(damage, v):
    v[0] = 100.0 * damage * (0.5 - random.random())
    v[1] = 100.0 * damage * (0.5 - random.random())
    v[2] = 200.0 + damage * random.random()


def ClipGibVelocity(ent):
    for i in range(3):
        if ent.velocity[i] < -300:
            ent.velocity[i] = -300.0
        elif ent.velocity[i] > 300:
            ent.velocity[i] = 300.0
    if ent.velocity[2] < 200:
        ent.velocity[2] = 200.0


def gib_think(self):
    self.s.frame += 1
    self.nextthink = level.time + 0.1
    if self.s.frame == 10:
        self.think     = _gib_free
        self.nextthink = level.time + 8 + random.random() * 10


def _gib_free(ent):
    from .g_utils import G_FreeEdict
    G_FreeEdict(ent)


def gib_touch(self, other, plane, surf):
    if not plane:
        return
    if gi.sound and gi.soundindex:
        gi.sound(self, 0, gi.soundindex("misc/fhit3.wav"), 1, 1, 0)
    self.touch = None


def gib_die(self, inflictor, attacker, damage, point):
    from .g_utils import G_FreeEdict
    G_FreeEdict(self)


def ThrowGib(self, gibname, damage, _type):
    from .g_utils import G_Spawn
    gib = G_Spawn()
    for i in range(3):
        gib.s.origin[i] = self.absmin[i] + random.random() * (self.absmax[i] - self.absmin[i])
    if gi.setmodel:
        gi.setmodel(gib, gibname)
    gib.solid      = solid_t.SOLID_NOT
    gib.s.effects |= 0x0080  # EF_GIB
    gib.takedamage = 1
    gib.die        = gib_die
    gib.movetype   = movetype_t.MOVETYPE_TOSS
    v = [0.0, 0.0, 0.0]
    VelocityForDamage(damage, v)
    for i in range(3):
        gib.velocity[i] = self.velocity[i] / 2 + v[i]
    ClipGibVelocity(gib)
    gib.avelocity[0] = random.random() * 600
    gib.avelocity[1] = random.random() * 600
    gib.avelocity[2] = random.random() * 600
    gib.nextthink    = level.time + 5 + random.random() * 5
    gib.think        = gib_think
    gib.touch        = gib_touch
    gi.linkentity(gib)


def ThrowHead(self, gibname, damage, _type):
    from .g_utils import G_Spawn
    gib = G_Spawn()
    gib.s.origin[:] = list(self.s.origin)
    if gi.setmodel:
        gi.setmodel(gib, gibname)
    gib.solid      = solid_t.SOLID_NOT
    gib.s.effects |= 0x0080
    gib.takedamage = 1
    gib.die        = gib_die
    gib.movetype   = movetype_t.MOVETYPE_TOSS
    v = [0.0, 0.0, 0.0]
    VelocityForDamage(damage, v)
    for i in range(3):
        gib.velocity[i] = self.velocity[i] / 2 + v[i]
    ClipGibVelocity(gib)
    gib.avelocity[0] = random.random() * 600
    gib.avelocity[1] = random.random() * 600
    gib.avelocity[2] = random.random() * 600
    gib.nextthink    = level.time + 5 + random.random() * 5
    gib.think        = gib_think
    gib.touch        = gib_touch
    gi.linkentity(gib)


def ThrowClientHead(self, damage):
    ThrowHead(self, "models/objects/gibs/head2/tris.md2", damage, GIB_ORGANIC)


def debris_die(self, inflictor, attacker, damage, point):
    from .g_utils import G_FreeEdict
    G_FreeEdict(self)


def ThrowDebris(self, modelname, speed, origin):
    from .g_utils import G_Spawn
    chunk = G_Spawn()
    chunk.s.origin[:] = list(origin)
    if gi.setmodel:
        gi.setmodel(chunk, modelname)
    chunk.velocity[0]  = speed * (0.5 - random.random())
    chunk.velocity[1]  = speed * (0.5 - random.random())
    chunk.velocity[2]  = speed * (0.5 - random.random())
    chunk.movetype     = movetype_t.MOVETYPE_BOUNCE
    chunk.solid        = solid_t.SOLID_NOT
    chunk.avelocity[0] = random.random() * 600
    chunk.avelocity[1] = random.random() * 600
    chunk.avelocity[2] = random.random() * 600
    chunk.takedamage   = 1
    chunk.health       = 5
    chunk.die          = debris_die
    chunk.think        = debris_die
    chunk.nextthink    = level.time + 2 + random.random() * 2
    gi.linkentity(chunk)


def BecomeExplosion1(self):
    if gi.WriteByte and gi.multicast:
        gi.WriteByte(5)
        gi.WriteByte(3)  # TE_EXPLOSION1
        gi.WritePosition(self.s.origin)
        gi.multicast(self.s.origin, 1)
    from .g_utils import G_FreeEdict
    G_FreeEdict(self)


def BecomeExplosion2(self):
    if gi.WriteByte and gi.multicast:
        gi.WriteByte(5)
        gi.WriteByte(4)  # TE_EXPLOSION2
        gi.WritePosition(self.s.origin)
        gi.multicast(self.s.origin, 1)
    from .g_utils import G_FreeEdict
    G_FreeEdict(self)


def path_corner_touch(self, other, plane, surf):
    if other.movetarget != self:
        return
    if other.enemy:
        return
    if self.pathtarget:
        save = self.target
        self.target = self.pathtarget
        from .g_utils import G_UseTargets
        G_UseTargets(self, other)
        self.target = save
    from .g_utils import G_Find
    target = G_Find(None, 'targetname', self.target)
    if target and target != self:
        other.goalentity = target
        other.movetarget = target
    if self.wait:
        other.monsterinfo.pausetime = level.time + self.wait
        if other.monsterinfo.stand:
            other.monsterinfo.stand(other)
    else:
        if not other.movetarget:
            other.monsterinfo.pausetime = level.time + 100000000
            if other.monsterinfo.stand:
                other.monsterinfo.stand(other)
        else:
            if other.monsterinfo.walk:
                other.monsterinfo.walk(other)


def SP_path_corner(self):
    if not getattr(self, 'targetname', None):
        if gi.dprintf:
            gi.dprintf("path_corner with no targetname at %s\n" % str(self.s.origin))
        return
    self.solid   = solid_t.SOLID_TRIGGER
    self.touch   = path_corner_touch
    self.mins    = [-8, -8, -8]
    self.maxs    = [8, 8, 8]
    self.svflags = 0x04
    gi.linkentity(self)


def point_combat_touch(self, other, plane, surf):
    if other.movetarget != self:
        return
    if self.target:
        from .g_utils import G_Find
        targ = G_Find(None, 'targetname', self.target)
        if targ:
            other.goalentity = targ
            other.movetarget = targ
        if self.pathtarget:
            save = self.target
            self.target = self.pathtarget
            from .g_utils import G_UseTargets
            G_UseTargets(self, other)
            self.target = save
    else:
        other.goalentity = other.enemy


def SP_point_combat(self):
    self.solid   = solid_t.SOLID_TRIGGER
    self.touch   = point_combat_touch
    self.mins    = [-8, -8, -16]
    self.maxs    = [8, 8, 16]
    self.svflags = 0x04
    gi.linkentity(self)


def TH_viewthing(ent):
    ent.s.frame = (ent.s.frame + 1) % 7
    ent.nextthink = level.time + 0.1


def SP_viewthing(ent):
    if gi.setmodel:
        gi.setmodel(ent, "models/objects/gibs/bone/tris.md2")
    ent.movetype  = movetype_t.MOVETYPE_NONE
    ent.solid     = solid_t.SOLID_BBOX
    ent.mins      = [-16, -16, -24]
    ent.maxs      = [16, 16, -4]
    ent.think     = TH_viewthing
    ent.nextthink = level.time + 0.1
    gi.linkentity(ent)


def SP_info_null(self):
    from .g_utils import G_FreeEdict
    G_FreeEdict(self)


def SP_info_notnull(self):
    pass


def light_use(self, other, activator):
    self.spawnflags ^= 1


def SP_light(self):
    if not self.targetname:
        from .g_utils import G_FreeEdict
        G_FreeEdict(self)
        return
    if self.style >= 32:
        self.use = light_use


def func_wall_use(self, other, activator):
    if self.solid == solid_t.SOLID_NOT:
        self.solid    = solid_t.SOLID_BSP
        self.svflags &= ~0x04
    else:
        self.solid    = solid_t.SOLID_NOT
        self.svflags |= 0x04
        gi.unlinkentity(self)
    gi.linkentity(self)


def SP_func_wall(self):
    self.movetype = movetype_t.MOVETYPE_PUSH
    if gi.setmodel:
        gi.setmodel(self, self.model)
    if self.spawnflags & 4:
        self.solid    = solid_t.SOLID_NOT
        self.svflags |= 0x04
    else:
        self.solid = solid_t.SOLID_BSP
    if self.spawnflags & 7:
        self.use = func_wall_use
    gi.linkentity(self)


def func_object_touch(self, other, plane, surf):
    if not plane:
        return
    if other.takedamage:
        from .g_combat import T_Damage
        normal = list(getattr(plane, 'normal', [0, 0, 1]))
        T_Damage(other, self, self, [0, 0, 0], other.s.origin, normal,
                 self.dmg, 1, 0, 11)


def func_object_release(self):
    self.movetype = movetype_t.MOVETYPE_TOSS
    self.touch    = func_object_touch


def func_object_use(self, other, activator):
    self.solid    = solid_t.SOLID_BSP
    self.svflags &= ~0x04
    self.use      = None
    func_object_release(self)
    gi.linkentity(self)


def SP_func_object(self):
    if gi.setmodel:
        gi.setmodel(self, self.model)
    self.mins[2] += 1
    if self.spawnflags & 1:
        self.solid    = solid_t.SOLID_NOT
        self.svflags |= 0x04
        self.use      = func_object_use
    else:
        self.solid = solid_t.SOLID_BSP
        self.use   = func_object_use
    if not self.dmg:
        self.dmg = 100
    self.movetype = movetype_t.MOVETYPE_PUSH
    gi.linkentity(self)


def func_explosive_explode(self, inflictor, attacker, damage, point):
    from .g_combat import T_RadiusDamage
    T_RadiusDamage(self, attacker, self.dmg, None, self.dmg + 40, 13)
    BecomeExplosion1(self)


def func_explosive_use(self, other, activator):
    func_explosive_explode(self, other, activator, self.health, self.s.origin)


def func_explosive_spawn(self, other, activator):
    self.solid    = solid_t.SOLID_BSP
    self.svflags &= ~0x04
    self.use      = None
    from .g_utils import KillBox
    KillBox(self)
    gi.linkentity(self)


def SP_func_explosive(self):
    if gi.setmodel:
        gi.setmodel(self, self.model)
    if self.spawnflags & 1:
        self.svflags |= 0x04
        self.solid    = solid_t.SOLID_NOT
        self.use      = func_explosive_spawn
    else:
        self.solid = solid_t.SOLID_BSP
        self.use   = func_explosive_use
    if not self.health:
        self.health = 100
    self.takedamage = 1
    self.die        = func_explosive_explode
    self.movetype   = movetype_t.MOVETYPE_PUSH
    if not self.dmg:
        self.dmg = 150
    gi.linkentity(self)


def barrel_touch(self, other, plane, surf):
    if not other.groundentity:
        return
    from .g_combat import T_Damage
    T_Damage(other, self, self, [0, 0, 0], other.s.origin, [0, 0, 1], self.dmg, 1, 0, 11)


def barrel_explode(self):
    from .g_combat import T_RadiusDamage
    T_RadiusDamage(self, self.activator, self.dmg, None, self.dmg + 40, 13)
    BecomeExplosion2(self)


def barrel_delay(self, inflictor, attacker, damage, point):
    self.takedamage = 0
    self.activator  = attacker
    self.think      = barrel_explode
    self.nextthink  = level.time + 0.2


def SP_misc_explobox(self):
    if gi.modelindex:
        self.s.modelindex = gi.modelindex("models/objects/barrels/tris.md2")
    if not self.mass:
        self.mass = 400
    if not self.health:
        self.health = 10
    if not self.dmg:
        self.dmg = 150
    self.movetype   = movetype_t.MOVETYPE_STEP
    self.solid      = solid_t.SOLID_BBOX
    self.takedamage = 1
    self.die        = barrel_delay
    self.touch      = barrel_touch
    self.mins       = [-16, -16, 0]
    self.maxs       = [16, 16, 40]
    gi.linkentity(self)


def misc_blackhole_use(ent, other, activator):
    from .g_utils import G_FreeEdict
    G_FreeEdict(ent)


def misc_blackhole_think(self):
    self.s.frame = (self.s.frame + 1) % 19
    self.nextthink = level.time + 0.1


def SP_misc_blackhole(ent):
    ent.movetype  = movetype_t.MOVETYPE_NONE
    ent.solid     = solid_t.SOLID_NOT
    if gi.setmodel:
        gi.setmodel(ent, "models/objects/black/tris.md2")
    ent.s.renderfx = 0x0004  # RF_TRANSLUCENT
    ent.use       = misc_blackhole_use
    ent.think     = misc_blackhole_think
    ent.nextthink = level.time + 2
    gi.linkentity(ent)


def misc_eastertank_think(self):
    self.s.frame = (self.s.frame + 1) % 382
    self.nextthink = level.time + 0.1


def SP_misc_eastertank(ent):
    ent.movetype  = movetype_t.MOVETYPE_NONE
    ent.solid     = solid_t.SOLID_BBOX
    if gi.setmodel:
        gi.setmodel(ent, "models/monsters/tank/tris.md2")
    ent.mins      = [-32, -32, -16]
    ent.maxs      = [32, 32, 32]
    ent.think     = misc_eastertank_think
    ent.nextthink = level.time + 0.1
    gi.linkentity(ent)


def misc_easterchick_think(self):
    self.s.frame = (self.s.frame + 1) % 247
    self.nextthink = level.time + 0.1


def SP_misc_easterchick(ent):
    ent.movetype  = movetype_t.MOVETYPE_NONE
    ent.solid     = solid_t.SOLID_BBOX
    if gi.setmodel:
        gi.setmodel(ent, "models/monsters/bitch/tris.md2")
    ent.mins      = [-32, -32, 0]
    ent.maxs      = [32, 32, 48]
    ent.think     = misc_easterchick_think
    ent.nextthink = level.time + 0.1
    gi.linkentity(ent)


def misc_easterchick2_think(self):
    self.s.frame = (self.s.frame + 1) % 247
    self.nextthink = level.time + 0.1


def SP_misc_easterchick2(ent):
    SP_misc_easterchick(ent)
    ent.think = misc_easterchick2_think


def commander_body_think(self):
    self.s.frame = (self.s.frame + 1) % 24
    if self.s.frame == 22:
        ThrowGib(self, "models/objects/gibs/sm_meat/tris.md2", 500, GIB_ORGANIC)
    self.nextthink = level.time + 0.1


def commander_body_use(self, other, activator):
    self.takedamage = 0
    self.think     = commander_body_think
    self.nextthink = level.time + 0.1
    if gi.sound and gi.soundindex:
        gi.sound(self, 3, gi.soundindex("tank/pain.wav"), 1, 1, 0)


def commander_body_drop(self):
    self.movetype    = movetype_t.MOVETYPE_TOSS
    self.s.origin[2] += 2


def SP_monster_commander_body(self):
    if gi.setmodel:
        gi.setmodel(self, "models/monsters/boss3/rider/tris.md2")
    self.solid      = solid_t.SOLID_BBOX
    self.movetype   = movetype_t.MOVETYPE_NONE
    self.mins       = [-32, -32, 0]
    self.maxs       = [32, 32, 48]
    self.use        = commander_body_use
    self.takedamage = 1
    self.health     = 400
    gi.linkentity(self)


def misc_banner_think(ent):
    ent.s.frame = (ent.s.frame + 1) % 16
    ent.nextthink = level.time + 0.1


def SP_misc_banner(ent):
    ent.movetype  = movetype_t.MOVETYPE_NONE
    ent.solid     = solid_t.SOLID_NOT
    if gi.setmodel:
        gi.setmodel(ent, "models/objects/banner/tris.md2")
    ent.think     = misc_banner_think
    ent.nextthink = level.time + 0.1
    gi.linkentity(ent)


def misc_deadsoldier_die(self, inflictor, attacker, damage, point):
    if self.health > -80:
        return
    if gi.soundindex and gi.sound:
        gi.sound(self, 0, gi.soundindex("misc/udeath.wav"), 1, 1, 0)
    for _ in range(4):
        ThrowGib(self, "models/objects/gibs/sm_meat/tris.md2", damage, GIB_ORGANIC)
    ThrowGib(self, "models/objects/gibs/head2/tris.md2", damage, GIB_ORGANIC)
    from .g_utils import G_FreeEdict
    G_FreeEdict(self)


def SP_misc_deadsoldier(ent):
    model = getattr(ent, 'model', None) or "models/deadbods/dude/tris.md2"
    if gi.modelindex:
        ent.s.modelindex = gi.modelindex(model)
    ent.solid      = solid_t.SOLID_BBOX
    ent.movetype   = movetype_t.MOVETYPE_NONE
    ent.mins       = [-16, -16, 0]
    ent.maxs       = [16, 16, 16]
    ent.die        = misc_deadsoldier_die
    ent.takedamage = 1
    ent.health     = -1
    gi.linkentity(ent)


def misc_viper_use(self, other, activator):
    self.svflags &= ~0x04
    self.use       = None
    self.think     = _viper_fly
    self.nextthink = level.time + 0.2


def _viper_fly(self):
    self.s.origin[2] += self.speed * 0.1 if self.speed else 30
    self.nextthink = level.time + 0.1


def SP_misc_viper(ent):
    if not ent.speed:
        ent.speed = 300
    ent.movetype  = movetype_t.MOVETYPE_NONE
    ent.solid     = solid_t.SOLID_NOT
    if gi.setmodel:
        gi.setmodel(ent, "models/ships/viper/tris.md2")
    ent.svflags  |= 0x04
    ent.use       = misc_viper_use
    gi.linkentity(ent)


def SP_misc_bigviper(ent):
    ent.movetype  = movetype_t.MOVETYPE_NONE
    ent.solid     = solid_t.SOLID_BBOX
    if gi.setmodel:
        gi.setmodel(ent, "models/ships/bigviper/tris.md2")
    ent.mins      = [-176, -120, -24]
    ent.maxs      = [176, 120, 24]
    gi.linkentity(ent)


def misc_viper_bomb_touch(self, other, plane, surf):
    from .g_combat import T_RadiusDamage
    T_RadiusDamage(self, self.activator, self.dmg, None, self.dmg + 40, 13)
    BecomeExplosion1(self)


def misc_viper_bomb_prethink(self):
    self.groundentity  = None
    self.velocity[2]  -= 60 * 0.1


def misc_viper_bomb_use(self, other, activator):
    self.activator = activator
    self.solid     = solid_t.SOLID_BBOX
    self.svflags  &= ~0x04
    self.movetype  = movetype_t.MOVETYPE_TOSS
    self.prethink  = misc_viper_bomb_prethink
    self.touch     = misc_viper_bomb_touch
    gi.linkentity(self)


def SP_misc_viper_bomb(self):
    self.movetype  = movetype_t.MOVETYPE_NONE
    self.solid     = solid_t.SOLID_NOT
    if gi.setmodel:
        gi.setmodel(self, "models/objects/bomb/tris.md2")
    if not self.dmg:
        self.dmg = 1000
    self.svflags |= 0x04
    self.use      = misc_viper_bomb_use
    gi.linkentity(self)


def misc_strogg_ship_use(self, other, activator):
    self.svflags &= ~0x04
    self.think     = _strogg_fly
    self.nextthink = level.time + 0.2


def _strogg_fly(self):
    self.s.origin[2] += 2
    self.nextthink = level.time + 0.2


def SP_misc_strogg_ship(ent):
    if not ent.speed:
        ent.speed = 1000
    ent.movetype  = movetype_t.MOVETYPE_NONE
    ent.solid     = solid_t.SOLID_NOT
    if gi.setmodel:
        gi.setmodel(ent, "models/ships/strogg1/tris.md2")
    ent.svflags  |= 0x04
    ent.use       = misc_strogg_ship_use
    gi.linkentity(ent)


def misc_satellite_dish_think(self, other=None, activator=None):
    self.s.frame += 1
    if self.s.frame < 38:
        self.nextthink = level.time + 0.1


def SP_misc_satellite_dish(ent):
    ent.movetype  = movetype_t.MOVETYPE_NONE
    ent.solid     = solid_t.SOLID_BBOX
    if gi.setmodel:
        gi.setmodel(ent, "models/objects/satellite/tris.md2")
    ent.mins      = [-64, -64, 0]
    ent.maxs      = [64, 64, 128]
    gi.linkentity(ent)


def SP_light_mine1(ent):
    ent.movetype  = movetype_t.MOVETYPE_NONE
    ent.solid     = solid_t.SOLID_BBOX
    if gi.setmodel:
        gi.setmodel(ent, "models/objects/lightmine1/tris.md2")
    gi.linkentity(ent)


def SP_light_mine2(ent):
    ent.movetype  = movetype_t.MOVETYPE_NONE
    ent.solid     = solid_t.SOLID_BBOX
    if gi.setmodel:
        gi.setmodel(ent, "models/objects/lightmine2/tris.md2")
    gi.linkentity(ent)


def SP_misc_gib_arm(ent):
    if gi.setmodel:
        gi.setmodel(ent, "models/objects/gibs/arm/tris.md2")
    ent.solid     = solid_t.SOLID_NOT
    ent.s.effects = 0x0080
    ent.movetype  = movetype_t.MOVETYPE_TOSS
    ent.svflags  |= 0x04
    ent.think     = _gib_free
    ent.nextthink = level.time + 30
    gi.linkentity(ent)


def SP_misc_gib_leg(ent):
    if gi.setmodel:
        gi.setmodel(ent, "models/objects/gibs/leg/tris.md2")
    ent.solid     = solid_t.SOLID_NOT
    ent.s.effects = 0x0080
    ent.movetype  = movetype_t.MOVETYPE_TOSS
    ent.svflags  |= 0x04
    ent.think     = _gib_free
    ent.nextthink = level.time + 30
    gi.linkentity(ent)


def SP_misc_gib_head(ent):
    if gi.setmodel:
        gi.setmodel(ent, "models/objects/gibs/head/tris.md2")
    ent.solid     = solid_t.SOLID_NOT
    ent.s.effects = 0x0080
    ent.movetype  = movetype_t.MOVETYPE_TOSS
    ent.svflags  |= 0x04
    ent.think     = _gib_free
    ent.nextthink = level.time + 30
    gi.linkentity(ent)


def SP_target_character(self):
    self.movetype = movetype_t.MOVETYPE_PUSH
    if gi.setmodel:
        gi.setmodel(self, self.model)
    self.solid    = solid_t.SOLID_BSP
    self.s.frame  = 12
    gi.linkentity(self)


def target_string_use(self, other, activator):
    from .g_utils import G_Find
    msg = getattr(self, 'message', '') or ''
    n   = len(msg)
    ec  = G_Find(None, 'targetname', self.targetname)
    i   = 0
    while ec:
        if ec.classname == 'target_character':
            if i < n:
                ch = ord(msg[i]) - 32
                if ch < 0:
                    ch = 0
                ec.s.frame = ch
            else:
                ec.s.frame = 0
            gi.linkentity(ec)
            i += 1
        ec = G_Find(ec, 'targetname', self.targetname)


def SP_target_string(self):
    if not getattr(self, 'message', None):
        self.message = ""
    self.use = target_string_use


def func_clock_reset(self):
    self.activator = None
    if not (self.spawnflags & 1):
        self.nextthink = level.time + 1


def func_clock_format_countdown(self):
    secs  = int(self.health)
    mins  = secs // 60
    secs %= 60
    return "%d:%02d" % (mins, secs)


def func_clock_think(self):
    if not self.activator:
        self.nextthink = level.time + 1
        return
    self.health -= 1
    if self.health <= 0:
        from .g_utils import G_UseTargets
        G_UseTargets(self, self.activator)
        func_clock_reset(self)
        return
    msg = func_clock_format_countdown(self)
    if gi.centerprintf:
        gi.centerprintf(self.activator, "%s\n" % msg)
    self.nextthink = level.time + 1


def func_clock_use(self, other, activator):
    self.activator = activator
    if not self.health:
        self.health = int(self.speed) if self.speed else 60
    self.think     = func_clock_think
    self.nextthink = level.time + 1


def SP_func_clock(self):
    self.use     = func_clock_use
    self.svflags = 0x04
    if not self.speed:
        self.speed = 60.0


def teleporter_touch(self, other, plane, surf):
    if not other.client:
        return
    from .g_utils import G_Find
    dest = G_Find(None, 'classname', 'misc_teleporter_dest')
    if not dest:
        if gi.dprintf:
            gi.dprintf("teleporter_touch: no destination\n")
        return
    other.s.origin[:] = list(dest.s.origin)
    other.s.angles[:] = list(dest.s.angles)
    if other.client:
        other.client.ps.pmove.origin[:] = [int(x * 8) for x in dest.s.origin]
        other.client.ps.viewangles[:] = list(dest.s.angles)
        other.velocity[:] = [0.0, 0.0, 0.0]
    gi.linkentity(other)


def SP_misc_teleporter(ent):
    if not getattr(ent, 'target', None):
        if gi.dprintf:
            gi.dprintf("teleporter at %s has no target\n" % str(ent.s.origin))
        return
    if gi.setmodel:
        gi.setmodel(ent, "models/objects/dmspot/tris.md2")
    ent.solid    = solid_t.SOLID_BBOX
    ent.movetype = movetype_t.MOVETYPE_NONE
    ent.mins     = [-32, -32, -24]
    ent.maxs     = [32, 32, -16]
    ent.touch    = teleporter_touch
    gi.linkentity(ent)


def SP_misc_teleporter_dest(ent):
    if gi.setmodel:
        gi.setmodel(ent, "models/objects/dmspot/tris.md2")
    ent.solid    = solid_t.SOLID_BBOX
    ent.movetype = movetype_t.MOVETYPE_NONE
    ent.mins     = [-32, -32, -24]
    ent.maxs     = [32, 32, -16]
    gi.linkentity(ent)


@TODO
def SP_func_areaportal(ent):
    pass


@TODO
def VelocityForDamage(damage, v):
    pass


@TODO
def ClipGibVelocity(ent):
    pass


@TODO
def gib_think(_self):
    pass


@TODO
def gib_touch(_self, other, plane, surf):
    pass


@TODO
def gib_die(_self, inflictor, attacker, damage, point):
    pass


@TODO
def ThrowGib(_self, gibname, damage, _type):
    pass


@TODO
def ThrowHead(_self, gibname, damage, _type):
    pass


@TODO
def ThrowClientHead(_self, damage):
    pass


@TODO
def debris_die(_self, inflictor, attacker, damage, point):
    pass


@TODO
def ThrowDebris(_self, modelname, speed, origin):
    pass


@TODO
def BecomeExplosion1(_self):
    pass


@TODO
def BecomeExplosion2(_self):
    pass


@TODO
def path_corner_touch(_self, other, plane, surf):
    pass


@TODO
def SP_path_corner(_self):
    pass


@TODO
def point_combat_touch(_self, other, plane, surf):
    pass


@TODO
def SP_point_combat(_self):
    pass


@TODO
def TH_viewthing(ent):
    pass


@TODO
def SP_viewthing(ent):
    pass


@TODO
def SP_info_null(_self):
    pass


@TODO
def SP_info_notnull(_self):
    pass


@TODO
def light_use(_self, other, activator):
    pass


@TODO
def SP_light(_self):
    pass


@TODO
def func_wall_use(_self, other, activator):
    pass


@TODO
def SP_func_wall(_self):
    pass


@TODO
def func_object_touch(_self, other, plane, surf):
    pass


@TODO
def func_object_release(_self):
    pass


@TODO
def func_object_use(_self, other, activator):
    pass


@TODO
def SP_func_object(_self):
    pass


@TODO
def func_explosive_explode(_self, inflictor, attacker, damage, point):
    pass


@TODO
def func_explosive_use(_self, other, activator):
    pass


@TODO
def func_explosive_spawn(_self, other, activator):
    pass


@TODO
def SP_func_explosive(_self):
    pass


@TODO
def barrel_touch(_self, other, plane, surf):
    pass


@TODO
def barrel_explode(_self):
    pass


@TODO
def barrel_delay(_self, inflictor, attacker, damage, point):
    pass


@TODO
def SP_misc_explobox(_self):
    pass


@TODO
def misc_blackhole_use(ent, other, activator):
    pass


@TODO
def misc_blackhole_think(_self):
    pass


@TODO
def SP_misc_blackhole(ent):
    pass


@TODO
def misc_eastertank_think(_self):
    pass


@TODO
def SP_misc_eastertank(ent):
    pass


@TODO
def misc_easterchick_think(_self):
    pass


@TODO
def SP_misc_easterchick(ent):
    pass


@TODO
def misc_easterchick2_think(_self):
    pass


@TODO
def SP_misc_easterchick2(ent):
    pass


@TODO
def commander_body_think(_self):
    pass


@TODO
def commander_body_use(_self, other, activator):
    pass


@TODO
def commander_body_drop(_self):
    pass


@TODO
def SP_monster_commander_body(_self):
    pass


@TODO
def misc_banner_think(ent):
    pass


@TODO
def SP_misc_banner(ent):
    pass


@TODO
def misc_deadsoldier_die(_self, inflictor, attacker, damage, point):
    pass


@TODO
def SP_misc_deadsoldier(ent):
    pass


@TODO
def misc_viper_use(_self, other, activator):
    pass


@TODO
def SP_misc_viper(ent):
    pass


@TODO
def SP_misc_bigviper(ent):
    pass


@TODO
def misc_viper_bomb_touch(_self, other, plane, surf):
    pass


@TODO
def misc_viper_bomb_prethink(_self):
    pass


@TODO
def misc_viper_bomb_use(_self, other, activator):
    pass


@TODO
def SP_misc_viper_bomb(_self):
    pass


@TODO
def misc_strogg_ship_use(_self, other, activator):
    pass


@TODO
def SP_misc_strogg_ship(ent):
    pass


@TODO
def misc_satellite_dish_think(_self, other, activator):
    pass


@TODO
def SP_misc_satellite_dish(ent):
    pass


@TODO
def SP_light_mine1(ent):
    pass


@TODO
def SP_light_mine2(ent):
    pass


@TODO
def SP_misc_gib_arm(ent):
    pass


@TODO
def SP_misc_gib_leg(ent):
    pass


@TODO
def SP_misc_gib_head(ent):
    pass


@TODO
def SP_target_character(_self):
    pass


@TODO
def target_string_use(_self, other, activator):
    pass


@TODO
def SP_target_string(_self):
    pass


@TODO
def func_clock_reset(_self):
    pass


@TODO
def func_clock_format_countdown(_self):
    pass


@TODO
def func_clock_think(_self):
    pass


@TODO
def func_clock_use(_self, other, activator):
    pass


@TODO
def SP_func_clock(_self):
    pass


@TODO
def teleporter_touch(_self, other, plane, surf):
    pass


@TODO
def SP_misc_teleporter(ent):
    pass


@TODO
def SP_misc_teleporter_dest(ent):
    pass
