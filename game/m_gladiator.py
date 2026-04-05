from wrapper_qpy.decorators import TODO
from wrapper_qpy.custom_classes import Mutable
from .reference_import import gi
from wrapper_qpy.linker import LinkEmptyFunctions
from .m_flash import monster_flash_offset
from shared.QConstants import MZ2_GLADIATOR_RAILGUN_1


LinkEmptyFunctions(globals(), ["AngleVectors", "G_ProjectSource", "_VectorSubtract", "VectorNormalize"])


def gladiator_idle():
    return


def gladiator_sight():
    return


def gladiator_search():
    return


def gladiator_cleaver_swing():
    return


def gladiator_stand():
    return


def gladiator_walk():
    return


def gladiator_run():
    return


def GaldiatorMelee():
    return


def gladiator_melee():
    return


def GladiatorGun(_self):
    start = [0, 0, 0]
    _dir = [0, 0, 0]
    forward = [0, 0, 0]
    right = [0, 0, 0]
    AngleVectors(_self.s.angles, forward, right, None)
    G_ProjectSource(_self.s.origin, monster_flash_offset[MZ2_GLADIATOR_RAILGUN_1], forward, right, start)
    _VectorSubtract(_self.pos1, start, _dir)
    VectorNormalize(_dir)
    monster_fire_railgun(_self, start, _dir, 50, 100, MZ2_GLADIATOR_RAILGUN_1)


def gladiator_attack():
    return


def gladiator_pain():
    return


def gladiator_dead():
    return


def gladiator_die():
    return


def SP_monster_gladiator():
    return


from .q_shared import AngleVectors, _VectorSubtract, VectorNormalize
from .g_utils import G_ProjectSource
from .g_monster import monster_fire_railgun

