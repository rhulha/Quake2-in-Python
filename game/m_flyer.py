import random as _random

from .reference_import import gi
from shared.QClasses import mmove_t, mframe_t
from shared.QEnums import movetype_t, solid_t, MONSTER_AI_FLAGS
from shared.QConstants import (
    MZ2_FLYER_BLASTER_1,
    MZ2_FLYER_BLASTER_2,
    EF_HYPERBLASTER,
)
from .global_vars import level, skill

ACTION_nothing = 0
ACTION_attack1 = 1
ACTION_attack2 = 2
ACTION_run = 3
ACTION_walk = 4

FRAME_start01 = 0
FRAME_start02 = 1
FRAME_start03 = 2
FRAME_start04 = 3
FRAME_start05 = 4
FRAME_start06 = 5
FRAME_stop01 = 6
FRAME_stop02 = 7
FRAME_stop03 = 8
FRAME_stop04 = 9
FRAME_stop05 = 10
FRAME_stop06 = 11
FRAME_stop07 = 12
FRAME_stand01 = 13
FRAME_stand02 = 14
FRAME_stand03 = 15
FRAME_stand04 = 16
FRAME_stand05 = 17
FRAME_stand06 = 18
FRAME_stand07 = 19
FRAME_stand08 = 20
FRAME_stand09 = 21
FRAME_stand10 = 22
FRAME_stand11 = 23
FRAME_stand12 = 24
FRAME_stand13 = 25
FRAME_stand14 = 26
FRAME_stand15 = 27
FRAME_stand16 = 28
FRAME_stand17 = 29
FRAME_stand18 = 30
FRAME_stand19 = 31
FRAME_stand20 = 32
FRAME_stand21 = 33
FRAME_stand22 = 34
FRAME_stand23 = 35
FRAME_stand24 = 36
FRAME_stand25 = 37
FRAME_stand26 = 38
FRAME_stand27 = 39
FRAME_stand28 = 40
FRAME_stand29 = 41
FRAME_stand30 = 42
FRAME_stand31 = 43
FRAME_stand32 = 44
FRAME_stand33 = 45
FRAME_stand34 = 46
FRAME_stand35 = 47
FRAME_stand36 = 48
FRAME_stand37 = 49
FRAME_stand38 = 50
FRAME_stand39 = 51
FRAME_stand40 = 52
FRAME_stand41 = 53
FRAME_stand42 = 54
FRAME_stand43 = 55
FRAME_stand44 = 56
FRAME_stand45 = 57
FRAME_attak101 = 58
FRAME_attak102 = 59
FRAME_attak103 = 60
FRAME_attak104 = 61
FRAME_attak105 = 62
FRAME_attak106 = 63
FRAME_attak107 = 64
FRAME_attak108 = 65
FRAME_attak109 = 66
FRAME_attak110 = 67
FRAME_attak111 = 68
FRAME_attak112 = 69
FRAME_attak113 = 70
FRAME_attak114 = 71
FRAME_attak115 = 72
FRAME_attak116 = 73
FRAME_attak117 = 74
FRAME_attak118 = 75
FRAME_attak119 = 76
FRAME_attak120 = 77
FRAME_attak121 = 78
FRAME_attak201 = 79
FRAME_attak202 = 80
FRAME_attak203 = 81
FRAME_attak204 = 82
FRAME_attak205 = 83
FRAME_attak206 = 84
FRAME_attak207 = 85
FRAME_attak208 = 86
FRAME_attak209 = 87
FRAME_attak210 = 88
FRAME_attak211 = 89
FRAME_attak212 = 90
FRAME_attak213 = 91
FRAME_attak214 = 92
FRAME_attak215 = 93
FRAME_attak216 = 94
FRAME_attak217 = 95
FRAME_bankl01 = 96
FRAME_bankl02 = 97
FRAME_bankl03 = 98
FRAME_bankl04 = 99
FRAME_bankl05 = 100
FRAME_bankl06 = 101
FRAME_bankl07 = 102
FRAME_bankr01 = 103
FRAME_bankr02 = 104
FRAME_bankr03 = 105
FRAME_bankr04 = 106
FRAME_bankr05 = 107
FRAME_bankr06 = 108
FRAME_bankr07 = 109
FRAME_rollf01 = 110
FRAME_rollf02 = 111
FRAME_rollf03 = 112
FRAME_rollf04 = 113
FRAME_rollf05 = 114
FRAME_rollf06 = 115
FRAME_rollf07 = 116
FRAME_rollf08 = 117
FRAME_rollf09 = 118
FRAME_rollr01 = 119
FRAME_rollr02 = 120
FRAME_rollr03 = 121
FRAME_rollr04 = 122
FRAME_rollr05 = 123
FRAME_rollr06 = 124
FRAME_rollr07 = 125
FRAME_rollr08 = 126
FRAME_rollr09 = 127
FRAME_defens01 = 128
FRAME_defens02 = 129
FRAME_defens03 = 130
FRAME_defens04 = 131
FRAME_defens05 = 132
FRAME_defens06 = 133
FRAME_pain101 = 134
FRAME_pain102 = 135
FRAME_pain103 = 136
FRAME_pain104 = 137
FRAME_pain105 = 138
FRAME_pain106 = 139
FRAME_pain107 = 140
FRAME_pain108 = 141
FRAME_pain109 = 142
FRAME_pain201 = 143
FRAME_pain202 = 144
FRAME_pain203 = 145
FRAME_pain204 = 146
FRAME_pain301 = 147
FRAME_pain302 = 148
FRAME_pain303 = 149
FRAME_pain304 = 150

MODEL_SCALE = 1.000000

AI_STAND_GROUND = MONSTER_AI_FLAGS.AI_STAND_GROUND.value
nextmove = ACTION_nothing

_sound_sight = 0
_sound_idle = 0
_sound_pain1 = 0
_sound_pain2 = 0
_sound_slash = 0
_sound_sproing = 0
_sound_die = 0


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


def _ai_stand():
    from .g_ai import ai_stand
    return ai_stand


def _ai_walk():
    from .g_ai import ai_walk
    return ai_walk


def _ai_run():
    from .g_ai import ai_run
    return ai_run


def _ai_move():
    from .g_ai import ai_move
    return ai_move


def _ai_charge():
    from .g_ai import ai_charge
    return ai_charge


def flyer_sight(self, other):
    if gi.sound:
        gi.sound(self, _chan_voice(), _sound_sight, 1, _attn_norm(), 0)


def flyer_idle(self):
    if gi.sound:
        gi.sound(self, _chan_voice(), _sound_idle, 1, _attn_idle(), 0)


def flyer_pop_blades(self):
    if gi.sound:
        gi.sound(self, _chan_voice(), _sound_sproing, 1, _attn_norm(), 0)


def flyer_run(self):
    if self.monsterinfo.aiflags & AI_STAND_GROUND:
        self.monsterinfo.currentmove = flyer_move_stand
    else:
        self.monsterinfo.currentmove = flyer_move_run


def flyer_walk(self):
    self.monsterinfo.currentmove = flyer_move_walk


def flyer_stand(self):
    self.monsterinfo.currentmove = flyer_move_stand


def flyer_stop(self):
    self.monsterinfo.currentmove = flyer_move_stop


def flyer_start(self):
    self.monsterinfo.currentmove = flyer_move_start


def flyer_fire(self, flash_number):
    from .q_shared import AngleVectors
    from .g_utils import G_ProjectSource
    from .m_flash import monster_flash_offset
    from .g_monster import monster_fire_blaster

    start = [0.0, 0.0, 0.0]
    forward = [0.0, 0.0, 0.0]
    right = [0.0, 0.0, 0.0]
    end = [0.0, 0.0, 0.0]
    _dir = [0.0, 0.0, 0.0]

    if self.s.frame in (FRAME_attak204, FRAME_attak207, FRAME_attak210):
        effect = EF_HYPERBLASTER
    else:
        effect = 0

    AngleVectors(self.s.angles, forward, right, None)
    G_ProjectSource(self.s.origin, monster_flash_offset[flash_number], forward, right, start)

    if self.enemy:
        end[0] = self.enemy.s.origin[0]
        end[1] = self.enemy.s.origin[1]
        end[2] = self.enemy.s.origin[2] + self.enemy.viewheight
    _dir[0] = end[0] - start[0]
    _dir[1] = end[1] - start[1]
    _dir[2] = end[2] - start[2]

    monster_fire_blaster(self, start, _dir, 1, 1000, flash_number, effect)


def flyer_fireleft(self):
    flyer_fire(self, MZ2_FLYER_BLASTER_1)


def flyer_fireright(self):
    flyer_fire(self, MZ2_FLYER_BLASTER_2)


def flyer_slash_left(self):
    from .g_ai import MELEE_DISTANCE
    from .g_weapon import fire_hit

    aim = [MELEE_DISTANCE, self.mins[0], 0]
    fire_hit(self, aim, 5, 0)
    if gi.sound:
        gi.sound(self, _chan_weapon(), _sound_slash, 1, _attn_norm(), 0)


def flyer_slash_right(self):
    from .g_ai import MELEE_DISTANCE
    from .g_weapon import fire_hit

    aim = [MELEE_DISTANCE, self.maxs[0], 0]
    fire_hit(self, aim, 5, 0)
    if gi.sound:
        gi.sound(self, _chan_weapon(), _sound_slash, 1, _attn_norm(), 0)


def flyer_loop_melee(self):
    self.monsterinfo.currentmove = flyer_move_loop_melee


def flyer_attack(self):
    self.monsterinfo.currentmove = flyer_move_attack2


def flyer_setstart(self):
    global nextmove
    nextmove = ACTION_run
    self.monsterinfo.currentmove = flyer_move_start


def flyer_nextmove(self):
    if nextmove == ACTION_attack1:
        self.monsterinfo.currentmove = flyer_move_start_melee
    elif nextmove == ACTION_attack2:
        self.monsterinfo.currentmove = flyer_move_attack2
    elif nextmove == ACTION_run:
        self.monsterinfo.currentmove = flyer_move_run


def flyer_melee(self):
    self.monsterinfo.currentmove = flyer_move_start_melee


def flyer_check_melee(self):
    from .g_ai import range as ai_range, RANGE_MELEE
    if self.enemy and ai_range(self, self.enemy) == RANGE_MELEE:
        if _random.random() <= 0.8:
            self.monsterinfo.currentmove = flyer_move_loop_melee
        else:
            self.monsterinfo.currentmove = flyer_move_end_melee
    else:
        self.monsterinfo.currentmove = flyer_move_end_melee


def flyer_pain(self, other, kick, damage):
    if self.health < (self.max_health / 2):
        self.s.skinnum = 1

    if level.time < self.pain_debounce_time:
        return

    self.pain_debounce_time = level.time + 3
    if skill and skill.value == 3:
        return

    n = _random.randint(0, 2)
    if n == 0:
        if gi.sound:
            gi.sound(self, _chan_voice(), _sound_pain1, 1, _attn_norm(), 0)
        self.monsterinfo.currentmove = flyer_move_pain1
    elif n == 1:
        if gi.sound:
            gi.sound(self, _chan_voice(), _sound_pain2, 1, _attn_norm(), 0)
        self.monsterinfo.currentmove = flyer_move_pain2
    else:
        if gi.sound:
            gi.sound(self, _chan_voice(), _sound_pain1, 1, _attn_norm(), 0)
        self.monsterinfo.currentmove = flyer_move_pain3


def flyer_die(self, inflictor, attacker, damage, point):
    from .g_misc import BecomeExplosion1
    if gi.sound:
        gi.sound(self, _chan_voice(), _sound_die, 1, _attn_norm(), 0)
    BecomeExplosion1(self)


flyer_frames_stand = [
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, None)
    for _ in range(45)
]
flyer_move_stand = mmove_t(FRAME_stand01, FRAME_stand45, flyer_frames_stand, None)

flyer_frames_walk = [
    mframe_t(lambda s, d: _ai_walk()(s, d), 5, None)
    for _ in range(45)
]
flyer_move_walk = mmove_t(FRAME_stand01, FRAME_stand45, flyer_frames_walk, None)

flyer_frames_run = [
    mframe_t(lambda s, d: _ai_run()(s, d), 10, None)
    for _ in range(45)
]
flyer_move_run = mmove_t(FRAME_stand01, FRAME_stand45, flyer_frames_run, None)

flyer_frames_start = [
    mframe_t(lambda s, d: _ai_move()(s, d), 0, flyer_nextmove if i == 5 else None)
    for i in range(6)
]
flyer_move_start = mmove_t(FRAME_start01, FRAME_start06, flyer_frames_start, None)

flyer_frames_stop = [
    mframe_t(lambda s, d: _ai_move()(s, d), 0, flyer_nextmove if i == 6 else None)
    for i in range(7)
]
flyer_move_stop = mmove_t(FRAME_stop01, FRAME_stop07, flyer_frames_stop, None)

flyer_frames_rollright = [
    mframe_t(lambda s, d: _ai_move()(s, d), 0, None)
    for _ in range(9)
]
flyer_move_rollright = mmove_t(FRAME_rollr01, FRAME_rollr09, flyer_frames_rollright, None)

flyer_frames_rollleft = [
    mframe_t(lambda s, d: _ai_move()(s, d), 0, None)
    for _ in range(9)
]
flyer_move_rollleft = mmove_t(FRAME_rollf01, FRAME_rollf09, flyer_frames_rollleft, None)

flyer_frames_pain3 = [
    mframe_t(lambda s, d: _ai_move()(s, d), 0, None)
    for _ in range(4)
]
flyer_move_pain3 = mmove_t(FRAME_pain301, FRAME_pain304, flyer_frames_pain3, flyer_run)

flyer_frames_pain2 = [
    mframe_t(lambda s, d: _ai_move()(s, d), 0, None)
    for _ in range(4)
]
flyer_move_pain2 = mmove_t(FRAME_pain201, FRAME_pain204, flyer_frames_pain2, flyer_run)

flyer_frames_pain1 = [
    mframe_t(lambda s, d: _ai_move()(s, d), 0, None)
    for _ in range(9)
]
flyer_move_pain1 = mmove_t(FRAME_pain101, FRAME_pain109, flyer_frames_pain1, flyer_run)

flyer_frames_defense = [
    mframe_t(lambda s, d: _ai_move()(s, d), 0, None)
    for _ in range(6)
]
flyer_move_defense = mmove_t(FRAME_defens01, FRAME_defens06, flyer_frames_defense, None)

flyer_frames_bankright = [
    mframe_t(lambda s, d: _ai_move()(s, d), 0, None)
    for _ in range(7)
]
flyer_move_bankright = mmove_t(FRAME_bankr01, FRAME_bankr07, flyer_frames_bankright, None)

flyer_frames_bankleft = [
    mframe_t(lambda s, d: _ai_move()(s, d), 0, None)
    for _ in range(7)
]
flyer_move_bankleft = mmove_t(FRAME_bankl01, FRAME_bankl07, flyer_frames_bankleft, None)

_attack2_d = [0, 0, 0, -10, -10, -10, -10, -10, -10, -10, -10, 0, 0, 0, 0, 0, 0]
_attack2_cb = [
    None, None, None,
    flyer_fireleft, flyer_fireright, flyer_fireleft, flyer_fireright,
    flyer_fireleft, flyer_fireright, flyer_fireleft, flyer_fireright,
    None, None, None, None, None, None,
]
flyer_frames_attack2 = [
    mframe_t(lambda s, d: _ai_charge()(s, d), _attack2_d[i], _attack2_cb[i])
    for i in range(17)
]
flyer_move_attack2 = mmove_t(FRAME_attak201, FRAME_attak217, flyer_frames_attack2, flyer_run)

_start_melee_cb = [flyer_pop_blades, None, None, None, None, None]
flyer_frames_start_melee = [
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, _start_melee_cb[i])
    for i in range(6)
]
flyer_move_start_melee = mmove_t(FRAME_attak101, FRAME_attak106, flyer_frames_start_melee, flyer_loop_melee)

flyer_frames_end_melee = [
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, None)
    for _ in range(3)
]
flyer_move_end_melee = mmove_t(FRAME_attak119, FRAME_attak121, flyer_frames_end_melee, flyer_run)

_loop_melee_cb = [None, None, flyer_slash_left, None, None, None, None, flyer_slash_right, None, None, None, None]
flyer_frames_loop_melee = [
    mframe_t(lambda s, d: _ai_charge()(s, d), 0, _loop_melee_cb[i])
    for i in range(12)
]
flyer_move_loop_melee = mmove_t(FRAME_attak107, FRAME_attak118, flyer_frames_loop_melee, flyer_check_melee)


def SP_monster_flyer(self):
    global _sound_sight, _sound_idle, _sound_pain1, _sound_pain2
    global _sound_slash, _sound_sproing, _sound_die

    from .g_monster import flymonster_start

    if not gi.soundindex:
        return

    _sound_sight = gi.soundindex("flyer/flysght1.wav")
    _sound_idle = gi.soundindex("flyer/flysrch1.wav")
    _sound_pain1 = gi.soundindex("flyer/flypain1.wav")
    _sound_pain2 = gi.soundindex("flyer/flypain2.wav")
    _sound_slash = gi.soundindex("flyer/flyatck2.wav")
    _sound_sproing = gi.soundindex("flyer/flyatck1.wav")
    _sound_die = gi.soundindex("flyer/flydeth1.wav")

    gi.soundindex("flyer/flyatck3.wav")

    if gi.modelindex:
        self.s.modelindex = gi.modelindex("models/monsters/flyer/tris.md2")

    self.mins[:] = [-16.0, -16.0, -24.0]
    self.maxs[:] = [16.0, 16.0, 32.0]
    self.movetype = movetype_t.MOVETYPE_STEP.value
    self.solid = solid_t.SOLID_BBOX.value
    self.s.sound = gi.soundindex("flyer/flyidle1.wav")

    self.health = 50
    self.mass = 50

    self.pain = flyer_pain
    self.die = flyer_die

    self.monsterinfo.stand = flyer_stand
    self.monsterinfo.walk = flyer_walk
    self.monsterinfo.run = flyer_run
    self.monsterinfo.attack = flyer_attack
    self.monsterinfo.melee = flyer_melee
    self.monsterinfo.sight = flyer_sight
    self.monsterinfo.idle = flyer_idle
    self.monsterinfo.currentmove = flyer_move_stand
    self.monsterinfo.scale = MODEL_SCALE

    if gi.linkentity:
        gi.linkentity(self)

    flymonster_start(self)

