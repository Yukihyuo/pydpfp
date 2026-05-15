#!/usr/bin/env python3
"""
Test: Use generic c_void_p and raw memory allocation
"""

import ctypes
from ctypes import c_int, c_uint, POINTER, byref, sizeof, string_at, create_string_buffer

# Simple test: allocate raw memory and use as generic buffer
print("[TEST] Raw memory allocation with c_void_p")

lib = ctypes.WinDLL('./dpfpdd.dll')
lib.dpfpdd_init.argtypes = []
lib.dpfpdd_init.restype = c_int
lib.dpfpdd_query_devices.argtypes = [POINTER(c_uint), POINTER(c_int)]  # Use c_int as generic type
lib.dpfpdd_query_devices.restype = c_int

res_init = lib.dpfpdd_init()
print(f"Init: {res_init}")

# Allocate buffer for device info
# Estimated size per structure: 4 + 1024 + (128*3) + 4 + 26 + 4 + 4 = 1452 bytes
struct_size = 1452
max_devices = 1
buffer_size = struct_size * max_devices

# Create raw buffer
buf = create_string_buffer(buffer_size)

# Try to initialize first 4 bytes as size (little-endian c_uint)
size_val = ctypes.c_uint(struct_size)
ctypes.memmove(buf, byref(size_val), 4)

print(f"Allocated {buffer_size} bytes, set size field to {struct_size}")

# Attempt query
count = c_uint(1)
try:
    # Cast buffer to proper type for function signature
    res = lib.dpfpdd_query_devices(byref(count), ctypes.cast(buf, POINTER(c_int)))
    print(f"Query result: {res}, count: {count.value}")
    
    # Try to read device name (starts at offset 4)
    device_name = buf[4:4+1024].rstrip(b'\x00').decode('utf-8', errors='ignore')
    print(f"Device name: {device_name[:50]}")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

lib.dpfpdd_exit()
