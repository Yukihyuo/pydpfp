#!/usr/bin/env python3
"""
Diagnostic: Struct field offsets and padding
"""

import ctypes
from ctypes import c_int, c_char, c_uint, c_ushort, POINTER, Structure, sizeof

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

# Print sizes
print("[STRUCTURE SIZES]")
print(f"DPFPDD_VER_INFO: {sizeof(DPFPDD_VER_INFO)} bytes")
print(f"DPFPDD_HW_DESCR: {sizeof(DPFPDD_HW_DESCR)} bytes")
print(f"DPFPDD_HW_ID: {sizeof(DPFPDD_HW_ID)} bytes")
print(f"DPFPDD_HW_VERSION: {sizeof(DPFPDD_HW_VERSION)} bytes")
print(f"DPFPDD_DEV_INFO: {sizeof(DPFPDD_DEV_INFO)} bytes")

# Print field offsets
print("\n[DPFPDD_DEV_INFO FIELD SIZES]")
print(f"size: {sizeof(c_uint)} bytes")
print(f"name: {sizeof(c_char * 1024)} bytes")
print(f"descr: {sizeof(DPFPDD_HW_DESCR)} bytes")
print(f"id: {sizeof(DPFPDD_HW_ID)} bytes")
print(f"ver: {sizeof(DPFPDD_HW_VERSION)} bytes")
print(f"modality: {sizeof(c_uint)} bytes")
print(f"technology: {sizeof(c_uint)} bytes")

# Manual calculation
manual_size = 4 + 1024 + (128*3) + 4 + (12*2 + 2) + 4 + 4
print(f"\nManual calculation: {manual_size} bytes")
print(f"Actual: {sizeof(DPFPDD_DEV_INFO)} bytes")
print(f"Match: {manual_size == sizeof(DPFPDD_DEV_INFO)}")

# Also check VERSION structure used in dpfpdd_version (which works!)
print("\n[DPFPDD_VERSION (for comparison - this one works)]")
class DPFPDD_VERSION(Structure):
    _fields_ = [("size", c_uint), ("lib_ver", DPFPDD_VER_INFO), ("api_ver", DPFPDD_VER_INFO)]

print(f"DPFPDD_VERSION: {sizeof(DPFPDD_VERSION)} bytes")
print(f"  Manual: 4 + 12 + 12 = {4+12+12} bytes")

# Try creating instances
print("\n[INSTANCE CREATION TEST]")
try:
    v = DPFPDD_VERSION()
    v.size = sizeof(DPFPDD_VERSION)
    print(f"DPFPDD_VERSION instance created OK, size set to {v.size}")
except Exception as e:
    print(f"ERROR creating DPFPDD_VERSION: {e}")

try:
    d = DPFPDD_DEV_INFO()
    d.size = sizeof(DPFPDD_DEV_INFO)
    print(f"DPFPDD_DEV_INFO instance created OK, size set to {d.size}")
except Exception as e:
    print(f"ERROR creating DPFPDD_DEV_INFO: {e}")
