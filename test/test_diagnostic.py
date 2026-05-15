#!/usr/bin/env python3
"""
Diagnostic test for dpfpdd_query_devices to identify struct mismatch
"""

import ctypes
from ctypes import c_int, c_char_p, c_char, c_uint, c_ubyte, c_void_p, c_ushort, POINTER, Structure, byref, sizeof

# Minimal structure matching dpfpdd.h exactly
class DPFPDD_VER_INFO(Structure):
    _fields_ = [
        ("major", c_int),
        ("minor", c_int),
        ("maintenance", c_int),
    ]

class DPFPDD_HW_DESCR(Structure):
    _fields_ = [
        ("vendor_name", c_char * 128),
        ("product_name", c_char * 128),
        ("serial_num", c_char * 128),
    ]

class DPFPDD_HW_ID(Structure):
    _fields_ = [
        ("vendor_id", c_ushort),
        ("product_id", c_ushort),
    ]

class DPFPDD_HW_VERSION(Structure):
    _fields_ = [
        ("hw_ver", DPFPDD_VER_INFO),
        ("fw_ver", DPFPDD_VER_INFO),
        ("bcd_rev", c_ushort),
    ]

class DPFPDD_DEV_INFO(Structure):
    _fields_ = [
        ("size", c_uint),
        ("name", c_char * 1024),
        ("descr", DPFPDD_HW_DESCR),
        ("id", DPFPDD_HW_ID),
        ("ver", DPFPDD_HW_VERSION),
        ("modality", c_uint),
        ("technology", c_uint),
    ]

print(f"[*] DPFPDD_DEV_INFO size: {sizeof(DPFPDD_DEV_INFO)} bytes")
print(f"    Expected: ~1450 bytes")

lib = ctypes.WinDLL('./dpfpdd.dll')
lib.dpfpdd_init.argtypes = []
lib.dpfpdd_init.restype = c_int
lib.dpfpdd_exit.argtypes = []
lib.dpfpdd_exit.restype = c_int
lib.dpfpdd_query_devices.argtypes = [POINTER(c_uint), POINTER(DPFPDD_DEV_INFO)]
lib.dpfpdd_query_devices.restype = c_int

print("\n[*] Calling dpfpdd_init...")
res_init = lib.dpfpdd_init()
print(f"    Result: {res_init}")

print("\n[*] Creating array for devices...")
count = c_uint(1)
infos = (DPFPDD_DEV_INFO * 1)()
infos[0].size = sizeof(DPFPDD_DEV_INFO)
print(f"    Array created, item size set to {infos[0].size}")

print("\n[*] Calling dpfpdd_query_devices...")
try:
    res = lib.dpfpdd_query_devices(byref(count), infos)
    print(f"    Result: {res}, count: {count.value}")
    if count.value > 0:
        print(f"    Device 0 name: {bytes(infos[0].name).split(b'\\x00')[0]}")
        print(f"    Device 0 product: {bytes(infos[0].descr.product_name).split(b'\\x00')[0]}")
except Exception as e:
    print(f"    ERROR: {e}")

print("\n[*] Calling dpfpdd_exit...")
res_exit = lib.dpfpdd_exit()
print(f"    Result: {res_exit}")
