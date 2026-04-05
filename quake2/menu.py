"""menu.py — Quake2 in-game menu system (Python port)

All draw functions are no-ops (renderer not yet connected).
State management and command dispatch are fully implemented.
"""
from wrapper_qpy.linker import LinkEmptyFunctions

LinkEmptyFunctions(globals(), [])

# --------------------------------------------------------------------------
# Module state
# --------------------------------------------------------------------------

_m_drawfunc = None
_m_keyfunc = None
_m_entersound = False
_m_layers = []           # stack of (drawfunc, keyfunc) tuples

# Shared menu item lists (populated by *_MenuInit functions)
_main_items = ["Game", "Multiplayer", "Options", "Credits", "Quit"]
_main_cursor = 0

_options_cursor = 0
_game_cursor = 0
_keys_cursor = 0
_multiplayer_cursor = 0
_joinserver_cursor = 0
_startserver_cursor = 0
_dmoptions_cursor = 0
_addressbook_cursor = 0
_loadgame_cursor = 0
_savegame_cursor = 0
_downloadoptions_cursor = 0
_playerconfig_cursor = 0

# Server browser state
_serverlist = []          # list of (netadr, info) tuples
_servercount = 0

# Key bindings menu state
_bindnames = [
    ["+attack",          "attack"],
    ["weapnext",         "next weapon"],
    ["weapprev",         "prev weapon"],
    ["+forward",         "walk forward"],
    ["+back",            "backpedal"],
    ["+left",            "turn left"],
    ["+right",           "turn right"],
    ["+speed",           "run"],
    ["+moveleft",        "step left"],
    ["+moveright",       "step right"],
    ["+strafe",          "sidestep"],
    ["+lookup",          "look up"],
    ["+lookdown",        "look down"],
    ["centerview",       "center view"],
    ["+mlook",           "mouse look"],
    ["+klook",           "keyboard look"],
    ["+moveup",          "up / jump"],
    ["+movedown",        "down / crouch"],
    ["inven",            "inventory"],
    ["invuse",           "use item"],
    ["invdrop",          "drop item"],
    ["invprev",          "prev item"],
    ["invnext",          "next item"],
    ["cmd help",         "help computer"],
]
_bind_grab = False

# Options menu cvars (populated on init)
_sens_cvar = None
_alwaysrun_cvar = None
_invertmouse_cvar = None
_lookspring_cvar = None
_lookstrafe_cvar = None
_freelook_cvar = None
_crosshair_cvar = None
_sfxvol_cvar = None
_cdvol_cvar = None
_noalttab_cvar = None

# Player config state
_player_model = ''
_player_skin = ''
_model_files = []
_skin_files = []

# Quit menu state
_credits_offset = 0
_credits_lines = [
    "Quake II was created by",
    "id Software",
    "",
    "Programming: John Carmack",
    "Program Design: John Carmack",
    "Technical Director: John Carmack",
    "Lead Artist: Adrian Carmack",
    "Art Director: Kevin Cloud",
    "Art: Paul Steed",
    "Design: Sandy Petersen, American McGee, Tim Willits",
    "Sound: Trent Reznor, Nine Inch Nails",
    "Biz: Todd Hollenshead, Jerry Roka",
]

# --------------------------------------------------------------------------
# Core push/pop stack
# --------------------------------------------------------------------------

def M_PushMenu(draw, key):
    global _m_drawfunc, _m_keyfunc, _m_entersound
    _m_entersound = True
    if _m_drawfunc is not None:
        _m_layers.append((_m_drawfunc, _m_keyfunc))
    _m_drawfunc = draw
    _m_keyfunc = key


def M_ForceMenuOff():
    global _m_drawfunc, _m_keyfunc, _m_layers
    _m_drawfunc = None
    _m_keyfunc = None
    _m_layers.clear()
    try:
        from .keys import Key_SetDest
        Key_SetDest(0)  # KEY_GAME
    except Exception:
        pass


def M_PopMenu():
    global _m_drawfunc, _m_keyfunc
    if _m_layers:
        _m_drawfunc, _m_keyfunc = _m_layers.pop()
    else:
        M_ForceMenuOff()


def Default_MenuKey(m, key):
    K_ESCAPE = 27
    K_UPARROW = 128
    K_DOWNARROW = 129
    K_ENTER = 13
    if key == K_ESCAPE:
        M_PopMenu()
        return None
    return None


# --------------------------------------------------------------------------
# Draw helpers (no-ops — renderer not connected)
# --------------------------------------------------------------------------

def M_Banner(name):
    return


def M_DrawCharacter(cx, cy, num):
    return


def M_Print(cx, cy, _str):
    return


def M_PrintWhite(cx, cy, _str):
    return


def M_DrawPic(x, y, pic):
    return


def M_DrawCursor(x, y, f):
    return


def M_DrawTextBox(x, y, width, lines):
    return


# --------------------------------------------------------------------------
# Main menu
# --------------------------------------------------------------------------

def M_Main_Draw():
    return


def M_Main_Key(key):
    global _main_cursor
    K_ESCAPE = 27
    K_UPARROW = 128
    K_DOWNARROW = 129
    K_ENTER = 13
    if key == K_ESCAPE:
        M_PopMenu()
    elif key == K_UPARROW:
        _main_cursor = (_main_cursor - 1) % len(_main_items)
    elif key == K_DOWNARROW:
        _main_cursor = (_main_cursor + 1) % len(_main_items)
    elif key == K_ENTER:
        choice = _main_items[_main_cursor]
        if choice == "Game":
            M_Menu_Game_f()
        elif choice == "Multiplayer":
            M_Menu_Multiplayer_f()
        elif choice == "Options":
            M_Menu_Options_f()
        elif choice == "Credits":
            M_Menu_Credits_f()
        elif choice == "Quit":
            M_Menu_Quit_f()


def M_Menu_Main_f():
    M_PushMenu(M_Main_Draw, M_Main_Key)


# --------------------------------------------------------------------------
# Multiplayer menu
# --------------------------------------------------------------------------

def PlayerSetupFunc(unused):
    M_Menu_PlayerConfig_f()


def JoinNetworkServerFunc(unused):
    M_Menu_JoinServer_f()


def StartNetworkServerFunc(unused):
    M_Menu_StartServer_f()


def Multiplayer_MenuInit():
    return


def Multiplayer_MenuDraw():
    return


def Multiplayer_MenuKey(key):
    global _multiplayer_cursor
    K_ESCAPE = 27
    K_UPARROW = 128
    K_DOWNARROW = 129
    K_ENTER = 13
    _items = ["Join Server", "Start Server", "Player Setup"]
    if key == K_ESCAPE:
        M_PopMenu()
    elif key == K_UPARROW:
        _multiplayer_cursor = (_multiplayer_cursor - 1) % len(_items)
    elif key == K_DOWNARROW:
        _multiplayer_cursor = (_multiplayer_cursor + 1) % len(_items)
    elif key == K_ENTER:
        if _multiplayer_cursor == 0:
            JoinNetworkServerFunc(None)
        elif _multiplayer_cursor == 1:
            StartNetworkServerFunc(None)
        else:
            PlayerSetupFunc(None)


def M_Menu_Multiplayer_f():
    Multiplayer_MenuInit()
    M_PushMenu(Multiplayer_MenuDraw, Multiplayer_MenuKey)


# --------------------------------------------------------------------------
# Key bindings menu
# --------------------------------------------------------------------------

def M_UnbindCommand(command):
    try:
        from .keys import Key_GetBindings, Key_SetBinding
        for i in range(256):
            b = Key_GetBindings(i)
            if b and b == command:
                Key_SetBinding(i, '')
    except Exception:
        pass


def M_FindKeysForCommand(command, twokeys):
    twokeys[0] = -1
    twokeys[1] = -1
    count = 0
    try:
        from .keys import Key_GetBindings
        for i in range(256):
            b = Key_GetBindings(i)
            if b and b == command:
                twokeys[count] = i
                count += 1
                if count == 2:
                    return
    except Exception:
        pass


def KeyCursorDrawFunc(menu):
    return


def DrawKeyBindingFunc(_self):
    return


def KeyBindingFunc(_self):
    global _bind_grab, _keys_cursor
    _bind_grab = True


def Keys_MenuInit():
    global _keys_cursor
    _keys_cursor = 0


def Keys_MenuDraw():
    return


def Keys_MenuKey(key):
    global _keys_cursor, _bind_grab
    K_ESCAPE = 27
    K_UPARROW = 128
    K_DOWNARROW = 129
    K_ENTER = 13
    K_BACKSPACE = 8
    K_DEL = 127
    if _bind_grab:
        if key != K_ESCAPE:
            try:
                from .keys import Key_SetBinding
                cmd = _bindnames[_keys_cursor][0]
                Key_SetBinding(key, cmd)
            except Exception:
                pass
        _bind_grab = False
        return
    if key == K_ESCAPE:
        M_PopMenu()
    elif key == K_UPARROW:
        _keys_cursor = (_keys_cursor - 1) % len(_bindnames)
    elif key == K_DOWNARROW:
        _keys_cursor = (_keys_cursor + 1) % len(_bindnames)
    elif key in (K_ENTER, K_BACKSPACE, K_DEL):
        if key == K_ENTER:
            _bind_grab = True
        else:
            M_UnbindCommand(_bindnames[_keys_cursor][0])


def M_Menu_Keys_f():
    Keys_MenuInit()
    M_PushMenu(Keys_MenuDraw, Keys_MenuKey)


# --------------------------------------------------------------------------
# Options menu
# --------------------------------------------------------------------------

def CrosshairFunc(unused):
    if _crosshair_cvar:
        _crosshair_cvar.value = not _crosshair_cvar.value


def JoystickFunc(unused):
    return


def CustomizeControlsFunc(unused):
    M_Menu_Keys_f()


def AlwaysRunFunc(unused):
    if _alwaysrun_cvar:
        _alwaysrun_cvar.value = 1 - int(_alwaysrun_cvar.value)


def FreeLookFunc(unused):
    if _freelook_cvar:
        _freelook_cvar.value = 1 - int(_freelook_cvar.value)


def MouseSpeedFunc(unused):
    return


def NoAltTabFunc(unused):
    if _noalttab_cvar:
        _noalttab_cvar.value = 1 - int(_noalttab_cvar.value)


def ClampCvar(_min, _max, value):
    return max(_min, min(_max, value))


def ControlsSetMenuItemValues():
    return


def ControlsResetDefaultsFunc(unused):
    try:
        from .cvar import Cvar_SetValue
        Cvar_SetValue('sensitivity', 3.0)
        Cvar_SetValue('cl_run', 0)
        Cvar_SetValue('m_pitch', 0.022)
        Cvar_SetValue('lookspring', 0)
        Cvar_SetValue('lookstrafe', 0)
        Cvar_SetValue('m_freelook', 1)
        Cvar_SetValue('crosshair', 0)
    except Exception:
        pass


def InvertMouseFunc(unused):
    if _invertmouse_cvar:
        _invertmouse_cvar.value = -_invertmouse_cvar.value


def LookspringFunc(unused):
    if _lookspring_cvar:
        _lookspring_cvar.value = 1 - int(_lookspring_cvar.value)


def LookstrafeFunc(unused):
    if _lookstrafe_cvar:
        _lookstrafe_cvar.value = 1 - int(_lookstrafe_cvar.value)


def UpdateVolumeFunc(unused):
    return


def UpdateCDVolumeFunc(unused):
    return


def ConsoleFunc(unused):
    M_ForceMenuOff()
    try:
        from .console import Con_ToggleConsole_f
        Con_ToggleConsole_f()
    except Exception:
        pass


def UpdateSoundQualityFunc(unused):
    return


def Options_MenuInit():
    global _options_cursor, _sens_cvar, _alwaysrun_cvar, _invertmouse_cvar
    global _lookspring_cvar, _lookstrafe_cvar, _freelook_cvar
    global _crosshair_cvar, _sfxvol_cvar, _cdvol_cvar, _noalttab_cvar
    _options_cursor = 0
    try:
        from .cvar import Cvar_Get
        _sens_cvar = Cvar_Get('sensitivity', '3', 0)
        _alwaysrun_cvar = Cvar_Get('cl_run', '0', 0)
        _invertmouse_cvar = Cvar_Get('m_pitch', '0.022', 0)
        _lookspring_cvar = Cvar_Get('lookspring', '0', 0)
        _lookstrafe_cvar = Cvar_Get('lookstrafe', '0', 0)
        _freelook_cvar = Cvar_Get('m_freelook', '1', 0)
        _crosshair_cvar = Cvar_Get('crosshair', '0', 0)
        _sfxvol_cvar = Cvar_Get('s_volume', '0.7', 0)
        _cdvol_cvar = Cvar_Get('cd_volume', '0.4', 0)
        _noalttab_cvar = Cvar_Get('win_noalttab', '0', 0)
    except Exception:
        pass


def Options_MenuDraw():
    return


def Options_MenuKey(key):
    return Default_MenuKey(None, key)


def M_Menu_Options_f():
    Options_MenuInit()
    M_PushMenu(Options_MenuDraw, Options_MenuKey)


# --------------------------------------------------------------------------
# Credits menu
# --------------------------------------------------------------------------

def M_Credits_MenuDraw():
    return


def M_Credits_Key(key):
    K_ESCAPE = 27
    if key == K_ESCAPE:
        M_PopMenu()


def M_Menu_Credits_f():
    M_PushMenu(M_Credits_MenuDraw, M_Credits_Key)


# --------------------------------------------------------------------------
# Game menu
# --------------------------------------------------------------------------

def StartGame():
    M_ForceMenuOff()
    try:
        from .cmd import Cbuf_AddText
        Cbuf_AddText('killserver\n')
        Cbuf_AddText('newgame\n')
    except Exception:
        pass


def EasyGameFunc(data):
    try:
        from .cvar import Cvar_ForceSet
        Cvar_ForceSet('skill', '0')
    except Exception:
        pass
    StartGame()


def MediumGameFunc(data):
    try:
        from .cvar import Cvar_ForceSet
        Cvar_ForceSet('skill', '1')
    except Exception:
        pass
    StartGame()


def HardGameFunc(data):
    try:
        from .cvar import Cvar_ForceSet
        Cvar_ForceSet('skill', '2')
    except Exception:
        pass
    StartGame()


def LoadGameFunc(unused):
    M_Menu_LoadGame_f()


def SaveGameFunc(unused):
    M_Menu_SaveGame_f()


def CreditsFunc(unused):
    M_Menu_Credits_f()


def Game_MenuInit():
    global _game_cursor
    _game_cursor = 0


def Game_MenuDraw():
    return


def Game_MenuKey(key):
    global _game_cursor
    K_ESCAPE = 27
    K_UPARROW = 128
    K_DOWNARROW = 129
    K_ENTER = 13
    _funcs = [EasyGameFunc, MediumGameFunc, HardGameFunc, LoadGameFunc, SaveGameFunc, CreditsFunc]
    if key == K_ESCAPE:
        M_PopMenu()
    elif key == K_UPARROW:
        _game_cursor = (_game_cursor - 1) % len(_funcs)
    elif key == K_DOWNARROW:
        _game_cursor = (_game_cursor + 1) % len(_funcs)
    elif key == 13:
        _funcs[_game_cursor](None)


def M_Menu_Game_f():
    Game_MenuInit()
    M_PushMenu(Game_MenuDraw, Game_MenuKey)


# --------------------------------------------------------------------------
# Load / Save game menus
# --------------------------------------------------------------------------

_savestrings = [''] * 15
_savevalid = [False] * 15


def Create_Savestrings():
    import os
    for i in range(15):
        path = f'save/slot{i}/game.ssv'
        if os.path.exists(path):
            _savevalid[i] = True
            _savestrings[i] = f'Slot {i}'
        else:
            _savevalid[i] = False
            _savestrings[i] = '<empty>'


def LoadGameCallback(_self):
    idx = _self if isinstance(_self, int) else _loadgame_cursor
    try:
        from .cmd import Cbuf_AddText
        Cbuf_AddText(f'load save/slot{idx}/game\n')
    except Exception:
        pass
    M_ForceMenuOff()


def LoadGame_MenuInit():
    global _loadgame_cursor
    _loadgame_cursor = 0
    Create_Savestrings()


def LoadGame_MenuDraw():
    return


def LoadGame_MenuKey(key):
    global _loadgame_cursor
    K_ESCAPE = 27
    K_UPARROW = 128
    K_DOWNARROW = 129
    K_ENTER = 13
    if key == K_ESCAPE:
        M_PopMenu()
    elif key == K_UPARROW:
        _loadgame_cursor = (_loadgame_cursor - 1) % 15
    elif key == K_DOWNARROW:
        _loadgame_cursor = (_loadgame_cursor + 1) % 15
    elif key == K_ENTER:
        if _savevalid[_loadgame_cursor]:
            LoadGameCallback(_loadgame_cursor)


def M_Menu_LoadGame_f():
    LoadGame_MenuInit()
    M_PushMenu(LoadGame_MenuDraw, LoadGame_MenuKey)


def SaveGameCallback(_self):
    idx = _self if isinstance(_self, int) else _savegame_cursor
    try:
        from .cmd import Cbuf_AddText
        Cbuf_AddText(f'save save/slot{idx}/game\n')
    except Exception:
        pass
    M_ForceMenuOff()


def SaveGame_MenuDraw():
    return


def SaveGame_MenuInit():
    global _savegame_cursor
    _savegame_cursor = 0
    Create_Savestrings()


def SaveGame_MenuKey(key):
    global _savegame_cursor
    K_ESCAPE = 27
    K_UPARROW = 128
    K_DOWNARROW = 129
    K_ENTER = 13
    if key == K_ESCAPE:
        M_PopMenu()
    elif key == K_UPARROW:
        _savegame_cursor = (_savegame_cursor - 1) % 15
    elif key == K_DOWNARROW:
        _savegame_cursor = (_savegame_cursor + 1) % 15
    elif key == K_ENTER:
        SaveGameCallback(_savegame_cursor)


def M_Menu_SaveGame_f():
    SaveGame_MenuInit()
    M_PushMenu(SaveGame_MenuDraw, SaveGame_MenuKey)


# --------------------------------------------------------------------------
# Join server menu
# --------------------------------------------------------------------------

def M_AddToServerList(adr, info):
    global _servercount
    for s in _serverlist:
        if s[1] == info:
            return
    _serverlist.append((adr, info))
    _servercount = len(_serverlist)


def JoinServerFunc(_self):
    idx = _self if isinstance(_self, int) else _joinserver_cursor
    if 0 <= idx < len(_serverlist):
        adr = _serverlist[idx][0]
        try:
            from .cmd import Cbuf_AddText
            Cbuf_AddText(f'connect {adr}\n')
        except Exception:
            pass
        M_ForceMenuOff()


def AddressBookFunc(_self):
    M_Menu_AddressBook_f()


def NullCursorDraw(_self):
    return


def SearchLocalGames():
    global _serverlist, _servercount
    _serverlist.clear()
    _servercount = 0
    try:
        from .cmd import Cbuf_AddText
        Cbuf_AddText('ping_servers\n')
    except Exception:
        pass


def SearchLocalGamesFunc(_self):
    SearchLocalGames()


def JoinServer_MenuInit():
    global _joinserver_cursor
    _joinserver_cursor = 0


def JoinServer_MenuDraw():
    return


def JoinServer_MenuKey(key):
    global _joinserver_cursor
    K_ESCAPE = 27
    K_UPARROW = 128
    K_DOWNARROW = 129
    K_ENTER = 13
    if key == K_ESCAPE:
        M_PopMenu()
    elif key == K_UPARROW:
        if _servercount > 0:
            _joinserver_cursor = (_joinserver_cursor - 1) % _servercount
    elif key == K_DOWNARROW:
        if _servercount > 0:
            _joinserver_cursor = (_joinserver_cursor + 1) % _servercount
    elif key == K_ENTER:
        JoinServerFunc(_joinserver_cursor)


def M_Menu_JoinServer_f():
    JoinServer_MenuInit()
    M_PushMenu(JoinServer_MenuDraw, JoinServer_MenuKey)


# --------------------------------------------------------------------------
# Start server menu
# --------------------------------------------------------------------------

def DMOptionsFunc(_self):
    M_Menu_DMOptions_f()


def RulesChangeFunc(_self):
    return


def StartServerActionFunc(_self):
    try:
        from .cmd import Cbuf_AddText
        Cbuf_AddText('map base1\n')
    except Exception:
        pass
    M_ForceMenuOff()


def StartServer_MenuInit():
    return


def StartServer_MenuDraw():
    return


def StartServer_MenuKey(key):
    return Default_MenuKey(None, key)


def M_Menu_StartServer_f():
    StartServer_MenuInit()
    M_PushMenu(StartServer_MenuDraw, StartServer_MenuKey)


# --------------------------------------------------------------------------
# DM options menu
# --------------------------------------------------------------------------

def DMFlagCallback(_self):
    return


def DMOptions_MenuInit():
    return


def DMOptions_MenuDraw():
    return


def DMOptions_MenuKey(key):
    return Default_MenuKey(None, key)


def M_Menu_DMOptions_f():
    DMOptions_MenuInit()
    M_PushMenu(DMOptions_MenuDraw, DMOptions_MenuKey)


# --------------------------------------------------------------------------
# Download options menu
# --------------------------------------------------------------------------

def DownloadCallback(_self):
    return


def DownloadOptions_MenuInit():
    return


def DownloadOptions_MenuDraw():
    return


def DownloadOptions_MenuKey(key):
    return Default_MenuKey(None, key)


def M_Menu_DownloadOptions_f():
    DownloadOptions_MenuInit()
    M_PushMenu(DownloadOptions_MenuDraw, DownloadOptions_MenuKey)


# --------------------------------------------------------------------------
# Address book menu
# --------------------------------------------------------------------------

_addressbook = [''] * 9


def AddressBook_MenuInit():
    global _addressbook_cursor
    _addressbook_cursor = 0
    try:
        from .cvar import Cvar_Get
        for i in range(9):
            cv = Cvar_Get(f'adr{i}', '', 0)
            _addressbook[i] = cv.string if cv else ''
    except Exception:
        pass


def AddressBook_MenuKey(key):
    global _addressbook_cursor
    K_ESCAPE = 27
    K_UPARROW = 128
    K_DOWNARROW = 129
    K_ENTER = 13
    if key == K_ESCAPE:
        try:
            from .cvar import Cvar_Set
            for i in range(9):
                Cvar_Set(f'adr{i}', _addressbook[i])
        except Exception:
            pass
        M_PopMenu()
    elif key == K_UPARROW:
        _addressbook_cursor = (_addressbook_cursor - 1) % 9
    elif key == K_DOWNARROW:
        _addressbook_cursor = (_addressbook_cursor + 1) % 9
    elif key == K_ENTER:
        adr = _addressbook[_addressbook_cursor]
        if adr:
            try:
                from .cmd import Cbuf_AddText
                Cbuf_AddText(f'connect {adr}\n')
            except Exception:
                pass
            M_ForceMenuOff()


def AddressBook_MenuDraw():
    return


def M_Menu_AddressBook_f():
    AddressBook_MenuInit()
    M_PushMenu(AddressBook_MenuDraw, AddressBook_MenuKey)


def DownloadOptionsFunc(_self):
    M_Menu_DownloadOptions_f()


# --------------------------------------------------------------------------
# Player config menu
# --------------------------------------------------------------------------

def HandednessCallback(unused):
    return


def RateCallback(unused):
    return


def ModelCallback(unused):
    return


def FreeFileList(_list, n):
    del _list[:]


def IconOfSkinExists(skin, pcxfiles, npcxfiles):
    icon = skin.rsplit('.', 1)[0] + '_i.pcx'
    return icon in pcxfiles[:npcxfiles]


def PlayerConfig_ScanDirectories():
    global _model_files, _skin_files
    import os
    _model_files.clear()
    _skin_files.clear()
    base = 'baseq2/players'
    if os.path.isdir(base):
        for entry in os.listdir(base):
            if os.path.isdir(os.path.join(base, entry)):
                _model_files.append(entry)


def pmicmpfnc(_a, _b):
    return (_a > _b) - (_a < _b)


def PlayerConfig_MenuInit():
    global _playerconfig_cursor
    _playerconfig_cursor = 0
    PlayerConfig_ScanDirectories()


def PlayerConfig_MenuDraw():
    return


def PlayerConfig_MenuKey(key):
    return Default_MenuKey(None, key)


def M_Menu_PlayerConfig_f():
    PlayerConfig_MenuInit()
    M_PushMenu(PlayerConfig_MenuDraw, PlayerConfig_MenuKey)


# --------------------------------------------------------------------------
# Quit menu
# --------------------------------------------------------------------------

def M_Quit_Key(key):
    K_ESCAPE = 27
    K_N = ord('n')
    K_Y = ord('y')
    if key in (K_ESCAPE, K_N):
        M_PopMenu()
    elif key == K_Y:
        M_ForceMenuOff()
        try:
            from .cmd import Cbuf_AddText
            Cbuf_AddText('quit\n')
        except Exception:
            pass


def M_Quit_Draw():
    return


def M_Menu_Quit_f():
    M_PushMenu(M_Quit_Draw, M_Quit_Key)


# --------------------------------------------------------------------------
# Top-level: M_Init, M_Draw, M_Keydown
# --------------------------------------------------------------------------

def M_Init():
    try:
        from .cmd import Cmd_AddCommand
        Cmd_AddCommand('menu_main', M_Menu_Main_f)
        Cmd_AddCommand('menu_game', M_Menu_Game_f)
        Cmd_AddCommand('menu_loadgame', M_Menu_LoadGame_f)
        Cmd_AddCommand('menu_savegame', M_Menu_SaveGame_f)
        Cmd_AddCommand('menu_joinserver', M_Menu_JoinServer_f)
        Cmd_AddCommand('menu_startserver', M_Menu_StartServer_f)
        Cmd_AddCommand('menu_dmoptions', M_Menu_DMOptions_f)
        Cmd_AddCommand('menu_addressbook', M_Menu_AddressBook_f)
        Cmd_AddCommand('menu_multiplayer', M_Menu_Multiplayer_f)
        Cmd_AddCommand('menu_keys', M_Menu_Keys_f)
        Cmd_AddCommand('menu_options', M_Menu_Options_f)
        Cmd_AddCommand('menu_playerconfig', M_Menu_PlayerConfig_f)
        Cmd_AddCommand('menu_downloadoptions', M_Menu_DownloadOptions_f)
        Cmd_AddCommand('menu_credits', M_Menu_Credits_f)
        Cmd_AddCommand('menu_quit', M_Menu_Quit_f)
    except Exception:
        pass


def M_Draw():
    global _m_entersound
    if _m_drawfunc is None:
        return
    if _m_entersound:
        _m_entersound = False
    try:
        _m_drawfunc()
    except Exception:
        pass


def M_Keydown(key):
    if _m_keyfunc is None:
        return
    try:
        _m_keyfunc(key)
    except Exception:
        pass
