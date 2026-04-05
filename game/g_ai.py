import math
import random as _random

from .reference_import import gi
from .global_vars import level
from shared.QEnums import movetype_t, solid_t, damage_t
from shared.QConstants import MASK_SHOT, MASK_SOLID, CONTENTS_SOLID

RANGE_MELEE  = 0
RANGE_NEAR   = 1
RANGE_MID    = 2
RANGE_FAR    = 3

MELEE_DISTANCE = 80
NEAR_DISTANCE  = 500
MID_DISTANCE   = 1000

_sight_client = None
_sight_client_time = 0.0


def AI_SetSightClient():
    """Pick the best player for monsters to track as their sight target."""
    global _sight_client, _sight_client_time
    from .g_main import game as g
    best = None
    best_priority = -1e30

    for i in range(1, g.maxclients + 1):
        if i >= len(g.entities):
            break
        cl = g.entities[i]
        if cl is None or not cl.inuse:
            continue
        if cl.health <= 0:
            continue
        priority = cl.health
        if priority > best_priority:
            best_priority = priority
            best = cl

    _sight_client = best
    _sight_client_time = level.time


def _move_toward_goal(self, dist):
    """Move self toward self.movetarget or self.goalentity by dist units."""
    from .m_move import M_MoveToGoal
    M_MoveToGoal(self, dist)


def ai_move(self, dist):
    """Monster movement — advance dist units toward ideal_yaw."""
    from .m_move import M_MoveToGoal
    M_MoveToGoal(self, dist)


def ai_stand(_self, dist):
    """Monster stand — scan for enemies, only move if told to turn."""
    if dist:
        from .m_move import M_MoveToGoal
        M_MoveToGoal(_self, dist)

    if level.time > _self.monsterinfo.pausetime:
        _self.monsterinfo.stand(_self)
        return

    if _self.spawnflags & 1:  # MONSTER_STAND_GROUND
        if _self.enemy:
            HuntTarget(_self)
        return

    if FindTarget(_self):
        return

    if level.time > _self.monsterinfo.pausetime:
        _self.monsterinfo.walk(_self)
        return

    if not (level.framenum & 15):
        _self.ideal_yaw = _random.uniform(0, 360)


def ai_walk(_self, dist):
    """Monster walk — advance and scan for enemies."""
    _move_toward_goal(_self, dist)
    if FindTarget(_self):
        return


def ai_charge(_self, dist):
    """Monster charge — rush toward enemy."""
    if _self.enemy and _self.enemy.inuse:
        enemy = _self.enemy
        from .g_utils import vectoangles
        v = [
            enemy.s.origin[0] - _self.s.origin[0],
            enemy.s.origin[1] - _self.s.origin[1],
            enemy.s.origin[2] - _self.s.origin[2],
        ]
        angles = [0.0, 0.0, 0.0]
        vectoangles(v, angles)
        _self.ideal_yaw = angles[1]

    if dist:
        from .m_move import M_MoveToGoal
        M_MoveToGoal(_self, dist)


def ai_turn(_self, dist):
    """Monster turn in place."""
    if dist:
        from .m_move import M_MoveToGoal
        M_MoveToGoal(_self, dist)

    if FindTarget(_self):
        return

    _self.ideal_yaw = _random.uniform(0, 360)


def range(_self, other):
    """Return range constant from _self to other."""
    diff = [
        other.s.origin[0] - _self.s.origin[0],
        other.s.origin[1] - _self.s.origin[1],
        other.s.origin[2] - _self.s.origin[2],
    ]
    d = math.sqrt(diff[0]**2 + diff[1]**2 + diff[2]**2)
    if d < MELEE_DISTANCE:
        return RANGE_MELEE
    if d < NEAR_DISTANCE:
        return RANGE_NEAR
    if d < MID_DISTANCE:
        return RANGE_MID
    return RANGE_FAR


def visible(_self, other):
    """Return True if _self has LOS to other."""
    spot1 = [
        _self.s.origin[0],
        _self.s.origin[1],
        _self.s.origin[2] + _self.viewheight,
    ]
    spot2 = [
        other.s.origin[0],
        other.s.origin[1],
        other.s.origin[2] + other.viewheight,
    ]
    tr = gi.trace(spot1, None, None, spot2, _self, MASK_SOLID)
    return tr.fraction == 1.0


def infront(_self, other):
    """Return True if other is in _self's forward hemisphere."""
    from .q_shared import AngleVectors
    forward = [0.0, 0.0, 0.0]
    AngleVectors(_self.s.angles, forward, None, None)
    diff = [
        other.s.origin[0] - _self.s.origin[0],
        other.s.origin[1] - _self.s.origin[1],
        other.s.origin[2] - _self.s.origin[2],
    ]
    length = math.sqrt(diff[0]**2 + diff[1]**2 + diff[2]**2)
    if length > 0:
        diff[0] /= length
        diff[1] /= length
        diff[2] /= length
    dot = forward[0]*diff[0] + forward[1]*diff[1] + forward[2]*diff[2]
    return dot > 0.3


def HuntTarget(_self):
    """Set self.goalentity to enemy and run toward it."""
    _self.goalentity = _self.enemy
    if _self.monsterinfo and _self.monsterinfo.run:
        _self.monsterinfo.run(_self)
    else:
        ai_run(_self, 0)
    from .g_utils import vectoangles
    v = [
        _self.enemy.s.origin[0] - _self.s.origin[0],
        _self.enemy.s.origin[1] - _self.s.origin[1],
        _self.enemy.s.origin[2] - _self.s.origin[2],
    ]
    angles = [0.0, 0.0, 0.0]
    vectoangles(v, angles)
    _self.ideal_yaw = angles[1]


def FoundTarget(_self):
    """Called when monster discovers its enemy."""
    enemy = _self.enemy
    if not enemy or not enemy.inuse:
        return

    _self.show_hostile = level.time + 1
    _self.monsterinfo.last_sighting = list(_self.enemy.s.origin)

    if gi.sound:
        if _self.monsterinfo and _self.monsterinfo.sight:
            _self.monsterinfo.sight(_self, _self.enemy)

    HuntTarget(_self)


def FindTarget(_self):
    """Scan for a visible player enemy. Returns True if found."""
    global _sight_client

    if _self.flags & 0x08:  # FL_NOTARGET
        return False

    if level.time - _sight_client_time > 0.5:
        AI_SetSightClient()

    if _sight_client is None:
        return False

    client = _sight_client
    if not client.inuse or client.health <= 0:
        return False

    if not (level.framenum & 3):  # only check periodically
        if not visible(_self, client):
            return False

    # already fighting this client
    if _self.enemy is client and _self.monsterinfo:
        return True

    _self.enemy = client
    FoundTarget(_self)
    return True


def FacingIdeal(_self):
    """Return True if self is facing its ideal_yaw (within 2 degrees)."""
    delta = _self.s.angles[1] - _self.ideal_yaw
    delta = ((delta + 180) % 360) - 180
    return abs(delta) < 2.0


def M_CheckAttack(_self):
    """Generic monster attack check. Returns True if attacking."""
    if not _self.enemy or not _self.enemy.inuse:
        return False

    enemy_range = range(_self, _self.enemy)
    enemy_yaw = 0.0

    diff = [
        _self.enemy.s.origin[0] - _self.s.origin[0],
        _self.enemy.s.origin[1] - _self.s.origin[1],
        _self.enemy.s.origin[2] - _self.s.origin[2],
    ]
    enemy_yaw = math.degrees(math.atan2(diff[1], diff[0]))

    if _self.monsterinfo.currentmove and _self.monsterinfo.attack_state == 1:  # AS_MELEE
        if _self.monsterinfo.melee:
            _self.monsterinfo.melee(_self)
            return True
        _self.monsterinfo.attack_state = 2  # AS_MISSILE

    if _self.monsterinfo.attack_state == 2:  # AS_MISSILE
        if _self.monsterinfo.attack:
            _self.monsterinfo.attack(_self)
            return True

    if enemy_range == RANGE_FAR:
        return False

    if _self.monsterinfo.checkattack:
        return _self.monsterinfo.checkattack(_self)

    return False


def ai_run_melee(_self):
    """Turn and if facing, do melee attack."""
    _self.ideal_yaw = _self.monsterinfo.ideal_yaw if hasattr(_self.monsterinfo, 'ideal_yaw') else _self.ideal_yaw
    if FacingIdeal(_self):
        _self.monsterinfo.melee(_self)
        _self.monsterinfo.attack_state = 3  # AS_STRAIGHT


def ai_run_missile(_self):
    """Turn and if facing, launch missile."""
    _self.ideal_yaw = _self.monsterinfo.ideal_yaw if hasattr(_self.monsterinfo, 'ideal_yaw') else _self.ideal_yaw
    if FacingIdeal(_self):
        _self.monsterinfo.attack(_self)
        _self.monsterinfo.attack_state = 3  # AS_STRAIGHT


def ai_run_slide(_self, distance):
    """Strafe movement during attack."""
    from .m_move import M_MoveToGoal
    enemy = _self.enemy
    if not enemy:
        _move_toward_goal(_self, distance)
        return

    ofs = _self.monsterinfo.lefty * 90
    diff = [
        enemy.s.origin[0] - _self.s.origin[0],
        enemy.s.origin[1] - _self.s.origin[1],
        0,
    ]
    base_yaw = math.degrees(math.atan2(diff[1], diff[0]))

    _self.ideal_yaw = base_yaw + ofs
    if not M_MoveToGoal(_self, distance):
        _self.monsterinfo.lefty = 1 - _self.monsterinfo.lefty
        M_MoveToGoal(_self, distance)


def ai_checkattack(_self, dist):
    """Check and execute attack logic. Returns True if attacking."""
    if not _self.enemy or not _self.enemy.inuse:
        return False
    if _self.enemy.health <= 0:
        _self.enemy = None
        if _self.monsterinfo and _self.monsterinfo.stand:
            _self.monsterinfo.stand(_self)
        return False

    if level.time >= _self.monsterinfo.attack_finished:
        if M_CheckAttack(_self):
            return True

    return False


def ai_run(_self, dist):
    """Main run AI — advance, check attack, slide."""
    enemy = _self.enemy

    if dist:
        from .m_move import M_MoveToGoal
        M_MoveToGoal(_self, dist)

    if ai_checkattack(_self, dist):
        return

    if not enemy or not enemy.inuse or enemy.health <= 0:
        if not FindTarget(_self):
            if _self.monsterinfo and _self.monsterinfo.walk:
                _self.monsterinfo.walk(_self)
        return

    if not visible(_self, _self.enemy):
        if not FindTarget(_self):
            if _self.monsterinfo and _self.monsterinfo.walk:
                _self.monsterinfo.walk(_self)
        return
