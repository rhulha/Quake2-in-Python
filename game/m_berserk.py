import random as _random

from .reference_import import gi
from .global_vars import level
from shared.QClasses import mmove_t, mframe_t
from shared.QEnums import movetype_t, solid_t, damage_t, MONSTER_AI_FLAGS

# ── frame constants ───────────────────────────────────────────────────────────
FRAME_stand1   = 0
FRAME_stand5   = 4
FRAME_standb1  = 5
FRAME_standb20 = 24
FRAME_walkc1   = 25
FRAME_walkc11  = 35
FRAME_run1     = 36
FRAME_run6     = 41
FRAME_att_c1   = 76
FRAME_att_c8   = 83
FRAME_att_c9   = 84
FRAME_att_c20  = 95
FRAME_att_c21  = 96
FRAME_att_c34  = 109
FRAME_painc1   = 199
FRAME_painc4   = 202
FRAME_painb1   = 203
FRAME_painb20  = 222
FRAME_death1   = 223
FRAME_death13  = 235
FRAME_deathc1  = 236
FRAME_deathc8  = 243

MODEL_SCALE = 1.0

DEAD_DEAD       = 2
DAMAGE_YES      = damage_t.DAMAGE_YES.value
SVF_DEADMONSTER = 0x00000010
GIB_ORGANIC     = 0
AI_STAND_GROUND = MONSTER_AI_FLAGS.AI_STAND_GROUND.value

_sound_pain   = 0
_sound_die    = 0
_sound_idle   = 0
_sound_punch  = 0
_sound_sight  = 0
_sound_search = 0


def _chan_voice():
    from shared.QEnums import SOUND_CHANNELS
    return SOUND_CHANNELS.CHAN_VOICE.value

def _chan_weapon():
    from shared.QEnums import SOUND_CHANNELS
    return SOUND_CHANNELS.CHAN_WEAPON.value

def _attn_norm():
    from shared.QEnums import SOUND_ATTN_VALUES
    return SOUND_ATTN_VALUES.ATTN_NORM.value

def _attn_idle():
    from shared.QEnums import SOUND_ATTN_VALUES
    return SOUND_ATTN_VALUES.ATTN_IDLE.value


def berserk_sight(self, other):
    if gi.sound:
        gi.sound(self, _chan_voice(), _sound_sight, 1, _attn_norm(), 0)


def berserk_search(self):
    if gi.sound:
        gi.sound(self, _chan_voice(), _sound_search, 1, _attn_norm(), 0)


def berserk_fidget(self):
    if self.monsterinfo.aiflags & AI_STAND_GROUND:
        return
    if _random.random() > 0.15:
        return
    self.monsterinfo.currentmove = berserk_move_stand_fidget
    if gi.sound:
        gi.sound(self, _chan_weapon(), _sound_idle, 1, _attn_idle(), 0)


def berserk_stand(self):
    self.monsterinfo.currentmove = berserk_move_stand


def berserk_walk(self):
    self.monsterinfo.currentmove = berserk_move_walk


def berserk_run(self):
    if self.monsterinfo.aiflags & AI_STAND_GROUND:
        self.monsterinfo.currentmove = berserk_move_stand
    else:
        self.monsterinfo.currentmove = berserk_move_run1


def berserk_swing(self):
    if gi.sound:
        gi.sound(self, _chan_weapon(), _sound_punch, 1, _attn_norm(), 0)


def berserk_attack_spike(self):
    from .g_weapon import fire_hit
    from .g_ai import MELEE_DISTANCE
    aim = [MELEE_DISTANCE, 0, -24]
    fire_hit(self, aim, 15 + _random.randint(0, 5), 400)


def berserk_attack_club(self):
    from .g_weapon import fire_hit
    from .g_ai import MELEE_DISTANCE
    aim = [MELEE_DISTANCE, self.mins[0], -4]
    fire_hit(self, aim, 5 + _random.randint(0, 5), 400)


def berserk_strike(self):
    pass


def berserk_melee(self):
    if _random.randint(0, 1) == 0:
        self.monsterinfo.currentmove = berserk_move_attack_spike
    else:
        self.monsterinfo.currentmove = berserk_move_attack_club


def berserk_pain(self, other, kick, damage):
    if self.health < (self.max_health // 2):
        self.s.skinnum = 1
    if level.time < self.pain_debounce_time:
        return
    self.pain_debounce_time = level.time + 3
    if gi.sound:
        gi.sound(self, _chan_voice(), _sound_pain, 1, _attn_norm(), 0)
    if damage < 20 or _random.random() < 0.5:
        self.monsterinfo.currentmove = berserk_move_pain1
    else:
        self.monsterinfo.currentmove = berserk_move_pain2


def berserk_dead(self):
    self.mins[0] = -16; self.mins[1] = -16; self.mins[2] = -24
    self.maxs[0] =  16; self.maxs[1] =  16; self.maxs[2] =  -8
    self.movetype = movetype_t.MOVETYPE_TOSS.value
    self.svflags |= SVF_DEADMONSTER
    if gi.linkentity:
        gi.linkentity(self)
    from .g_monster import M_FlyCheck
    M_FlyCheck(self)


def berserk_die(self, inflictor, attacker, damage, point):
    from .g_misc import ThrowGib, ThrowHead
    if self.health <= self.gib_health:
        if gi.sound and gi.soundindex:
            gi.sound(self, _chan_voice(), gi.soundindex("misc/udeath.wav"), 1, _attn_norm(), 0)
        for _ in range(2):
            ThrowGib(self, "models/objects/gibs/bone/tris.md2", damage, GIB_ORGANIC)
        for _ in range(4):
            ThrowGib(self, "models/objects/gibs/sm_meat/tris.md2", damage, GIB_ORGANIC)
        ThrowHead(self, "models/objects/gibs/head2/tris.md2", damage, GIB_ORGANIC)
        self.deadflag = DEAD_DEAD
        return
    if self.deadflag == DEAD_DEAD:
        return
    if gi.sound:
        gi.sound(self, _chan_voice(), _sound_die, 1, _attn_norm(), 0)
    self.deadflag = DEAD_DEAD
    self.takedamage = DAMAGE_YES
    if damage >= 50:
        self.monsterinfo.currentmove = berserk_move_death1
    else:
        self.monsterinfo.currentmove = berserk_move_death2


# ── AI helpers (deferred imports to avoid circular refs) ─────────────────────
def _ai_stand():
    from .g_ai import ai_stand
    return ai_stand

def _ai_walk():
    from .g_ai import ai_walk
    return ai_walk

def _ai_run():
    from .g_ai import ai_run
    return ai_run

def _ai_charge():
    from .g_ai import ai_charge
    return ai_charge

def _ai_move():
    from .g_ai import ai_move
    return ai_move


# ── move tables ───────────────────────────────────────────────────────────────
berserk_frames_stand = [
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, berserk_fidget),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
]
berserk_move_stand = mmove_t(FRAME_stand1, FRAME_stand5, berserk_frames_stand, None)

berserk_frames_stand_fidget = [
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None)
    for _ in range(20)
]
berserk_move_stand_fidget = mmove_t(FRAME_standb1, FRAME_standb20, berserk_frames_stand_fidget, berserk_stand)

berserk_frames_walk = [
    mframe_t(lambda s, d: _ai_walk()(s, d), dist, None)
    for dist in [9.1, 6.3, 4.9, 6.7, 6.0, 8.2, 7.2, 6.1, 4.9, 4.7, 4.7]
]
berserk_move_walk = mmove_t(FRAME_walkc1, FRAME_walkc11, berserk_frames_walk, None)

berserk_frames_run1 = [
    mframe_t(lambda s, d: _ai_run()(s, d), dist, None)
    for dist in [21, 11, 21, 25, 18, 19]
]
berserk_move_run1 = mmove_t(FRAME_run1, FRAME_run6, berserk_frames_run1, None)

berserk_frames_attack_spike = [
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, berserk_swing),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, berserk_attack_spike),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None),
]
berserk_move_attack_spike = mmove_t(FRAME_att_c1, FRAME_att_c8, berserk_frames_attack_spike, berserk_run)

berserk_frames_attack_club = [
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, berserk_swing),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, berserk_attack_club),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None),
]
berserk_move_attack_club = mmove_t(FRAME_att_c9, FRAME_att_c20, berserk_frames_attack_club, berserk_run)

_strike_data = [
    (0, None), (0, None), (0, None), (0, berserk_swing),
    (0, None), (0, None), (0, None), (0, berserk_strike),
    (0, None), (0, None), (0, None), (0, None),
    (9.7, None), (13.6, None),
]
berserk_frames_attack_strike = [
    mframe_t(lambda s, d: _ai_move()(s, d), dist, fn)
    for dist, fn in _strike_data
]
berserk_move_attack_strike = mmove_t(FRAME_att_c21, FRAME_att_c34, berserk_frames_attack_strike, berserk_run)

berserk_frames_pain1 = [
    mframe_t(lambda s, d: _ai_move()(s, d), 0, None)
    for _ in range(4)
]
berserk_move_pain1 = mmove_t(FRAME_painc1, FRAME_painc4, berserk_frames_pain1, berserk_run)

berserk_frames_pain2 = [
    mframe_t(lambda s, d: _ai_move()(s, d), 0, None)
    for _ in range(20)
]
berserk_move_pain2 = mmove_t(FRAME_painb1, FRAME_painb20, berserk_frames_pain2, berserk_run)

berserk_frames_death1 = [
    mframe_t(lambda s, d: _ai_move()(s, d), 0, None)
    for _ in range(13)
]
berserk_move_death1 = mmove_t(FRAME_death1, FRAME_death13, berserk_frames_death1, berserk_dead)

berserk_frames_death2 = [
    mframe_t(lambda s, d: _ai_move()(s, d), 0, None)
    for _ in range(8)
]
berserk_move_death2 = mmove_t(FRAME_deathc1, FRAME_deathc8, berserk_frames_death2, berserk_dead)


# ── spawn ─────────────────────────────────────────────────────────────────────
def SP_monster_berserk(self):
    global _sound_pain, _sound_die, _sound_idle, _sound_punch, _sound_sight, _sound_search
    from .g_monster import walkmonster_start

    if gi.soundindex:
        _sound_pain   = gi.soundindex("berserk/berpain2.wav")
        _sound_die    = gi.soundindex("berserk/berdeth2.wav")
        _sound_idle   = gi.soundindex("berserk/beridle1.wav")
        _sound_punch  = gi.soundindex("berserk/attack.wav")
        _sound_search = gi.soundindex("berserk/bersrch1.wav")
        _sound_sight  = gi.soundindex("berserk/sight.wav")

    self.movetype = movetype_t.MOVETYPE_STEP.value
    self.solid    = solid_t.SOLID_BBOX.value
    if gi.modelindex:
        self.s.modelindex = gi.modelindex("models/monsters/berserk/tris.md2")

    self.mins[:]  = [-16.0, -16.0, -24.0]
    self.maxs[:]  = [ 16.0,  16.0,  32.0]

    self.health     = 240
    self.gib_health = -60
    self.mass       = 250

    self.pain = berserk_pain
    self.die  = berserk_die

    self.monsterinfo.stand        = berserk_stand
    self.monsterinfo.walk         = berserk_walk
    self.monsterinfo.run          = berserk_run
    self.monsterinfo.dodge        = None
    self.monsterinfo.attack       = None
    self.monsterinfo.melee        = berserk_melee
    self.monsterinfo.sight        = berserk_sight
    self.monsterinfo.search       = berserk_search
    self.monsterinfo.currentmove  = berserk_move_stand
    self.monsterinfo.scale        = MODEL_SCALE

    if gi.linkentity:
        gi.linkentity(self)
    walkmonster_start(self)

