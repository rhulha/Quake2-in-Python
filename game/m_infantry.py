import random as _random

from .reference_import import gi
from .global_vars import level
from shared.QClasses import mmove_t, mframe_t
from shared.QEnums import movetype_t, solid_t, damage_t, MONSTER_AI_FLAGS
from shared.QConstants import (MZ2_INFANTRY_MACHINEGUN_1, MZ2_INFANTRY_MACHINEGUN_2)

# ── frame constants ───────────────────────────────────────────────────────────
FRAME_stand50   = 49
FRAME_stand71   = 70
FRAME_stand01   = 1
FRAME_stand49   = 48
FRAME_walk03    = 74
FRAME_walk14    = 85
FRAME_run01     = 92
FRAME_run08     = 99
FRAME_pain101   = 100
FRAME_pain110   = 109
FRAME_pain201   = 110
FRAME_pain210   = 119
FRAME_duck01    = 120
FRAME_duck05    = 124
FRAME_death101  = 125
FRAME_death120  = 144
FRAME_death201  = 145
FRAME_death225  = 169
FRAME_death211  = 155
FRAME_death301  = 170
FRAME_death309  = 178
FRAME_attak101  = 184
FRAME_attak111  = 194
FRAME_attak115  = 198
FRAME_attak201  = 199
FRAME_attak208  = 206

MODEL_SCALE = 1.0
FRAMETIME   = 0.1

# ── dead / damage constants ───────────────────────────────────────────────────
DEAD_DEAD       = 2
DAMAGE_YES      = damage_t.DAMAGE_YES.value
DAMAGE_AIM      = 2
SVF_DEADMONSTER = 0x00000010
GIB_ORGANIC     = 0

AI_STAND_GROUND  = MONSTER_AI_FLAGS.AI_STAND_GROUND.value
AI_HOLD_FRAME    = MONSTER_AI_FLAGS.AI_HOLD_FRAME.value
AI_DUCKED        = MONSTER_AI_FLAGS.AI_DUCKED.value

DEFAULT_BULLET_HSPREAD = 300
DEFAULT_BULLET_VSPREAD = 500

# ── per-spawn sound indices ────────────────────────────────────────────────────
_sound_pain1         = 0
_sound_pain2         = 0
_sound_die1          = 0
_sound_die2          = 0
_sound_gunshot       = 0
_sound_weapon_cock   = 0
_sound_punch_swing   = 0
_sound_punch_hit     = 0
_sound_sight         = 0
_sound_idle          = 0

# aim angle table for the machinegun death-sequence shots (C: aimangles[])
_aimangles = [
    [0.0,   5.0,  0.0],
    [10.0,  15.0, 0.0],
    [20.0,  25.0, 0.0],
    [25.0,  35.0, 0.0],
    [30.0,  40.0, 0.0],
    [30.0,  45.0, 0.0],
    [25.0,  50.0, 0.0],
    [20.0,  40.0, 0.0],
    [15.0,  35.0, 0.0],
    [40.0,  35.0, 0.0],
    [70.0,  35.0, 0.0],
    [90.0,  35.0, 0.0],
]


# ── helpers ───────────────────────────────────────────────────────────────────

def _chan_voice():
    from shared.QEnums import SOUND_CHANNELS
    return SOUND_CHANNELS.CHAN_VOICE.value

def _chan_weapon():
    from shared.QEnums import SOUND_CHANNELS
    return SOUND_CHANNELS.CHAN_WEAPON.value

def _chan_body():
    from shared.QEnums import SOUND_CHANNELS
    return SOUND_CHANNELS.CHAN_BODY.value

def _attn_norm():
    from shared.QEnums import SOUND_ATTN_VALUES
    return SOUND_ATTN_VALUES.ATTN_NORM.value

def _attn_idle():
    from shared.QEnums import SOUND_ATTN_VALUES
    return SOUND_ATTN_VALUES.ATTN_IDLE.value


# ── InfantryMachineGun ────────────────────────────────────────────────────────

def InfantryMachineGun(self):
    from .g_utils import G_ProjectSource
    from .q_shared import AngleVectors, VectorNormalize
    from .g_monster import monster_fire_bullet
    from .m_flash import monster_flash_offset

    forward = [0.0, 0.0, 0.0]
    right   = [0.0, 0.0, 0.0]
    start   = [0.0, 0.0, 0.0]
    target  = [0.0, 0.0, 0.0]

    if self.s.frame == FRAME_attak111:
        flash_number = MZ2_INFANTRY_MACHINEGUN_1
        AngleVectors(self.s.angles, forward, right, None)
        G_ProjectSource(self.s.origin, monster_flash_offset[flash_number], forward, right, start)

        if self.enemy:
            target[0] = self.enemy.s.origin[0] + (-0.2) * self.enemy.velocity[0]
            target[1] = self.enemy.s.origin[1] + (-0.2) * self.enemy.velocity[1]
            target[2] = self.enemy.s.origin[2] + (-0.2) * self.enemy.velocity[2]
            target[2] += self.enemy.viewheight
            forward[0] = target[0] - start[0]
            forward[1] = target[1] - start[1]
            forward[2] = target[2] - start[2]
            VectorNormalize(forward)
        else:
            AngleVectors(self.s.angles, forward, right, None)
    else:
        flash_number = MZ2_INFANTRY_MACHINEGUN_2 + (self.s.frame - FRAME_death211)
        AngleVectors(self.s.angles, forward, right, None)
        G_ProjectSource(self.s.origin, monster_flash_offset[flash_number], forward, right, start)

        idx = flash_number - MZ2_INFANTRY_MACHINEGUN_2
        if 0 <= idx < len(_aimangles):
            vec = [
                self.s.angles[0] - _aimangles[idx][0],
                self.s.angles[1] - _aimangles[idx][1],
                self.s.angles[2] - _aimangles[idx][2],
            ]
            AngleVectors(vec, forward, None, None)

    monster_fire_bullet(self, start, forward, 3, 4,
                        DEFAULT_BULLET_HSPREAD, DEFAULT_BULLET_VSPREAD,
                        flash_number)


# ── stand / fidget ────────────────────────────────────────────────────────────

def infantry_stand(self):
    self.monsterinfo.currentmove = infantry_move_stand


def infantry_fidget(self):
    self.monsterinfo.currentmove = infantry_move_fidget
    if gi.sound:
        gi.sound(self, _chan_voice(), _sound_idle, 1, _attn_idle(), 0)


# ── walk / run ────────────────────────────────────────────────────────────────

def infantry_walk(self):
    self.monsterinfo.currentmove = infantry_move_walk


def infantry_run(self):
    if self.monsterinfo.aiflags & AI_STAND_GROUND:
        self.monsterinfo.currentmove = infantry_move_stand
    else:
        self.monsterinfo.currentmove = infantry_move_run


# ── pain ──────────────────────────────────────────────────────────────────────

def infantry_pain(self, other, kick, damage):
    if self.health < (self.max_health // 2):
        self.s.skinnum = 1

    if level.time < self.pain_debounce_time:
        return

    self.pain_debounce_time = level.time + 3

    if _random.random() < 0.5:
        self.monsterinfo.currentmove = infantry_move_pain1
        if gi.sound:
            gi.sound(self, _chan_voice(), _sound_pain1, 1, _attn_norm(), 0)
    else:
        self.monsterinfo.currentmove = infantry_move_pain2
        if gi.sound:
            gi.sound(self, _chan_voice(), _sound_pain2, 1, _attn_norm(), 0)


# ── sight ─────────────────────────────────────────────────────────────────────

def infantry_sight(self, other):
    if gi.sound:
        gi.sound(self, _chan_body(), _sound_sight, 1, _attn_norm(), 0)


# ── dead / die ────────────────────────────────────────────────────────────────

def infantry_dead(self):
    self.mins[0] = -16; self.mins[1] = -16; self.mins[2] = -24
    self.maxs[0] =  16; self.maxs[1] =  16; self.maxs[2] =  -8
    self.movetype = movetype_t.MOVETYPE_TOSS.value
    self.svflags |= SVF_DEADMONSTER
    if gi.linkentity:
        gi.linkentity(self)
    from .g_monster import M_FlyCheck
    M_FlyCheck(self)


def infantry_die(self, inflictor, attacker, damage, point):
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

    self.deadflag = DEAD_DEAD
    self.takedamage = DAMAGE_YES

    n = _random.randint(0, 2)
    if n == 0:
        self.monsterinfo.currentmove = infantry_move_death1
        if gi.sound:
            gi.sound(self, _chan_voice(), _sound_die2, 1, _attn_norm(), 0)
    elif n == 1:
        self.monsterinfo.currentmove = infantry_move_death2
        if gi.sound:
            gi.sound(self, _chan_voice(), _sound_die1, 1, _attn_norm(), 0)
    else:
        self.monsterinfo.currentmove = infantry_move_death3
        if gi.sound:
            gi.sound(self, _chan_voice(), _sound_die2, 1, _attn_norm(), 0)


# ── duck / dodge ──────────────────────────────────────────────────────────────

def infantry_duck_down(self):
    if self.monsterinfo.aiflags & AI_DUCKED:
        return
    self.monsterinfo.aiflags |= AI_DUCKED
    self.maxs[2] -= 32
    self.takedamage = DAMAGE_YES
    self.monsterinfo.pausetime = level.time + 1
    if gi.linkentity:
        gi.linkentity(self)


def infantry_duck_hold(self):
    if level.time >= self.monsterinfo.pausetime:
        self.monsterinfo.aiflags &= ~AI_HOLD_FRAME
    else:
        self.monsterinfo.aiflags |= AI_HOLD_FRAME


def infantry_duck_up(self):
    self.monsterinfo.aiflags &= ~AI_DUCKED
    self.maxs[2] += 32
    self.takedamage = DAMAGE_AIM
    if gi.linkentity:
        gi.linkentity(self)


def infantry_dodge(self, attacker, eta):
    if _random.random() > 0.25:
        return
    if not self.enemy:
        self.enemy = attacker
    self.monsterinfo.currentmove = infantry_move_duck


# ── gun attack helpers ────────────────────────────────────────────────────────

def infantry_cock_gun(self):
    if gi.sound:
        gi.sound(self, _chan_weapon(), _sound_weapon_cock, 1, _attn_norm(), 0)
    n = (_random.randint(0, 15)) + 10
    self.monsterinfo.pausetime = level.time + n * FRAMETIME


def infantry_fire(self):
    InfantryMachineGun(self)
    if level.time >= self.monsterinfo.pausetime:
        self.monsterinfo.aiflags &= ~AI_HOLD_FRAME
    else:
        self.monsterinfo.aiflags |= AI_HOLD_FRAME


# ── melee attack helpers ──────────────────────────────────────────────────────

def infantry_swing(self):
    if gi.sound:
        gi.sound(self, _chan_weapon(), _sound_punch_swing, 1, _attn_norm(), 0)


def infantry_smack(self):
    from .g_weapon import fire_hit
    from .g_ai import MELEE_DISTANCE
    aim = [MELEE_DISTANCE, 0.0, 0.0]
    if fire_hit(self, aim, 5 + _random.randint(0, 4), 50):
        if gi.sound:
            gi.sound(self, _chan_weapon(), _sound_punch_hit, 1, _attn_norm(), 0)


# ── attack dispatcher ─────────────────────────────────────────────────────────

def infantry_attack(self):
    from .g_ai import range as ai_range, RANGE_MELEE
    if ai_range(self, self.enemy) == RANGE_MELEE:
        self.monsterinfo.currentmove = infantry_move_attack2
    else:
        self.monsterinfo.currentmove = infantry_move_attack1


# ── move tables ───────────────────────────────────────────────────────────────

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


infantry_frames_stand = [
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None),
]
infantry_move_stand = mmove_t(FRAME_stand50, FRAME_stand71, infantry_frames_stand, None)

_fidget_dists = [1, 0, 1, 3, 6, 3, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, -1, 0, 0,
                 1, 0, -2, 1, 1, 1, -1, 0, 0, -1, 0, 0, 0, 0, 0, -1, 0, 0, 1, 0,
                 0, -1, -1, 0, -3, -2, -3, -3, -2]
infantry_frames_fidget = [
    mframe_t(lambda s, d: _ai_stand()(s, d), dist, None)
    for dist in _fidget_dists
]
infantry_move_fidget = mmove_t(FRAME_stand01, FRAME_stand49, infantry_frames_fidget, infantry_stand)

_walk_dists = [5, 4, 4, 5, 4, 5, 6, 4, 4, 4, 4, 5]
infantry_frames_walk = [
    mframe_t(lambda s, d: _ai_walk()(s, d), dist, None)
    for dist in _walk_dists
]
infantry_move_walk = mmove_t(FRAME_walk03, FRAME_walk14, infantry_frames_walk, None)

_run_dists = [10, 20, 5, 7, 30, 35, 2, 6]
infantry_frames_run = [
    mframe_t(lambda s, d: _ai_run()(s, d), dist, None)
    for dist in _run_dists
]
infantry_move_run = mmove_t(FRAME_run01, FRAME_run08, infantry_frames_run, None)

_pain1_dists = [-3, -2, -1, -2, -1, 1, -1, 1, 6, 2]
infantry_frames_pain1 = [
    mframe_t(lambda s, d: _ai_move()(s, d), dist, None)
    for dist in _pain1_dists
]
infantry_move_pain1 = mmove_t(FRAME_pain101, FRAME_pain110, infantry_frames_pain1, infantry_run)

_pain2_dists = [-3, -3, 0, -1, -2, 0, 0, 2, 5, 2]
infantry_frames_pain2 = [
    mframe_t(lambda s, d: _ai_move()(s, d), dist, None)
    for dist in _pain2_dists
]
infantry_move_pain2 = mmove_t(FRAME_pain201, FRAME_pain210, infantry_frames_pain2, infantry_run)

infantry_frames_duck = [
    mframe_t(lambda s, d: _ai_move()(s, d), -2, infantry_duck_down),
    mframe_t(lambda s, d: _ai_move()(s, d), -5, infantry_duck_hold),
    mframe_t(lambda s, d: _ai_move()(s, d),  3, None),
    mframe_t(lambda s, d: _ai_move()(s, d),  4, infantry_duck_up),
    mframe_t(lambda s, d: _ai_move()(s, d),  0, None),
]
infantry_move_duck = mmove_t(FRAME_duck01, FRAME_duck05, infantry_frames_duck, infantry_run)

_death1_dists = [-4, 0, 0, -1, -4, 0, 0, 0, -1, 3, 1, 1, -2, 2, 2, 9, 9, 5, -3, -3]
infantry_frames_death1 = [
    mframe_t(lambda s, d: _ai_move()(s, d), dist, None)
    for dist in _death1_dists
]
infantry_move_death1 = mmove_t(FRAME_death101, FRAME_death120, infantry_frames_death1, infantry_dead)

# death2 — frames 211–221 also fire InfantryMachineGun
_death2_data = [
    (0, None), (1, None), (5, None), (-1, None), (0, None),
    (1, None), (1, None), (4, None), (3, None), (0, None),
    (-2, InfantryMachineGun), (-2, InfantryMachineGun), (-3, InfantryMachineGun),
    (-1, InfantryMachineGun), (-2, InfantryMachineGun), (0, InfantryMachineGun),
    (2, InfantryMachineGun), (2, InfantryMachineGun), (3, InfantryMachineGun),
    (-10, InfantryMachineGun), (-7, InfantryMachineGun), (-8, InfantryMachineGun),
    (-6, None), (4, None), (0, None),
]
infantry_frames_death2 = [
    mframe_t(lambda s, d: _ai_move()(s, d), dist, fn)
    for dist, fn in _death2_data
]
infantry_move_death2 = mmove_t(FRAME_death201, FRAME_death225, infantry_frames_death2, infantry_dead)

_death3_dists = [0, 0, 0, -6, -11, -3, -11, 0, 0]
infantry_frames_death3 = [
    mframe_t(lambda s, d: _ai_move()(s, d), dist, None)
    for dist in _death3_dists
]
infantry_move_death3 = mmove_t(FRAME_death301, FRAME_death309, infantry_frames_death3, infantry_dead)

_atk1_data = [
    (4, None), (-1, None), (-1, None), (0, infantry_cock_gun),
    (-1, None), (1, None), (1, None), (2, None),
    (-2, None), (-3, None), (1, infantry_fire),
    (5, None), (-1, None), (-2, None), (-3, None),
]
infantry_frames_attack1 = [
    mframe_t(lambda s, d: _ai_charge()(s, d), dist, fn)
    for dist, fn in _atk1_data
]
infantry_move_attack1 = mmove_t(FRAME_attak101, FRAME_attak115, infantry_frames_attack1, infantry_run)

_atk2_data = [
    (3, None), (6, None), (0, infantry_swing),
    (8, None), (5, None), (8, infantry_smack),
    (6, None), (3, None),
]
infantry_frames_attack2 = [
    mframe_t(lambda s, d: _ai_charge()(s, d), dist, fn)
    for dist, fn in _atk2_data
]
infantry_move_attack2 = mmove_t(FRAME_attak201, FRAME_attak208, infantry_frames_attack2, infantry_run)


# ── spawn ─────────────────────────────────────────────────────────────────────

def SP_monster_infantry(self):
    global _sound_pain1, _sound_pain2, _sound_die1, _sound_die2
    global _sound_gunshot, _sound_weapon_cock, _sound_punch_swing
    global _sound_punch_hit, _sound_sight, _sound_idle

    from .g_utils import G_FreeEdict
    from .g_monster import walkmonster_start

    if gi.soundindex:
        _sound_pain1        = gi.soundindex("infantry/infpain1.wav")
        _sound_pain2        = gi.soundindex("infantry/infpain2.wav")
        _sound_die1         = gi.soundindex("infantry/infdeth1.wav")
        _sound_die2         = gi.soundindex("infantry/infdeth2.wav")
        _sound_gunshot      = gi.soundindex("infantry/infatck1.wav")
        _sound_weapon_cock  = gi.soundindex("infantry/infatck3.wav")
        _sound_punch_swing  = gi.soundindex("infantry/infatck2.wav")
        _sound_punch_hit    = gi.soundindex("infantry/melee2.wav")
        _sound_sight        = gi.soundindex("infantry/infsght1.wav")
        _sound_idle         = gi.soundindex("infantry/infidle1.wav")

    self.movetype = movetype_t.MOVETYPE_STEP.value
    self.solid    = solid_t.SOLID_BBOX.value
    if gi.modelindex:
        self.s.modelindex = gi.modelindex("models/monsters/infantry/tris.md2")

    self.mins[:]  = [-16.0, -16.0, -24.0]
    self.maxs[:]  = [ 16.0,  16.0,  32.0]

    self.health     = 100
    self.gib_health = -40
    self.mass       = 200

    self.pain = infantry_pain
    self.die  = infantry_die

    self.monsterinfo.stand        = infantry_stand
    self.monsterinfo.walk         = infantry_walk
    self.monsterinfo.run          = infantry_run
    self.monsterinfo.dodge        = infantry_dodge
    self.monsterinfo.attack       = infantry_attack
    self.monsterinfo.melee        = None
    self.monsterinfo.sight        = infantry_sight
    self.monsterinfo.idle         = infantry_fidget
    self.monsterinfo.scale        = MODEL_SCALE
    self.monsterinfo.currentmove  = infantry_move_stand

    if gi.linkentity:
        gi.linkentity(self)

    walkmonster_start(self)

