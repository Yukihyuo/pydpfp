import struct

with open('dpfpdd.dll', 'rb') as f:
    data = f.read(1024)

# Check MZ header
if data[:2] == b'MZ':
    print("[+] Valid PE header found (MZ signature)")
    # Get PE offset at bytes 0x3C-0x3F
    pe_offset = struct.unpack('<I', data[0x3C:0x40])[0]
    print(f"[*] PE offset: {hex(pe_offset)}")
    
    # Machine type is at offset 4 in PE header
    if pe_offset + 4 < len(data):
        machine = struct.unpack('<H', data[pe_offset+4:pe_offset+6])[0]
        machine_names = {0x8664: 'x64', 0x14c: 'i386', 0xaa64: 'ARM64'}
        print(f"[*] Machine type: {hex(machine)} ({machine_names.get(machine, 'unknown')})")
else:
    print("[-] Not a PE file")
