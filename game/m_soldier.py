import random as _random

from .reference_import import gi
from .global_vars import level
from shared.QClasses import mmove_t, mframe_t
from shared.QEnums import movetype_t, solid_t, damage_t, MONSTER_AI_FLAGS
from shared.QConstants import (
    MZ2_SOLDIER_BLASTER_1, MZ2_SOLDIER_BLASTER_2, MZ2_SOLDIER_BLASTER_3,
    MZ2_SOLDIER_BLASTER_4, MZ2_SOLDIER_BLASTER_5, MZ2_SOLDIER_BLASTER_6,
    MZ2_SOLDIER_BLASTER_7, MZ2_SOLDIER_BLASTER_8,
    MZ2_SOLDIER_SHOTGUN_1, MZ2_SOLDIER_SHOTGUN_2, MZ2_SOLDIER_SHOTGUN_3,
    MZ2_SOLDIER_SHOTGUN_4, MZ2_SOLDIER_SHOTGUN_5, MZ2_SOLDIER_SHOTGUN_6,
    MZ2_SOLDIER_SHOTGUN_7, MZ2_SOLDIER_SHOTGUN_8,
    MZ2_SOLDIER_MACHINEGUN_1, MZ2_SOLDIER_MACHINEGUN_2, MZ2_SOLDIER_MACHINEGUN_3,
    MZ2_SOLDIER_MACHINEGUN_4, MZ2_SOLDIER_MACHINEGUN_5, MZ2_SOLDIER_MACHINEGUN_6,
    MZ2_SOLDIER_MACHINEGUN_7, MZ2_SOLDIER_MACHINEGUN_8,
    EF_BLASTER,
)

# ── frame constants ───────────────────────────────────────────────────────────
FRAME_attak101 = 0;  FRAME_attak102 = 1;  FRAME_attak112 = 11
FRAME_attak201 = 12; FRAME_attak204 = 15; FRAME_attak216 = 27; FRAME_attak218 = 29
FRAME_attak301 = 30; FRAME_attak303 = 32; FRAME_attak309 = 38
FRAME_attak401 = 39; FRAME_attak406 = 44
FRAME_duck01   = 45; FRAME_duck05   = 49
FRAME_pain101  = 50; FRAME_pain105  = 54
FRAME_pain201  = 55; FRAME_pain207  = 61
FRAME_pain301  = 62; FRAME_pain318  = 79
FRAME_pain401  = 80; FRAME_pain417  = 96
FRAME_run01    = 97; FRAME_run02    = 98; FRAME_run03 = 99; FRAME_run08 = 104
FRAME_runs01   = 109; FRAME_runs03  = 111; FRAME_runs04 = 112; FRAME_runs14 = 122
FRAME_stand101 = 146; FRAME_stand130 = 175
FRAME_stand301 = 176; FRAME_stand339 = 214
FRAME_walk101  = 215; FRAME_walk110  = 224; FRAME_walk133 = 247
FRAME_walk209  = 256; FRAME_walk218  = 265
FRAME_death101 = 272; FRAME_death136 = 307
FRAME_death201 = 308; FRAME_death235 = 342
FRAME_death301 = 343; FRAME_death345 = 387
FRAME_death401 = 388; FRAME_death453 = 440
FRAME_death501 = 441; FRAME_death524 = 464
FRAME_death601 = 465; FRAME_death610 = 474

MODEL_SCALE  = 1.2
FRAMETIME    = 0.1
DEAD_DEAD    = 2
DAMAGE_YES   = damage_t.DAMAGE_YES.value
DAMAGE_AIM   = 2
SVF_DEADMONSTER = 0x00000010
GIB_ORGANIC  = 0
AI_STAND_GROUND = MONSTER_AI_FLAGS.AI_STAND_GROUND.value
AI_DUCKED       = MONSTER_AI_FLAGS.AI_DUCKED.value
AI_HOLD_FRAME   = MONSTER_AI_FLAGS.AI_HOLD_FRAME.value

DEFAULT_BULLET_HSPREAD  = 300
DEFAULT_BULLET_VSPREAD  = 500
DEFAULT_SHOTGUN_HSPREAD = 1000
DEFAULT_SHOTGUN_VSPREAD = 500
DEFAULT_SHOTGUN_COUNT   = 12

_blaster_flash    = [MZ2_SOLDIER_BLASTER_1, MZ2_SOLDIER_BLASTER_2, MZ2_SOLDIER_BLASTER_3,
                     MZ2_SOLDIER_BLASTER_4, MZ2_SOLDIER_BLASTER_5, MZ2_SOLDIER_BLASTER_6,
                     MZ2_SOLDIER_BLASTER_7, MZ2_SOLDIER_BLASTER_8]
_shotgun_flash    = [MZ2_SOLDIER_SHOTGUN_1, MZ2_SOLDIER_SHOTGUN_2, MZ2_SOLDIER_SHOTGUN_3,
                     MZ2_SOLDIER_SHOTGUN_4, MZ2_SOLDIER_SHOTGUN_5, MZ2_SOLDIER_SHOTGUN_6,
                     MZ2_SOLDIER_SHOTGUN_7, MZ2_SOLDIER_SHOTGUN_8]
_machinegun_flash = [MZ2_SOLDIER_MACHINEGUN_1, MZ2_SOLDIER_MACHINEGUN_2, MZ2_SOLDIER_MACHINEGUN_3,
                     MZ2_SOLDIER_MACHINEGUN_4, MZ2_SOLDIER_MACHINEGUN_5, MZ2_SOLDIER_MACHINEGUN_6,
                     MZ2_SOLDIER_MACHINEGUN_7, MZ2_SOLDIER_MACHINEGUN_8]

_sound_idle         = 0
_sound_sight1       = 0
_sound_sight2       = 0
_sound_pain_light   = 0
_sound_pain         = 0
_sound_pain_ss      = 0
_sound_death_light  = 0
_sound_death        = 0
_sound_death_ss     = 0
_sound_cock         = 0


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


def soldier_idle(self):
    if _random.random() > 0.8:
        if gi.sound:
            gi.sound(self, _chan_voice(), _sound_idle, 1, _attn_idle(), 0)


def soldier_cock(self):
    if not gi.sound:
        return
    if self.s.frame == FRAME_stand301 + 21:
        gi.sound(self, _chan_weapon(), _sound_cock, 1, _attn_idle(), 0)
    else:
        gi.sound(self, _chan_weapon(), _sound_cock, 1, _attn_norm(), 0)


def soldier_stand(self):
    if (self.monsterinfo.currentmove is soldier_move_stand3 or _random.random() < 0.8):
        self.monsterinfo.currentmove = soldier_move_stand1
    else:
        self.monsterinfo.currentmove = soldier_move_stand3


def soldier_walk1_random(self):
    if _random.random() > 0.1:
        self.monsterinfo.nextframe = FRAME_walk101


def soldier_walk(self):
    if _random.random() < 0.5:
        self.monsterinfo.currentmove = soldier_move_walk1
    else:
        self.monsterinfo.currentmove = soldier_move_walk2


def soldier_run(self):
    if self.monsterinfo.aiflags & AI_STAND_GROUND:
        self.monsterinfo.currentmove = soldier_move_stand1
        return
    if (self.monsterinfo.currentmove is soldier_move_walk1 or
            self.monsterinfo.currentmove is soldier_move_walk2 or
            self.monsterinfo.currentmove is soldier_move_start_run):
        self.monsterinfo.currentmove = soldier_move_run
    else:
        self.monsterinfo.currentmove = soldier_move_start_run


def soldier_fire(self, flash_number):
    from .g_utils import G_ProjectSource, vectoangles
    from .q_shared import AngleVectors, VectorMA, _VectorSubtract, VectorNormalize
    from .g_monster import monster_fire_bullet, monster_fire_blaster, monster_fire_shotgun
    from .m_flash import monster_flash_offset

    if self.s.skinnum < 2:
        flash_index = _blaster_flash[flash_number]
    elif self.s.skinnum < 4:
        flash_index = _shotgun_flash[flash_number]
    else:
        flash_index = _machinegun_flash[flash_number]

    forward = [0.0, 0.0, 0.0]
    right   = [0.0, 0.0, 0.0]
    start   = [0.0, 0.0, 0.0]
    aim     = [0.0, 0.0, 0.0]

    AngleVectors(self.s.angles, forward, right, None)
    G_ProjectSource(self.s.origin, monster_flash_offset[flash_index], forward, right, start)

    if flash_number in (5, 6):
        aim[:] = forward
    else:
        if self.enemy:
            end = [
                self.enemy.s.origin[0],
                self.enemy.s.origin[1],
                self.enemy.s.origin[2] + self.enemy.viewheight,
            ]
            diff = [end[0]-start[0], end[1]-start[1], end[2]-start[2]]
            angles = [0.0, 0.0, 0.0]
            vectoangles(diff, angles)
            fw2 = [0.0, 0.0, 0.0]; rt2 = [0.0, 0.0, 0.0]; up2 = [0.0, 0.0, 0.0]
            AngleVectors(angles, fw2, rt2, up2)
            r = _random.uniform(-1.0, 1.0) * 1000
            u = _random.uniform(-1.0, 1.0) * 500
            end2 = [start[0]+8192*fw2[0], start[1]+8192*fw2[1], start[2]+8192*fw2[2]]
            VectorMA(end2, r, rt2, end2)
            VectorMA(end2, u, up2, end2)
            aim[:] = [end2[0]-start[0], end2[1]-start[1], end2[2]-start[2]]
            VectorNormalize(aim)
        else:
            aim[:] = forward

    if self.s.skinnum <= 1:
        monster_fire_blaster(self, start, aim, 5, 600, flash_index, EF_BLASTER)
    elif self.s.skinnum <= 3:
        monster_fire_shotgun(self, start, aim, 2, 1,
                             DEFAULT_SHOTGUN_HSPREAD, DEFAULT_SHOTGUN_VSPREAD,
                             DEFAULT_SHOTGUN_COUNT, flash_index)
    else:
        if not (self.monsterinfo.aiflags & AI_HOLD_FRAME):
            self.monsterinfo.pausetime = level.time + (3 + _random.randint(0, 7)) * FRAMETIME
        monster_fire_bullet(self, start, aim, 2, 4,
                            DEFAULT_BULLET_HSPREAD, DEFAULT_BULLET_VSPREAD, flash_index)
        if level.time >= self.monsterinfo.pausetime:
            self.monsterinfo.aiflags &= ~AI_HOLD_FRAME
        else:
            self.monsterinfo.aiflags |= AI_HOLD_FRAME


def soldier_fire1(self):    soldier_fire(self, 0)
def soldier_fire2(self):    soldier_fire(self, 1)
def soldier_fire4(self):    soldier_fire(self, 3)
def soldier_fire6(self):    soldier_fire(self, 5)
def soldier_fire7(self):    soldier_fire(self, 6)
def soldier_fire8(self):    soldier_fire(self, 7)


def soldier_attack1_refire1(self):
    if self.s.skinnum > 1:
        return
    if self.enemy and self.enemy.health <= 0:
        return
    from .g_ai import range as ai_range, RANGE_MELEE
    if _random.random() < 0.5 or ai_range(self, self.enemy) == RANGE_MELEE:
        self.monsterinfo.nextframe = FRAME_attak102
    else:
        self.monsterinfo.nextframe = FRAME_attak112 - 2


def soldier_attack1_refire2(self):
    if self.s.skinnum < 2:
        return
    if self.enemy and self.enemy.health <= 0:
        return
    from .g_ai import range as ai_range, RANGE_MELEE
    if _random.random() < 0.5 or ai_range(self, self.enemy) == RANGE_MELEE:
        self.monsterinfo.nextframe = FRAME_attak102


def soldier_attack2_refire1(self):
    if self.s.skinnum > 1:
        return
    if self.enemy and self.enemy.health <= 0:
        return
    from .g_ai import range as ai_range, RANGE_MELEE
    if _random.random() < 0.5 or ai_range(self, self.enemy) == RANGE_MELEE:
        self.monsterinfo.nextframe = FRAME_attak204
    else:
        self.monsterinfo.nextframe = FRAME_attak216


def soldier_attack2_refire2(self):
    if self.s.skinnum < 2:
        return
    if self.enemy and self.enemy.health <= 0:
        return
    from .g_ai import range as ai_range, RANGE_MELEE
    if _random.random() < 0.5 or ai_range(self, self.enemy) == RANGE_MELEE:
        self.monsterinfo.nextframe = FRAME_attak204


def soldier_duck_down(self):
    if self.monsterinfo.aiflags & AI_DUCKED:
        return
    self.monsterinfo.aiflags |= AI_DUCKED
    self.maxs[2] -= 32
    self.takedamage = DAMAGE_YES
    self.monsterinfo.pausetime = level.time + 1
    if gi.linkentity:
        gi.linkentity(self)


def soldier_duck_up(self):
    self.monsterinfo.aiflags &= ~AI_DUCKED
    self.maxs[2] += 32
    self.takedamage = DAMAGE_AIM
    if gi.linkentity:
        gi.linkentity(self)


def soldier_duck_hold(self):
    if level.time >= self.monsterinfo.pausetime:
        self.monsterinfo.aiflags &= ~AI_HOLD_FRAME
    else:
        self.monsterinfo.aiflags |= AI_HOLD_FRAME


def soldier_fire3(self):
    soldier_duck_down(self)
    soldier_fire(self, 2)


def soldier_attack3_refire(self):
    if (level.time + 0.4) < self.monsterinfo.pausetime:
        self.monsterinfo.nextframe = FRAME_attak303


def soldier_attack6_refire(self):
    if self.enemy and self.enemy.health <= 0:
        return
    from .g_ai import range as ai_range, RANGE_MID
    if ai_range(self, self.enemy) < RANGE_MID:
        return
    self.monsterinfo.nextframe = FRAME_runs03


def soldier_attack(self):
    if self.s.skinnum < 4:
        if _random.random() < 0.5:
            self.monsterinfo.currentmove = soldier_move_attack1
        else:
            self.monsterinfo.currentmove = soldier_move_attack2
    else:
        self.monsterinfo.currentmove = soldier_move_attack4


def soldier_sight(self, other):
    if not gi.sound:
        return
    if _random.random() < 0.5:
        gi.sound(self, _chan_voice(), _sound_sight1, 1, _attn_norm(), 0)
    else:
        gi.sound(self, _chan_voice(), _sound_sight2, 1, _attn_norm(), 0)
    from .g_ai import range as ai_range, RANGE_MID
    if ai_range(self, self.enemy) >= RANGE_MID and _random.random() > 0.5:
        self.monsterinfo.currentmove = soldier_move_attack6


def soldier_dodge(self, attacker, eta):
    if _random.random() > 0.25:
        return
    if not self.enemy:
        self.enemy = attacker
    self.monsterinfo.pausetime = level.time + eta + 0.3
    r = _random.random()
    if r > 0.66:
        self.monsterinfo.currentmove = soldier_move_duck
    else:
        self.monsterinfo.currentmove = soldier_move_attack3


def soldier_pain(self, other, kick, damage):
    if self.health < (self.max_health // 2):
        self.s.skinnum |= 1
    if level.time < self.pain_debounce_time:
        if self.velocity[2] > 100:
            if (self.monsterinfo.currentmove is soldier_move_pain1 or
                    self.monsterinfo.currentmove is soldier_move_pain2 or
                    self.monsterinfo.currentmove is soldier_move_pain3):
                self.monsterinfo.currentmove = soldier_move_pain4
        return
    self.pain_debounce_time = level.time + 3
    if gi.sound:
        n = self.s.skinnum | 1
        if n == 1:
            gi.sound(self, _chan_voice(), _sound_pain_light, 1, _attn_norm(), 0)
        elif n == 3:
            gi.sound(self, _chan_voice(), _sound_pain, 1, _attn_norm(), 0)
        else:
            gi.sound(self, _chan_voice(), _sound_pain_ss, 1, _attn_norm(), 0)
    if self.velocity[2] > 100:
        self.monsterinfo.currentmove = soldier_move_pain4
        return
    r = _random.random()
    if r < 0.33:
        self.monsterinfo.currentmove = soldier_move_pain1
    elif r < 0.66:
        self.monsterinfo.currentmove = soldier_move_pain2
    else:
        self.monsterinfo.currentmove = soldier_move_pain3


def soldier_dead(self):
    self.mins[0] = -16; self.mins[1] = -16; self.mins[2] = -24
    self.maxs[0] =  16; self.maxs[1] =  16; self.maxs[2] =  -8
    self.movetype = movetype_t.MOVETYPE_TOSS.value
    self.svflags |= SVF_DEADMONSTER
    if gi.linkentity:
        gi.linkentity(self)
    from .g_monster import M_FlyCheck
    M_FlyCheck(self)


def soldier_die(self, inflictor, attacker, damage, point):
    from .g_misc import ThrowGib, ThrowHead
    if self.health <= self.gib_health:
        if gi.sound and gi.soundindex:
            gi.sound(self, _chan_voice(), gi.soundindex("misc/udeath.wav"), 1, _attn_norm(), 0)
        for _ in range(3):
            ThrowGib(self, "models/objects/gibs/sm_meat/tris.md2", damage, GIB_ORGANIC)
        ThrowGib(self, "models/objects/gibs/chest/tris.md2", damage, GIB_ORGANIC)
        ThrowHead(self, "models/objects/gibs/head2/tris.md2", damage, GIB_ORGANIC)
        self.deadflag = DEAD_DEAD
        return
    if self.deadflag == DEAD_DEAD:
        return
    self.deadflag = DEAD_DEAD
    self.takedamage = DAMAGE_YES
    self.s.skinnum |= 1
    if gi.sound:
        n = self.s.skinnum
        if n == 1:
            gi.sound(self, _chan_voice(), _sound_death_light, 1, _attn_norm(), 0)
        elif n == 3:
            gi.sound(self, _chan_voice(), _sound_death, 1, _attn_norm(), 0)
        else:
            gi.sound(self, _chan_voice(), _sound_death_ss, 1, _attn_norm(), 0)
    if point and abs((self.s.origin[2] + self.viewheight) - point[2]) <= 4:
        self.monsterinfo.currentmove = soldier_move_death3
        return
    n = _random.randint(0, 4)
    if n == 0:      self.monsterinfo.currentmove = soldier_move_death1
    elif n == 1:    self.monsterinfo.currentmove = soldier_move_death2
    elif n == 2:    self.monsterinfo.currentmove = soldier_move_death4
    elif n == 3:    self.monsterinfo.currentmove = soldier_move_death5
    else:           self.monsterinfo.currentmove = soldier_move_death6


# ── AI helpers ────────────────────────────────────────────────────────────────
def _ai_stand():
    from .g_ai import ai_stand;  return ai_stand

def _ai_walk():
    from .g_ai import ai_walk;   return ai_walk

def _ai_run():
    from .g_ai import ai_run;    return ai_run

def _ai_charge():
    from .g_ai import ai_charge; return ai_charge

def _ai_move():
    from .g_ai import ai_move;   return ai_move


# ── move tables ───────────────────────────────────────────────────────────────
_stand1_cbs = {0: soldier_idle}
soldier_frames_stand1 = [
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, _stand1_cbs.get(i))
    for i in range(30)
]
soldier_move_stand1 = mmove_t(FRAME_stand101, FRAME_stand130, soldier_frames_stand1, soldier_stand)

_stand3_cbs = {21: soldier_cock}
soldier_frames_stand3 = [
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, _stand3_cbs.get(i))
    for i in range(39)
]
soldier_move_stand3 = mmove_t(FRAME_stand301, FRAME_stand339, soldier_frames_stand3, soldier_stand)

_walk1_dists = [3, 6, 2, 2, 2, 1, 6, 5, 3, -1] + [0]*23
_walk1_cbs   = {9: soldier_walk1_random}
soldier_frames_walk1 = [
    mframe_t(lambda s, d: _ai_walk()(s, d), _walk1_dists[i], _walk1_cbs.get(i))
    for i in range(33)
]
soldier_move_walk1 = mmove_t(FRAME_walk101, FRAME_walk133, soldier_frames_walk1, None)

_walk2_dists = [4, 4, 9, 8, 5, 1, 3, 7, 6, 7]
soldier_frames_walk2 = [
    mframe_t(lambda s, d: _ai_walk()(s, d), _walk2_dists[i], None)
    for i in range(10)
]
soldier_move_walk2 = mmove_t(FRAME_walk209, FRAME_walk218, soldier_frames_walk2, None)

soldier_frames_start_run = [
    mframe_t(lambda s, d: _ai_run()(s, d), 7, None),
    mframe_t(lambda s, d: _ai_run()(s, d), 5, None),
]
soldier_move_start_run = mmove_t(FRAME_run01, FRAME_run02, soldier_frames_start_run, soldier_run)

_run_dists = [10, 11, 11, 16, 10, 15]
soldier_frames_run = [
    mframe_t(lambda s, d: _ai_run()(s, d), _run_dists[i], None)
    for i in range(6)
]
soldier_move_run = mmove_t(FRAME_run03, FRAME_run08, soldier_frames_run, None)

_pain1_dists = [-3, 4, 1, 1, 0]
soldier_frames_pain1 = [
    mframe_t(lambda s, d: _ai_move()(s, d), _pain1_dists[i], None)
    for i in range(5)
]
soldier_move_pain1 = mmove_t(FRAME_pain101, FRAME_pain105, soldier_frames_pain1, soldier_run)

_pain2_dists = [-13, -1, 2, 4, 2, 3, 2]
soldier_frames_pain2 = [
    mframe_t(lambda s, d: _ai_move()(s, d), _pain2_dists[i], None)
    for i in range(7)
]
soldier_move_pain2 = mmove_t(FRAME_pain201, FRAME_pain207, soldier_frames_pain2, soldier_run)

_pain3_dists = [-8, 10, -4, -1, -3, 0, 3, 0, 0, 0, 0, 1, 0, 1, 2, 4, 3, 2]
soldier_frames_pain3 = [
    mframe_t(lambda s, d: _ai_move()(s, d), _pain3_dists[i], None)
    for i in range(18)
]
soldier_move_pain3 = mmove_t(FRAME_pain301, FRAME_pain318, soldier_frames_pain3, soldier_run)

_pain4_dists = [0, 0, 0, -10, -6, 8, 4, 1, 0, 2, 5, 2, -1, -1, 3, 2, 0]
soldier_frames_pain4 = [
    mframe_t(lambda s, d: _ai_move()(s, d), _pain4_dists[i], None)
    for i in range(17)
]
soldier_move_pain4 = mmove_t(FRAME_pain401, FRAME_pain417, soldier_frames_pain4, soldier_run)

_atk1_cbs = {2: soldier_fire1, 5: soldier_attack1_refire1, 7: soldier_cock, 8: soldier_attack1_refire2}
soldier_frames_attack1 = [
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, _atk1_cbs.get(i))
    for i in range(12)
]
soldier_move_attack1 = mmove_t(FRAME_attak101, FRAME_attak112, soldier_frames_attack1, soldier_run)

_atk2_cbs = {4: soldier_fire2, 7: soldier_attack2_refire1, 12: soldier_cock, 14: soldier_attack2_refire2}
soldier_frames_attack2 = [
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, _atk2_cbs.get(i))
    for i in range(18)
]
soldier_move_attack2 = mmove_t(FRAME_attak201, FRAME_attak218, soldier_frames_attack2, soldier_run)

_atk3_cbs = {2: soldier_fire3, 5: soldier_attack3_refire, 6: soldier_duck_up}
soldier_frames_attack3 = [
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, _atk3_cbs.get(i))
    for i in range(9)
]
soldier_move_attack3 = mmove_t(FRAME_attak301, FRAME_attak309, soldier_frames_attack3, soldier_run)

_atk4_cbs = {2: soldier_fire4}
soldier_frames_attack4 = [
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, _atk4_cbs.get(i))
    for i in range(6)
]
soldier_move_attack4 = mmove_t(FRAME_attak401, FRAME_attak406, soldier_frames_attack4, soldier_run)

_atk6_dists = [10, 4, 12, 11, 13, 18, 15, 14, 11, 8, 11, 12, 12, 17]
_atk6_cbs   = {3: soldier_fire8, 13: soldier_attack6_refire}
soldier_frames_attack6 = [
    mframe_t(lambda s, d: _ai_charge()(s, d), _atk6_dists[i], _atk6_cbs.get(i))
    for i in range(14)
]
soldier_move_attack6 = mmove_t(FRAME_runs01, FRAME_runs14, soldier_frames_attack6, soldier_run)

soldier_frames_duck = [
    mframe_t(lambda s, d: _ai_move()(s, d), 5,  soldier_duck_down),
    mframe_t(lambda s, d: _ai_move()(s, d), -1, soldier_duck_hold),
    mframe_t(lambda s, d: _ai_move()(s, d), 1,  None),
    mframe_t(lambda s, d: _ai_move()(s, d), 0,  soldier_duck_up),
    mframe_t(lambda s, d: _ai_move()(s, d), 5,  None),
]
soldier_move_duck = mmove_t(FRAME_duck01, FRAME_duck05, soldier_frames_duck, soldier_run)

_d1_dists = [0, -10, -10, -10, -5] + [0]*31
_d1_cbs   = {21: soldier_fire6, 24: soldier_fire7}
soldier_frames_death1 = [
    mframe_t(lambda s, d: _ai_move()(s, d), _d1_dists[i], _d1_cbs.get(i))
    for i in range(36)
]
soldier_move_death1 = mmove_t(FRAME_death101, FRAME_death136, soldier_frames_death1, soldier_dead)

_d2_dists = [-5, -5, -5] + [0]*32
soldier_frames_death2 = [
    mframe_t(lambda s, d: _ai_move()(s, d), _d2_dists[i], None)
    for i in range(35)
]
soldier_move_death2 = mmove_t(FRAME_death201, FRAME_death235, soldier_frames_death2, soldier_dead)

_d3_dists = [-5, -5, -5] + [0]*42
soldier_frames_death3 = [
    mframe_t(lambda s, d: _ai_move()(s, d), _d3_dists[i], None)
    for i in range(45)
]
soldier_move_death3 = mmove_t(FRAME_death301, FRAME_death345, soldier_frames_death3, soldier_dead)

soldier_frames_death4 = [
    mframe_t(lambda s, d: _ai_move()(s, d), 0, None)
    for _ in range(53)
]
soldier_move_death4 = mmove_t(FRAME_death401, FRAME_death453, soldier_frames_death4, soldier_dead)

_d5_dists = [-5, -5, -5] + [0]*21
soldier_frames_death5 = [
    mframe_t(lambda s, d: _ai_move()(s, d), _d5_dists[i], None)
    for i in range(24)
]
soldier_move_death5 = mmove_t(FRAME_death501, FRAME_death524, soldier_frames_death5, soldier_dead)

soldier_frames_death6 = [
    mframe_t(lambda s, d: _ai_move()(s, d), 0, None)
    for _ in range(10)
]
soldier_move_death6 = mmove_t(FRAME_death601, FRAME_death610, soldier_frames_death6, soldier_dead)


# ── spawn ─────────────────────────────────────────────────────────────────────
def _SP_monster_soldier_x(self):
    global _sound_idle, _sound_sight1, _sound_sight2, _sound_cock
    from .g_monster import walkmonster_start

    if gi.modelindex:
        self.s.modelindex = gi.modelindex("models/monsters/soldier/tris.md2")
    if gi.soundindex:
        _sound_idle   = gi.soundindex("soldier/solidle1.wav")
        _sound_sight1 = gi.soundindex("soldier/solsght1.wav")
        _sound_sight2 = gi.soundindex("soldier/solsrch1.wav")
        _sound_cock   = gi.soundindex("infantry/infatck3.wav")

    self.movetype = movetype_t.MOVETYPE_STEP.value
    self.solid    = solid_t.SOLID_BBOX.value
    self.mins[:]  = [-16.0, -16.0, -24.0]
    self.maxs[:]  = [ 16.0,  16.0,  32.0]
    self.mass     = 100
    self.pain = soldier_pain
    self.die  = soldier_die
    self.monsterinfo.stand  = soldier_stand
    self.monsterinfo.walk   = soldier_walk
    self.monsterinfo.run    = soldier_run
    self.monsterinfo.dodge  = soldier_dodge
    self.monsterinfo.attack = soldier_attack
    self.monsterinfo.melee  = None
    self.monsterinfo.sight  = soldier_sight
    self.monsterinfo.scale  = MODEL_SCALE
    if gi.linkentity:
        gi.linkentity(self)
    soldier_stand(self)
    walkmonster_start(self)


def SP_monster_soldier_light(self):
    global _sound_pain_light, _sound_death_light
    _SP_monster_soldier_x(self)
    if gi.soundindex:
        _sound_pain_light  = gi.soundindex("soldier/solpain2.wav")
        _sound_death_light = gi.soundindex("soldier/soldeth2.wav")
    self.s.skinnum  = 0
    self.health     = 20
    self.gib_health = -30


def SP_monster_soldier(self):
    global _sound_pain, _sound_death
    _SP_monster_soldier_x(self)
    if gi.soundindex:
        _sound_pain  = gi.soundindex("soldier/solpain1.wav")
        _sound_death = gi.soundindex("soldier/soldeth1.wav")
    self.s.skinnum  = 2
    self.health     = 30
    self.gib_health = -30


def SP_monster_soldier_ss(self):
    global _sound_pain_ss, _sound_death_ss
    _SP_monster_soldier_x(self)
    if gi.soundindex:
        _sound_pain_ss  = gi.soundindex("soldier/solpain3.wav")
        _sound_death_ss = gi.soundindex("soldier/soldeth3.wav")
    self.s.skinnum  = 4
    self.health     = 40
    self.gib_health = -30


def soldier_fire4():
    return


def soldier_fire8():
    return


def soldier_attack6_refire():
    return


def soldier_attack():
    return


def soldier_sight():
    return


def soldier_duck_hold():
    return


def soldier_dodge():
    return


def soldier_fire6():
    return


def soldier_fire7():
    return


def soldier_dead():
    return


def soldier_die():
    return


def SP_monster_soldier_x():
    return


def SP_monster_soldier_light():
    return


def SP_monster_soldier():
    return


def SP_monster_soldier_ss():
    return

