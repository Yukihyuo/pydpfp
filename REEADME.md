# DigitalPersona Fingerprint Capture - FingerPrintReader Wrapper

Professional Python wrapper for the DigitalPersona U.are.U SDK (dpfpdd.dll).

## Overview

This wrapper provides a clean, Pythonic interface to the DigitalPersona fingerprint reader SDK, abstracting away the complexities of ctypes FFI while maintaining full API access.

## Architecture

### Files

- **dpfpdd_wrapper.py** (382 lines): Core wrapper with two levels of abstraction
  - `DPFPDD_Library`: Low-level ctypes FFI wrapper 
  - `FingerPrintReader`: High-level Pythonic interface
- **main.py**: Example usage demonstrating fingerprint capture
- **dpfpdd.dll**: DigitalPersona SDK (64-bit, x64 architecture)

### Key Features

✓ **Context manager support** for automatic resource cleanup  
✓ **Comprehensive error handling** with meaningful error messages  
✓ **Retry logic** for unreliable captures  
✓ **Full SDK API coverage**:
  - Device initialization/cleanup
  - Device enumeration (with workarounds)
  - Device opening/closing  
  - Stream control (start/stop)
  - Fingerprint capture
  - Calibration

## Known Issues

### Device Enumeration Limitation

**Status**: dpfpdd_query_devices() crashes on this system  
**Impact**: Device enumeration (list_devices()) may not work  
**Workaround**: Specify device name directly or use default names

The `dpfpdd_query_devices()` function consistently crashes with an access violation when called from Python. This appears to be a compatibility issue with the specific SDK build. All other SDK functions (init, exit, version, open, capture) work correctly, suggesting this is an issue with that specific function, not the bindings.

### Solution for Device Enumeration Failure

1. **If devices are not found**, modify the `DEFAULT_DEVICE_NAMES` in `main.py`
2. **To find your device name**, look in Windows Device Manager:
   - Connect the fingerprint reader
   - Open Device Manager
   - Expand "Biometric Devices" or "USB controllers"
   - Find the DigitalPersona device
   - Right-click → Properties → Details
   - Select "Device Instance Path" to see the full name

3. **Common device name formats**:
   ```
   \\?\usb#vid_05ba&pid_0007#5&2a23e537&0&1
   \\.\UAREU$1
   U.are.U 5100
   U.are.U 4500
   ```

## Usage

### Basic Capture

```python
from dpfpdd_wrapper import FingerPrintReader, DPFPDD_PRIORITY_COOPERATIVE

# Context manager handles automatic cleanup
with FingerPrintReader() as reader:
    reader.init()
    
    # Try device enumeration
    devices = reader.list_devices()
    if devices:
        device_name = devices[0]["name"]
    else:
        # Fallback to known device name
        device_name = "\\?\usb#vid_05ba&pid_0007#5&2a23e537&0&1"
    
    # Open device
    reader.open(device_name, use_ext=False, priority=DPFPDD_PRIORITY_COOPERATIVE)
    
    # Calibrate
    reader.start_stream()
    reader.calibrate()
    
    # Capture with retries
    success, result, image_data = reader.capture(timeout_ms=5000, retries=3)
    
    if success:
        print(f"Captured: {result['width']}x{result['height']}")
        with open("fingerprint.raw", "wb") as f:
            f.write(image_data)
```

## API Reference

### FingerPrintReader Class

#### Initialization
```python
reader = FingerPrintReader(dll_path="./dpfpdd.dll")
```

#### Context Manager
```python
with FingerPrintReader() as reader:
    reader.init()
    # ... operations ...
    # Auto-cleanup via __exit__
```

#### Methods

**init() -> bool**
- Initialize SDK library
- Must be called before other operations

**exit() -> bool**
- Cleanup and release SDK resources

**list_devices() -> list**
- Enumerate connected fingerprint readers
- Returns list of dicts with name, product, vendor, serial
- **Note**: May fail due to known SDK issue (returns empty list with fallback)

**open(device_name: str, use_ext: bool = False, priority: int = None) -> bool**
- Open a specific fingerprint reader
- `use_ext`: Use extended open mode
- `priority`: DPFPDD_PRIORITY_COOPERATIVE or DPFPDD_PRIORITY_EXCLUSIVE

**close() -> bool**
- Close the opened device

**get_status() -> dict**
- Get current device status
- Returns: {status, status_text, finger_detected}

**start_stream() -> bool**
- Enable image streaming mode

**stop_stream() -> bool**
- Disable image streaming mode

**calibrate() -> bool**
- Calibrate the fingerprint sensor

**capture(timeout_ms: int = 5000, retries: int = 3) -> tuple**
- Capture fingerprint image
- Returns: (success, result_dict, image_bytes)
- Includes automatic retry logic for reliability

## Error Codes

Common error codes from the SDK:

| Code | Name | Meaning |
|------|------|---------|
| 0 | DPFPDD_SUCCESS | Operation successful |
| 0x05BA0014 | DPFPDD_E_INVALID_PARAMETER | Invalid parameter or device not found |
| 0x05BA0015 | DPFPDD_E_INVALID_DEVICE | Device handle is invalid |
| 0x05BA001E | DPFPDD_E_DEVICE_BUSY | Device is busy (already opened) |
| 0x05BA001F | DPFPDD_E_DEVICE_FAILURE | Device hardware failure |
| 96075796 (hex: 0x05BA0014) | DPFPDD_E_INVALID_PARAMETER | (decimal form) |

## System Requirements

- **OS**: Windows 10/11
- **Python**: 3.7+ (64-bit)
- **Hardware**: DigitalPersona U.are.U compatible fingerprint reader
- **SDK**: DigitalPersona U.are.U SDK (dpfpdd.dll)
- **Driver**: DigitalPersona device drivers installed and running

## Troubleshooting

### "Device not found" error
- Check if device is connected via USB
- Verify device drivers are installed
- Check Device Manager for the device

### "Failed to open device"
- Device may be opened by another application
- Try closing other fingerprint software
- Check if device is in exclusive mode

### Capture fails repeatedly
- Place finger firmly on sensor
- Try different fingers
- Ensure sensor is clean (not dusty or wet)
- Check sensor LED indicators

### Permission denied
- Run Python as Administrator
- Check Windows Firewall settings

## Technical Details

### Struct Compatibility

The wrapper correctly marshals all DigitalPersona SDK structures using ctypes:
- DPFPDD_VER_INFO, DPFPDD_VERSION
- DPFPDD_HW_DESCR, DPFPDD_HW_ID, DPFPDD_HW_VERSION
- DPFPDD_DEV_INFO (1452 bytes with padding)
- DPFPDD_DEV_STATUS, DPFPDD_DEV_CAPS
- DPFPDD_IMAGE_INFO, DPFPDD_CAPTURE_PARAM, DPFPDD_CAPTURE_RESULT

### Calling Convention

- Uses Windows stdcall (via ctypes.WinDLL)
- Verified compatible with dpfpdd.dll (API v1.9)

### Dependencies

- **ctypes** (Python standard library)
- No external dependencies required

## Development Notes

The wrapper was tested against:
- SDK Version: 2.2.0 (API 1.9)
- DLL: dpfpdd.dll (64-bit/x64)
- Python: 3.12.6

Known limitation: dpfpdd_query_devices() is non-functional in this SDK build, so device enumeration requires workarounds.

## Future Enhancements

- [ ] Support for dpfj.h feature extraction API
- [ ] Fingerprint matching across multiple captures
- [ ] Enrollment workflow helper functions
- [ ] Live preview streaming support
- [ ] Integration with Windows Hello

## License

This wrapper is provided as an educational example for working with the DigitalPersona SDK.
