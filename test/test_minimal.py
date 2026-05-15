#!/usr/bin/env python3
"""
Test: dpfpdd_version as simpler test case
"""

import ctypes
from ctypes import c_int, c_uint, POINTER, Structure, byref, sizeof

# Define simple structures
class DPFPDD_VER_INFO(Structure):
    _fields_ = [("major", c_int), ("minor", c_int), ("maintenance", c_int)]

class DPFPDD_VERSION(Structure):
    _fields_ = [("size", c_uint), ("lib_ver", DPFPDD_VER_INFO), ("api_ver", DPFPDD_VER_INFO)]

lib = ctypes.WinDLL('./dpfpdd.dll')
lib.dpfpdd_init.argtypes = []
lib.dpfpdd_init.restype = c_int
lib.dpfpdd_exit.argtypes = []
lib.dpfpdd_exit.restype = c_int
lib.dpfpdd_version.argtypes = [POINTER(DPFPDD_VERSION)]
lib.dpfpdd_version.restype = c_int

print("[*] Init:", lib.dpfpdd_init())

# Test: Call dpfpdd_version
print("\n[TEST] Call dpfpdd_version")
print(f"    Structure size: {sizeof(DPFPDD_VERSION)} bytes")
ver = DPFPDD_VERSION()
ver.size = sizeof(DPFPDD_VERSION)
try:
    res = lib.dpfpdd_version(byref(ver))
    print(f"  Result: {res}")
    if res == 0:
        print(f"  Library version: {ver.lib_ver.major}.{ver.lib_ver.minor}.{ver.lib_ver.maintenance}")
        print(f"  API version: {ver.api_ver.major}.{ver.api_ver.minor}.{ver.api_ver.maintenance}")
    else:
        print(f"  ERROR: {res} (hex: {hex(res)})")
except Exception as e:
    print(f"  EXCEPTION: {e}")
    import traceback
    traceback.print_exc()

print("\n[*] Exit:", lib.dpfpdd_exit())
