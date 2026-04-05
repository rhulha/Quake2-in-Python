"""
files.py - Quake 2 filesystem with PAK file support
Handles loading files from PAK archives and directories
"""

import struct
import os
from pathlib import Path
from wrapper_qpy.decorators import TODO
from wrapper_qpy.linker import LinkEmptyFunctions
from shared.QConstants import MAX_QPATH, MAX_OSPATH


LinkEmptyFunctions(globals(), ["Com_Printf", "Com_DPrintf", "Com_Error", "Z_Malloc", "Z_Free", "Sys_Mkdir"])


# ===== Constants =====

IDPAKHEADER = ((ord('K')<<24) + (ord('C')<<16) + (ord('A')<<8) + ord('P'))
MAX_FILES_IN_PACK = 4096
MAX_READ = 0x10000  # 64KB blocks for reading


# ===== Structures =====

class DPackFile:
    """Entry in PAK directory"""
    def __init__(self, name='', filepos=0, filelen=0):
        self.name = name
        self.filepos = filepos
        self.filelen = filelen


class DPackHeader:
    """PAK file header"""
    def __init__(self, ident=0, dirofs=0, dirlen=0):
        self.ident = ident
        self.dirofs = dirofs
        self.dirlen = dirlen


class PackFile:
    """In-memory PAK file entry"""
    def __init__(self, name='', filepos=0, filelen=0):
        self.name = name
        self.filepos = filepos
        self.filelen = filelen


class Pack:
    """In-memory loaded PAK file"""
    def __init__(self, filename='', handle=None, numfiles=0, files=None):
        self.filename = filename
        self.handle = handle
        self.numfiles = numfiles
        self.files = files or []


class FileLink:
    """File link/redirect"""
    def __init__(self, from_path='', to_path=''):
        self.from_path = from_path
        self.fromlength = len(from_path)
        self.to_path = to_path


class SearchPath:
    """Search path element"""
    def __init__(self, filename='', pack=None):
        self.filename = filename
        self.pack = pack
        self.next = None


# ===== Global State =====

fs_gamedir = ""
fs_basedir = None
fs_cddir = None
fs_gamedirvar = None
fs_searchpaths = None
fs_base_searchpaths = None
fs_links = None
file_from_pak = False


# ===== Public Functions =====

def FS_Gamedir():
    """Get current game directory"""
    return fs_gamedir


@TODO
def FS_ExecAutoexec():
    pass


@TODO
def FS_SetGameDir(_dir):
    pass


def FS_LoadFile(path, return_buffer=True):
    """
    Load file from filesystem or PAK archive.
    Returns tuple (data, length) where data is bytes or None if return_buffer=False.
    If file not found, returns (None, -1).
    """
    global file_from_pak

    # Open the file
    h, length = FS_FOpenFile(path)

    if h is None:
        return (None, -1)

    # If just want length, close and return
    if not return_buffer:
        if hasattr(h, 'close'):
            h.close()
        return (None, length)

    # Read file contents
    buf = bytearray(length)
    FS_Read(buf, length, h)

    # Close file
    if hasattr(h, 'close'):
        h.close()

    return (bytes(buf), length)


def FS_FreeFile(buffer):
    """Free file buffer - in Python, just let GC handle it"""
    pass


def FS_FOpenFile(filename):
    """
    Find file in search path and open it.
    Returns (file_handle, length) where file_handle is a file object positioned at start of data.
    Returns (None, -1) if not found.
    """
    global fs_links, fs_searchpaths, file_from_pak

    file_from_pak = False

    # Check file links first
    link = fs_links
    while link:
        if filename.lower().startswith(link.from_path.lower()):
            # Redirect to linked file
            netpath = link.to_path + filename[link.fromlength:]
            try:
                h = open(netpath, 'rb')
                Com_DPrintf(f"link file: {netpath}\n")
                length = _FS_filelength(h)
                return (h, length)
            except:
                return (None, -1)
        link = link.next

    # Search through search paths
    search = fs_searchpaths
    while search:
        # Try PAK file
        if search.pack:
            pak = search.pack
            # Look through PAK directory
            for i in range(pak.numfiles):
                if pak.files[i].name.lower() == filename.lower():
                    # Found it in PAK!
                    file_from_pak = True
                    Com_DPrintf(f"PackFile: {pak.filename} : {filename}\n")

                    # Open PAK file and seek to data
                    try:
                        h = open(pak.filename, 'rb')
                        h.seek(pak.files[i].filepos)
                        return (h, pak.files[i].filelen)
                    except:
                        Com_Error(1, f"Couldn't reopen {pak.filename}")
                        return (None, -1)
        else:
            # Try directory
            netpath = f"{search.filename}/{filename}"
            try:
                h = open(netpath, 'rb')
                Com_DPrintf(f"FindFile: {netpath}\n")
                length = _FS_filelength(h)
                return (h, length)
            except:
                pass

        search = search.next

    Com_DPrintf(f"FindFile: can't find {filename}\n")
    return (None, -1)


def FS_Read(buffer, length, f):
    """
    Read file data in blocks.
    buffer should be a bytearray.
    """
    remaining = length
    offset = 0

    while remaining > 0:
        block = min(remaining, MAX_READ)
        data = f.read(block)

        if len(data) == 0:
            Com_Error(1, "FS_Read: 0 bytes read")
            return

        if len(data) < block:
            Com_Error(1, "FS_Read: incomplete read")
            return

        # Copy to buffer
        buffer[offset:offset+len(data)] = data
        offset += len(data)
        remaining -= len(data)


def FS_LoadPackFile(packfile):
    """
    Load a PAK file and return Pack object, or None if invalid.
    """
    try:
        packhandle = open(packfile, 'rb')
    except:
        return None

    # Read header
    header_data = packhandle.read(12)  # 3 ints = 12 bytes
    if len(header_data) < 12:
        packhandle.close()
        return None

    # Parse header (little-endian)
    ident, dirofs, dirlen = struct.unpack('<III', header_data)

    # Check header
    if ident != IDPAKHEADER:
        Com_Error(1, f"{packfile} is not a packfile")
        packhandle.close()
        return None

    # Check number of files
    numpackfiles = dirlen // 64  # Each entry is 56 bytes name + 4 + 4
    if numpackfiles > MAX_FILES_IN_PACK:
        Com_Error(1, f"{packfile} has {numpackfiles} files")
        packhandle.close()
        return None

    # Read directory
    packhandle.seek(dirofs)
    dir_data = packhandle.read(dirlen)

    if len(dir_data) < dirlen:
        Com_Error(1, f"Couldn't read directory from {packfile}")
        packhandle.close()
        return None

    # Parse directory entries
    newfiles = []
    for i in range(numpackfiles):
        offset = i * 64
        # Entry is: name[56] (null-terminated), filepos (4 bytes), filelen (4 bytes)
        name_bytes = dir_data[offset:offset+56]
        name = name_bytes.split(b'\0')[0].decode('ascii', errors='ignore')
        filepos, filelen = struct.unpack('<II', dir_data[offset+56:offset+64])

        newfiles.append(PackFile(name, filepos, filelen))

    # Create pack object
    pack = Pack(packfile, packhandle, numpackfiles, newfiles)
    return pack


def FS_AddGameDirectory(dir_path):
    """
    Add directory to search path.
    Also loads any .PAK files in the directory.
    """
    global fs_searchpaths

    # Look for .pak files
    try:
        pak_files = sorted([f for f in os.listdir(dir_path) if f.lower().endswith('.pak')])
    except:
        pak_files = []

    # Load each PAK file
    for pak_name in pak_files:
        pak_path = os.path.join(dir_path, pak_name)
        pack = FS_LoadPackFile(pak_path)
        if pack:
            # Add to search path
            new_search = SearchPath(pak_name, pack)
            new_search.next = fs_searchpaths
            fs_searchpaths = new_search

    # Add directory to search path
    new_search = SearchPath(dir_path, None)
    new_search.next = fs_searchpaths
    fs_searchpaths = new_search


def FS_InitFilesystem():
    """Initialize filesystem with search paths"""
    global fs_gamedir, fs_searchpaths, fs_base_searchpaths

    # For now, use current directory as base
    base_dir = os.getcwd()

    # Add baseq2 directory
    baseq2_path = os.path.join(base_dir, "baseq2")
    if os.path.isdir(baseq2_path):
        FS_AddGameDirectory(baseq2_path)
    else:
        # Try relative to Quake2Python
        baseq2_path = os.path.join(os.path.dirname(__file__), "..", "baseq2")
        if os.path.isdir(baseq2_path):
            FS_AddGameDirectory(baseq2_path)

    fs_base_searchpaths = fs_searchpaths
    fs_gamedir = baseq2_path


# ===== Internal Helper Functions =====

def _FS_filelength(f):
    """Get file length without changing position"""
    current_pos = f.tell()
    f.seek(0, 2)  # Seek to end
    length = f.tell()
    f.seek(current_pos)  # Restore position
    return length


# ===== TODO Functions (not yet implemented) =====

@TODO
def FS_CreatePath(path):
    """Create directories as needed for path"""
    pass


@TODO
def FS_FCloseFile(f):
    """Close a file opened by FS_FOpenFile"""
    pass


@TODO
def COM_SkipPath(pathname):
    pass


@TODO
def COM_StripExtension(in_str):
    pass


@TODO
def COM_FileBase(in_str):
    pass

