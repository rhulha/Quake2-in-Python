#!/usr/bin/env python
"""Simple test to check if texinfo parsing works"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ref_gl import gl_rsurf

# Create a mock worldmodel with some test data
class MockModel:
    def __init__(self):
        self.lump_texinfo = b'\x00' * 76  # One dummy texinfo entry
        self._texinfo_cache = None
        self.faces = [{'texinfo': 0}]

print("Testing _parse_texinfo_entry...")
model = MockModel()
result = gl_rsurf._parse_texinfo_entry(model.lump_texinfo, 0)
print(f"Parse result keys: {result.keys() if result else 'None'}")

print("\nTesting _get_texinfo...")
texinfo = gl_rsurf._get_texinfo(model, 0)
print(f"Get texinfo result: {texinfo is not None}")

print(f"\nTexinfo cache after call: {model._texinfo_cache is not None}")
