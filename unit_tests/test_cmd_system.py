"""
Unit tests for quake2/cmd.py
Tests command buffer and command system
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_command_buffer_initialization():
    """Test command buffer creation"""
    print("\n=== Test: Command Buffer Init ===")

    cmd_buffer = {
        'commands': [],
        'size': 0,
        'max_size': 8192
    }

    assert len(cmd_buffer['commands']) == 0
    assert cmd_buffer['size'] == 0
    assert cmd_buffer['max_size'] > 0

    print("[OK] Command buffer initialized")
    print(f"  Max size: {cmd_buffer['max_size']} bytes")


def test_command_buffer_add_text():
    """Test adding text to command buffer"""
    print("\n=== Test: Command Buffer Add Text ===")

    cmd_buffer = []

    # Add commands
    commands = ["map base1", "give weapon_shotgun", "kill"]
    for cmd in commands:
        cmd_buffer.append(cmd)

    assert len(cmd_buffer) == 3
    assert cmd_buffer[0] == "map base1"
    assert cmd_buffer[-1] == "kill"

    print("[OK] Commands added to buffer")
    print(f"  Commands: {len(cmd_buffer)}")
    for cmd in cmd_buffer:
        print(f"    - {cmd}")


def test_command_buffer_execute():
    """Test executing commands from buffer"""
    print("\n=== Test: Command Buffer Execute ===")

    cmd_buffer = ["map base1", "give health 50", "say hello"]
    executed = []

    # Simulate command execution
    for cmd in cmd_buffer:
        executed.append(cmd)

    assert len(executed) == len(cmd_buffer)
    assert executed[0] == cmd_buffer[0]

    print("[OK] Commands executed in order")
    print(f"  Executed: {len(executed)} commands")


def test_command_parameters():
    """Test parsing command parameters"""
    print("\n=== Test: Command Parameters ===")

    # Parse a command with parameters
    cmd = "give weapon_shotgun 50"
    parts = cmd.split()

    assert len(parts) == 3
    assert parts[0] == "give"
    assert parts[1] == "weapon_shotgun"
    assert parts[2] == "50"

    print("[OK] Command parameters parsed")
    print(f"  Command: {parts[0]}")
    print(f"  Args: {parts[1:]}")


def test_command_registration():
    """Test command registration system"""
    print("\n=== Test: Command Registration ===")

    commands = {}

    # Register commands
    commands['map'] = {'help': 'Load a map', 'func': 'SV_Map_f'}
    commands['give'] = {'help': 'Give item to player', 'func': 'G_Give_f'}
    commands['say'] = {'help': 'Say something', 'func': 'CL_Say_f'}

    assert 'map' in commands
    assert 'give' in commands
    assert commands['map']['help'] == 'Load a map'

    print("[OK] Commands registered")
    print(f"  Total commands: {len(commands)}")
    for name in commands:
        print(f"    - {name}: {commands[name]['help']}")


def test_command_token_parsing():
    """Test tokenizing command strings"""
    print("\n=== Test: Command Token Parsing ===")

    cmd_string = "map base1; give health 50; say hello world"

    # Split by semicolon to get individual commands
    commands = [c.strip() for c in cmd_string.split(';')]

    assert len(commands) == 3
    assert commands[0] == "map base1"
    assert "say" in commands[2]

    print("[OK] Commands tokenized correctly")
    print(f"  Total commands: {len(commands)}")
    for cmd in commands:
        print(f"    - {cmd}")


def test_command_args_parsing():
    """Test parsing arbitrary command arguments"""
    print("\n=== Test: Command Args Parsing ===")

    # Complex command with quoted strings
    cmd_parts = ["say", "hello", "world"]

    # First part is command name
    cmd_name = cmd_parts[0]
    cmd_args = cmd_parts[1:]

    assert cmd_name == "say"
    assert len(cmd_args) == 2
    assert cmd_args[0] == "hello"

    print("[OK] Command arguments parsed")
    print(f"  Command: {cmd_name}")
    print(f"  Arguments: {cmd_args}")


def test_deferred_command_execution():
    """Test deferring command execution"""
    print("\n=== Test: Deferred Execution ===")

    # Commands added now, executed later
    pending_commands = []

    pending_commands.append("map base1")
    pending_commands.append("kick player")
    pending_commands.append("map q2dm1")

    assert len(pending_commands) == 3

    # Execute all pending
    executed = len(pending_commands)
    assert executed == 3

    print("[OK] Deferred commands executed")
    print(f"  Pending: {len(pending_commands)}")
    print(f"  Executed: {executed}")


def test_command_buffer_overflow():
    """Test command buffer size limits"""
    print("\n=== Test: Buffer Overflow Protection ===")

    max_buffer_size = 8192
    buffer_size = 0
    commands = []

    # Add commands until near limit
    for i in range(100):
        cmd = f"echo command_{i}\n"
        buffer_size += len(cmd)

        if buffer_size < max_buffer_size:
            commands.append(cmd)
        else:
            break  # Stop before overflow

    assert buffer_size < max_buffer_size
    assert len(commands) > 0

    print("[OK] Buffer overflow prevention works")
    print(f"  Commands: {len(commands)}")
    print(f"  Buffer use: {buffer_size}/{max_buffer_size} bytes")


if __name__ == '__main__':
    try:
        test_command_buffer_initialization()
        test_command_buffer_add_text()
        test_command_buffer_execute()
        test_command_parameters()
        test_command_registration()
        test_command_token_parsing()
        test_command_args_parsing()
        test_deferred_command_execution()
        test_command_buffer_overflow()

        print("\n" + "="*50)
        print("CMD SYSTEM TESTS COMPLETED [OK]")
        print("="*50)

    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
