#!/usr/bin/env python3
"""
Test: Try both CDLL and WinDLL calling conventions
"""

import ctypes
from ctypes import c_int, c_char, c_uint, c_ushort, POINTER, Structure, byref, sizeof

class DPFPDD_VER_INFO(Structure):
    _fields_ = [("major", c_int), ("minor", c_int), ("maintenance", c_int)]

class DPFPDD_HW_DESCR(Structure):
    _fields_ = [("vendor_name", c_char * 128), ("product_name", c_char * 128), ("serial_num", c_char * 128)]

class DPFPDD_HW_ID(Structure):
    _fields_ = [("vendor_id", c_ushort), ("product_id", c_ushort)]

class DPFPDD_HW_VERSION(Structure):
    _fields_ = [("hw_ver", DPFPDD_VER_INFO), ("fw_ver", DPFPDD_VER_INFO), ("bcd_rev", c_ushort)]

class DPFPDD_DEV_INFO(Structure):
    _fields_ = [("size", c_uint), ("name", c_char * 1024), ("descr", DPFPDD_HW_DESCR), ("id", DPFPDD_HW_ID), ("ver", DPFPDD_HW_VERSION), ("modality", c_uint), ("technology", c_uint)]

# Test 1: WinDLL
print("[TEST 1] WinDLL (stdcall)")
try:
    lib = ctypes.WinDLL('./dpfpdd.dll')
    lib.dpfpdd_init.argtypes = []
    lib.dpfpdd_init.restype = c_int
    lib.dpfpdd_query_devices.argtypes = [POINTER(c_uint), POINTER(DPFPDD_DEV_INFO)]
    lib.dpfpdd_query_devices.restype = c_int
    
    res_init = lib.dpfpdd_init()
    print(f"  Init result: {res_init}")
    
    count = c_uint(1)
    infos = (DPFPDD_DEV_INFO * 1)()
    infos[0].size = sizeof(DPFPDD_DEV_INFO)
    res = lib.dpfpdd_query_devices(byref(count), byref(infos[0]))
    print(f"  Query result: {res}, count: {count.value}")
    print("  [SUCCESS]")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 2: CDLL
print("\n[TEST 2] CDLL (cdecl)")
try:
    lib2 = ctypes.CDLL('./dpfpdd.dll')
    lib2.dpfpdd_init.argtypes = []
    lib2.dpfpdd_init.restype = c_int
    lib2.dpfpdd_query_devices.argtypes = [POINTER(c_uint), POINTER(DPFPDD_DEV_INFO)]
    lib2.dpfpdd_query_devices.restype = c_int
    
    res_init = lib2.dpfpdd_init()
    print(f"  Init result: {res_init}")
    
    count = c_uint(1)
    infos = (DPFPDD_DEV_INFO * 1)()
    infos[0].size = sizeof(DPFPDD_DEV_INFO)
    res = lib2.dpfpdd_query_devices(byref(count), byref(infos[0]))
    print(f"  Query result: {res}, count: {count.value}")
    print("  [SUCCESS]")
except Exception as e:
    print(f"  ERROR: {e}")
