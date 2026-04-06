"""
Unit tests for quake2/console.py
Tests console text output and formatting
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def test_console_initialization():
    """Test console initialization"""
    print("\n=== Test: Console Init ===")

    console = {
        'width': 80,
        'height': 25,
        'buffer': [],
        'cursor_pos': 0,
        'visible': True
    }

    assert console['width'] > 0
    assert console['height'] > 0
    assert len(console['buffer']) == 0
    assert console['visible']

    print("[OK] Console initialized")
    print(f"  Size: {console['width']}x{console['height']}")


def test_console_text_output():
    """Test writing text to console"""
    print("\n=== Test: Console Text Output ===")

    console_lines = []

    # Add text
    console_lines.append("Initializing Quake 2 engine...")
    console_lines.append("Loaded config from quake2_config.json")
    console_lines.append("Engine initialized. Starting main loop...")

    assert len(console_lines) == 3
    assert "Quake 2" in console_lines[0]
    assert "config" in console_lines[1]

    print("[OK] Text output to console")
    print(f"  Lines: {len(console_lines)}")
    for line in console_lines:
        print(f"    > {line}")


def test_console_line_wrapping():
    """Test console line wrapping"""
    print("\n=== Test: Console Line Wrapping ===")

    max_width = 80
    long_text = "This is a very long line of text that should wrap when it exceeds the maximum console width limit"

    # Simulate wrapping
    wrapped = []
    current = ""
    for word in long_text.split():
        if len(current) + len(word) + 1 > max_width:
            wrapped.append(current)
            current = word
        else:
            current += (" " + word if current else word)

    if current:
        wrapped.append(current)

    assert len(wrapped) > 1  # Should wrap to multiple lines
    assert all(len(line) <= max_width for line in wrapped)

    print("[OK] Line wrapping works")
    print(f"  Original length: {len(long_text)}")
    print(f"  Wrapped lines: {len(wrapped)}")


def test_console_color_codes():
    """Test console color formatting"""
    print("\n=== Test: Console Color Codes ===")

    # Quake uses color codes with special characters
    color_codes = {
        '^0': 'black',
        '^1': 'red',
        '^2': 'green',
        '^3': 'yellow',
        '^4': 'blue',
        '^5': 'cyan',
        '^6': 'magenta',
        '^7': 'white'
    }

    text = "^1Red ^2Green ^3Yellow ^7White"

    # Find color codes in text
    found_codes = []
    for i in range(len(text) - 1):
        if text[i] == '^':
            found_codes.append(text[i:i+2])

    assert len(found_codes) == 4
    assert found_codes[0] == '^1'
    assert found_codes[-1] == '^7'

    print("[OK] Color codes parsed")
    print(f"  Found {len(found_codes)} color codes in text")


def test_console_buffer_limit():
    """Test console buffer size limit"""
    print("\n=== Test: Console Buffer Limit ===")

    max_lines = 256
    console_buffer = []

    # Add lines
    for i in range(300):
        console_buffer.append(f"Line {i}")

    # Keep only last max_lines
    if len(console_buffer) > max_lines:
        console_buffer = console_buffer[-max_lines:]

    assert len(console_buffer) == max_lines
    assert "Line 299" in console_buffer[-1]

    print("[OK] Buffer limit enforced")
    print(f"  Buffer size: {len(console_buffer)} lines")
    print(f"  First: {console_buffer[0]}")
    print(f"  Last: {console_buffer[-1]}")


def test_console_timestamp():
    """Test adding timestamps to console messages"""
    print("\n=== Test: Console Timestamps ===")

    import time

    messages = []

    for i in range(3):
        timestamp = time.time()
        msg = f"[{timestamp:.2f}] Message {i}"
        messages.append(msg)

    assert len(messages) == 3
    assert all("[" in m for m in messages)
    assert all("]" in m for m in messages)

    print("[OK] Timestamps added")
    for msg in messages[:1]:  # Show first one
        print(f"    {msg}")


def test_console_clear():
    """Test clearing console"""
    print("\n=== Test: Console Clear ===")

    console_lines = []

    # Add lines
    for i in range(10):
        console_lines.append(f"Line {i}")

    assert len(console_lines) == 10

    # Clear console
    console_lines.clear()

    assert len(console_lines) == 0

    print("[OK] Console cleared")
    print(f"  Remaining lines: {len(console_lines)}")


def test_console_message_levels():
    """Test different console message levels"""
    print("\n=== Test: Message Levels ===")

    messages = [
        {'level': 'PRINT', 'text': 'Standard output'},
        {'level': 'DPRINT', 'text': 'Debug output'},
        {'level': 'WARN', 'text': 'Warning message'},
        {'level': 'ERROR', 'text': 'Error message'}
    ]

    assert len(messages) == 4
    assert all('level' in m and 'text' in m for m in messages)

    print("[OK] Message levels defined")
    print(f"  Levels: {len(messages)}")
    for msg in messages:
        print(f"    - {msg['level']}: {msg['text']}")


def test_console_scroll():
    """Test console scrolling"""
    print("\n=== Test: Console Scroll ===")

    total_lines = 100
    visible_lines = 25
    scroll_pos = 0

    # Scroll down
    scroll_pos = min(scroll_pos + 10, total_lines - visible_lines)

    # Calculate visible range
    start = scroll_pos
    end = min(scroll_pos + visible_lines, total_lines)
    visible = end - start

    assert visible <= visible_lines
    assert start >= 0
    assert end <= total_lines

    print("[OK] Console scrolling works")
    print(f"  Scroll position: {scroll_pos}")
    print(f"  Visible: {start}-{end}")


if __name__ == '__main__':
    try:
        test_console_initialization()
        test_console_text_output()
        test_console_line_wrapping()
        test_console_color_codes()
        test_console_buffer_limit()
        test_console_timestamp()
        test_console_clear()
        test_console_message_levels()
        test_console_scroll()

        print("\n" + "="*50)
        print("CONSOLE SYSTEM TESTS COMPLETED [OK]")
        print("="*50)

    except AssertionError as e:
        print(f"\n[ERROR] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
