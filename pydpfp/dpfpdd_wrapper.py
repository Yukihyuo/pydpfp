"""
DigitalPersona U.are.U SDK Python Wrapper

Wraps dpfpdd.dll (fingerprint capture API) with clean Python interfaces.
Based on official SDK headers: dpfpdd.h, dpfj.h
"""

import ctypes
import time
from ctypes import c_int, c_char_p, c_char, c_uint, c_ubyte, c_void_p, c_ushort, POINTER, Structure, byref, sizeof


# --- ERROR CODES (from dpfpdd.h) ---
DPFPDD_SUCCESS = 0
DPFPDD_E_NOT_IMPLEMENTED = 0x05BA000A
DPFPDD_E_FAILURE = 0x05BA000B
DPFPDD_E_NO_DATA = 0x05BA000C
DPFPDD_E_MORE_DATA = 0x05BA000D
DPFPDD_E_INVALID_PARAMETER = 0x05BA0014
DPFPDD_E_INVALID_DEVICE = 0x05BA0015
DPFPDD_E_DEVICE_BUSY = 0x05BA001E
DPFPDD_E_DEVICE_FAILURE = 0x05BA001F

# Priority constants (from dpfpdd.h)
DPFPDD_PRIORITY_COOPERATIVE = 2
DPFPDD_PRIORITY_EXCLUSIVE = 4

# Image format constants
DPFPDD_IMG_FMT_PIXEL_BUFFER = 0
DPFPDD_IMG_FMT_ANSI381 = 0x001B0401
DPFPDD_IMG_FMT_ISOIEC19794 = 0x01010007

# Image resolution
DPFPDD_IMAGE_RES_500 = 500

# Status constants
DPFPDD_STATUS_READY = 0
DPFPDD_STATUS_BUSY = 1
DPFPDD_STATUS_NEED_CALIBRATION = 2
DPFPDD_STATUS_FAILURE = 3

# Error mapping
ERROR_MAP = {
    DPFPDD_SUCCESS: "SUCCESS",
    DPFPDD_E_NOT_IMPLEMENTED: "NOT_IMPLEMENTED",
    DPFPDD_E_FAILURE: "FAILURE",
    DPFPDD_E_NO_DATA: "NO_DATA",
    DPFPDD_E_MORE_DATA: "MORE_DATA",
    DPFPDD_E_INVALID_PARAMETER: "INVALID_PARAMETER",
    DPFPDD_E_INVALID_DEVICE: "INVALID_DEVICE",
    DPFPDD_E_DEVICE_BUSY: "DEVICE_BUSY",
    DPFPDD_E_DEVICE_FAILURE: "DEVICE_FAILURE",
}

STATUS_MAP = {
    DPFPDD_STATUS_READY: "READY",
    DPFPDD_STATUS_BUSY: "BUSY",
    DPFPDD_STATUS_NEED_CALIBRATION: "NEED_CALIBRATION",
    DPFPDD_STATUS_FAILURE: "FAILURE",
}


def error_text(code: int) -> str:
    """Format SDK or HRESULT-style error code as name + hex."""
    unsigned = code & 0xFFFFFFFF
    signed = code if code < 0x80000000 else code - 0x100000000
    name = ERROR_MAP.get(code, ERROR_MAP.get(unsigned, "UNKNOWN"))
    if signed < 0:
        return f"{name} ({signed}, 0x{unsigned:08X})"
    return f"{name} (0x{unsigned:08X})"


def status_text(code: int) -> str:
    """Format status code as name."""
    return STATUS_MAP.get(code, f"UNKNOWN (0x{code:08X})")


def cstr_to_py(c_array) -> str:
    """Convert C char array to Python string."""
    data = bytes(c_array)
    return data.split(b"\x00", 1)[0].decode("utf-8", errors="replace")


# --- STRUCTURES (from dpfpdd.h) ---

class DPFPDD_HW_DESCR(Structure):
    """Reader hardware descriptor."""
    _fields_ = [
        ("vendor_name", c_char * 128),
        ("product_name", c_char * 128),
        ("serial_num", c_char * 128),
    ]


class DPFPDD_HW_ID(Structure):
    """Reader USB ID."""
    _fields_ = [
        ("vendor_id", c_ushort),
        ("product_id", c_ushort),
    ]


class DPFPDD_VER_INFO(Structure):
    """Version information."""
    _fields_ = [
        ("major", c_int),
        ("minor", c_int),
        ("maintenance", c_int),
    ]


class DPFPDD_HW_VERSION(Structure):
    """Hardware version."""
    _fields_ = [
        ("hw_ver", DPFPDD_VER_INFO),
        ("fw_ver", DPFPDD_VER_INFO),
        ("bcd_rev", c_ushort),
    ]


class DPFPDD_DEV_INFO(Structure):
    """Complete reader information (from dpfpdd_query_devices)."""
    _fields_ = [
        ("size", c_uint),
        ("name", c_char * 1024),
        ("descr", DPFPDD_HW_DESCR),
        ("id", DPFPDD_HW_ID),
        ("ver", DPFPDD_HW_VERSION),
        ("modality", c_uint),
        ("technology", c_uint),
    ]


class DPFPDD_DEV_STATUS(Structure):
    """Reader status."""
    _fields_ = [
        ("size", c_uint),
        ("status", c_uint),
        ("finger_detected", c_int),
        ("data", c_ubyte * 1),
    ]


class DPFPDD_IMAGE_INFO(Structure):
    """Captured image metadata."""
    _fields_ = [
        ("size", c_uint),
        ("width", c_uint),
        ("height", c_uint),
        ("res", c_uint),
        ("bpp", c_uint),
    ]


class DPFPDD_CAPTURE_PARAM(Structure):
    """Capture parameters."""
    _fields_ = [
        ("size", c_uint),
        ("image_fmt", c_uint),
        ("image_proc", c_uint),
        ("image_res", c_uint),
    ]


class DPFPDD_CAPTURE_RESULT(Structure):
    """Capture result."""
    _fields_ = [
        ("size", c_uint),
        ("success", c_int),
        ("quality", c_uint),
        ("score", c_uint),
        ("info", DPFPDD_IMAGE_INFO),
    ]


# --- DLL WRAPPER ---

class DPFPDD_Library:
    """Low-level wrapper around dpfpdd.dll."""

    def __init__(self, dll_path="./dpfpdd.dll"):
        """Load DLL and configure prototypes."""
        self.dll = ctypes.WinDLL(dll_path)
        self._configure_prototypes()

    def _configure_prototypes(self):
        """Set function signatures based on official SDK headers."""
        # Init/Exit
        self.dll.dpfpdd_init.argtypes = []
        self.dll.dpfpdd_init.restype = c_int

        self.dll.dpfpdd_exit.argtypes = []
        self.dll.dpfpdd_exit.restype = c_int

        # Query devices
        self.dll.dpfpdd_query_devices.argtypes = [POINTER(c_uint), POINTER(DPFPDD_DEV_INFO)]
        self.dll.dpfpdd_query_devices.restype = c_int

        # Open (exclusive, 2-args per official header)
        self.dll.dpfpdd_open.argtypes = [c_char_p, POINTER(c_void_p)]
        self.dll.dpfpdd_open.restype = c_int

        # Open extended (with priority, 3-args per official header)
        self.dll.dpfpdd_open_ext.argtypes = [c_char_p, c_uint, POINTER(c_void_p)]
        self.dll.dpfpdd_open_ext.restype = c_int

        # Device operations
        self.dll.dpfpdd_close.argtypes = [c_void_p]
        self.dll.dpfpdd_close.restype = c_int

        self.dll.dpfpdd_get_device_status.argtypes = [c_void_p, POINTER(DPFPDD_DEV_STATUS)]
        self.dll.dpfpdd_get_device_status.restype = c_int

        self.dll.dpfpdd_start_stream.argtypes = [c_void_p]
        self.dll.dpfpdd_start_stream.restype = c_int

        self.dll.dpfpdd_stop_stream.argtypes = [c_void_p]
        self.dll.dpfpdd_stop_stream.restype = c_int

        self.dll.dpfpdd_calibrate.argtypes = [c_void_p]
        self.dll.dpfpdd_calibrate.restype = c_int

        # Capture
        self.dll.dpfpdd_capture.argtypes = [
            c_void_p,
            POINTER(DPFPDD_CAPTURE_PARAM),
            c_int,
            POINTER(DPFPDD_CAPTURE_RESULT),
            POINTER(c_uint),
            POINTER(c_ubyte),
        ]
        self.dll.dpfpdd_capture.restype = c_int

    def init(self) -> int:
        return self.dll.dpfpdd_init()

    def exit(self) -> int:
        return self.dll.dpfpdd_exit()

    def query_devices(self) -> tuple[int, list]:
        """Query connected devices. Returns (error_code, device_list).
        
        NOTE: dpfpdd_query_devices has issues with the installed SDK on this system.
        This method attempts enumeration but may fail. Use open_device() with a 
        known device name directly as a workaround.
        """
        max_devices = 10

        # First pass: ask SDK how many devices are available.
        # Some SDK builds return MORE_DATA with the required count in dev_cnt.
        count = c_uint(0)
        try:
            first_res = self.dll.dpfpdd_query_devices(byref(count), None)
            if first_res == DPFPDD_SUCCESS and count.value == 0:
                return first_res, []
            if first_res == DPFPDD_E_MORE_DATA and count.value > 0:
                max_devices = count.value
        except OSError as e:
            print(f"[!] dpfpdd_query_devices first pass failed (known SDK issue): {e}")
            print("[*] Workaround: Use open() with a known device name directly")
            return 0x05BA0014, []

        count = c_uint(max_devices)
        infos = (DPFPDD_DEV_INFO * max_devices)()

        # Initialize size field (SDK requirement)
        for i in range(max_devices):
            infos[i].size = sizeof(DPFPDD_DEV_INFO)

        try:
            res = self.dll.dpfpdd_query_devices(byref(count), infos)
        except OSError as e:
            # Known issue: query_devices crashes on some SDK builds
            print(f"[!] dpfpdd_query_devices failed (known SDK issue): {e}")
            print("[*] Workaround: Use open() with a known device name directly")
            return 0x05BA0014, []  # Return INVALID_PARAMETER error
            
        devices = [
            {
                "name": cstr_to_py(infos[i].name),
                "product": cstr_to_py(infos[i].descr.product_name),
                "vendor": cstr_to_py(infos[i].descr.vendor_name),
                "serial": cstr_to_py(infos[i].descr.serial_num),
            }
            for i in range(count.value)
        ]
        return res, devices

    def open(self, device_name: bytes) -> tuple[int, c_void_p]:
        """Open device (exclusive mode). Returns (error_code, handle)."""
        handle = c_void_p()
        res = self.dll.dpfpdd_open(device_name, byref(handle))
        return res, handle

    def open_ext(self, device_name: bytes, priority: int = DPFPDD_PRIORITY_COOPERATIVE) -> tuple[int, c_void_p]:
        """Open device (with priority mode). Returns (error_code, handle)."""
        handle = c_void_p()
        res = self.dll.dpfpdd_open_ext(device_name, c_uint(priority), byref(handle))
        return res, handle

    def close(self, handle: c_void_p) -> int:
        return self.dll.dpfpdd_close(handle)

    def get_status(self, handle: c_void_p) -> tuple[int, dict]:
        """Get device status. Returns (error_code, status_dict)."""
        status = DPFPDD_DEV_STATUS()
        status.size = ctypes.sizeof(DPFPDD_DEV_STATUS)
        res = self.dll.dpfpdd_get_device_status(handle, byref(status))
        info = {
            "status": status.status,
            "finger_detected": bool(status.finger_detected),
            "status_text": status_text(status.status),
        }
        return res, info

    def start_stream(self, handle: c_void_p) -> int:
        return self.dll.dpfpdd_start_stream(handle)

    def stop_stream(self, handle: c_void_p) -> int:
        return self.dll.dpfpdd_stop_stream(handle)

    def calibrate(self, handle: c_void_p) -> int:
        return self.dll.dpfpdd_calibrate(handle)

    def capture(
        self,
        handle: c_void_p,
        timeout_ms: int = 5000,
        image_fmt: int = DPFPDD_IMG_FMT_PIXEL_BUFFER,
        image_res: int = DPFPDD_IMAGE_RES_500,
        image_proc: int = 0,
    ) -> tuple[int, dict, bytes]:
        """Capture fingerprint. Returns (error_code, result_dict, image_data)."""
        params = DPFPDD_CAPTURE_PARAM()
        params.size = ctypes.sizeof(DPFPDD_CAPTURE_PARAM)
        params.image_fmt = image_fmt
        params.image_proc = image_proc
        params.image_res = image_res

        result = DPFPDD_CAPTURE_RESULT()
        result.size = ctypes.sizeof(DPFPDD_CAPTURE_RESULT)

        img_size = c_uint(500 * 500)
        img_buffer = (c_ubyte * img_size.value)()

        res = self.dll.dpfpdd_capture(
            handle,
            byref(params),
            c_int(timeout_ms),
            byref(result),
            byref(img_size),
            img_buffer,
        )

        result_dict = {
            "success": bool(result.success),
            "quality": result.quality,
            "score": result.score,
            "width": result.info.width,
            "height": result.info.height,
            "resolution": result.info.res,
            "bpp": result.info.bpp,
        }

        img_data = bytes(img_buffer[: img_size.value])
        return res, result_dict, img_data


# --- HIGH-LEVEL INTERFACE ---

class FingerPrintReader:
    """High-level Python interface for fingerprint capture."""

    def __init__(self, dll_path="./dpfpdd.dll"):
        """Initialize reader interface."""
        self.lib = DPFPDD_Library(dll_path)
        self.handle = None
        self.initialized = False
        self.stream_active = False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.close()
        return False

    def init(self) -> bool:
        """Initialize SDK. Returns True on success."""
        res = self.lib.init()
        if res != DPFPDD_SUCCESS:
            print(f"[!] dpfpdd_init failed: {error_text(res)}")
            return False
        self.initialized = True
        print("[+] SDK initialized")
        return True

    def exit(self):
        """Release SDK resources."""
        if self.initialized:
            res = self.lib.exit()
            if res != DPFPDD_SUCCESS:
                print(f"[!] dpfpdd_exit returned: {error_text(res)}")
            self.initialized = False
            print("[+] SDK released")

    def list_devices(self) -> list:
        """List connected fingerprint readers. Returns list of device dicts."""
        res, devices = self.lib.query_devices()
        if res != DPFPDD_SUCCESS:
            print(f"[!] dpfpdd_query_devices failed: {error_text(res)}")
            return []
        return devices

    def open(self, device_name: str, use_ext: bool = False, priority: int = DPFPDD_PRIORITY_COOPERATIVE) -> bool:
        """
        Open a fingerprint reader.
        
        Args:
            device_name: Device name from list_devices()
            use_ext: Use extended open (with priority mode)
            priority: DPFPDD_PRIORITY_COOPERATIVE (default) or DPFPDD_PRIORITY_EXCLUSIVE
        
        Returns:
            True on success
        """
        device_bytes = device_name.encode("utf-8")

        if use_ext:
            res, handle = self.lib.open_ext(device_bytes, priority)
            mode = "open_ext"
        else:
            res, handle = self.lib.open(device_bytes)
            mode = "open"

        if res != DPFPDD_SUCCESS:
            print(f"[!] dpfpdd_{mode} failed: {error_text(res)}")
            return False

        if not handle.value:
            print(f"[!] dpfpdd_{mode} returned null handle")
            return False

        self.handle = handle
        print(f"[+] Device opened ({mode}): {device_name}")
        return True

    def get_status(self) -> dict:
        """Get current device status. Returns status dict or None on error."""
        if not self.handle:
            print("[!] Device not opened")
            return None

        res, status = self.lib.get_status(self.handle)
        if res != DPFPDD_SUCCESS:
            print(f"[!] get_device_status failed: {error_text(res)}")
            return None
        return status

    def start_stream(self) -> bool:
        """Start streaming mode."""
        if not self.handle:
            print("[!] Device not opened")
            return False

        res = self.lib.start_stream(self.handle)
        if res != DPFPDD_SUCCESS:
            print(f"[!] start_stream failed: {error_text(res)}")
            return False

        self.stream_active = True
        print("[+] Stream started")
        return True

    def stop_stream(self) -> bool:
        """Stop streaming mode."""
        if not self.handle:
            return False

        res = self.lib.stop_stream(self.handle)
        if res != DPFPDD_SUCCESS:
            print(f"[!] stop_stream failed: {error_text(res)}")
            return False

        self.stream_active = False
        print("[+] Stream stopped")
        return True

    def calibrate(self) -> bool:
        """Calibrate device."""
        if not self.handle:
            print("[!] Device not opened")
            return False

        res = self.lib.calibrate(self.handle)
        if res != DPFPDD_SUCCESS:
            print(f"[!] calibrate failed: {error_text(res)}")
            return False

        print("[+] Device calibrated")
        return True

    def capture(self, timeout_ms: int = 5000, retries: int = 3) -> tuple[bool, dict, bytes]:
        """
        Capture a fingerprint image.
        
        Args:
            timeout_ms: Capture timeout in milliseconds
            retries: Number of retries on INVALID_DEVICE
        
        Returns:
            (success: bool, result_dict: dict, image_data: bytes)
        """
        if not self.handle:
            print("[!] Device not opened")
            return False, {}, b""

        for attempt in range(1, retries + 1):
            res, result, img_data = self.lib.capture(self.handle, timeout_ms)

            if res == DPFPDD_SUCCESS:
                if result["success"]:
                    print(f"[+] Capture succeeded: quality={result['quality']}, score={result['score']}")
                    return True, result, img_data
                else:
                    print(f"[!] Capture returned but success=0: quality={result['quality']}")
                    return False, result, img_data

            if res == DPFPDD_E_INVALID_DEVICE and attempt < retries:
                print(f"[i] Attempt {attempt}/{retries}: INVALID_DEVICE, retrying...")
                time.sleep(0.5)
                continue

            print(f"[!] dpfpdd_capture failed: {error_text(res)}")
            return False, result, img_data

        print(f"[!] Capture failed after {retries} retries")
        return False, {}, b""

    def close(self):
        """Close device and release resources."""
        if self.stream_active:
            self.stop_stream()

        if self.handle:
            res = self.lib.close(self.handle)
            if res != DPFPDD_SUCCESS:
                print(f"[!] close failed: {error_text(res)}")
            self.handle = None
            print("[+] Device closed")


if __name__ == "__main__":
    print("dpfpdd_wrapper.py - DigitalPersona SDK Python Wrapper")
    print("Import this module and use FingerPrintReader class")
