"""Unit tests for game/m_infantry.py"""
import types
import pytest

import game.m_infantry as inf
from shared.QClasses import edict_t, mmove_t, mframe_t, monsterinfo_t


# ── minimal entity factory ─────────────────────────────────────────────────────

def _make_entity():
    e = edict_t()
    e.inuse = True
    e.health = 100
    e.max_health = 100
    e.gib_health = -40
    e.mass = 200
    e.deadflag = 0
    e.takedamage = 0
    e.monsterinfo = monsterinfo_t()
    e.monsterinfo.aiflags = 0
    e.monsterinfo.pausetime = 0.0
    e.monsterinfo.currentmove = None
    e.velocity = [0.0, 0.0, 0.0]
    e.viewheight = 32
    return e


def _patch_gi(monkeypatch):
    """Replace gi callable attributes with no-ops."""
    from game import reference_import as ri
    for attr in ("sound", "soundindex", "linkentity", "modelindex",
                 "WriteByte", "WriteShort", "WritePosition", "WriteDir", "multicast"):
        monkeypatch.setattr(ri.gi, attr, lambda *a, **kw: None, raising=False)
    monkeypatch.setattr(ri.gi, "soundindex", lambda *a: 0, raising=False)
    monkeypatch.setattr(ri.gi, "modelindex", lambda *a: 0, raising=False)


# ── Frame / move-table constants ───────────────────────────────────────────────

def test_frame_constants_order():
    assert inf.FRAME_stand50 < inf.FRAME_stand71
    assert inf.FRAME_walk03  < inf.FRAME_walk14
    assert inf.FRAME_run01   < inf.FRAME_run08
    assert inf.FRAME_pain101 < inf.FRAME_pain110
    assert inf.FRAME_pain201 < inf.FRAME_pain210
    assert inf.FRAME_duck01  < inf.FRAME_duck05
    assert inf.FRAME_death101 < inf.FRAME_death120
    assert inf.FRAME_death201 < inf.FRAME_death225
    assert inf.FRAME_attak101 < inf.FRAME_attak115
    assert inf.FRAME_attak201 < inf.FRAME_attak208


def test_move_table_frame_counts():
    assert len(inf.infantry_frames_stand)   == inf.FRAME_stand71  - inf.FRAME_stand50 + 1
    assert len(inf.infantry_frames_fidget)  == 49   # FRAME_stand01..FRAME_stand49 (49 frames per C source)
    assert len(inf.infantry_frames_walk)    == inf.FRAME_walk14   - inf.FRAME_walk03  + 1
    assert len(inf.infantry_frames_run)     == inf.FRAME_run08    - inf.FRAME_run01   + 1
    assert len(inf.infantry_frames_pain1)   == inf.FRAME_pain110  - inf.FRAME_pain101 + 1
    assert len(inf.infantry_frames_pain2)   == inf.FRAME_pain210  - inf.FRAME_pain201 + 1
    assert len(inf.infantry_frames_duck)    == inf.FRAME_duck05   - inf.FRAME_duck01  + 1
    assert len(inf.infantry_frames_death1)  == inf.FRAME_death120 - inf.FRAME_death101 + 1
    assert len(inf.infantry_frames_death2)  == inf.FRAME_death225 - inf.FRAME_death201 + 1
    assert len(inf.infantry_frames_death3)  == inf.FRAME_death309 - inf.FRAME_death301 + 1
    assert len(inf.infantry_frames_attack1) == inf.FRAME_attak115 - inf.FRAME_attak101 + 1
    assert len(inf.infantry_frames_attack2) == inf.FRAME_attak208 - inf.FRAME_attak201 + 1


def test_mmove_t_fields():
    m = inf.infantry_move_stand
    assert isinstance(m, mmove_t)
    assert m.firstframe == inf.FRAME_stand50
    assert m.lastframe  == inf.FRAME_stand71
    assert m.frame      == inf.infantry_frames_stand
    assert m.endfunc    is None


def test_fidget_move_end_loops_to_stand():
    assert inf.infantry_move_fidget.endfunc is inf.infantry_stand


def test_pain_moves_end_to_run():
    assert inf.infantry_move_pain1.endfunc is inf.infantry_run
    assert inf.infantry_move_pain2.endfunc is inf.infantry_run


def test_duck_move_end_to_run():
    assert inf.infantry_move_duck.endfunc is inf.infantry_run


def test_attack_moves_end_to_run():
    assert inf.infantry_move_attack1.endfunc is inf.infantry_run
    assert inf.infantry_move_attack2.endfunc is inf.infantry_run


def test_death_moves_end_to_dead():
    assert inf.infantry_move_death1.endfunc is inf.infantry_dead
    assert inf.infantry_move_death2.endfunc is inf.infantry_dead
    assert inf.infantry_move_death3.endfunc is inf.infantry_dead


# ── infantry_stand ─────────────────────────────────────────────────────────────

def test_infantry_stand_sets_move():
    e = _make_entity()
    inf.infantry_stand(e)
    assert e.monsterinfo.currentmove is inf.infantry_move_stand


# ── infantry_fidget ────────────────────────────────────────────────────────────

def test_infantry_fidget_sets_move(monkeypatch):
    e = _make_entity()
    _patch_gi(monkeypatch)
    inf.infantry_fidget(e)
    assert e.monsterinfo.currentmove is inf.infantry_move_fidget


# ── infantry_walk ──────────────────────────────────────────────────────────────

def test_infantry_walk_sets_move():
    e = _make_entity()
    inf.infantry_walk(e)
    assert e.monsterinfo.currentmove is inf.infantry_move_walk


# ── infantry_run ───────────────────────────────────────────────────────────────

def test_infantry_run_sets_run_move():
    e = _make_entity()
    e.monsterinfo.aiflags = 0
    inf.infantry_run(e)
    assert e.monsterinfo.currentmove is inf.infantry_move_run


def test_infantry_run_stand_ground():
    e = _make_entity()
    e.monsterinfo.aiflags = inf.AI_STAND_GROUND
    inf.infantry_run(e)
    assert e.monsterinfo.currentmove is inf.infantry_move_stand


# ── infantry_pain ──────────────────────────────────────────────────────────────

def test_infantry_pain_skips_if_debounce(monkeypatch):
    e = _make_entity()
    inf.level.time = 5.0
    e.pain_debounce_time = 10.0
    _patch_gi(monkeypatch)
    inf.infantry_pain(e, None, 0, 10)
    assert e.monsterinfo.currentmove is None


def test_infantry_pain_sets_pain_move_and_debounce(monkeypatch):
    e = _make_entity()
    inf.level.time = 5.0
    e.pain_debounce_time = 0.0
    _patch_gi(monkeypatch)
    inf.infantry_pain(e, None, 0, 10)
    assert e.monsterinfo.currentmove in (inf.infantry_move_pain1, inf.infantry_move_pain2)
    assert e.pain_debounce_time == pytest.approx(8.0)


def test_infantry_pain_skinnum_half_health(monkeypatch):
    e = _make_entity()
    e.health = 49
    e.max_health = 100
    e.pain_debounce_time = 0.0
    inf.level.time = 1.0
    _patch_gi(monkeypatch)
    inf.infantry_pain(e, None, 0, 5)
    assert e.s.skinnum == 1


# ── infantry_sight ─────────────────────────────────────────────────────────────

def test_infantry_sight_callable():
    assert callable(inf.infantry_sight)


def test_infantry_sight_does_not_raise(monkeypatch):
    e = _make_entity()
    _patch_gi(monkeypatch)
    inf.infantry_sight(e, None)


# ── infantry_dead ──────────────────────────────────────────────────────────────

def test_infantry_dead_sets_bbox(monkeypatch):
    e = _make_entity()
    _patch_gi(monkeypatch)
    monkeypatch.setattr("game.g_monster.M_FlyCheck", lambda s: None)
    inf.infantry_dead(e)
    assert e.mins[:] == [-16, -16, -24]
    assert e.maxs[:] == [16, 16, -8]


def test_infantry_dead_sets_deadmonster_flag(monkeypatch):
    e = _make_entity()
    e.svflags = 0
    _patch_gi(monkeypatch)
    monkeypatch.setattr("game.g_monster.M_FlyCheck", lambda s: None)
    inf.infantry_dead(e)
    assert e.svflags & inf.SVF_DEADMONSTER


def test_infantry_dead_sets_toss_movetype(monkeypatch):
    from shared.QEnums import movetype_t
    e = _make_entity()
    _patch_gi(monkeypatch)
    monkeypatch.setattr("game.g_monster.M_FlyCheck", lambda s: None)
    inf.infantry_dead(e)
    assert e.movetype == movetype_t.MOVETYPE_TOSS.value


# ── infantry_die ───────────────────────────────────────────────────────────────

def test_infantry_die_no_double_death(monkeypatch):
    e = _make_entity()
    e.health = 10
    e.deadflag = inf.DEAD_DEAD
    _patch_gi(monkeypatch)
    inf.infantry_die(e, None, None, 10, None)
    assert e.monsterinfo.currentmove is None   # no move was set


def test_infantry_die_sets_dead_move(monkeypatch):
    e = _make_entity()
    e.health = 10
    e.deadflag = 0
    _patch_gi(monkeypatch)
    monkeypatch.setattr("game.g_misc.ThrowGib",  lambda *a: None)
    monkeypatch.setattr("game.g_misc.ThrowHead", lambda *a: None)
    inf.infantry_die(e, None, None, 10, None)
    assert e.monsterinfo.currentmove in (
        inf.infantry_move_death1,
        inf.infantry_move_death2,
        inf.infantry_move_death3,
    )
    assert e.deadflag == inf.DEAD_DEAD


def test_infantry_die_gib_path(monkeypatch):
    e = _make_entity()
    e.health = -100
    e.gib_health = -40
    e.deadflag = 0
    _patch_gi(monkeypatch)
    gibs = []
    monkeypatch.setattr("game.g_misc.ThrowGib",  lambda *a: gibs.append(a[1]))
    monkeypatch.setattr("game.g_misc.ThrowHead", lambda *a: gibs.append("HEAD"))
    inf.infantry_die(e, None, None, 120, None)
    assert e.deadflag == inf.DEAD_DEAD
    assert "HEAD" in gibs


# ── duck / dodge ───────────────────────────────────────────────────────────────

def test_duck_down_sets_ducked_flag(monkeypatch):
    e = _make_entity()
    e.maxs = [16.0, 16.0, 32.0]
    e.monsterinfo.aiflags = 0
    _patch_gi(monkeypatch)
    inf.level.time = 1.0
    inf.infantry_duck_down(e)
    assert e.monsterinfo.aiflags & inf.AI_DUCKED
    assert e.maxs[2] == pytest.approx(0.0)


def test_duck_down_idempotent(monkeypatch):
    e = _make_entity()
    e.maxs = [16.0, 16.0, 32.0]
    e.monsterinfo.aiflags = inf.AI_DUCKED
    _patch_gi(monkeypatch)
    inf.infantry_duck_down(e)
    assert e.maxs[2] == pytest.approx(32.0)   # not changed again


def test_duck_hold_sets_hold_frame(monkeypatch):
    e = _make_entity()
    e.monsterinfo.aiflags = 0
    e.monsterinfo.pausetime = 100.0
    inf.level.time = 1.0
    inf.infantry_duck_hold(e)
    assert e.monsterinfo.aiflags & inf.AI_HOLD_FRAME


def test_duck_hold_clears_hold_frame_when_time_up(monkeypatch):
    e = _make_entity()
    e.monsterinfo.aiflags = inf.AI_HOLD_FRAME
    e.monsterinfo.pausetime = 0.0
    inf.level.time = 5.0
    inf.infantry_duck_hold(e)
    assert not (e.monsterinfo.aiflags & inf.AI_HOLD_FRAME)


def test_duck_up_clears_ducked(monkeypatch):
    e = _make_entity()
    e.maxs = [16.0, 16.0, 0.0]
    e.monsterinfo.aiflags = inf.AI_DUCKED
    _patch_gi(monkeypatch)
    inf.infantry_duck_up(e)
    assert not (e.monsterinfo.aiflags & inf.AI_DUCKED)
    assert e.maxs[2] == pytest.approx(32.0)
    assert e.takedamage == inf.DAMAGE_AIM


def test_infantry_dodge_usually_skips(monkeypatch):
    e = _make_entity()
    import random
    monkeypatch.setattr(random, "random", lambda: 0.9)
    inf.infantry_dodge(e, None, 0.5)
    assert e.monsterinfo.currentmove is None


def test_infantry_dodge_sometimes_ducks(monkeypatch):
    e = _make_entity()
    import random
    monkeypatch.setattr(random, "random", lambda: 0.0)
    attacker = _make_entity()
    inf.infantry_dodge(e, attacker, 0.5)
    assert e.monsterinfo.currentmove is inf.infantry_move_duck
    assert e.enemy is attacker


# ── cock / fire ────────────────────────────────────────────────────────────────

def test_cock_gun_sets_pausetime(monkeypatch):
    e = _make_entity()
    _patch_gi(monkeypatch)
    inf.level.time = 0.0
    inf.infantry_cock_gun(e)
    assert e.monsterinfo.pausetime > 0.0


def test_infantry_fire_holds_frame_when_not_expired(monkeypatch):
    e = _make_entity()
    e.monsterinfo.aiflags = 0
    e.monsterinfo.pausetime = 999.0
    inf.level.time = 0.0
    called = []
    monkeypatch.setattr(inf, "InfantryMachineGun", lambda s: called.append(s))
    inf.infantry_fire(e)
    assert e.monsterinfo.aiflags & inf.AI_HOLD_FRAME
    assert len(called) == 1


def test_infantry_fire_clears_hold_when_expired(monkeypatch):
    e = _make_entity()
    e.monsterinfo.aiflags = inf.AI_HOLD_FRAME
    e.monsterinfo.pausetime = 0.0
    inf.level.time = 5.0
    monkeypatch.setattr(inf, "InfantryMachineGun", lambda s: None)
    inf.infantry_fire(e)
    assert not (e.monsterinfo.aiflags & inf.AI_HOLD_FRAME)


# ── attack dispatcher ──────────────────────────────────────────────────────────

def test_infantry_attack_melee_range(monkeypatch):
    e = _make_entity()
    enemy = _make_entity()
    e.enemy = enemy
    e.s.origin[:] = [0.0, 0.0, 0.0]
    enemy.s.origin[:] = [10.0, 0.0, 0.0]   # well within MELEE_DISTANCE (80)
    inf.infantry_attack(e)
    assert e.monsterinfo.currentmove is inf.infantry_move_attack2


def test_infantry_attack_ranged(monkeypatch):
    e = _make_entity()
    enemy = _make_entity()
    e.enemy = enemy
    e.s.origin[:] = [0.0, 0.0, 0.0]
    enemy.s.origin[:] = [600.0, 0.0, 0.0]   # beyond NEAR_DISTANCE(500)
    inf.infantry_attack(e)
    assert e.monsterinfo.currentmove is inf.infantry_move_attack1


# ── smack / swing ──────────────────────────────────────────────────────────────

def test_infantry_swing_callable():
    assert callable(inf.infantry_swing)


def test_infantry_swing_no_raise(monkeypatch):
    e = _make_entity()
    _patch_gi(monkeypatch)
    inf.infantry_swing(e)


# ── SP_monster_infantry ────────────────────────────────────────────────────────

def test_sp_monster_infantry_sets_stats(monkeypatch):
    e = _make_entity()
    _patch_gi(monkeypatch)
    monkeypatch.setattr("game.g_monster.walkmonster_start", lambda s: None)
    inf.SP_monster_infantry(e)
    assert e.health      == 100
    assert e.gib_health  == -40
    assert e.mass        == 200
    assert e.pain        is inf.infantry_pain
    assert e.die         is inf.infantry_die


def test_sp_monster_infantry_sets_monsterinfo(monkeypatch):
    e = _make_entity()
    _patch_gi(monkeypatch)
    monkeypatch.setattr("game.g_monster.walkmonster_start", lambda s: None)
    inf.SP_monster_infantry(e)
    mi = e.monsterinfo
    assert mi.stand  is inf.infantry_stand
    assert mi.walk   is inf.infantry_walk
    assert mi.run    is inf.infantry_run
    assert mi.dodge  is inf.infantry_dodge
    assert mi.attack is inf.infantry_attack
    assert mi.sight  is inf.infantry_sight
    assert mi.idle   is inf.infantry_fidget
    assert mi.currentmove is inf.infantry_move_stand


def test_sp_monster_infantry_calls_walkmonster_start(monkeypatch):
    e = _make_entity()
    _patch_gi(monkeypatch)
    started = []
    monkeypatch.setattr("game.g_monster.walkmonster_start", lambda s: started.append(s))
    inf.SP_monster_infantry(e)
    assert started == [e]


def test_sp_monster_infantry_bbox(monkeypatch):
    e = _make_entity()
    _patch_gi(monkeypatch)
    monkeypatch.setattr("game.g_monster.walkmonster_start", lambda s: None)
    inf.SP_monster_infantry(e)
    assert e.mins[:] == [-16.0, -16.0, -24.0]
    assert e.maxs[:] == [ 16.0,  16.0,  32.0]
