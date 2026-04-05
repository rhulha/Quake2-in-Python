import math

from .reference_import import gi
from .global_vars import level
from shared.QEnums import movetype_t, solid_t


def Use_Target_Tent(self, other, activator):
    if gi.WriteByte and gi.multicast:
        gi.WriteByte(5)  # svc_temp_entity
        gi.WriteByte(self.style)
        gi.WritePosition(self.s.origin)
        gi.multicast(self.s.origin, 1)


def SP_target_temp_entity(self):
    self.use = Use_Target_Tent


def Use_Target_Speaker(self, other, activator):
    if not self.volume:
        self.volume = 1.0
    if not self.attenuation:
        self.attenuation = 1.0
    if gi.sound:
        gi.sound(self, 1, self.noise_index, self.volume, self.attenuation, 0)


def SP_target_speaker(self):
    if not getattr(self, 'noise', None):
        if gi.dprintf:
            gi.dprintf("target_speaker with no noise set at %s\n" % str(self.s.origin))
        return
    if not self.volume:
        self.volume = 1.0
    if not self.attenuation:
        self.attenuation = 1.0
    elif self.attenuation == -1:
        self.attenuation = 0
    if gi.soundindex:
        self.noise_index = gi.soundindex(self.noise)
    if not self.targetname or (self.spawnflags & 1):
        if gi.sound:
            gi.sound(self, 1, self.noise_index, self.volume, self.attenuation, 0)
    self.use = Use_Target_Speaker


def Use_Target_Help(self, other, activator):
    from .global_vars import game as _gv
    if hasattr(_gv, 'helpchanged'):
        _gv.helpchanged = 1


def SP_target_help(self):
    self.use = Use_Target_Help


def use_target_secret(self, other, activator):
    if gi.sound and gi.soundindex:
        gi.sound(self, 1, gi.soundindex("misc/secret.wav"), 1, 1, 0)
    level.found_secrets += 1
    from .g_utils import G_UseTargets, G_FreeEdict
    G_UseTargets(self, activator)
    G_FreeEdict(self)


def SP_target_secret(self):
    if gi.soundindex:
        gi.soundindex("misc/secret.wav")
    level.total_secrets += 1
    self.svflags = 0x04
    self.use = use_target_secret


def use_target_goal(self, other, activator):
    if gi.sound and gi.soundindex:
        gi.sound(self, 1, gi.soundindex("misc/secret.wav"), 1, 1, 0)
    level.found_goals += 1
    from .g_utils import G_UseTargets, G_FreeEdict
    G_UseTargets(self, activator)
    G_FreeEdict(self)


def SP_target_goal(self):
    if gi.soundindex:
        gi.soundindex("misc/secret.wav")
    level.total_goals += 1
    self.svflags = 0x04
    self.use = use_target_goal


def target_explosion_explode(self):
    from .g_combat import T_RadiusDamage
    T_RadiusDamage(self, self.activator, self.dmg, None, self.dmg + 40, 13)
    if gi.WriteByte and gi.multicast:
        gi.WriteByte(5)
        gi.WriteByte(3)  # TE_EXPLOSION1
        gi.WritePosition(self.s.origin)
        gi.multicast(self.s.origin, 1)
    if self.delay:
        self.think     = _explosion_use_targets
        self.nextthink = level.time + self.delay
    else:
        from .g_utils import G_UseTargets, G_FreeEdict
        G_UseTargets(self, self.activator)
        G_FreeEdict(self)


def _explosion_use_targets(self):
    from .g_utils import G_UseTargets, G_FreeEdict
    G_UseTargets(self, self.activator)
    G_FreeEdict(self)


def use_target_explosion(self, other, activator):
    self.activator = activator
    if not self.delay:
        target_explosion_explode(self)
        return
    self.think     = target_explosion_explode
    self.nextthink = level.time + self.delay


def SP_target_explosion(self):
    self.use     = use_target_explosion
    self.svflags = 0x04


def use_target_changelevel(self, other, activator):
    if level.intermissiontime:
        return
    if gi.AddCommandString:
        gi.AddCommandString("gamemap \"%s\"\n" % self.map)
    level.intermissiontime = level.time


def SP_target_changelevel(self):
    if not getattr(self, 'map', None):
        if gi.dprintf:
            gi.dprintf("target_changelevel with no map at %s\n" % str(self.s.origin))
        return
    self.svflags = 0x04
    self.use     = use_target_changelevel


def use_target_splash(self, other, activator):
    if gi.WriteByte and gi.multicast:
        gi.WriteByte(5)
        gi.WriteByte(20)  # TE_SPLASH
        gi.WriteByte(self.count or 32)
        gi.WritePosition(self.s.origin)
        gi.WriteDir([0, 0, 1])
        gi.WriteByte(self.sounds or 0)
        gi.multicast(self.s.origin, 1)


def SP_target_splash(self):
    self.use     = use_target_splash
    if not self.count:
        self.count = 32
    self.svflags = 0x04


def use_target_spawner(self, other, activator):
    from .g_utils import G_Spawn, KillBox
    from .g_spawn import ED_CallSpawn
    ent = G_Spawn()
    ent.classname = self.target
    ent.s.origin[:] = list(self.s.origin)
    ent.s.angles[:] = list(self.s.angles)
    ED_CallSpawn(ent)
    gi.unlinkentity(ent)
    KillBox(ent)
    gi.linkentity(ent)
    if self.speed:
        for i in range(3):
            ent.velocity[i] = self.movedir[i] * self.speed


def SP_target_spawner(self):
    self.use     = use_target_spawner
    self.svflags = 0x04
    if self.speed:
        from .g_utils import G_SetMovedir
        G_SetMovedir(self.s.angles, self.movedir)


def use_target_blaster(self, other, activator):
    from .g_weapon import fire_blaster
    effect = 8 if not (self.spawnflags & 2) else 0
    fire_blaster(self, self.s.origin, self.movedir,
                 self.dmg or 15, self.speed or 1000, effect, bool(effect))


def SP_target_blaster(self):
    self.use     = use_target_blaster
    self.svflags = 0x04
    from .g_utils import G_SetMovedir
    G_SetMovedir(self.s.angles, self.movedir)
    if not self.dmg:
        self.dmg = 15
    if not self.speed:
        self.speed = 1000
    if gi.soundindex:
        gi.soundindex("weapons/laser2.wav")


def trigger_crosslevel_trigger_use(self, other, activator):
    from .g_main import game
    if hasattr(game, 'serverflags'):
        game.serverflags |= self.spawnflags


def SP_target_crosslevel_trigger(self):
    self.svflags = 0x04
    self.use     = trigger_crosslevel_trigger_use


def target_crosslevel_target_think(self):
    from .g_main import game
    serverflags = getattr(game, 'serverflags', 0)
    if self.spawnflags and (self.spawnflags == (serverflags & self.spawnflags)):
        from .g_utils import G_UseTargets, G_FreeEdict
        G_UseTargets(self, self)
        G_FreeEdict(self)
    else:
        self.nextthink = level.time + 1


def SP_target_crosslevel_target(self):
    if not self.delay:
        self.delay = 1
    self.svflags   = 0x04
    self.think     = target_crosslevel_target_think
    self.nextthink = level.time + self.delay


def target_laser_think(self):
    start = list(self.s.origin)
    end   = [start[i] + self.movedir[i] * 2048 for i in range(3)]
    if gi.trace:
        tr = gi.trace(start, None, None, end, self, 0x00000001)
        if tr and tr.ent and tr.ent.takedamage:
            from .g_combat import T_Damage
            normal = tr.plane.normal if tr.plane else [0, 0, 1]
            T_Damage(tr.ent, self, self.activator or self, self.movedir, tr.endpos,
                     normal, self.dmg, 1, 0, 10)
    self.nextthink = level.time + 0.1


def target_laser_on(self):
    if not self.activator:
        self.activator = self
    self.spawnflags |= 0x01
    self.svflags    &= ~0x04
    self.think       = target_laser_think
    self.nextthink   = level.time


def target_laser_off(self):
    self.spawnflags &= ~0x01
    self.svflags    |= 0x04
    self.think       = None
    self.nextthink   = 0


def target_laser_use(self, other, activator):
    self.activator = activator
    if self.spawnflags & 0x01:
        target_laser_off(self)
    else:
        target_laser_on(self)


def target_laser_start(self):
    self.movetype   = movetype_t.MOVETYPE_NONE
    self.solid      = solid_t.SOLID_NOT
    from .g_utils import G_SetMovedir
    G_SetMovedir(self.s.angles, self.movedir)
    if not self.dmg:
        self.dmg = 1
    self.use = target_laser_use
    if self.spawnflags & 0x01:
        target_laser_on(self)
    else:
        target_laser_off(self)


def SP_target_laser(self):
    self.think     = target_laser_start
    self.nextthink = level.time + 1


def target_lightramp_think(self):
    elapsed = level.time - self.timestamp
    total   = max(0.001, self.speed)
    frac    = max(0.0, min(1.0, elapsed / total))
    val     = int(self.movedir[0] + frac * (self.movedir[1] - self.movedir[0]))
    if gi.configstring:
        gi.configstring(32 + self.style, chr(val + ord('a')))
    if elapsed < total:
        self.nextthink = level.time + 0.1
    else:
        self.think     = None
        self.nextthink = 0


def target_lightramp_use(self, other, activator):
    self.activator = activator
    self.timestamp = level.time
    self.think     = target_lightramp_think
    self.nextthink = level.time


def SP_target_lightramp(self):
    msg = getattr(self, 'message', None) or ''
    if len(msg) != 2:
        if gi.dprintf:
            gi.dprintf("target_lightramp needs 2 chars in message\n")
        return
    if not self.speed:
        self.speed = 1.0
    self.movedir = [ord(msg[0]) - ord('a'), ord(msg[1]) - ord('a'), 0.0]
    self.svflags = 0x04
    self.use     = target_lightramp_use


def target_earthquake_think(self):
    from .g_main import game
    for i in range(1, game.maxclients + 1):
        cl = game.entities[i]
        if not cl.inuse or not cl.client:
            continue
        if cl.groundentity:
            cl.velocity[2] += 100 * (0.5 - __import__('random').random())
    if level.time < self.timestamp + self.speed:
        self.nextthink = level.time + 0.1
    else:
        self.think     = None
        self.nextthink = 0


def target_earthquake_use(self, other, activator):
    self.activator = activator
    self.timestamp = level.time
    self.think     = target_earthquake_think
    self.nextthink = level.time + 0.1
    if gi.sound and gi.soundindex:
        gi.sound(self, 1, gi.soundindex("world/quake.wav"), 1, 1, 0)


def SP_target_earthquake(self):
    if not self.speed:
        self.speed = 10.0
    if not self.count:
        self.count = 80
    self.svflags = 0x04
    self.use     = target_earthquake_use
    if gi.soundindex:
        gi.soundindex("world/quake.wav")
