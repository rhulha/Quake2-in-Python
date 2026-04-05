import math

from .reference_import import gi
from .global_vars import level
from shared.QEnums import movetype_t, solid_t


def InitTrigger(self):
    """Set up a trigger entity — set mins/maxs from model, make trigger-solid."""
    if self.s.angles[0] or self.s.angles[1] or self.s.angles[2]:
        from .g_utils import G_SetMovedir
        G_SetMovedir(self.s.angles, self.movedir)

    self.solid    = solid_t.SOLID_TRIGGER
    self.movetype = movetype_t.MOVETYPE_NONE
    if self.model and gi.setmodel:
        gi.setmodel(self, self.model)
    self.svflags   = 0x04  # SVF_NOCLIENT
    gi.linkentity(self)


def multi_wait(self):
    """Clear the wait timer so trigger can fire again."""
    self.nextthink  = 0
    self.think      = None


def multi_trigger(self, activator):
    """Fire the trigger's targets."""
    if self.nextthink:
        return  # waiting
    from .g_utils import G_UseTargets
    G_UseTargets(self, activator)

    if self.wait > 0:
        self.activator = activator
        self.think     = multi_wait
        self.nextthink = level.time + self.wait
    else:
        self.touch  = None
        self.nextthink = level.time + 0.1
        self.think  = lambda e: _FreeEdict(e)


def _FreeEdict(e):
    from .g_utils import G_FreeEdict
    G_FreeEdict(e)


def Use_Multi(self, other, activator):
    multi_trigger(self, activator)


def Touch_Multi(self, other, plane, surf):
    if other.client:
        if self.spawnflags & 2:  # TRIGGER_MONSTER — not players
            return
    else:
        if not (self.spawnflags & 1):  # TRIGGER_MONSTER
            if not (other.svflags & 0x01):
                return

    if self.movedir[0] or self.movedir[1] or self.movedir[2]:
        from .q_shared import AngleVectors
        forward = [0.0, 0.0, 0.0]
        AngleVectors(other.s.angles, forward, None, None)
        dot = forward[0]*self.movedir[0] + forward[1]*self.movedir[1] + forward[2]*self.movedir[2]
        if dot < 0:
            return

    self.activator = other
    multi_trigger(self, other)


def trigger_enable(self, other, activator):
    self.solid = solid_t.SOLID_TRIGGER
    self.use   = Use_Multi
    gi.linkentity(self)


def SP_trigger_multiple(self):
    if self.sounds == 1:
        if gi.soundindex:
            self.noise_index = gi.soundindex("misc/secret.wav")
    elif self.sounds == 2:
        if gi.soundindex:
            self.noise_index = gi.soundindex("misc/talk.wav")
    elif self.sounds == 3:
        if gi.soundindex:
            self.noise_index = gi.soundindex("misc/trigger1.wav")

    if not self.wait:
        self.wait = 0.2

    self.touch = Touch_Multi
    self.moveable = True

    if self.spawnflags & 4:  # TRIGGER_LATCHED
        self.use = trigger_enable
    else:
        self.use = Use_Multi

    InitTrigger(self)


def SP_trigger_once(self):
    self.wait = -1
    SP_trigger_multiple(self)


def trigger_relay_use(self, other, activator):
    from .g_utils import G_UseTargets
    G_UseTargets(self, activator)


def SP_trigger_relay(self):
    self.use = trigger_relay_use


def trigger_key_use(self, other, activator):
    if not activator or not activator.client:
        return
    if not self.item:
        return
    index = self.item.index
    if not activator.client.pers.inventory[index]:
        if gi.centerprintf:
            gi.centerprintf(activator, "You need the %s\n" % self.item.pickup_name)
        if gi.sound and gi.soundindex:
            gi.sound(activator, 0, gi.soundindex("misc/keytry.wav"), 1, 1, 0)
        return
    if gi.sound and gi.soundindex:
        gi.sound(activator, 0, gi.soundindex("misc/keyuse.wav"), 1, 1, 0)
    activator.client.pers.inventory[index] -= 1
    from .g_utils import G_UseTargets
    G_UseTargets(self, activator)
    self.use = None


def SP_trigger_key(self):
    if not self.item:
        if gi.dprintf:
            gi.dprintf("no key set for trigger_key at %s\n" %
                       str(self.s.origin))
        return
    self.use = trigger_key_use
    if gi.soundindex:
        gi.soundindex("misc/keytry.wav")
        gi.soundindex("misc/keyuse.wav")


def trigger_counter_use(self, other, activator):
    if not self.count:
        return
    self.count -= 1
    if self.count:
        if not (self.spawnflags & 1):  # NO_MESSAGE
            if gi.centerprintf:
                gi.centerprintf(activator, "%d more to go...\n" % self.count)
            if gi.sound and gi.soundindex:
                gi.sound(activator, 0, gi.soundindex("misc/talk1.wav"), 1, 1, 0)
        return
    if not (self.spawnflags & 1):
        if gi.centerprintf:
            gi.centerprintf(activator, "Sequence completed!\n")
        if gi.sound and gi.soundindex:
            gi.sound(activator, 0, gi.soundindex("misc/secret.wav"), 1, 1, 0)
    self.activator = activator
    from .g_utils import G_UseTargets
    G_UseTargets(self, activator)


def SP_trigger_counter(self):
    self.wait = -1
    if not self.count:
        self.count = 2
    self.use = trigger_counter_use


def SP_trigger_always(self):
    if self.delay < 0.2:
        self.delay = 0.2
    from .g_utils import G_UseTargets
    G_UseTargets(self, self)


def trigger_push_touch(self, other, plane, surf):
    if other.health <= 0:
        return
    other.velocity[0] = self.movedir[0] * self.speed * 10
    other.velocity[1] = self.movedir[1] * self.speed * 10
    other.velocity[2] = self.movedir[2] * self.speed * 10
    if other.client:
        other.client.oldvelocity[:] = list(other.velocity)


def SP_trigger_push(self):
    InitTrigger(self)
    if gi.soundindex:
        gi.soundindex("misc/windfly.wav")
    self.touch = trigger_push_touch
    if not self.speed:
        self.speed = 1000
    gi.linkentity(self)


def hurt_use(self, other, activator):
    if self.solid == solid_t.SOLID_NOT:
        self.solid = solid_t.SOLID_TRIGGER
        if not (self.spawnflags & 2):  # HURT_ONCE
            self.use = None
    else:
        self.solid = solid_t.SOLID_NOT
        self.use = hurt_use
    gi.linkentity(self)


def hurt_touch(self, other, plane, surf):
    if other.health <= 0:
        return
    if level.time < self.touch_debounce_time:
        return
    self.touch_debounce_time = level.time + 1
    from .g_combat import T_Damage
    T_Damage(other, self, self, [0,0,0], other.s.origin, [0,0,0],
             self.dmg, self.dmg, 0, 31)  # MOD_TRIGGER_HURT


def SP_trigger_hurt(self):
    InitTrigger(self)
    if gi.soundindex:
        self.noise_index = gi.soundindex("world/electro.wav")
    self.touch = hurt_touch
    if not self.dmg:
        self.dmg = 5
    if self.spawnflags & 1:  # HURT_START_OFF
        self.solid = solid_t.SOLID_NOT
        self.use = hurt_use
    else:
        self.solid = solid_t.SOLID_TRIGGER
        self.use = hurt_use


def trigger_gravity_touch(self, other, plane, surf):
    other.gravity = self.gravity


def SP_trigger_gravity(self):
    if not self.gravity:
        if gi.dprintf:
            gi.dprintf("trigger_gravity without gravity set at %s\n" % str(self.s.origin))
        from .g_utils import G_FreeEdict
        G_FreeEdict(self)
        return
    InitTrigger(self)
    self.touch = trigger_gravity_touch


def trigger_monsterjump_touch(self, other, plane, surf):
    if not (other.svflags & 0x01):  # SVF_MONSTER
        return
    if other.health <= 0:
        return
    other.velocity[0] += self.movedir[0] * self.speed
    other.velocity[1] += self.movedir[1] * self.speed
    other.velocity[2]  = self.movedir[2] * self.height if hasattr(self, 'height') else 200


def SP_trigger_monsterjump(self):
    if not self.speed:
        self.speed = 200
    if not hasattr(self, 'height') or not self.height:
        self.height = 200
    if self.s.angles[1] == 0:
        self.s.angles[1] = 360
    InitTrigger(self)
    self.touch = trigger_monsterjump_touch
