#!/usr/bin/env python3
"""
Test: Get function address and examine it
"""

import ctypes

lib = ctypes.WinDLL('./dpfpdd.dll')

# Get addresses
try:
    addr_query = ctypes.cast(lib.dpfpdd_query_devices, ctypes.c_void_p).value
    addr_version = ctypes.cast(lib.dpfpdd_version, ctypes.c_void_p).value
    addr_init = ctypes.cast(lib.dpfpdd_init, ctypes.c_void_p).value
    
    print(f"dpfpdd_init: 0x{addr_init:x}")
    print(f"dpfpdd_version: 0x{addr_version:x}")
    print(f"dpfpdd_query_devices: 0x{addr_query:x}")
    
    # Try to read first few bytes of query_devices to see if it's valid code
    print(f"\n[*] First 16 bytes of dpfpdd_query_devices:")
    try:
        # This is risky but let's see
        data = ctypes.string_at(addr_query, 16)
        print(f"    Hex: {data.hex()}")
        print(f"    As text: {repr(data)}")
    except:
        print("    Cannot read")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
