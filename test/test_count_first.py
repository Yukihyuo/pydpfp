#!/usr/bin/env python3
"""
Test: Initialize count with max devices first
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

# Try: First call count to get max, pass NULL buffer
print("\n[TEST] First: Get count with NULL buffer")
count = c_uint(10)  # Initialize with max count
res = lib.dpfpdd_query_devices(byref(count), None)
print(f"  Result: {res}, count returned: {count.value}")

if count.value > 0:
    print(f"\n[SUCCESS] Found {count.value} device(s)!")
    # Now allocate based on count and retrieve device info
    max_dev = count.value
    infos = (DPFPDD_DEV_INFO * max_dev)()
    for i in range(max_dev):
        infos[i].size = sizeof(DPFPDD_DEV_INFO)
    
    count = c_uint(max_dev)
    res2 = lib.dpfpdd_query_devices(byref(count), infos)
    print(f"  Second call result: {res2}, count: {count.value}")
    for i in range(count.value):
        print(f"    Device {i}: {bytes(infos[i].name).split(b'\\x00')[0]}")
else:
    print(f"\n[INFO] No devices found (count={count.value})")

print("\n[*] Exit...", lib.dpfpdd_exit())
