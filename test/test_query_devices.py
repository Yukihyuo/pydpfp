#!/usr/bin/env python3
"""
Test: dpfpdd_query_devices now that we know struct marshaling works
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

print("[*] Init:", lib.dpfpdd_init())

print(f"\nDPFPDD_DEV_INFO size: {sizeof(DPFPDD_DEV_INFO)} bytes")

# Test 1: Try with larger buffer allocation (10 devices)
print("\n[TEST 1] Allocate for 10 devices, try query")
max_devices = 10
count1 = c_uint(max_devices)
infos1 = (DPFPDD_DEV_INFO * max_devices)()

# Initialize all size fields
for i in range(max_devices):
    infos1[i].size = sizeof(DPFPDD_DEV_INFO)

try:
    res1 = lib.dpfpdd_query_devices(byref(count1), infos1)
    print(f"  Result: {res1} (hex: {hex(res1)}), count returned: {count1.value}")
    
    # Try to read first device if successful
    if res1 == 0 and count1.value > 0:
        dev_name = bytes(infos1[0].name).split(b'\x00')[0].decode('utf-8', errors='ignore')
        print(f"  First device: {dev_name}")
    else:
        # Try to decode error
        if res1 == 96075796:
            print("  Error: DPFPDD_E_INVALID_PARAMETER")
        elif res1 == 96075789:
            print("  Error: DPFPDD_E_MORE_DATA")
        else:
            print(f"  Error code: {res1}")
except Exception as e:
    print(f"  EXCEPTION: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Try passing a pointer cast instead of array
print("\n[TEST 2] Cast to proper pointer type")
count2 = c_uint(10)
info2 = DPFPDD_DEV_INFO()
info2.size = sizeof(DPFPDD_DEV_INFO)
try:
    res2 = lib.dpfpdd_query_devices(byref(count2), byref(info2))
    print(f"  Result: {res2} (hex: {hex(res2)}), count: {count2.value}")
except Exception as e:
    print(f"  EXCEPTION: {e}")

print("\n[*] Exit:", lib.dpfpdd_exit())
