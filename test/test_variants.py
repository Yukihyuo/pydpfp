#!/usr/bin/env python3
"""
Test variant: Single struct instead of array
"""

import ctypes
from ctypes import c_int, c_char_p, c_char, c_uint, c_ubyte, c_void_p, c_ushort, POINTER, Structure, byref, sizeof

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

# Variant 1: Allocate array, pass first element
print("\n[VARIANT 1] Array[1], pass first element")
count1 = c_uint(1)
arr1 = (DPFPDD_DEV_INFO * 1)()
arr1[0].size = sizeof(DPFPDD_DEV_INFO)
try:
    res1 = lib.dpfpdd_query_devices(byref(count1), byref(arr1[0]))
    print(f"  Result: {res1}, count: {count1.value}")
    if count1.value > 0:
        print(f"  Device: {bytes(arr1[0].name).split(b'\\x00')[0]}")
except Exception as e:
    print(f"  ERROR: {e}")

# Variant 2: Create single struct, pass its pointer
print("\n[VARIANT 2] Single struct")
count2 = c_uint(1)
info2 = DPFPDD_DEV_INFO()
info2.size = sizeof(DPFPDD_DEV_INFO)
try:
    res2 = lib.dpfpdd_query_devices(byref(count2), byref(info2))
    print(f"  Result: {res2}, count: {count2.value}")
    if count2.value > 0:
        print(f"  Device: {bytes(info2.name).split(b'\\x00')[0]}")
except Exception as e:
    print(f"  ERROR: {e}")

# Variant 3: Use only count in first call to get device count
print("\n[VARIANT 3] First call with count only")
count3 = c_uint(0)
try:
    res3 = lib.dpfpdd_query_devices(byref(count3), None)
    print(f"  Result: {res3}, count: {count3.value}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n[*] Exit...", lib.dpfpdd_exit())
