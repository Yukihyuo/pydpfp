#!/usr/bin/env python3
"""
Test: Try different parameter types for query_devices
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

print("[*] Init:", lib.dpfpdd_init())

# Try with use_errno to capture more error info
lib.dpfpdd_query_devices.use_errno = True

# Test 1: Try passing array directly without byref
print("\n[TEST 1] Direct array pass")
lib.dpfpdd_query_devices.argtypes = [POINTER(c_uint), POINTER(DPFPDD_DEV_INFO)]
lib.dpfpdd_query_devices.restype = c_int
count1 = c_uint(1)
infos1 = (DPFPDD_DEV_INFO * 1)()
infos1[0].size = sizeof(DPFPDD_DEV_INFO)
try:
    res1 = lib.dpfpdd_query_devices(ctypes.cast(infos1, POINTER(c_uint)), byref(infos1[0]))
    print(f"  Result: {res1}, count: {count1.value}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test 2: Try with no signatures set
print("\n[TEST 2] No argtypes/restype set")
lib2 = ctypes.WinDLL('./dpfpdd.dll')
count2 = c_uint(1)
infos2 = (DPFPDD_DEV_INFO * 1)()
infos2[0].size = sizeof(DPFPDD_DEV_INFO)
try:
    res2 = lib2.dpfpdd_query_devices(byref(count2), byref(infos2[0]))
    print(f"  Result: {res2}, count: {count2.value}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n[*] Exit:", lib.dpfpdd_exit())
