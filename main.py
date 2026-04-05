import sys
import os

# Add project root to path so all modules can import each other
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import quake2, game, ref_gl

quake2.sys_win.WinMain(len(sys.argv), sys.argv)
