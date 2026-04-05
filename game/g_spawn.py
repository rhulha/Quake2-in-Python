import math

from .reference_import import gi
from .global_vars import level
from shared.QEnums import movetype_t, solid_t
from shared.QClasses import edict_t
from shared.QConstants import MAX_EDICTS, PRINT_HIGH


def _game():
    from .g_main import game
    return game


# Spawn function registry — populated by register_spawn / auto-built from game modules.
_spawn_map = {}


def _build_spawn_map():
    """Gather all SP_xxx functions from game modules."""
    if _spawn_map:
        return
    from . import (g_misc, g_func, g_trigger, g_target,
                   g_items, p_client)
    for ns in [g_misc, g_func, g_trigger, g_target, g_items, p_client]:
        for name, fn in vars(ns).items():
            if name.startswith("SP_") and callable(fn):
                key = name[3:]  # drop "SP_"
                _spawn_map[key] = fn
    # Also add monster modules
    _add_monsters()


def _add_monsters():
    """Register monster SP_ functions."""
    monster_modules = [
        "m_actor", "m_berserk", "m_boss2", "m_boss3",
        "m_boss31", "m_boss32", "m_brain", "m_chick",
        "m_flipper", "m_float", "m_flyer", "m_gladiator",
        "m_gunner", "m_hover", "m_infantry", "m_insane",
        "m_medic", "m_mutant", "m_parasite", "m_soldier",
        "m_supertank", "m_tank",
    ]
    import importlib
    for mod_name in monster_modules:
        try:
            mod = importlib.import_module("." + mod_name, package="game")
            for name, fn in vars(mod).items():
                if name.startswith("SP_") and callable(fn):
                    _spawn_map[name[3:]] = fn
        except Exception:
            pass


def ED_CallSpawn(ent):
    """Look up and call the spawn function for ent.classname."""
    _build_spawn_map()

    if not ent.classname:
        if gi.dprintf:
            gi.dprintf("ED_CallSpawn: no classname\n")
        from .g_utils import G_FreeEdict
        G_FreeEdict(ent)
        return

    fn = _spawn_map.get(ent.classname)
    if fn:
        fn(ent)
        return

    # Check if it is an item
    from .g_items import FindItemByClassname, SpawnItem
    item = FindItemByClassname(ent.classname)
    if item:
        SpawnItem(ent, item)
        return

    if gi.dprintf:
        gi.dprintf("%s doesn't have a spawn function\n" % ent.classname)
    from .g_utils import G_FreeEdict
    G_FreeEdict(ent)


def ED_NewString(string):
    """Return a copy of string (trivial in Python)."""
    return str(string) if string else ""


def ED_ParseField(key, value, ent):
    """Set a field on ent by key=value (from BSP entity lump)."""
    # Vector fields stored as "x y z" strings
    _vector_fields = {
        "origin", "angles", "velocity", "avelocity",
        "mins", "maxs", "movedir", "pos1", "pos2",
    }
    _float_fields = {
        "angle", "speed", "accel", "decel", "wait", "delay",
        "random", "yaw_speed", "mass", "gravity", "health",
        "max_health", "gib_health", "dmg", "volume", "attenuation",
        "lip", "height", "distance", "knockback", "pathdist",
        "dmg_radius", "radius", "count", "skill",
    }
    _int_fields = {
        "spawnflags", "style", "sounds",
    }

    if key == "classname":
        ent.classname = value
        return
    if key == "targetname":
        ent.targetname = value
        return
    if key == "target":
        ent.target = value
        return
    if key == "killtarget":
        ent.killtarget = value
        return
    if key == "message":
        ent.message = value
        return
    if key == "team":
        ent.team = value
        return
    if key == "model":
        ent.model = value
        return
    if key == "deathtarget":
        ent.deathtarget = value
        return
    if key == "combattarget":
        ent.combattarget = value
        return
    if key == "map":
        ent.map = value
        return
    if key == "pathtarget":
        ent.pathtarget = value
        return

    if key in _vector_fields:
        parts = value.split()
        try:
            vec = [float(p) for p in parts]
        except ValueError:
            return
        if hasattr(ent, key):
            attr = getattr(ent, key)
            for i in range(min(len(vec), len(attr))):
                attr[i] = vec[i]
        elif key == "origin" and hasattr(ent, 's'):
            for i in range(min(len(vec), 3)):
                ent.s.origin[i] = vec[i]
        return

    if key in _float_fields:
        try:
            setattr(ent, key, float(value))
        except (ValueError, AttributeError):
            pass
        return

    if key in _int_fields:
        try:
            setattr(ent, key, int(float(value)))
        except (ValueError, AttributeError):
            pass
        return

    # Fallback: try to set directly
    try:
        setattr(ent, key, value)
    except AttributeError:
        pass


def ED_ParseEdict(data, ent):
    """Parse one entity block from the BSP entity string.
    data is the remaining string (starting after '{').
    Returns the remaining string after '}'.
    """
    import re
    # parse key-value pairs until '}'
    pos = 0
    while pos < len(data):
        # skip whitespace
        while pos < len(data) and data[pos] in ' \t\r\n':
            pos += 1
        if pos >= len(data):
            break
        if data[pos] == '}':
            pos += 1
            break
        if data[pos] == '{':
            # nested block — skip (shouldn't happen in entity strings)
            pos += 1
            continue
        if data[pos] != '"':
            # advance past unquoted token
            while pos < len(data) and data[pos] not in ' \t\r\n"{}':
                pos += 1
            continue
        # read quoted key
        pos += 1
        key_start = pos
        while pos < len(data) and data[pos] != '"':
            pos += 1
        key = data[key_start:pos]
        if pos < len(data):
            pos += 1

        # skip whitespace
        while pos < len(data) and data[pos] in ' \t\r\n':
            pos += 1

        if pos >= len(data) or data[pos] != '"':
            continue
        pos += 1
        val_start = pos
        while pos < len(data) and data[pos] != '"':
            pos += 1
        value = data[val_start:pos]
        if pos < len(data):
            pos += 1

        if key == "origin":
            # Special handling: set both ent.s.origin and ent.origin
            parts = value.split()
            try:
                vec = [float(p) for p in parts]
                for i in range(min(len(vec), 3)):
                    ent.s.origin[i] = vec[i]
                    ent.origin[i] = vec[i]
            except (ValueError, IndexError):
                pass
        else:
            ED_ParseField(key, value, ent)

    return data[pos:]


def G_FindTeams():
    """Link entities that share a team field."""
    g = _game()
    for ent in g.entities:
        if ent is None or not ent.inuse:
            continue
        if not ent.team:
            continue
        if ent.flags & 0x01:  # FL_TEAMSLAVE
            continue
        # this entity is the team master
        chain = ent
        ent.teammaster = ent
        c = 0
        for other in g.entities:
            if other is None or not other.inuse:
                continue
            if other is ent:
                continue
            if not other.team or other.team != ent.team:
                continue
            if other.flags & 0x01:  # FL_TEAMSLAVE
                continue
            c += 1
            chain.teamchain = other
            other.teammaster = ent
            other.flags |= 0x01  # FL_TEAMSLAVE
            chain = other
        if c:
            pass  # optional debug print


def SpawnEntities(mapname, entities, spawnpoint):
    """Parse entities string and spawn all entities."""
    from .g_utils import G_InitEdict, G_Spawn
    from .g_main import game as g

    level.mapname = mapname

    # Ensure world entity (slot 0) is initialized
    world = g.entities[0]
    if world is None:
        world = edict_t()
        world.index = 0
        g.entities[0] = world
    G_InitEdict(world)
    world.classname = "worldspawn"
    world.solid = solid_t.SOLID_BSP
    world.movetype = movetype_t.MOVETYPE_PUSH
    gi.linkentity(world)

    inhibit = 0
    data = entities

    # Check for coop / single player inhibit (skill filtering)
    skill_val = 1
    if gi.cvar:
        try:
            skill_val = int(float(gi.cvar('skill', '1', 0).value))
        except Exception:
            skill_val = 1

    while True:
        # Find next '{'
        idx = data.find('{')
        if idx < 0:
            break
        data = data[idx + 1:]

        ent = G_Spawn()

        # Parse key-value pairs into ent
        data = ED_ParseEdict(data, ent)

        # Apply angle shorthand
        if hasattr(ent, 'angle') and ent.angle and ent.angles[1] == 0:
            ent.angles[1] = ent.angle

        # Inhibit entities with skill/notarget flags
        if ent.spawnflags & (0x00000100 | 0x00000200 | 0x00000400 | 0x00000800):
            spawnflag_mask = 1 << (skill_val + 7)
            if ent.spawnflags & spawnflag_mask:
                from .g_utils import G_FreeEdict
                G_FreeEdict(ent)
                inhibit += 1
                continue

        ED_CallSpawn(ent)

    if gi.dprintf:
        gi.dprintf("%i entities inhibited.\n" % inhibit)

    G_FindTeams()


def SP_worldspawn(ent):
    """Process worldspawn entity — set sky, music, gravity, etc."""
    ent.movetype = movetype_t.MOVETYPE_PUSH
    ent.solid = solid_t.SOLID_BSP
    ent.inuse = True

    if gi.configstring:
        gi.configstring(1, "quake2")  # CS_NAME
        gi.configstring(2, level.mapname)  # CS_CDTRACK (approximate)

    if ent.gravity and gi.cvar_set:
        gi.cvar_set("sv_gravity", str(ent.gravity))

    gi.linkentity(ent)
