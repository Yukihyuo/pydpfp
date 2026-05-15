#!/usr/bin/env python3
"""
Test: Query devices without initializing size field
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

lib = ctypes.WinDLL('./dpfpdd.dll')
lib.dpfpdd_init.argtypes = []
lib.dpfpdd_init.restype = c_int
lib.dpfpdd_exit.argtypes = []
lib.dpfpdd_exit.restype = c_int
lib.dpfpdd_query_devices.argtypes = [POINTER(c_uint), POINTER(DPFPDD_DEV_INFO)]
lib.dpfpdd_query_devices.restype = c_int

print("[*] Init...", lib.dpfpdd_init())

# Test 1: Don't set size field
print("\n[TEST 1] Without size initialization")
count1 = c_uint(1)
infos1 = (DPFPDD_DEV_INFO * 1)()
# DON'T set size
try:
    res1 = lib.dpfpdd_query_devices(byref(count1), infos1)
    print(f"  Result: {res1}, count: {count1.value}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 2: With size = 0
print("\n[TEST 2] With size = 0")
count2 = c_uint(1)
infos2 = (DPFPDD_DEV_INFO * 1)()
infos2[0].size = 0
try:
    res2 = lib.dpfpdd_query_devices(byref(count2), infos2)
    print(f"  Result: {res2}, count: {count2.value}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 3: With different size value
print("\n[TEST 3] With size = 1024")
count3 = c_uint(1)
infos3 = (DPFPDD_DEV_INFO * 1)()
infos3[0].size = 1024
try:
    res3 = lib.dpfpdd_query_devices(byref(count3), infos3)
    print(f"  Result: {res3}, count: {count3.value}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 4: With correct size
print("\n[TEST 4] With correct size")
count4 = c_uint(1)
infos4 = (DPFPDD_DEV_INFO * 1)()
infos4[0].size = sizeof(DPFPDD_DEV_INFO)
print(f"  Setting size to {sizeof(DPFPDD_DEV_INFO)}")
try:
    res4 = lib.dpfpdd_query_devices(byref(count4), infos4)
    print(f"  Result: {res4}, count: {count4.value}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n[*] Exit...", lib.dpfpdd_exit())
