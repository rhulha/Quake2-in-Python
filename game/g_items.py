import math
import random as _random

from .reference_import import gi
from .global_vars import level
from shared.QEnums import movetype_t, solid_t, damage_t, multicast_t
from shared.QConstants import EF_ROTATE, EF_GIB, MAX_ITEMS

# Item flags
IT_WEAPON      = 1
IT_AMMO        = 2
IT_ARMOR       = 4
IT_STAY_COOP   = 8
IT_KEY         = 16
IT_POWERUP     = 32

# Armor types
ARMOR_NONE   = 0
ARMOR_JACKET = 1
ARMOR_COMBAT = 2
ARMOR_BODY   = 3
ARMOR_SHARD  = 4

# Power armor types
POWER_ARMOR_NONE    = 0
POWER_ARMOR_SCREEN  = 1
POWER_ARMOR_SHIELD  = 2

# Item index constants (matching Quake 2's ordering)
ITEM_ARMOR_SHARD  = 0
ITEM_ARMOR_JACKET = 1
ITEM_ARMOR_COMBAT = 2
ITEM_ARMOR_BODY   = 3
ITEM_POWER_SCREEN = 4
ITEM_POWER_SHIELD = 5

HEALTH_IGNORE_MAX = 1
HEALTH_TIMED      = 2


class ArmorInfo:
    def __init__(self, normal_protection, energy_protection, base_count, max_count, armor_type):
        self.normal_protection  = normal_protection
        self.energy_protection  = energy_protection
        self.base_count         = base_count
        self.max_count          = max_count
        self.armor_type         = armor_type


ARMOR_INFO = {
    ARMOR_JACKET: ArmorInfo(0.30, 0.00, 25, 50,  ARMOR_JACKET),
    ARMOR_COMBAT: ArmorInfo(0.60, 0.30, 50, 100, ARMOR_COMBAT),
    ARMOR_BODY:   ArmorInfo(0.80, 0.60, 75, 200, ARMOR_BODY),
}

_itemlist = []


def _build_itemlist():
    """Build the global item list (called once at startup)."""
    from shared.QClasses import gitem_t
    items = []

    def add(classname, pickup, use, drop, pickup_sound, world_model, view_model,
            icon, pickup_name, count_width, quantity, ammo, flags,
            precaches="", tag=0):
        it = gitem_t()
        it.classname   = classname
        it.pickup       = pickup
        it.use          = use
        it.drop         = drop
        it.pickup_sound = pickup_sound
        it.world_model  = world_model
        it.view_model   = view_model
        it.icon         = icon
        it.pickup_name  = pickup_name
        it.count_width  = count_width
        it.quantity     = quantity
        it.ammo         = ammo
        it.flags        = flags
        it.index        = len(items)
        items.append(it)
        return it

    # Armor / health items
    add("item_armor_shard",   Pickup_Armor,     None, None,
        "misc/ar1_pkup.wav",  "models/items/armor/shard/tris.md2", None,
        "i_aRMOR",            "Armor Shard",    3,  2,   None, IT_ARMOR, tag=ARMOR_SHARD)

    add("item_armor_jacket",  Pickup_Armor,     None, Drop_Armor,
        "misc/ar1_pkup.wav",  "models/items/armor/jacket/tris.md2", None,
        "i_JACKET_armor",     "Jacket Armor",   3,  25,  None, IT_ARMOR, tag=ARMOR_JACKET)

    add("item_armor_combat",  Pickup_Armor,     None, Drop_Armor,
        "misc/ar1_pkup.wav",  "models/items/armor/combat/tris.md2", None,
        "i_COMBAT_armor",     "Combat Armor",   3,  50,  None, IT_ARMOR, tag=ARMOR_COMBAT)

    add("item_armor_body",    Pickup_Armor,     None, Drop_Armor,
        "misc/ar1_pkup.wav",  "models/items/armor/body/tris.md2", None,
        "i_BODY_armor",       "Body Armor",     3,  75,  None, IT_ARMOR, tag=ARMOR_BODY)

    add("item_power_screen",  Pickup_PowerArmor,Use_PowerArmor, Drop_PowerArmor,
        "misc/ar3_pkup.wav",  "models/items/armor/screen/tris.md2", None,
        "i_POWER_screen",     "Power Screen",   0,  0,   None, IT_ARMOR, tag=POWER_ARMOR_SCREEN)

    add("item_power_shield",  Pickup_PowerArmor,Use_PowerArmor, Drop_PowerArmor,
        "misc/ar3_pkup.wav",  "models/items/armor/shield/tris.md2", None,
        "i_POWER_shield",     "Power Shield",   0,  0,   None, IT_ARMOR, tag=POWER_ARMOR_SHIELD)

    # Ammo
    add("ammo_shells",        Pickup_Ammo,   None, Drop_Ammo,
        "misc/am_pkup.wav",   "models/items/ammo/shells/medium/tris.md2", None,
        "a_shells",           "Shells",           3, 10, None, IT_AMMO)

    add("ammo_bullets",       Pickup_Ammo,   None, Drop_Ammo,
        "misc/am_pkup.wav",   "models/items/ammo/bullets/medium/tris.md2", None,
        "a_bullets",          "Bullets",          3, 50, None, IT_AMMO)

    add("ammo_grenades",      Pickup_Ammo,   None, Drop_Ammo,
        "misc/am_pkup.wav",   "models/items/ammo/grenades/medium/tris.md2", None,
        "a_grenades",         "Grenades",         3, 5,  None, IT_AMMO)

    add("ammo_rockets",       Pickup_Ammo,   None, Drop_Ammo,
        "misc/am_pkup.wav",   "models/items/ammo/rockets/medium/tris.md2", None,
        "a_rockets",          "Rockets",          3, 5,  None, IT_AMMO)

    add("ammo_cells",         Pickup_Ammo,   None, Drop_Ammo,
        "misc/am_pkup.wav",   "models/items/ammo/cells/medium/tris.md2", None,
        "a_cells",            "Cells",            3, 50, None, IT_AMMO)

    add("ammo_slugs",         Pickup_Ammo,   None, Drop_Ammo,
        "misc/am_pkup.wav",   "models/items/ammo/slugs/medium/tris.md2", None,
        "a_slugs",            "Slugs",            3, 10, None, IT_AMMO)

    # Health
    add("item_health_small",  Pickup_Health, None, None,
        "items/pkup.wav",     "models/items/healing/stimpack/tris.md2", None,
        "i_health",           "Small Health",     3, 2,  None, 0)

    add("item_health",        Pickup_Health, None, None,
        "items/pkup.wav",     "models/items/healing/medium/tris.md2", None,
        "i_health",           "Health",           3, 10, None, 0)

    add("item_health_large",  Pickup_Health, None, None,
        "items/pkup.wav",     "models/items/healing/large/tris.md2", None,
        "i_health",           "Large Health",     3, 25, None, 0)

    add("item_health_mega",   Pickup_Health, None, None,
        "items/pkup.wav",     "models/items/healing/megahealth/tris.md2", None,
        "i_health",           "Mega Health",      3, 100,None, HEALTH_TIMED|HEALTH_IGNORE_MAX)

    # Powerups
    add("item_quad",          Pickup_Powerup, Use_Quad, Drop_General,
        "items/pkup.wav",     "models/items/quaddama/tris.md2", None,
        "p_quad",             "Quad Damage",      2, 60, None, IT_POWERUP)

    add("item_invulnerability",Pickup_Powerup,Use_Invulnerability, Drop_General,
        "items/pkup.wav",     "models/items/invulner/tris.md2", None,
        "p_invulnerability",  "Invulnerability",  2, 300,None, IT_POWERUP)

    add("item_silencer",      Pickup_Powerup, Use_Silencer, Drop_General,
        "items/pkup.wav",     "models/items/silencer/tris.md2", None,
        "p_silencer",         "Silencer",         2, 60, None, IT_POWERUP)

    add("item_breather",      Pickup_Powerup, Use_Breather, Drop_General,
        "items/pkup.wav",     "models/items/breather/tris.md2", None,
        "p_rebreather",       "Rebreather",       2, 30, None, IT_POWERUP)

    add("item_enviro",        Pickup_Powerup, Use_Envirosuit, Drop_General,
        "items/pkup.wav",     "models/items/envirosuit/tris.md2", None,
        "p_envirosuit",       "Environment Suit", 2, 30, None, IT_POWERUP)

    add("item_adrenaline",    Pickup_Adrenaline, None, None,
        "items/pkup.wav",     "models/items/adrenal/tris.md2", None,
        "p_adrenaline",       "Adrenaline",       0, 0,  None, 0)

    add("item_ancient_head",  Pickup_AncientHead, None, None,
        "items/pkup.wav",     "models/items/c_head/tris.md2", None,
        "i_ancient_head",     "Ancient Head",     0, 0,  None, 0)

    add("item_bandolier",     Pickup_Bandolier, None, None,
        "items/pkup.wav",     "models/items/band/tris.md2", None,
        "p_bandolier",        "Bandolier",        0, 0,  None, 0)

    add("item_pack",          Pickup_Pack, None, None,
        "items/pkup.wav",     "models/items/pack/tris.md2", None,
        "i_pack",             "Ammo Pack",        0, 0,  None, 0)

    # Keys
    add("key_data_cd",        Pickup_Key, None, Drop_General,
        "items/pkup.wav",     "models/items/keys/data_cd/tris.md2", None,
        "k_datacd",           "Data CD",          0, 0,  None, IT_STAY_COOP|IT_KEY)
    add("key_power_cube",     Pickup_Key, None, Drop_General,
        "items/pkup.wav",     "models/items/keys/power/tris.md2", None,
        "k_powercube",        "Power Cube",       0, 0,  None, IT_STAY_COOP|IT_KEY)
    add("key_pyramid",        Pickup_Key, None, Drop_General,
        "items/pkup.wav",     "models/items/keys/pyramid/tris.md2", None,
        "k_pyramid",          "Pyramid Key",      0, 0,  None, IT_STAY_COOP|IT_KEY)
    add("key_data_spinner",   Pickup_Key, None, Drop_General,
        "items/pkup.wav",     "models/items/keys/spinner/tris.md2", None,
        "k_dataspin",         "Data Spinner",     0, 0,  None, IT_STAY_COOP|IT_KEY)
    add("key_pass",           Pickup_Key, None, Drop_General,
        "items/pkup.wav",     "models/items/keys/pass/tris.md2", None,
        "k_security",         "Security Pass",    0, 0,  None, IT_STAY_COOP|IT_KEY)
    add("key_blue_key",       Pickup_Key, None, Drop_General,
        "items/pkup.wav",     "models/items/keys/key/tris.md2", None,
        "k_bluekey",          "Blue Key",         0, 0,  None, IT_STAY_COOP|IT_KEY)
    add("key_red_key",        Pickup_Key, None, Drop_General,
        "items/pkup.wav",     "models/items/keys/red_key/tris.md2", None,
        "k_redkey",           "Red Key",          0, 0,  None, IT_STAY_COOP|IT_KEY)
    add("key_commander_head", Pickup_Key, None, Drop_General,
        "items/pkup.wav",     "models/monsters/commandr/head/tris.md2", None,
        "k_comhead",          "Commander's Head", 0, 0,  None, IT_STAY_COOP|IT_KEY)
    add("key_airstrike_target",Pickup_Key, None, Drop_General,
        "items/pkup.wav",     "models/items/keys/target/tris.md2", None,
        "i_airstrike",        "Airstrike Marker", 0, 0,  None, IT_STAY_COOP|IT_KEY)

    return items


def GetItemByIndex(index):
    if not _itemlist:
        _itemlist.extend(_build_itemlist())
    if 0 <= index < len(_itemlist):
        return _itemlist[index]
    return None


def FindItemByClassname(classname):
    if not _itemlist:
        _itemlist.extend(_build_itemlist())
    for item in _itemlist:
        if item.classname == classname:
            return item
    return None


def FindItem(pickup_name):
    if not _itemlist:
        _itemlist.extend(_build_itemlist())
    for item in _itemlist:
        if item.pickup_name == pickup_name:
            return item
    return None


def DoRespawn(ent):
    """Make item visible again after respawn delay."""
    ent.svflags &= ~0x04  # SVF_NOCLIENT
    ent.solid = solid_t.SOLID_TRIGGER
    gi.linkentity(ent)
    ent.s.event = 1  # EV_ITEM_RESPAWN


def SetRespawn(ent, delay):
    """Schedule DoRespawn after delay seconds."""
    ent.flags |= 0x01  # FL_RESPAWN
    ent.svflags |= 0x04  # SVF_NOCLIENT
    ent.solid = solid_t.SOLID_NOT
    gi.linkentity(ent)
    ent.think = DoRespawn
    ent.nextthink = level.time + delay


def Pickup_Powerup(ent, other):
    quantity = other.client.pers.inventory[ent.item.index] if other.client else 0
    other.client.pers.inventory[ent.item.index] += ent.item.quantity
    if gi.sound:
        gi.sound(other, 0, gi.soundindex(ent.item.pickup_sound) if gi.soundindex else 0, 1, 1, 0)
    if ent.item.use:
        ent.item.use(other, ent.item)
    return True


def Drop_General(ent, item):
    Drop_Item(ent, item)
    ent.client.pers.inventory[item.index] -= 1


def Pickup_Adrenaline(ent, other):
    if not other.client:
        return False
    if other.max_health < 150:
        other.max_health += 1
    if other.health < other.max_health:
        other.health = other.max_health
    if gi.sound and gi.soundindex:
        gi.sound(other, 0, gi.soundindex(ent.item.pickup_sound), 1, 1, 0)
    return True


def Pickup_AncientHead(ent, other):
    if not other.client:
        return False
    other.max_health += 2
    if gi.sound and gi.soundindex:
        gi.sound(other, 0, gi.soundindex(ent.item.pickup_sound), 1, 1, 0)
    return True


def Pickup_Bandolier(ent, other):
    if not other.client:
        return False
    client = other.client
    if gi.sound and gi.soundindex:
        gi.sound(other, 0, gi.soundindex(ent.item.pickup_sound), 1, 1, 0)
    # expand ammo maxima
    if hasattr(client.pers, 'max_bullets') and client.pers.max_bullets < 250:
        client.pers.max_bullets = 250
    if hasattr(client.pers, 'max_shells') and client.pers.max_shells < 150:
        client.pers.max_shells = 150
    if hasattr(client.pers, 'max_cells') and client.pers.max_cells < 250:
        client.pers.max_cells = 250
    if hasattr(client.pers, 'max_slugs') and client.pers.max_slugs < 75:
        client.pers.max_slugs = 75
    return True


def Pickup_Pack(ent, other):
    if not other.client:
        return False
    if gi.sound and gi.soundindex:
        gi.sound(other, 0, gi.soundindex(ent.item.pickup_sound), 1, 1, 0)
    return True


def Use_Quad(ent, item):
    if not ent.client:
        return
    ent.client.quad_framenum = level.framenum + 300
    if gi.sound and gi.soundindex:
        gi.sound(ent, 0, gi.soundindex("items/damage.wav"), 1, 1, 0)
    ent.client.pers.inventory[item.index] -= 1


def Use_Breather(ent, item):
    if not ent.client:
        return
    ent.client.breather_framenum = level.framenum + 300
    if gi.sound and gi.soundindex:
        gi.sound(ent, 0, gi.soundindex("items/airout.wav"), 1, 1, 0)
    ent.client.pers.inventory[item.index] -= 1


def Use_Envirosuit(ent, item):
    if not ent.client:
        return
    ent.client.enviro_framenum = level.framenum + 300
    if gi.sound and gi.soundindex:
        gi.sound(ent, 0, gi.soundindex("items/airout.wav"), 1, 1, 0)
    ent.client.pers.inventory[item.index] -= 1


def Use_Invulnerability(ent, item):
    if not ent.client:
        return
    ent.client.invincible_framenum = level.framenum + 300
    if gi.sound and gi.soundindex:
        gi.sound(ent, 0, gi.soundindex("items/protect.wav"), 1, 1, 0)
    ent.client.pers.inventory[item.index] -= 1


def Use_Silencer(ent, item):
    if not ent.client:
        return
    ent.client.silencer_shots += 30
    ent.client.pers.inventory[item.index] -= 1


def Pickup_Key(ent, other):
    if not other.client:
        return False
    other.client.pers.inventory[ent.item.index] = 1
    if gi.sound and gi.soundindex:
        gi.sound(other, 0, gi.soundindex(ent.item.pickup_sound), 1, 1, 0)
    return True


def Add_Ammo(ent, item, count):
    """Add count ammo of item type to ent. Returns True if picked up."""
    if not ent.client:
        return False
    max_val = 200  # default
    index = item.index
    if ent.client.pers.inventory[index] >= max_val:
        return False
    ent.client.pers.inventory[index] += count
    if ent.client.pers.inventory[index] > max_val:
        ent.client.pers.inventory[index] = max_val
    return True


def Pickup_Ammo(ent, other):
    if not other.client:
        return False
    count = ent.item.quantity
    if ent.count:
        count = ent.count
    if not Add_Ammo(other, ent.item, count):
        return False
    if gi.sound and gi.soundindex:
        gi.sound(other, 0, gi.soundindex(ent.item.pickup_sound), 1, 1, 0)
    return True


def Drop_Ammo(ent, item):
    dropped = Drop_Item(ent, item)
    if dropped:
        dropped.count = item.quantity
    if ent.client and ent.client.pers.inventory[item.index] > 0:
        ent.client.pers.inventory[item.index] -= item.quantity
        if ent.client.pers.inventory[item.index] < 0:
            ent.client.pers.inventory[item.index] = 0


def MegaHealth_think(_self):
    """Tick down MegaHealth above max health."""
    if _self.owner and _self.owner.health > _self.owner.max_health:
        _self.nextthink = level.time + 1
        _self.owner.health -= 1
    else:
        if gi.sound and _self.owner:
            pass  # optionally play drain sound
        from .g_utils import G_FreeEdict
        G_FreeEdict(_self)


def Pickup_Health(ent, other):
    if not other.client:
        return False
    flags = ent.item.flags if isinstance(ent.item.flags, int) else 0
    if not (flags & HEALTH_IGNORE_MAX):
        if other.health >= other.max_health:
            return False
    if flags & HEALTH_TIMED:
        # spawn a think entity to drain mega health back
        from .g_utils import G_Spawn
        t = G_Spawn()
        t.classname = "temp_entity"
        t.movetype = movetype_t.MOVETYPE_NONE
        t.solid = solid_t.SOLID_NOT
        t.owner = other
        t.nextthink = level.time + 5
        t.think = MegaHealth_think
        gi.linkentity(t)

    if other.health < 0:
        other.health = 0
    other.health += ent.item.quantity
    if not (flags & HEALTH_IGNORE_MAX) and other.health > other.max_health:
        other.health = other.max_health
    if gi.sound and gi.soundindex:
        gi.sound(other, 0, gi.soundindex(ent.item.pickup_sound), 1, 1, 0)
    return True


def ArmorIndex(ent):
    """Return inventory index of best armor, or -1 if none."""
    if not ent.client:
        return -1
    inv = ent.client.pers.inventory
    for idx in [ITEM_ARMOR_BODY, ITEM_ARMOR_COMBAT, ITEM_ARMOR_JACKET]:
        if inv[idx] > 0:
            return idx
    return -1


def Pickup_Armor(ent, other):
    if not other.client:
        return False
    item = ent.item

    # Shard: add 2, cap at 200
    if item.flags & IT_ARMOR and item.index == ITEM_ARMOR_SHARD:
        index = ArmorIndex(other)
        if index < 0:
            index = ITEM_ARMOR_JACKET
        other.client.pers.inventory[index] += 2
        if other.client.pers.inventory[index] > 200:
            other.client.pers.inventory[index] = 200
        if gi.sound and gi.soundindex:
            gi.sound(other, 0, gi.soundindex(item.pickup_sound), 1, 1, 0)
        return True

    # Real armor — keep best
    current_index = ArmorIndex(other)
    if current_index >= 0:
        if current_index > item.index:
            return False  # wearing better armor

    count = item.quantity if hasattr(item, 'quantity') and item.quantity else 25
    if current_index >= 0:
        other.client.pers.inventory[current_index] = 0
    other.client.pers.inventory[item.index] = count
    if gi.sound and gi.soundindex:
        gi.sound(other, 0, gi.soundindex(item.pickup_sound), 1, 1, 0)
    return True


def Drop_Armor(ent, item):
    if not ent.client:
        return
    dropped = Drop_Item(ent, item)
    if dropped:
        dropped.count = ent.client.pers.inventory[item.index]
    ent.client.pers.inventory[item.index] = 0


def PowerArmorType(ent):
    """Return the type of power armor this entity has equipped."""
    if not ent.client:
        return POWER_ARMOR_NONE
    if ent.client.pers.inventory[ITEM_POWER_SHIELD] > 0:
        if ent.flags & 0x20:  # FL_POWER_ARMOR
            return POWER_ARMOR_SHIELD
    if ent.client.pers.inventory[ITEM_POWER_SCREEN] > 0:
        if ent.flags & 0x20:
            return POWER_ARMOR_SCREEN
    return POWER_ARMOR_NONE


def Use_PowerArmor(ent, item):
    if not ent.client:
        return
    if ent.flags & 0x20:  # FL_POWER_ARMOR — toggle off
        ent.flags &= ~0x20
        if gi.sound and gi.soundindex:
            gi.sound(ent, 0, gi.soundindex("misc/power2.wav"), 1, 1, 0)
    else:
        if ent.client.pers.inventory[item.index] <= 0:
            if gi.cprintf:
                gi.cprintf(ent, 2, "No power cells!\n")
            return
        ent.flags |= 0x20
        if gi.sound and gi.soundindex:
            gi.sound(ent, 0, gi.soundindex("misc/power1.wav"), 1, 1, 0)


def Pickup_PowerArmor(ent, other):
    if not other.client:
        return False
    other.client.pers.inventory[ent.item.index] += ent.item.quantity
    if gi.sound and gi.soundindex:
        gi.sound(other, 0, gi.soundindex(ent.item.pickup_sound), 1, 1, 0)
    if not (other.flags & 0x20):
        Use_PowerArmor(other, ent.item)
    return True


def Drop_PowerArmor(ent, item):
    if not ent.client:
        return
    if ent.flags & 0x20:
        Use_PowerArmor(ent, item)
    dropped = Drop_Item(ent, item)
    if dropped:
        dropped.count = ent.client.pers.inventory[item.index]
    ent.client.pers.inventory[item.index] = 0


def Touch_Item(ent, other, plane, surf):
    """Generic item touch callback."""
    if not other.client:
        return
    if other.health <= 0:
        return
    if not ent.item:
        return
    if not ent.item.pickup:
        return

    taken = ent.item.pickup(ent, other)
    if not taken:
        return

    # Print pickup message
    if gi.cprintf and ent.item.pickup_name:
        gi.cprintf(other, 2, "Picked up the %s\n" % ent.item.pickup_name)

    # Respawn or free
    if ent.flags & 0x01:  # FL_RESPAWN
        SetRespawn(ent, 30)
    else:
        from .g_utils import G_FreeEdict
        G_FreeEdict(ent)


def drop_temp_touch(ent, other, plane, surf):
    """Dropped item: don't let the dropper pick it up immediately."""
    if other is ent.owner:
        return
    Touch_Item(ent, other, plane, surf)


def drop_make_touchable(ent):
    """Allow dropped item to be picked up now (1 second after drop)."""
    ent.touch = Touch_Item
    if ent.flags & 0x01:
        ent.think = _FreeEdict_think
        ent.nextthink = level.time + 29


def _FreeEdict_think(ent):
    from .g_utils import G_FreeEdict
    G_FreeEdict(ent)


def Drop_Item(ent, item):
    """Physically drop an item entity at ent's feet."""
    from .g_utils import G_Spawn
    from .q_shared import AngleVectors

    dropped = G_Spawn()
    dropped.classname = item.classname
    dropped.item      = item
    dropped.spawnflags = 1  # DROPPED_ITEM

    dropped.s.effects = 0
    dropped.s.renderfx = 0x08  # RF_GLOW
    dropped.mins[:] = [-15, -15, -15]
    dropped.maxs[:] = [ 15,  15,  15]

    if item.world_model:
        dropped.s.modelindex = gi.modelindex(item.world_model) if gi.modelindex else 0

    dropped.solid = solid_t.SOLID_TRIGGER
    dropped.movetype = movetype_t.MOVETYPE_TOSS
    dropped.touch = drop_temp_touch
    dropped.owner = ent

    forward = [0.0, 0.0, 0.0]
    right   = [0.0, 0.0, 0.0]
    AngleVectors(ent.s.angles, forward, right, None)
    dropped.s.origin[:] = [
        ent.s.origin[0] + forward[0] * 24,
        ent.s.origin[1] + forward[1] * 24,
        ent.s.origin[2] - 16,
    ]
    dropped.velocity[:] = [
        forward[0] * 100 + right[0] * (_random.uniform(-10, 10)),
        forward[1] * 100 + right[1] * (_random.uniform(-10, 10)),
        200,
    ]
    dropped.think = drop_make_touchable
    dropped.nextthink = level.time + 1.0

    gi.linkentity(dropped)
    return dropped


def Use_Item(ent, other, activator):
    """Use-targeted item: toggle the item's solid state."""
    ent.svflags &= ~0x04  # SVF_NOCLIENT
    ent.use = None
    if ent.spawnflags & 2:  # ITEM_TRIGGER_SPAWN
        ent.solid = solid_t.SOLID_TRIGGER
    gi.linkentity(ent)


def droptofloor(ent):
    """Drop item to the floor."""
    end = [ent.s.origin[0], ent.s.origin[1], ent.s.origin[2] - 128]
    tr = gi.trace(ent.s.origin, ent.mins, ent.maxs, end, ent, 1)  # MASK_SOLID
    if tr.startsolid:
        from .g_utils import G_FreeEdict
        G_FreeEdict(ent)
        return
    ent.s.origin[:] = list(tr.endpos)
    gi.linkentity(ent)


def PrecacheItem(it):
    """Precache all assets for an item."""
    if not it:
        return
    if it.pickup_sound and gi.soundindex:
        gi.soundindex(it.pickup_sound)
    if it.world_model and gi.modelindex:
        gi.modelindex(it.world_model)
    if it.view_model and gi.modelindex:
        gi.modelindex(it.view_model)
    if it.icon and gi.imageindex:
        gi.imageindex(it.icon)


def SpawnItem(ent, item):
    """Configure ent as a world item pickup."""
    PrecacheItem(item)

    if ent.spawnflags:
        if ent.classname != "key_power_cube":
            ent.spawnflags &= ~3
            if gi.dprintf:
                gi.dprintf("%s at (%g %g %g) has invalid spawnflags set\n" % (
                    ent.classname, ent.s.origin[0], ent.s.origin[1], ent.s.origin[2]))

    if item.flags & IT_ARMOR:
        ent.item = item

    ent.item   = item
    ent.touch  = Touch_Item
    ent.movetype = movetype_t.MOVETYPE_TOSS
    ent.solid  = solid_t.SOLID_TRIGGER
    ent.s.effects |= EF_ROTATE
    ent.s.renderfx |= 0x200  # RF_GLOW

    ent.mins[:] = [-15, -15, -15]
    ent.maxs[:] =  [15,  15,  15]

    if item.world_model and gi.modelindex:
        ent.s.modelindex = gi.modelindex(item.world_model)

    ent.think = droptofloor
    ent.nextthink = level.time + 0.2
    gi.linkentity(ent)


def SP_item_health(_self):
    _self.item = FindItemByClassname("item_health")
    SpawnItem(_self, _self.item)


def SP_item_health_small(_self):
    _self.item = FindItemByClassname("item_health_small")
    SpawnItem(_self, _self.item)


def SP_item_health_large(_self):
    _self.item = FindItemByClassname("item_health_large")
    SpawnItem(_self, _self.item)


def SP_item_health_mega(_self):
    _self.item = FindItemByClassname("item_health_mega")
    SpawnItem(_self, _self.item)


def InitItems():
    """Populate item list."""
    global _itemlist
    if not _itemlist:
        _itemlist.extend(_build_itemlist())


def SetItemNames():
    """Register item names with the server config strings."""
    InitItems()
    for item in _itemlist:
        if item.pickup_name and gi.configstring:
            gi.configstring(2048 + item.index, item.pickup_name)
