#!/usr/bin/env python3
"""
Test: Use _pack_=1 to eliminate struct padding
"""

import ctypes
from ctypes import c_int, c_char, c_uint, c_ushort, POINTER, Structure, byref, sizeof

class DPFPDD_VER_INFO(Structure):
    _pack_ = 1
    _fields_ = [("major", c_int), ("minor", c_int), ("maintenance", c_int)]

class DPFPDD_HW_DESCR(Structure):
    _pack_ = 1
    _fields_ = [("vendor_name", c_char * 128), ("product_name", c_char * 128), ("serial_num", c_char * 128)]

class DPFPDD_HW_ID(Structure):
    _pack_ = 1
    _fields_ = [("vendor_id", c_ushort), ("product_id", c_ushort)]

class DPFPDD_HW_VERSION(Structure):
    _pack_ = 1
    _fields_ = [("hw_ver", DPFPDD_VER_INFO), ("fw_ver", DPFPDD_VER_INFO), ("bcd_rev", c_ushort)]

class DPFPDD_DEV_INFO(Structure):
    _pack_ = 1
    _fields_ = [("size", c_uint), ("name", c_char * 1024), ("descr", DPFPDD_HW_DESCR), ("id", DPFPDD_HW_ID), ("ver", DPFPDD_HW_VERSION), ("modality", c_uint), ("technology", c_uint)]

lib = ctypes.WinDLL('./dpfpdd.dll')
lib.dpfpdd_init.argtypes = []
lib.dpfpdd_init.restype = c_int
lib.dpfpdd_exit.argtypes = []
lib.dpfpdd_exit.restype = c_int
lib.dpfpdd_query_devices.argtypes = [POINTER(c_uint), POINTER(DPFPDD_DEV_INFO)]
lib.dpfpdd_query_devices.restype = c_int

print("[*] Init:", lib.dpfpdd_init())

print(f"\nDPFPDD_DEV_INFO size with _pack_=1: {sizeof(DPFPDD_DEV_INFO)} bytes")

# Test with _pack_=1
print("\n[TEST] Call query_devices with _pack_=1")
count = c_uint(10)
infos = (DPFPDD_DEV_INFO * 10)()

# Initialize all size fields
for i in range(10):
    infos[i].size = sizeof(DPFPDD_DEV_INFO)

try:
    res = lib.dpfpdd_query_devices(byref(count), infos)
    print(f"  Result: {res} (hex: {hex(res)}), count: {count.value}")
    
    if res == 0 and count.value > 0:
        dev_name = bytes(infos[0].name).split(b'\x00')[0].decode('utf-8', errors='ignore')
        print(f"  First device: {dev_name}")
except Exception as e:
    print(f"  EXCEPTION: {e}")

print("\n[*] Exit:", lib.dpfpdd_exit())
