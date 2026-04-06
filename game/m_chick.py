import random as _random

from .reference_import import gi
from .global_vars import level, skill
from shared.QClasses import mmove_t, mframe_t
from shared.QEnums import movetype_t, solid_t, damage_t, MONSTER_AI_FLAGS
from shared.QConstants import MZ2_CHICK_ROCKET_1, SVF_DEADMONSTER

FRAME_attak101 = 0
FRAME_attak113 = 12
FRAME_attak114 = 13
FRAME_attak127 = 26
FRAME_attak128 = 27
FRAME_attak132 = 31
FRAME_attak201 = 32
FRAME_attak203 = 34
FRAME_attak204 = 35
FRAME_attak212 = 43
FRAME_attak213 = 44
FRAME_attak216 = 47
FRAME_death101 = 48
FRAME_death112 = 59
FRAME_death201 = 60
FRAME_death223 = 82
FRAME_duck01 = 83
FRAME_duck07 = 89
FRAME_pain101 = 90
FRAME_pain105 = 94
FRAME_pain201 = 95
FRAME_pain205 = 99
FRAME_pain301 = 100
FRAME_pain321 = 120
FRAME_stand101 = 121
FRAME_stand130 = 150
FRAME_stand201 = 151
FRAME_stand230 = 180
FRAME_walk01 = 181
FRAME_walk10 = 190
FRAME_walk11 = 191
FRAME_walk20 = 200

MODEL_SCALE = 1.0
DEAD_DEAD = 2
GIB_ORGANIC = 0
DAMAGE_YES = damage_t.DAMAGE_YES.value
DAMAGE_AIM = 2
AI_STAND_GROUND = MONSTER_AI_FLAGS.AI_STAND_GROUND.value
AI_DUCKED = MONSTER_AI_FLAGS.AI_DUCKED.value
AI_HOLD_FRAME = MONSTER_AI_FLAGS.AI_HOLD_FRAME.value

_sound_missile_prelaunch = 0
_sound_missile_launch = 0
_sound_melee_swing = 0
_sound_melee_hit = 0
_sound_missile_reload = 0
_sound_death1 = 0
_sound_death2 = 0
_sound_fall_down = 0
_sound_idle1 = 0
_sound_idle2 = 0
_sound_pain1 = 0
_sound_pain2 = 0
_sound_pain3 = 0
_sound_sight = 0
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


def ChickMoan(self):
    if not gi.sound:
        return
    if _random.random() < 0.5:
        gi.sound(self, _chan_voice(), _sound_idle1, 1, _attn_idle(), 0)
    else:
        gi.sound(self, _chan_voice(), _sound_idle2, 1, _attn_idle(), 0)


def chick_fidget(self):
    if self.monsterinfo.aiflags & AI_STAND_GROUND:
        return
    if _random.random() <= 0.3:
        self.monsterinfo.currentmove = chick_move_fidget


def chick_stand(self):
    self.monsterinfo.currentmove = chick_move_stand


def chick_walk(self):
    self.monsterinfo.currentmove = chick_move_walk


def chick_run(self):
    if self.monsterinfo.aiflags & AI_STAND_GROUND:
        self.monsterinfo.currentmove = chick_move_stand
        return

    if (self.monsterinfo.currentmove is chick_move_walk or
            self.monsterinfo.currentmove is chick_move_start_run):
        self.monsterinfo.currentmove = chick_move_run
    else:
        self.monsterinfo.currentmove = chick_move_start_run


def chick_pain(self, other, kick, damage):
    if self.health < (self.max_health / 2):
        self.s.skinnum = 1

    if level.time < self.pain_debounce_time:
        return

    self.pain_debounce_time = level.time + 3

    if gi.sound:
        r = _random.random()
        if r < 0.33:
            gi.sound(self, _chan_voice(), _sound_pain1, 1, _attn_norm(), 0)
        elif r < 0.66:
            gi.sound(self, _chan_voice(), _sound_pain2, 1, _attn_norm(), 0)
        else:
            gi.sound(self, _chan_voice(), _sound_pain3, 1, _attn_norm(), 0)

    if skill and skill.value == 3:
        return

    if damage <= 10:
        self.monsterinfo.currentmove = chick_move_pain1
    elif damage <= 25:
        self.monsterinfo.currentmove = chick_move_pain2
    else:
        self.monsterinfo.currentmove = chick_move_pain3


def chick_dead(self):
    self.mins[:] = [-16.0, -16.0, 0.0]
    self.maxs[:] = [16.0, 16.0, 16.0]
    self.movetype = movetype_t.MOVETYPE_TOSS.value
    self.svflags |= SVF_DEADMONSTER
    self.nextthink = 0
    if gi.linkentity:
        gi.linkentity(self)


def chick_die(self, inflictor, attacker, damage, point):
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

    if _random.randint(0, 1) == 0:
        self.monsterinfo.currentmove = chick_move_death1
        if gi.sound:
            gi.sound(self, _chan_voice(), _sound_death1, 1, _attn_norm(), 0)
    else:
        self.monsterinfo.currentmove = chick_move_death2
        if gi.sound:
            gi.sound(self, _chan_voice(), _sound_death2, 1, _attn_norm(), 0)


def chick_duck_down(self):
    if self.monsterinfo.aiflags & AI_DUCKED:
        return
    self.monsterinfo.aiflags |= AI_DUCKED
    self.maxs[2] -= 32
    self.takedamage = DAMAGE_YES
    self.monsterinfo.pausetime = level.time + 1
    if gi.linkentity:
        gi.linkentity(self)


def chick_duck_hold(self):
    if level.time >= self.monsterinfo.pausetime:
        self.monsterinfo.aiflags &= ~AI_HOLD_FRAME
    else:
        self.monsterinfo.aiflags |= AI_HOLD_FRAME


def chick_duck_up(self):
    self.monsterinfo.aiflags &= ~AI_DUCKED
    self.maxs[2] += 32
    self.takedamage = DAMAGE_AIM
    if gi.linkentity:
        gi.linkentity(self)


def chick_dodge(self, attacker, eta):
    if _random.random() > 0.25:
        return
    if not self.enemy:
        self.enemy = attacker
    self.monsterinfo.currentmove = chick_move_duck


def ChickSlash(self):
    from .g_ai import MELEE_DISTANCE
    from .g_weapon import fire_hit

    aim = [MELEE_DISTANCE, self.mins[0], 10]
    if gi.sound:
        gi.sound(self, _chan_weapon(), _sound_melee_swing, 1, _attn_norm(), 0)
    fire_hit(self, aim, 10 + _random.randint(0, 5), 100)


def ChickRocket(self):
    if not self.enemy:
        return
    from .q_shared import AngleVectors, VectorNormalize
    from .g_utils import G_ProjectSource
    from .g_monster import monster_fire_rocket
    from .m_flash import monster_flash_offset

    forward = [0.0, 0.0, 0.0]
    right = [0.0, 0.0, 0.0]
    start = [0.0, 0.0, 0.0]
    vec = [self.enemy.s.origin[0], self.enemy.s.origin[1], self.enemy.s.origin[2] + self.enemy.viewheight]
    _dir = [0.0, 0.0, 0.0]

    AngleVectors(self.s.angles, forward, right, None)
    G_ProjectSource(self.s.origin, monster_flash_offset[MZ2_CHICK_ROCKET_1], forward, right, start)

    _dir[0] = vec[0] - start[0]
    _dir[1] = vec[1] - start[1]
    _dir[2] = vec[2] - start[2]
    VectorNormalize(_dir)

    monster_fire_rocket(self, start, _dir, 50, 500, MZ2_CHICK_ROCKET_1)


def Chick_PreAttack1(self):
    if gi.sound:
        gi.sound(self, _chan_voice(), _sound_missile_prelaunch, 1, _attn_norm(), 0)


def ChickReload(self):
    if gi.sound:
        gi.sound(self, _chan_voice(), _sound_missile_reload, 1, _attn_norm(), 0)


def chick_rerocket(self):
    if self.enemy and self.enemy.health > 0:
        from .g_ai import range as ai_range, RANGE_MELEE, visible
        if ai_range(self, self.enemy) > RANGE_MELEE:
            if visible(self, self.enemy) and _random.random() <= 0.6:
                self.monsterinfo.currentmove = chick_move_attack1
                return
    self.monsterinfo.currentmove = chick_move_end_attack1


def chick_attack1(self):
    self.monsterinfo.currentmove = chick_move_attack1


def chick_reslash(self):
    if self.enemy and self.enemy.health > 0:
        from .g_ai import range as ai_range, RANGE_MELEE
        if ai_range(self, self.enemy) == RANGE_MELEE:
            if _random.random() <= 0.9:
                self.monsterinfo.currentmove = chick_move_slash
            else:
                self.monsterinfo.currentmove = chick_move_end_slash
            return
    self.monsterinfo.currentmove = chick_move_end_slash


def chick_slash(self):
    self.monsterinfo.currentmove = chick_move_slash


def chick_melee(self):
    self.monsterinfo.currentmove = chick_move_start_slash


def chick_attack(self):
    self.monsterinfo.currentmove = chick_move_start_attack1


def chick_sight(self, other):
    if gi.sound:
        gi.sound(self, _chan_voice(), _sound_sight, 1, _attn_norm(), 0)


chick_frames_fidget = [
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, ChickMoan if i == 8 else None)
    for i in range(30)
]
chick_move_fidget = mmove_t(FRAME_stand201, FRAME_stand230, chick_frames_fidget, chick_stand)

chick_frames_stand = [
    mframe_t(lambda s, d: _ai_stand()(s, d), 0, chick_fidget if i == 29 else None)
    for i in range(30)
]
chick_move_stand = mmove_t(FRAME_stand101, FRAME_stand130, chick_frames_stand, None)

_start_run_d = [1, 0, 0, -1, -1, 0, 1, 3, 6, 3]
chick_frames_start_run = [
    mframe_t(lambda s, d: _ai_run()(s, d), _start_run_d[i], None)
    for i in range(10)
]
chick_move_start_run = mmove_t(FRAME_walk01, FRAME_walk10, chick_frames_start_run, chick_run)

_run_d = [6, 8, 13, 5, 7, 4, 11, 5, 9, 7]
chick_frames_run = [
    mframe_t(lambda s, d: _ai_run()(s, d), _run_d[i], None)
    for i in range(10)
]
chick_move_run = mmove_t(FRAME_walk11, FRAME_walk20, chick_frames_run, None)

chick_frames_walk = [
    mframe_t(lambda s, d: _ai_walk()(s, d), _run_d[i], None)
    for i in range(10)
]
chick_move_walk = mmove_t(FRAME_walk11, FRAME_walk20, chick_frames_walk, None)

chick_frames_pain1 = [mframe_t(lambda s, d: _ai_move()(s, d), 0, None) for _ in range(5)]
chick_move_pain1 = mmove_t(FRAME_pain101, FRAME_pain105, chick_frames_pain1, chick_run)

chick_frames_pain2 = [mframe_t(lambda s, d: _ai_move()(s, d), 0, None) for _ in range(5)]
chick_move_pain2 = mmove_t(FRAME_pain201, FRAME_pain205, chick_frames_pain2, chick_run)

_pain3_d = [0, 0, -6, 3, 11, 3, 0, 0, 4, 1, 0, -3, -4, 5, 7, -2, 3, -5, -2, -8, 2]
chick_frames_pain3 = [
    mframe_t(lambda s, d: _ai_move()(s, d), _pain3_d[i], None)
    for i in range(21)
]
chick_move_pain3 = mmove_t(FRAME_pain301, FRAME_pain321, chick_frames_pain3, chick_run)

_death2_d = [-6, 0, -1, -5, 0, -1, -2, 1, 10, 2, 3, 1, 2, 0, 3, 3, 1, -3, -5, 4, 15, 14, 1]
chick_frames_death2 = [
    mframe_t(lambda s, d: _ai_move()(s, d), _death2_d[i], None)
    for i in range(23)
]
chick_move_death2 = mmove_t(FRAME_death201, FRAME_death223, chick_frames_death2, chick_dead)

_death1_d = [0, 0, -7, 4, 11, 0, 0, 0, 0, 0, 0, 0]
chick_frames_death1 = [
    mframe_t(lambda s, d: _ai_move()(s, d), _death1_d[i], None)
    for i in range(12)
]
chick_move_death1 = mmove_t(FRAME_death101, FRAME_death112, chick_frames_death1, chick_dead)

_duck_d = [0, 1, 4, -4, -5, 3, 1]
_duck_cb = [chick_duck_down, None, chick_duck_hold, None, chick_duck_up, None, None]
chick_frames_duck = [
    mframe_t(lambda s, d: _ai_move()(s, d), _duck_d[i], _duck_cb[i])
    for i in range(7)
]
chick_move_duck = mmove_t(FRAME_duck01, FRAME_duck07, chick_frames_duck, chick_run)

_start_attack1_d = [0, 0, 0, 4, 0, -3, 3, 5, 7, 0, 0, 0, 0]
_start_attack1_cb = [Chick_PreAttack1] + [None] * 11 + [chick_attack1]
chick_frames_start_attack1 = [
    mframe_t(lambda s, d: _ai_charge()(s, d), _start_attack1_d[i], _start_attack1_cb[i])
    for i in range(13)
]
chick_move_start_attack1 = mmove_t(FRAME_attak101, FRAME_attak113, chick_frames_start_attack1, None)

_attack1_d = [19, -6, -5, -2, -7, 0, 1, 10, 4, 5, 6, 6, 4, 3]
_attack1_cb = [ChickRocket, None, None, None, None, None, None, ChickReload, None, None, None, None, None, chick_rerocket]
chick_frames_attack1 = [
    mframe_t(lambda s, d: _ai_charge()(s, d), _attack1_d[i], _attack1_cb[i])
    for i in range(14)
]
chick_move_attack1 = mmove_t(FRAME_attak114, FRAME_attak127, chick_frames_attack1, None)

_end_attack1_d = [-3, 0, -6, -4, -2]
chick_frames_end_attack1 = [
    mframe_t(lambda s, d: _ai_charge()(s, d), _end_attack1_d[i], None)
    for i in range(5)
]
chick_move_end_attack1 = mmove_t(FRAME_attak128, FRAME_attak132, chick_frames_end_attack1, chick_run)

_slash_d = [1, 7, -7, 1, -1, 1, 0, 1, -2]
_slash_cb = [None, ChickSlash, None, None, None, None, None, None, chick_reslash]
chick_frames_slash = [
    mframe_t(lambda s, d: _ai_charge()(s, d), _slash_d[i], _slash_cb[i])
    for i in range(9)
]
chick_move_slash = mmove_t(FRAME_attak204, FRAME_attak212, chick_frames_slash, None)

_end_slash_d = [-6, -1, -6, 0]
chick_frames_end_slash = [
    mframe_t(lambda s, d: _ai_charge()(s, d), _end_slash_d[i], None)
    for i in range(4)
]
chick_move_end_slash = mmove_t(FRAME_attak213, FRAME_attak216, chick_frames_end_slash, chick_run)

_start_slash_d = [1, 8, 3]
chick_frames_start_slash = [
    mframe_t(lambda s, d: _ai_charge()(s, d), _start_slash_d[i], None)
    for i in range(3)
]
chick_move_start_slash = mmove_t(FRAME_attak201, FRAME_attak203, chick_frames_start_slash, chick_slash)


def SP_monster_chick(self):
    global _sound_missile_prelaunch, _sound_missile_launch, _sound_melee_swing, _sound_melee_hit
    global _sound_missile_reload, _sound_death1, _sound_death2, _sound_fall_down
    global _sound_idle1, _sound_idle2, _sound_pain1, _sound_pain2, _sound_pain3
    global _sound_sight, _sound_search

    from .g_monster import walkmonster_start

    if gi.soundindex:
        _sound_missile_prelaunch = gi.soundindex("chick/chkatck1.wav")
        _sound_missile_launch = gi.soundindex("chick/chkatck2.wav")
        _sound_melee_swing = gi.soundindex("chick/chkatck3.wav")
        _sound_melee_hit = gi.soundindex("chick/chkatck4.wav")
        _sound_missile_reload = gi.soundindex("chick/chkatck5.wav")
        _sound_death1 = gi.soundindex("chick/chkdeth1.wav")
        _sound_death2 = gi.soundindex("chick/chkdeth2.wav")
        _sound_fall_down = gi.soundindex("chick/chkfall1.wav")
        _sound_idle1 = gi.soundindex("chick/chkidle1.wav")
        _sound_idle2 = gi.soundindex("chick/chkidle2.wav")
        _sound_pain1 = gi.soundindex("chick/chkpain1.wav")
        _sound_pain2 = gi.soundindex("chick/chkpain2.wav")
        _sound_pain3 = gi.soundindex("chick/chkpain3.wav")
        _sound_sight = gi.soundindex("chick/chksght1.wav")
        _sound_search = gi.soundindex("chick/chksrch1.wav")

    self.movetype = movetype_t.MOVETYPE_STEP.value
    self.solid = solid_t.SOLID_BBOX.value
    if gi.modelindex:
        self.s.modelindex = gi.modelindex("models/monsters/bitch/tris.md2")
    self.mins[:] = [-16.0, -16.0, 0.0]
    self.maxs[:] = [16.0, 16.0, 56.0]

    self.health = 175
    self.gib_health = -70
    self.mass = 200

    self.pain = chick_pain
    self.die = chick_die

    self.monsterinfo.stand = chick_stand
    self.monsterinfo.walk = chick_walk
    self.monsterinfo.run = chick_run
    self.monsterinfo.dodge = chick_dodge
    self.monsterinfo.attack = chick_attack
    self.monsterinfo.melee = chick_melee
    self.monsterinfo.sight = chick_sight
    self.monsterinfo.scale = MODEL_SCALE
    self.monsterinfo.currentmove = chick_move_stand

    if gi.linkentity:
        gi.linkentity(self)

    walkmonster_start(self)

