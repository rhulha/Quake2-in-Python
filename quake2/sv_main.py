"""
sv_main.py - Quake 2 server implementation
Handles server initialization, frame execution, and client management
"""

from wrapper_qpy.decorators import TODO
from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), ["Com_Printf", "Com_Error", "Cvar_Get", "Cmd_AddCommand"])

# ===== Server State =====

class Server:
    def __init__(self):
        self.state = 0                  # 0=not running, 1=loading, 2=running
        self.mapname = ""
        self.models = []
        self.edicts = []
        self.num_edicts = 0
        self.max_edicts = 1024
        self.time = 0.0
        self.frametime = 0.001
        self.entities = []


server = Server()

# ===== Initialization =====

def SV_Init():
    """Initialize server"""
    try:
        from .common import Com_Printf, Cvar_Get, Cmd_AddCommand

        Com_Printf("SV_Init()\n")

        # Register server cvars
        sv_gravity = Cvar_Get("sv_gravity", "800", 0)
        sv_friction = Cvar_Get("sv_friction", "6", 0)
        sv_stopspeed = Cvar_Get("sv_stopspeed", "100", 0)

        # Initialize entity list
        server.edicts = [None] * server.max_edicts
        server.num_edicts = 0

        # Register server commands
        Cmd_AddCommand("map", SV_Map_f)
        Cmd_AddCommand("killserver", SV_KillServer_f)

        Com_Printf("SV_Init complete\n")
        return True

    except Exception as e:
        print(f"SV_Init error: {e}")
        return False


def SV_Shutdown(message, reconnect=False):
    """Shutdown server"""
    try:
        from .common import Com_Printf

        Com_Printf(f"SV_Shutdown: {message}\n")

        server.state = 0
        server.edicts = []
        server.num_edicts = 0

    except Exception as e:
        print(f"SV_Shutdown error: {e}")


# ===== Frame Execution =====

def SV_Frame(msec):
    """
    Main server frame.
    Called once per frame to update all entities and physics.
    """
    try:
        from .common import Com_Printf
        from .cmodel import CM_LoadMap

        if server.state == 0:
            return

        # Update frame time
        server.frametime = msec / 1000.0
        server.time += server.frametime

        # Run game frame
        try:
            from game import G_RunFrame
            G_RunFrame()
        except Exception as e:
            Com_Printf(f"Game frame error: {e}\n")

        # Send messages to clients
        try:
            SV_SendClientMessages()
        except:
            pass

    except Exception as e:
        print(f"SV_Frame error: {e}")


def SV_RunGameFrame():
    """Run game logic frame"""
    try:
        # Call game DLL frame
        from game import G_RunFrame

        G_RunFrame()

    except Exception as e:
        print(f"SV_RunGameFrame error: {e}")


# ===== Map Loading =====

def SV_Map_f():
    """map <mapname> - Load a map"""
    try:
        from .cmd import Cmd_Argc, Cmd_Argv
        from .common import Com_Printf, Com_Error
        from .cmodel import CM_LoadMap
        from game import G_SpawnEntities

        if Cmd_Argc() < 2:
            Com_Printf("Usage: map <mapname>\n")
            return

        mapname = Cmd_Argv(1)

        # Load collision model
        try:
            CM_LoadMap(f"maps/{mapname}.bsp", False, None)
        except Exception as e:
            Com_Error(0, f"Couldn't load map {mapname}: {e}")
            return

        # Load game
        try:
            from game.g_main import G_Init
            G_Init()
        except:
            pass

        # Spawn entities from map
        try:
            G_SpawnEntities(mapname)
        except:
            pass

        server.state = 2  # Running
        server.mapname = mapname
        server.time = 0.0

        Com_Printf(f"Loaded map: {mapname}\n")

    except Exception as e:
        print(f"SV_Map_f error: {e}")


def SV_KillServer_f():
    """killserver - Stop the server"""
    SV_Shutdown("Server terminated", False)


# ===== Entity Management =====

def SV_SpawnEntity():
    """Allocate a new entity"""
    if server.num_edicts >= server.max_edicts:
        return None

    edict = {
        'number': server.num_edicts,
        'inuse': False,
        'classname': '',
        'model': '',
        'origin': [0, 0, 0],
        'angles': [0, 0, 0],
        'velocity': [0, 0, 0],
        'solid': 0,
        'svflags': 0,
        'owner': None,
        'think': None,
        'nextthink': 0,
        'health': 0,
    }

    server.edicts[server.num_edicts] = edict
    server.num_edicts += 1

    return edict


def SV_LinkEntity(ent):
    """Link entity into world (for collision)"""
    # TODO: Add entity to spatial structure for collision queries
    pass


def SV_UnlinkEntity(ent):
    """Unlink entity from world"""
    # TODO: Remove entity from spatial structure
    pass


def SV_TouchTriggers(ent):
    """Check for trigger touches"""
    # TODO: Implement trigger detection
    pass


# ===== Client Management =====

def SV_DropClient(drop):
    """Drop a client connection"""
    pass


def SV_SendClientMessages():
    """Send state updates to connected clients"""
    # TODO: Send entity state updates
    pass


def SV_ExecuteUserCommand(s):
    """Execute a user command"""
    # TODO: Parse and execute user commands (move, look, etc)
    pass


# ===== Network Commands (Server-side) =====

def SVC_Status():
    """Handle status query"""
    pass


def SVC_Ack():
    """Handle acknowledgment"""
    pass


def SVC_Info():
    """Handle info query"""
    pass


def SVC_Ping():
    """Handle ping"""
    pass


def SVC_GetChallenge():
    """Handle challenge request"""
    pass


def SVC_DirectConnect():
    """Handle direct connection"""
    pass


def SV_StatusString():
    """Get server status string"""
    return "Server status"


def Rcon_Validate():
    """Validate remote console command"""
    pass


# ===== Utilities =====

def SV_CheckTimeouts():
    """Check for client timeouts"""
    pass


def SV_CalculatePing(client):
    """Calculate client ping"""
    return 0


@TODO
def SV_WriteFrame(msg):
    pass


@TODO
def SV_Multicast(origin, to):
    pass


@TODO
def SV_StartSound(origin, ent, channel, soundindex, volume, attenuation):
    pass


@TODO
def SV_BroadcastCommand(fmt):
    pass


@TODO
def SV_BroadcastPrintf(fmt):
    pass
