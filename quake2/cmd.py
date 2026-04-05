"""
cmd.py - Quake 2 command buffer and execution system
Handles command parsing, execution, and builtin commands
"""

from wrapper_qpy.decorators import TODO
from wrapper_qpy.linker import LinkEmptyFunctions


LinkEmptyFunctions(globals(), ["Com_Printf", "Com_Error", "FS_LoadFile", "Z_Malloc", "Z_Free", "Sys_Mkdir"])


# ===== Constants =====

EXEC_NOW = 0
EXEC_INSERT = 1
EXEC_APPEND = 2

MAX_ALIAS_NAME = 32
ALIAS_LOOP_COUNT = 16
MAX_CMD_BUFFER = 8192
MAX_CMD_LINE = 1024


# ===== Global State =====

cmd_wait = False
cmd_text_buffer = bytearray(MAX_CMD_BUFFER)
cmd_text_size = 0
defer_text_buffer = bytearray(MAX_CMD_BUFFER)
defer_text_size = 0

cmd_argv = []
cmd_functions = {}  # Dictionary of command_name -> callable
alias_count = 0
com_argv = []


# ===== Command Buffer Functions =====

def Cbuf_Init():
    """Initialize command buffer"""
    global cmd_text_size, defer_text_size
    cmd_text_size = 0
    defer_text_size = 0


def Cbuf_AddText(text):
    """Add text to end of command buffer"""
    global cmd_text_size

    if isinstance(text, str):
        text = text.encode('utf-8')
    elif not isinstance(text, bytes):
        text = str(text).encode('utf-8')

    if cmd_text_size + len(text) >= MAX_CMD_BUFFER:
        Com_Printf("Cbuf_AddText: overflow\n")
        return

    cmd_text_buffer[cmd_text_size:cmd_text_size+len(text)] = text
    cmd_text_size += len(text)


def Cbuf_InsertText(text):
    """Insert text at beginning of buffer (after current command)"""
    global cmd_text_size

    if isinstance(text, str):
        text = text.encode('utf-8')

    # Save current buffer
    templen = cmd_text_size
    if templen > 0:
        temp = bytes(cmd_text_buffer[:templen])
    else:
        temp = None

    # Clear buffer
    cmd_text_size = 0

    # Add new text
    Cbuf_AddText(text)

    # Restore old content
    if templen > 0:
        Cbuf_AddText(temp)


def Cbuf_CopyToDefer():
    """Copy command buffer to defer buffer"""
    global defer_text_size, cmd_text_size
    defer_text_buffer[:cmd_text_size] = cmd_text_buffer[:cmd_text_size]
    defer_text_size = cmd_text_size
    cmd_text_size = 0


def Cbuf_InsertFromDefer():
    """Insert deferred buffer back into command buffer"""
    global defer_text_size
    if defer_text_size > 0:
        Cbuf_InsertText(bytes(defer_text_buffer[:defer_text_size]))
    defer_text_size = 0


def Cbuf_ExecuteText(exec_when, text):
    """Execute text based on timing"""
    if exec_when == EXEC_NOW:
        Cmd_ExecuteString(text)
    elif exec_when == EXEC_INSERT:
        Cbuf_InsertText(text)
    elif exec_when == EXEC_APPEND:
        Cbuf_AddText(text)
    else:
        Com_Error(0, f"Cbuf_ExecuteText: bad exec_when {exec_when}")


def Cbuf_Execute():
    """
    Process and execute all commands in buffer.
    Stops if cmd_wait is set.
    """
    global cmd_text_size, cmd_text_buffer, cmd_wait, alias_count

    alias_count = 0  # Prevent alias loops

    while cmd_text_size > 0:
        # Find end of line (\n) or semicolon (;), respecting quoted strings
        text = cmd_text_buffer
        quotes = 0
        i = 0

        while i < cmd_text_size:
            if text[i:i+1] == b'"':
                quotes += 1
            # Don't break if inside quoted string
            if (quotes & 1) == 0:
                if text[i:i+1] == b';':
                    break
            if text[i:i+1] == b'\n':
                break
            i += 1

        # Extract line
        line = bytes(text[:i]).decode('utf-8', errors='ignore')

        # Remove from buffer
        if i >= cmd_text_size:
            cmd_text_size = 0
        else:
            i += 1  # Skip the delimiter
            cmd_text_size -= i
            cmd_text_buffer[:cmd_text_size] = cmd_text_buffer[i:i+cmd_text_size]

        # Execute the line
        Cmd_ExecuteString(line)

        # Check wait flag
        if cmd_wait:
            cmd_wait = False
            break


def Cbuf_AddEarlyCommands(clear):
    """
    Add +set commands from command line.
    These are executed before config files.
    """
    i = 0
    while i < len(com_argv):
        s = com_argv[i]
        if s == "+set" and i + 2 < len(com_argv):
            Cbuf_AddText(f"set {com_argv[i+1]} {com_argv[i+2]}\n")
            if clear:
                com_argv[i] = ""
                com_argv[i+1] = ""
                com_argv[i+2] = ""
            i += 3
        else:
            i += 1


def Cbuf_AddLateCommands():
    """
    Add commands from command line starting with +.
    Returns True if any were added.
    """
    # Build combined command string from argv
    commands = []
    for arg in com_argv[1:]:  # Skip program name
        if arg and arg.startswith('+'):
            commands.append(arg)

    if not commands:
        return False

    # Process + commands
    buffer = ""
    i = 0
    combined = " ".join(com_argv[1:])

    while i < len(combined):
        if combined[i] == '+':
            i += 1
            j = i
            # Find next + or - or end
            while j < len(combined) and combined[j] not in ('+', '-'):
                j += 1

            # Extract command
            cmd = combined[i:j].strip()
            if cmd:
                buffer += cmd + "\n"
            i = j
        else:
            i += 1

    if buffer:
        Cbuf_AddText(buffer)
        return True

    return False


# ===== Command Tokenization and Execution =====

def Cmd_TokenizeString(text):
    """
    Parse text into tokens (argv).
    Handles quoted strings and comment removal.
    """
    global cmd_argv

    cmd_argv = []

    if not text or len(text) == 0:
        return

    # Remove comments
    comment_pos = text.find("//")
    if comment_pos >= 0:
        text = text[:comment_pos]

    # Tokenize
    i = 0
    while i < len(text):
        # Skip whitespace
        while i < len(text) and text[i] in (' ', '\t', '\n', '\r'):
            i += 1

        if i >= len(text):
            break

        # Check for quoted string
        if text[i] == '"':
            i += 1
            start = i
            while i < len(text) and text[i] != '"':
                i += 1
            if i < len(text):
                cmd_argv.append(text[start:i])
                i += 1  # Skip closing quote
        else:
            # Regular token
            start = i
            while i < len(text) and text[i] not in (' ', '\t', '\n', '\r', ';'):
                i += 1
            if i > start:
                cmd_argv.append(text[start:i])

        # Stop at semicolon
        if i < len(text) and text[i] == ';':
            break


def Cmd_Argc():
    """Get number of command arguments"""
    return len(cmd_argv)


def Cmd_Argv(arg):
    """Get command argument by index"""
    if arg < 0 or arg >= len(cmd_argv):
        return ""
    return cmd_argv[arg]


def Cmd_AddCommand(cmd_name, function):
    """Register a command"""
    cmd_functions[cmd_name.lower()] = function


def Cmd_RemoveCommand(cmd_name):
    """Unregister a command"""
    name = cmd_name.lower()
    if name in cmd_functions:
        del cmd_functions[name]


def Cmd_Exists(cmd_name):
    """Check if command exists"""
    return cmd_name.lower() in cmd_functions


def Cmd_ExecuteString(text):
    """
    Execute a single command string.
    Tokenizes the string and calls the command function.
    """
    global alias_count

    # Tokenize
    Cmd_TokenizeString(text)

    if len(cmd_argv) == 0:
        return

    # Get command name
    cmd_name = cmd_argv[0].lower()

    # Look up command
    if cmd_name in cmd_functions:
        func = cmd_functions[cmd_name]
        try:
            func()
        except Exception as e:
            Com_Printf(f"Command '{cmd_name}' error: {e}\n")
    else:
        # Try as cvar set
        try:
            from .cvar import Cvar_Command
            if not Cvar_Command():
                Com_Printf(f"Unknown command: {cmd_name}\n")
        except:
            Com_Printf(f"Unknown command: {cmd_name}\n")


def Cmd_MacroExpandString(text):
    """Expand macros in string (not implemented yet)"""
    return text


# ===== Builtin Commands =====

def Cmd_Wait_f():
    """wait command - pause execution until next frame"""
    global cmd_wait
    cmd_wait = True


def Cmd_Exec_f():
    """exec <filename> - execute config file"""
    if Cmd_Argc() < 2:
        Com_Printf("exec <filename>\n")
        return

    filename = Cmd_Argv(1)
    try:
        from .files import FS_LoadFile
        data, length = FS_LoadFile(filename)
        if data is None:
            Com_Printf(f"couldn't exec {filename}\n")
            return

        # Add file content to command buffer
        text = data.decode('utf-8', errors='ignore')
        Cbuf_InsertText(text + "\n")

    except Exception as e:
        Com_Printf(f"exec error: {e}\n")


def Cmd_Echo_f():
    """echo <text> - print text to console"""
    if Cmd_Argc() < 2:
        Com_Printf("\n")
        return

    # Print all arguments
    for i in range(1, Cmd_Argc()):
        Com_Printf(Cmd_Argv(i))
        if i < Cmd_Argc() - 1:
            Com_Printf(" ")

    Com_Printf("\n")


def Cmd_Alias_f():
    """alias <name> <commands> - create command alias"""
    if Cmd_Argc() < 2:
        Com_Printf("alias <name> <commands>\n")
        return

    name = Cmd_Argv(1).lower()
    if Cmd_Argc() == 2:
        # Print alias
        if name in cmd_functions:
            Com_Printf(f"alias: {name} already exists as a command\n")
        else:
            Com_Printf(f"alias not found: {name}\n")
        return

    # Create alias - concatenate remaining args
    if Cmd_Argc() > 2:
        cmd = " ".join(cmd_argv[2:])
        # Create wrapper function
        def alias_func(cmd_text=cmd):
            Cbuf_InsertText(cmd_text + "\n")

        cmd_functions[name] = alias_func


def Cmd_List_f():
    """cmdlist - list all commands"""
    count = 0
    for name in sorted(cmd_functions.keys()):
        Com_Printf(f"  {name}\n")
        count += 1
    Com_Printf(f"{count} commands\n")


# ===== Initialization =====

def Cmd_Init():
    """Initialize command system and register builtin commands"""
    Cmd_AddCommand("cmdlist", Cmd_List_f)
    Cmd_AddCommand("exec", Cmd_Exec_f)
    Cmd_AddCommand("echo", Cmd_Echo_f)
    Cmd_AddCommand("alias", Cmd_Alias_f)
    Cmd_AddCommand("wait", Cmd_Wait_f)


# ===== TODO Functions =====

@TODO
def Cmd_CompleteCommand(partial):
    """Return list of commands starting with partial"""
    pass


from .common import Com_Printf, Com_Error
