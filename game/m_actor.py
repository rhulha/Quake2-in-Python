from wrapper_qpy.decorators import TODO
from wrapper_qpy.custom_classes import Mutable
from .reference_import import gi
from wrapper_qpy.linker import LinkEmptyFunctions
from shared.QEnums import MONSTER_AI_FLAGS
from .global_vars import level


LinkEmptyFunctions(globals(), [])


actor_names = [
    "Hellrot",
    "Tokay",
    "Killme",
    "Disruptor",
    "Adrianator",
    "Rambear",
    "Titus",
    "Bitterman"
]
MAX_ACTOR_NAMES = len(actor_names)

def actor_stand():
    return


def actor_walk():
    return


def actor_run():
    return


def actor_pain():
    return


def actorMachineGun():
    return


def actor_dead():
    return


def actor_die():
    return


def actor_fire(_self):
    actorMachineGun(_self)
    if level.time >= _self.monsterinfo.pausetime:
        _self.monsterinfo.aiflags &= ~MONSTER_AI_FLAGS.AI_HOLD_FRAME
    else:
        _self.monsterinfo.aiflags &= MONSTER_AI_FLAGS.AI_HOLD_FRAME


def actor_attack():
    return


def actor_use():
    return


def SP_misc_actor():
    return


def target_actor_touch():
    return


def SP_target_actor():
    return

