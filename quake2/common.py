from wrapper_qpy.decorators import va_args, va_args2, static_vars, TODO
from wrapper_qpy.custom_classes import Mutable
from wrapper_qpy.linker import LinkEmptyFunctions
from shared.QEnums import ERROR_LVL


LinkEmptyFunctions(globals(), ["Con_Print", "Com_sprintf", "va", "FS_Gamedir", "CL_Drop", "CL_Shutdown", "SV_Shutdown",
                               "Sys_ConsoleOutput", "Sys_Error"])

MAXPRINTMSG = 4096
MAX_NUM_ARGVS = 50
MAX_QPATH = 64

com_argv = list()

realtime = 0

host_speeds = None
log_stats = None
developer = None
timescale = None
fixedtime = None
logfile_active = None
showtrace = None
dedicated = None

logfile = None

rd_target = 0
rd_buffer = None
rd_buffersize = 0
rd_flush = None

server_state = 0


def Com_BeginRedirect(target, buffer, buffersize, flush):
    global rd_target, rd_buffer, rd_buffersize, rd_flush
    if not target or not buffer or not buffersize or not flush:
        return
    rd_target, rd_buffer, rd_buffersize, rd_flush = target, buffer, buffersize, flush


def Com_EndRedirect():
    global rd_target, rd_buffer, rd_buffersize, rd_flush
    rd_flush(rd_target, rd_buffer)
    rd_target = 0
    rd_buffer = None
    rd_buffersize = 0
    rd_flush = None


@va_args
def Com_Printf(msg):
    global rd_buffer
    if rd_target > 0:
        if len(msg) + len(rd_buffer) > rd_buffersize -1:
            rd_flush(rd_target, rd_buffer)
        rd_buffer = msg
        return
    Con_Print(msg)
    Sys_ConsoleOutput(msg)
    if logfile_active is not None and logfile_active.value > 0:
        global logfile
        if logfile is None:
            name = Mutable()
            Com_sprintf(name, MAX_QPATH, "%s/qconsole.log", FS_Gamedir())
            logfile = open(name.GetValue(), "w")
        else:
            logfile.print(msg)
        if logfile_active.value > 1:
            logfile.flush()


def Com_DPrintf(msg):
    if developer is None or developer.value == 0:
        return
    Con_Print("%s", msg)



@va_args2(1)
@static_vars(recursive=False)
def Com_Error(code, msg):
    if Com_Error.recursive:
        Sys_Error("recursive error after: %s", msg)
    Com_Error.recursive = True
    if code == ERROR_LVL.ERR_DISCONNECT:
        CL_Drop()
        Com_Error.recursive = False
        # TODO: abortframe longjmp
    elif code == ERROR_LVL.ERR_DROP:
        Com_Printf("********************\nERROR: %s\n********************\n", msg)
        SV_Shutdown(va("Server crashed: %s\n", msg), False)
        CL_Drop()
        Com_Error.recursive = False
        # TODO: abortframe longjmp
    else:
        SV_Shutdown(va("Server fatal crashed: %s\n", msg), False)
        CL_Shutdown()
    global logfile
    if logfile is not None:
        logfile.flush()
        logfile.close()
        logfile = None
    Sys_Error("%s", msg)


@TODO
def Com_Quit():
    pass


def Com_ServerState():
    return server_state


def Com_SetServerState(state):
    global server_state
    server_state = state


@TODO
def MSG_WriteChar():
    pass


@TODO
def MSG_WriteByte():
    pass


@TODO
def MSG_WriteShort():
    pass


@TODO
def MSG_WriteLong():
    pass


@TODO
def MSG_WriteFloat():
    pass


@TODO
def MSG_WriteString():
    pass


@TODO
def MSG_WriteCoord():
    pass


@TODO
def MSG_WritePos():
    pass


@TODO
def MSG_WriteAngle():
    pass


@TODO
def MSG_WriteAngle16():
    pass


@TODO
def MSG_WriteDeltaUsercmd(buf, _from, cmd):
    pass


@TODO
def MSG_WriteDir():
    pass


@TODO
def MSG_ReadDir():
    pass


@TODO
def MSG_WriteDeltaEntity():
    pass


@TODO
def MSG_BeginReading():
    pass


@TODO
def MSG_ReadChar():
    pass


@TODO
def MSG_ReadByte():
    pass


@TODO
def MSG_ReadShort():
    pass


@TODO
def MSG_ReadLong():
    pass


@TODO
def MSG_ReadFloat():
    pass


@TODO
def MSG_ReadString():
    pass


@TODO
def MSG_ReadStringLine():
    pass


@TODO
def MSG_ReadCoord():
    pass


@TODO
def MSG_ReadPos():
    pass


@TODO
def MSG_ReadAngle():
    pass

@TODO
def MSG_ReadAngle16():
    pass

@TODO
def MSG_ReadDeltaUsercmd():
    pass

@TODO
def MSG_ReadData():
    pass


@TODO
def SZ_Init(buf, data, length):
    pass


@TODO
def SZ_Clear(buf):
    pass


@TODO
def SZ_GetSpace(buf, length):
    pass


@TODO
def SZ_Write(buf, data, length):
    pass


@TODO
def SZ_Print(buf, data):
    pass


@TODO
def COM_CheckParm(parm):
    pass


@TODO
def COM_Argc():
    pass


@TODO
def COM_Argv():
    pass


@TODO
def COM_ClearArgv(argc, argv):
    pass


@TODO
def COM_InitArgv():
    pass


@TODO
def COM_AddParm(parm):
    pass


@TODO
def memsearch(start, count, search):
    pass


@TODO
def CopyString(_in):
    pass


@TODO
def Info_Print(s):
    pass


@TODO
def Z_Free(ptr):
    pass


@TODO
def Z_Stats_f():
    pass


@TODO
def Z_FreeTags(tag):
    pass


@TODO
def Z_TagMalloc(size, tag):
    pass


@TODO
def Z_Malloc(size):
    return Z_TagMalloc(size, 0)


@TODO
def COM_BlockSequenceCheckByte(base, length, sequence, challenge):
    pass


@TODO
def COM_BlockSequenceCRCByte(base, length, sequence):
    pass


@TODO
def frand():
    pass


@TODO
def crand():
    pass


@TODO
def Com_Error_f():
    pass


def Qcommon_Init(argc, argv):
    """
    Initialize all engine subsystems.
    Called once at startup.
    """
    global host_speeds, log_stats, developer, timescale, fixedtime, logfile_active, showtrace, dedicated

    Com_Printf("====== Quake 2 Initializing ======\n\n")

    # Initialize memory
    # z_chain.next = z_chain.prev = &z_chain

    # Initialize basic subsystems first
    try:
        # Parse command line arguments
        com_argv.clear()
        for i in range(argc):
            if isinstance(argv, list):
                com_argv.append(argv[i])
            else:
                com_argv.append(str(argv[i]))

        # Initialize command buffer
        from .cmd import Cbuf_Init, Cbuf_AddText, Cbuf_Execute
        Cbuf_Init()

        # Initialize commands
        from .cmd import Cmd_Init, Cmd_AddCommand
        Cmd_Init()

        # Initialize console variables
        from .cvar import Cvar_Init, Cvar_Get
        Cvar_Init()

        # Initialize key binding system
        try:
            from .keys import Key_Init
            Key_Init()
        except:
            pass

        # Add early commands (before config)
        Cbuf_AddText("exec default.cfg\n")
        Cbuf_AddText("exec config.cfg\n")
        Cbuf_Execute()

        # Initialize filesystem
        from .files import FS_InitFilesystem
        FS_InitFilesystem()

        # Register cvars
        host_speeds = Cvar_Get("host_speeds", "0", 0)
        log_stats = Cvar_Get("log_stats", "0", 0)
        developer = Cvar_Get("developer", "0", 0)
        timescale = Cvar_Get("timescale", "1", 0)
        fixedtime = Cvar_Get("fixedtime", "0", 0)
        logfile_active = Cvar_Get("logfile", "0", 0)
        showtrace = Cvar_Get("showtrace", "0", 0)
        dedicated = Cvar_Get("dedicated", "0", 0)

        # Register version
        import sys
        version = "Quake2-Python 1.0"
        Cvar_Get("version", version, 0)

        # Register error command
        Cmd_AddCommand("error", Com_Error_f)

        # Initialize network
        try:
            from .net_chan import Netchan_Init
            Netchan_Init()
        except:
            pass

        # Initialize server
        try:
            from .sv_main import SV_Init
            SV_Init()
        except Exception as e:
            Com_Printf(f"Warning: SV_Init failed: {e}\n")

        # Initialize client
        try:
            from .cl_main import CL_Init
            CL_Init()
        except Exception as e:
            Com_Printf(f"Warning: CL_Init failed: {e}\n")

        # Default action: load first map
        try:
            Cbuf_AddText("d1\n")
            Cbuf_Execute()
        except:
            pass

        Com_Printf("====== Quake 2 Initialized ======\n\n")

    except Exception as e:
        Com_Error(0, f"Error during initialization: {e}")


def Qcommon_Frame(msec):
    """
    Main game loop frame.
    Called once per frame (~60 Hz).
    Handles both server and client frame updates.
    """
    global log_stats, fixedtime, timescale, showtrace, host_speeds

    # Apply timescale and fixed time
    if fixedtime and fixedtime.value:
        msec = int(fixedtime.value)
    elif timescale and timescale.value:
        msec = int(msec * timescale.value)
        if msec < 1:
            msec = 1

    try:
        # Process console input
        try:
            from .sys_win import Sys_ConsoleInput
            from .cmd import Cbuf_AddText, Cbuf_Execute
            s = Sys_ConsoleInput()
            if s:
                Cbuf_AddText(f"{s}\n")
            Cbuf_Execute()
        except:
            pass

        # Show trace statistics if enabled
        if showtrace and showtrace.value:
            Com_Printf("Trace statistics\n")

        # Time server frame
        time_before = 0
        if host_speeds and host_speeds.value:
            from .sys_win import Sys_Milliseconds
            time_before = Sys_Milliseconds()

        # Run server frame
        try:
            from .sv_main import SV_Frame
            SV_Frame(msec)
        except Exception as e:
            Com_Printf(f"Warning: SV_Frame error: {e}\n")

        time_between = 0
        if host_speeds and host_speeds.value:
            from .sys_win import Sys_Milliseconds
            time_between = Sys_Milliseconds()

        # Run client frame
        try:
            from .cl_main import CL_Frame
            CL_Frame(msec)
        except Exception as e:
            Com_Printf(f"Warning: CL_Frame error: {e}\n")

        time_after = 0
        if host_speeds and host_speeds.value:
            from .sys_win import Sys_Milliseconds
            time_after = Sys_Milliseconds()

            all_time = time_after - time_before
            sv_time = time_between - time_before
            cl_time = time_after - time_between

            Com_Printf(f"all:{all_time:3d}ms sv:{sv_time:3d}ms cl:{cl_time:3d}ms\n")

    except Exception as e:
        # On error, try to continue
        Com_Printf(f"Frame error: {e}\n")


def Qcommon_Shutdown():
    """
    Shut down all engine subsystems.
    Called once at exit.
    """
    global logfile

    try:
        from .sv_main import SV_Shutdown
        SV_Shutdown("Server shutdown", False)
    except:
        pass

    try:
        from .cl_main import CL_Shutdown
        CL_Shutdown()
    except:
        pass

    # Close logfile
    if logfile is not None:
        logfile.close()
        logfile = None

    Com_Printf("Quake 2 shutdown\n")


from .sys_win import Sys_ConsoleOutput, Sys_Error
from .console import Con_Print
from .q_shared import Com_sprintf, va
from .files import FS_Gamedir
from .cl_main import CL_Drop, CL_Shutdown
from .sv_main import SV_Shutdown