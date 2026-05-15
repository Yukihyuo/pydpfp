#!/usr/bin/env python3
"""
Test: Explicit pointer creation
"""

import ctypes
from ctypes import c_int, c_char, c_uint, c_ushort, POINTER, Structure, byref, sizeof, addressof

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

# Test 1: Using ctypes.cast() to create pointer
print("\n[TEST 1] Using ctypes.cast()")
count1 = c_uint(1)
infos1 = (DPFPDD_DEV_INFO * 1)()
infos1[0].size = sizeof(DPFPDD_DEV_INFO)
try:
    ptr = ctypes.cast(infos1, POINTER(DPFPDD_DEV_INFO))
    res1 = lib.dpfpdd_query_devices(byref(count1), ptr)
    print(f"  Result: {res1}, count: {count1.value}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 2: Using addressof and ctypes.cast
print("\n[TEST 2] Using addressof + cast")
count2 = c_uint(1)
infos2 = (DPFPDD_DEV_INFO * 1)()
infos2[0].size = sizeof(DPFPDD_DEV_INFO)
try:
    ptr2 = ctypes.cast(addressof(infos2), POINTER(DPFPDD_DEV_INFO))
    res2 = lib.dpfpdd_query_devices(byref(count2), ptr2)
    print(f"  Result: {res2}, count: {count2.value}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 3: Direct pointer to first element
print("\n[TEST 3] Direct pointer to first element")
count3 = c_uint(1)
infos3 = (DPFPDD_DEV_INFO * 1)()
infos3[0].size = sizeof(DPFPDD_DEV_INFO)
try:
    res3 = lib.dpfpdd_query_devices(byref(count3), byref(infos3[0]))
    print(f"  Result: {res3}, count: {count3.value}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n[*] Exit...", lib.dpfpdd_exit())
