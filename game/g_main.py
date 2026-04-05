"""
g_main.py - Quake 2 game logic main
Handles game initialization, entity spawning, and game frame execution
"""

import re
from wrapper_qpy.decorators import va_args, TODO
from shared.QEnums import ERROR_LVL
from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), ["Com_Printf", "Com_Error", "Cvar_Get", "Cmd_AddCommand"])

# ===== Game State =====

class GameState:
    def __init__(self):
        self.level = None
        self.maxclients = 1
        self.maxentities = 1024
        self.entities = []
        self.time = 0.0
        self.warmuptime = 0
        self.intermissiontime = 0
        self.exitintermission = False


game = GameState()

# ===== API Import =====

class GameImport:
    """Game import interface (callback functions from engine)"""
    def __init__(self):
        self.error = None
        self.dprintf = None
        self.debug_graph = None
        self.trace = None
        self.pointcontents = None
        self.inlinemodel = None
        self.setmodel = None
        self.sound = None
        self.positioned_sound = None
        self.unicast = None
        self.multicast = None
        self.writedata = None
        self.bprintf = None
        self.spritetrail = None
        self.gunindex = None
        self.configstring = None
        self.image = None
        self.client_print = None
        self.centerprintf = None


gi = GameImport()


# ===== Initialization =====

def G_Init():
    """Initialize game"""
    try:
        from ..quake2.common import Com_Printf, Cvar_Get, Cmd_AddCommand

        Com_Printf("G_Init()\n")

        # Register game cvars
        deathmatch = Cvar_Get("deathmatch", "0", 0)
        coop = Cvar_Get("coop", "0", 0)
        fraglimit = Cvar_Get("fraglimit", "0", 0)
        timelimit = Cvar_Get("timelimit", "0", 0)
        skill = Cvar_Get("skill", "1", 0)

        # Register game commands
        Cmd_AddCommand("say", Say_f)
        Cmd_AddCommand("say_team", Say_Team_f)

        # Initialize entity list
        game.entities = [None] * game.maxentities

        Com_Printf("G_Init complete\n")
        return True

    except Exception as e:
        print(f"G_Init error: {e}")
        return False


def ShutdownGame():
    """Shutdown game"""
    try:
        from ..quake2.common import Com_Printf

        Com_Printf("ShutdownGame()\n")

        game.entities = []
        game.time = 0.0

    except Exception as e:
        print(f"ShutdownGame error: {e}")


# ===== Frame Execution =====

def G_RunFrame():
    """
    Run a game frame.
    Called from server each frame to update all entities.
    """
    try:
        from ..quake2.common import Com_Printf

        # Update time
        game.time += 0.016  # 16ms = ~60Hz

        # Run entity thinks
        for ent in game.entities:
            if ent and hasattr(ent, 'think') and ent.think:
                try:
                    ent.think(ent)
                except:
                    pass

        # Physics simulation
        # TODO: Run physics for all entities

        # Check win conditions
        # TODO: CheckGameRules()

    except Exception as e:
        print(f"G_RunFrame error: {e}")


# ===== Entity Spawning =====

def G_SpawnEntities(mapname):
    """
    Spawn entities from map entity string.
    Parses ent file format and creates entities.
    """
    try:
        from ..quake2.cmodel import CM_EntityString
        from ..quake2.common import Com_Printf

        entity_string = CM_EntityString()

        if not entity_string:
            Com_Printf("No entities in map\n")
            return

        # Parse entity string
        ent_dict = _parse_entities(entity_string)

        spawn_count = 0

        for classname, entities_list in ent_dict.items():
            for ent_data in entities_list:
                # Spawn entity based on classname
                ent = _spawn_entity(classname, ent_data)
                if ent:
                    spawn_count += 1

        Com_Printf(f"Spawned {spawn_count} entities\n")

    except Exception as e:
        print(f"G_SpawnEntities error: {e}")


def _parse_entities(entity_string):
    """Parse entity string into dictionary of class->entities"""
    entities = {}

    # Split by entity blocks { ... }
    in_entity = False
    current_entity = {}

    for line in entity_string.split('\n'):
        line = line.strip()

        if line == '{':
            in_entity = True
            current_entity = {}
        elif line == '}':
            if in_entity and current_entity:
                classname = current_entity.get('classname', 'unknown')
                if classname not in entities:
                    entities[classname] = []
                entities[classname].append(current_entity)
            in_entity = False
            current_entity = {}
        elif in_entity and line and '"' in line:
            # Parse key "value" pair
            match = re.match(r'"([^"]*)"\s+"([^"]*)"', line)
            if match:
                key = match.group(1)
                value = match.group(2)
                current_entity[key] = value

    return entities


def _spawn_entity(classname, data):
    """Spawn a single entity"""
    try:
        # Parse position
        origin = [0, 0, 0]
        if 'origin' in data:
            parts = data['origin'].split()
            origin = [float(p) for p in parts[:3]]

        # Parse angles
        angles = [0, 0, 0]
        if 'angle' in data:
            angles[1] = float(data['angle'])

        # Create entity
        ent = {
            'classname': classname,
            'origin': origin,
            'angles': angles,
            'velocity': [0, 0, 0],
            'inuse': True,
            'data': data,
            'think': None,
        }

        # Special handling for specific entities
        if classname == 'worldspawn':
            # World entity - set sky and other properties
            pass
        elif classname == 'info_player_start':
            # Player spawn point
            ent['think'] = None
        elif classname.startswith('monster_'):
            # Monster entity
            ent['health'] = 100
            ent['think'] = G_MonsterThink
        elif classname.startswith('item_'):
            # Item entity
            ent['think'] = G_ItemThink

        game.entities.append(ent)
        return ent

    except Exception as e:
        print(f"_spawn_entity error: {classname}: {e}")
        return None


# ===== Entity Think Functions =====

def G_MonsterThink(ent):
    """Think function for monsters"""
    # TODO: Monster AI
    pass


def G_ItemThink(ent):
    """Think function for items"""
    # TODO: Item logic (rotation, pickup, etc)
    pass


def G_PlayerThink(ent):
    """Think function for players"""
    # TODO: Player think
    pass


# ===== Game Commands =====

def Say_f():
    """say <text> - Send message"""
    from ..quake2.cmd import Cmd_Argv, Cmd_Argc

    if Cmd_Argc() < 2:
        return

    msg = Cmd_Argv(1)
    # TODO: Send message to all clients
    print(f"SAY: {msg}")


def Say_Team_f():
    """say_team <text> - Send team message"""
    from ..quake2.cmd import Cmd_Argv, Cmd_Argc

    if Cmd_Argc() < 2:
        return

    msg = Cmd_Argv(1)
    # TODO: Send message to team only
    print(f"SAY_TEAM: {msg}")


def ClientEndServerFrames():
    """Called at end of server frame for clients"""
    pass


def CreateTargetChangeLevel(map):
    """Create change level entity"""
    pass


def EndDMLevel():
    """End deathmatch level"""
    pass


def CheckDMRules():
    """Check deathmatch rules"""
    pass


# ===== Game API Export =====

def GetGameAPI(import_func):
    """
    Export game API.
    Called by server to get game function pointers.
    """
    try:
        # Setup game import (callbacks from engine)
        global gi

        gi.error = import_func.error if hasattr(import_func, 'error') else None
        gi.dprintf = import_func.dprintf if hasattr(import_func, 'dprintf') else print
        gi.trace = import_func.trace if hasattr(import_func, 'trace') else None
        gi.pointcontents = import_func.pointcontents if hasattr(import_func, 'pointcontents') else None

        # Return game export
        class GameExport:
            def __init__(self):
                self.api_version = 3
                self.Init = G_Init
                self.Shutdown = ShutdownGame
                self.SpawnEntities = G_SpawnEntities
                self.WriteGame = None
                self.ReadGame = None
                self.WriteLevel = None
                self.ReadLevel = None
                self.ClientThink = None
                self.ClientConnect = None
                self.ClientUserinfoChanged = None
                self.ClientDisconnect = None
                self.ClientBeginServerFrame = None
                self.RunFrame = G_RunFrame
                self.ServerCommand = None
                self.entities = game.entities
                self.num_entities = 0

        return GameExport()

    except Exception as e:
        print(f"GetGameAPI error: {e}")
        return None


# ===== Error Handling =====

@va_args
def Sys_Error(error):
    """System error"""
    print(f"SYSTEM ERROR: {error}")
    if gi.error:
        gi.error(ERROR_LVL.ERR_FATAL, error)


@va_args
def Com_Printf(msg):
    """Print message"""
    print(msg)
    if gi.dprintf:
        gi.dprintf(msg)


@TODO
def ClientEndServerFrames():
    pass


@TODO
def CreateTargetChangeLevel(map):
    pass


@TODO
def EndDMLevel():
    pass


@TODO
def CheckDMRules():
    pass


@TODO
def UpdateChaseCam(ent):
    pass


@TODO
def ChaseNext(ent):
    pass


@TODO
def ChasePrev(ent):
    pass


@TODO
def GetChaseTarget(ent):
    pass
