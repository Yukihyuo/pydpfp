"""
DigitalPersona FingerJet (dpfj.dll) Python Wrapper.

Wraps dpfj.dll (feature extraction, comparison, enrollment, conversion)
using ctypes and the official declarations in dpfj.h.
"""

import ctypes
from ctypes import POINTER, Structure, byref, c_int, c_ubyte, c_uint, sizeof


# --- Error codes (from dpfj.h) ---
DPFJ_SUCCESS = 0
DPFJ_E_NOT_IMPLEMENTED = 0x05BA000A
DPFJ_E_FAILURE = 0x05BA000B
DPFJ_E_NO_DATA = 0x05BA000C
DPFJ_E_MORE_DATA = 0x05BA000D
DPFJ_E_INVALID_PARAMETER = 0x05BA0014
DPFJ_E_INVALID_FID = 0x05BA0065
DPFJ_E_TOO_SMALL_AREA = 0x05BA0066
DPFJ_E_INVALID_FMD = 0x05BA00C9
DPFJ_E_ENROLLMENT_IN_PROGRESS = 0x05BA012D
DPFJ_E_ENROLLMENT_NOT_STARTED = 0x05BA012E
DPFJ_E_ENROLLMENT_NOT_READY = 0x05BA012F
DPFJ_E_ENROLLMENT_INVALID_SET = 0x05BA0130

# --- Formats and constants (from dpfj.h) ---
DPFJ_PROBABILITY_ONE = 0x7FFFFFFF

DPFJ_FID_ANSI_381_2004 = 0x001B0401
DPFJ_FID_ISO_19794_4_2005 = 0x01010007

DPFJ_FMD_ANSI_378_2004 = 0x001B0001
DPFJ_FMD_ISO_19794_2_2005 = 0x01010001
DPFJ_FMD_DP_PRE_REG_FEATURES = 0
DPFJ_FMD_DP_REG_FEATURES = 1
DPFJ_FMD_DP_VER_FEATURES = 2

DPFJ_POSITION_UNKNOWN = 0
DPFJ_POSITION_RTHUMB = 1
DPFJ_POSITION_RINDEX = 2
DPFJ_POSITION_RMIDDLE = 3
DPFJ_POSITION_RRING = 4
DPFJ_POSITION_RLITTLE = 5
DPFJ_POSITION_LTHUMB = 6
DPFJ_POSITION_LINDEX = 7
DPFJ_POSITION_LMIDDLE = 8
DPFJ_POSITION_LRING = 9
DPFJ_POSITION_LLITTLE = 10

MAX_FMD_SIZE = 1562

ERROR_MAP = {
    DPFJ_SUCCESS: "SUCCESS",
    DPFJ_E_NOT_IMPLEMENTED: "NOT_IMPLEMENTED",
    DPFJ_E_FAILURE: "FAILURE",
    DPFJ_E_NO_DATA: "NO_DATA",
    DPFJ_E_MORE_DATA: "MORE_DATA",
    DPFJ_E_INVALID_PARAMETER: "INVALID_PARAMETER",
    DPFJ_E_INVALID_FID: "INVALID_FID",
    DPFJ_E_TOO_SMALL_AREA: "TOO_SMALL_AREA",
    DPFJ_E_INVALID_FMD: "INVALID_FMD",
    DPFJ_E_ENROLLMENT_IN_PROGRESS: "ENROLLMENT_IN_PROGRESS",
    DPFJ_E_ENROLLMENT_NOT_STARTED: "ENROLLMENT_NOT_STARTED",
    DPFJ_E_ENROLLMENT_NOT_READY: "ENROLLMENT_NOT_READY",
    DPFJ_E_ENROLLMENT_INVALID_SET: "ENROLLMENT_INVALID_SET",
}


def error_text(code: int) -> str:
    """Format SDK or HRESULT-like return code as text + hex."""
    unsigned = code & 0xFFFFFFFF
    signed = code if code < 0x80000000 else code - 0x100000000
    name = ERROR_MAP.get(code, ERROR_MAP.get(unsigned, "UNKNOWN"))
    if signed < 0:
        return f"{name} ({signed}, 0x{unsigned:08X})"
    return f"{name} (0x{unsigned:08X})"


# --- Structures (from dpfj.h) ---

class DPFJ_VER_INFO(Structure):
    _fields_ = [
        ("major", c_int),
        ("minor", c_int),
        ("maintanance", c_int),
    ]


class DPFJ_VERSION(Structure):
    _fields_ = [
        ("size", c_uint),
        ("lib_ver", DPFJ_VER_INFO),
        ("api_ver", DPFJ_VER_INFO),
    ]


class DPFJ_CANDIDATE(Structure):
    _fields_ = [
        ("size", c_uint),
        ("fmd_idx", c_uint),
        ("view_idx", c_uint),
    ]


class DPFJ_Library:
    """Low-level wrapper around dpfj.dll."""

    def __init__(self, dll_path: str = "./dpfj.dll"):
        self.dll = ctypes.WinDLL(dll_path)
        self._configure_prototypes()

    def _configure_prototypes(self):
        self.dll.dpfj_version.argtypes = [POINTER(DPFJ_VERSION)]
        self.dll.dpfj_version.restype = c_int

        self.dll.dpfj_create_fmd_from_raw.argtypes = [
            POINTER(c_ubyte),
            c_uint,
            c_uint,
            c_uint,
            c_uint,
            c_int,
            c_uint,
            c_int,
            POINTER(c_ubyte),
            POINTER(c_uint),
        ]
        self.dll.dpfj_create_fmd_from_raw.restype = c_int

        self.dll.dpfj_create_fmd_from_fid.argtypes = [
            c_int,
            POINTER(c_ubyte),
            c_uint,
            c_int,
            POINTER(c_ubyte),
            POINTER(c_uint),
        ]
        self.dll.dpfj_create_fmd_from_fid.restype = c_int

        self.dll.dpfj_compare.argtypes = [
            c_int,
            POINTER(c_ubyte),
            c_uint,
            c_uint,
            c_int,
            POINTER(c_ubyte),
            c_uint,
            c_uint,
            POINTER(c_uint),
        ]
        self.dll.dpfj_compare.restype = c_int

        self.dll.dpfj_fmd_convert.argtypes = [
            c_int,
            POINTER(c_ubyte),
            c_uint,
            c_int,
            POINTER(c_ubyte),
            POINTER(c_uint),
        ]
        self.dll.dpfj_fmd_convert.restype = c_int

        self.dll.dpfj_start_enrollment.argtypes = [c_int]
        self.dll.dpfj_start_enrollment.restype = c_int

        self.dll.dpfj_add_to_enrollment.argtypes = [
            c_int,
            POINTER(c_ubyte),
            c_uint,
            c_uint,
        ]
        self.dll.dpfj_add_to_enrollment.restype = c_int

        self.dll.dpfj_create_enrollment_fmd.argtypes = [POINTER(c_ubyte), POINTER(c_uint)]
        self.dll.dpfj_create_enrollment_fmd.restype = c_int

        self.dll.dpfj_finish_enrollment.argtypes = []
        self.dll.dpfj_finish_enrollment.restype = c_int


class FingerJetEngine:
    """High-level FingerJet API."""

    def __init__(self, dll_path: str = "./dpfj.dll"):
        self.lib = DPFJ_Library(dll_path)

    def version(self) -> dict:
        """Return library/API version info."""
        ver = DPFJ_VERSION()
        ver.size = sizeof(DPFJ_VERSION)
        res = self.lib.dll.dpfj_version(byref(ver))
        if res != DPFJ_SUCCESS:
            raise RuntimeError(f"dpfj_version failed: {error_text(res)}")

        return {
            "library": f"{ver.lib_ver.major}.{ver.lib_ver.minor}.{ver.lib_ver.maintanance}",
            "api": f"{ver.api_ver.major}.{ver.api_ver.minor}.{ver.api_ver.maintanance}",
        }

    def create_fmd_from_raw(
        self,
        image_data: bytes,
        image_width: int,
        image_height: int,
        image_dpi: int = 500,
        finger_pos: int = DPFJ_POSITION_UNKNOWN,
        cbeff_id: int = 0,
        fmd_type: int = DPFJ_FMD_ANSI_378_2004,
    ) -> bytes:
        """Extract an FMD from raw 8bpp grayscale image bytes."""
        if not image_data:
            raise ValueError("image_data must not be empty")

        expected_size = int(image_width) * int(image_height)
        if expected_size <= 0:
            raise ValueError("image_width and image_height must be > 0")
        if len(image_data) < expected_size:
            raise ValueError(
                f"raw image_data too small: got {len(image_data)} bytes, expected {expected_size}"
            )

        # dpfpdd_capture may return a larger padded buffer than width*height.
        # FingerJet expects image_size to match the actual raster dimensions.
        if len(image_data) != expected_size:
            image_data = image_data[:expected_size]

        img = (c_ubyte * len(image_data)).from_buffer_copy(image_data)

        # First pass asks SDK for required output size.
        fmd_size = c_uint(0)
        res = self.lib.dll.dpfj_create_fmd_from_raw(
            img,
            c_uint(expected_size),
            c_uint(image_width),
            c_uint(image_height),
            c_uint(image_dpi),
            c_int(finger_pos),
            c_uint(cbeff_id),
            c_int(fmd_type),
            None,
            byref(fmd_size),
        )
        if res not in (DPFJ_E_MORE_DATA, DPFJ_SUCCESS):
            raise RuntimeError(f"dpfj_create_fmd_from_raw(size query) failed: {error_text(res)}")

        alloc_size = max(fmd_size.value, MAX_FMD_SIZE)
        fmd_out = (c_ubyte * alloc_size)()
        out_size = c_uint(alloc_size)

        res = self.lib.dll.dpfj_create_fmd_from_raw(
            img,
            c_uint(expected_size),
            c_uint(image_width),
            c_uint(image_height),
            c_uint(image_dpi),
            c_int(finger_pos),
            c_uint(cbeff_id),
            c_int(fmd_type),
            fmd_out,
            byref(out_size),
        )
        if res != DPFJ_SUCCESS:
            raise RuntimeError(f"dpfj_create_fmd_from_raw failed: {error_text(res)}")

        return bytes(fmd_out[: out_size.value])

    def create_fmd_from_fid(
        self,
        fid_data: bytes,
        fid_type: int = DPFJ_FID_ANSI_381_2004,
        fmd_type: int = DPFJ_FMD_ANSI_378_2004,
    ) -> bytes:
        """Extract an FMD from ANSI/ISO FID bytes."""
        if not fid_data:
            raise ValueError("fid_data must not be empty")

        fid = (c_ubyte * len(fid_data)).from_buffer_copy(fid_data)

        fmd_size = c_uint(0)
        res = self.lib.dll.dpfj_create_fmd_from_fid(
            c_int(fid_type),
            fid,
            c_uint(len(fid_data)),
            c_int(fmd_type),
            None,
            byref(fmd_size),
        )
        if res not in (DPFJ_E_MORE_DATA, DPFJ_SUCCESS):
            raise RuntimeError(f"dpfj_create_fmd_from_fid(size query) failed: {error_text(res)}")

        alloc_size = max(fmd_size.value, MAX_FMD_SIZE)
        fmd_out = (c_ubyte * alloc_size)()
        out_size = c_uint(alloc_size)

        res = self.lib.dll.dpfj_create_fmd_from_fid(
            c_int(fid_type),
            fid,
            c_uint(len(fid_data)),
            c_int(fmd_type),
            fmd_out,
            byref(out_size),
        )
        if res != DPFJ_SUCCESS:
            raise RuntimeError(f"dpfj_create_fmd_from_fid failed: {error_text(res)}")

        return bytes(fmd_out[: out_size.value])

    def compare(
        self,
        fmd1: bytes,
        fmd2: bytes,
        fmd_type: int = DPFJ_FMD_ANSI_378_2004,
        fmd1_type: int | None = None,
        fmd2_type: int | None = None,
        view_idx1: int = 0,
        view_idx2: int = 0,
    ) -> int:
        """Compare two FMDs. Lower score means better match (0 is best)."""
        if not fmd1 or not fmd2:
            raise ValueError("fmd1 and fmd2 must not be empty")

        if fmd1_type is None:
            fmd1_type = fmd_type
        if fmd2_type is None:
            fmd2_type = fmd_type

        buf1 = (c_ubyte * len(fmd1)).from_buffer_copy(fmd1)
        buf2 = (c_ubyte * len(fmd2)).from_buffer_copy(fmd2)
        score = c_uint(0)

        res = self.lib.dll.dpfj_compare(
            c_int(fmd1_type),
            buf1,
            c_uint(len(fmd1)),
            c_uint(view_idx1),
            c_int(fmd2_type),
            buf2,
            c_uint(len(fmd2)),
            c_uint(view_idx2),
            byref(score),
        )
        if res != DPFJ_SUCCESS:
            raise RuntimeError(f"dpfj_compare failed: {error_text(res)}")

        return score.value

    def convert_fmd(
        self,
        fmd_data: bytes,
        src_type: int,
        dst_type: int,
    ) -> bytes:
        """Convert an FMD between supported formats."""
        if not fmd_data:
            raise ValueError("fmd_data must not be empty")

        src = (c_ubyte * len(fmd_data)).from_buffer_copy(fmd_data)

        # A buffer of MAX_FMD_SIZE is usually enough for one view.
        out_buf = (c_ubyte * MAX_FMD_SIZE)()
        out_size = c_uint(MAX_FMD_SIZE)

        res = self.lib.dll.dpfj_fmd_convert(
            c_int(src_type),
            src,
            c_uint(len(fmd_data)),
            c_int(dst_type),
            out_buf,
            byref(out_size),
        )
        if res != DPFJ_SUCCESS:
            raise RuntimeError(f"dpfj_fmd_convert failed: {error_text(res)}")

        return bytes(out_buf[: out_size.value])

    def enrollment_start(self, fmd_type: int = DPFJ_FMD_ANSI_378_2004):
        """Start enrollment session."""
        res = self.lib.dll.dpfj_start_enrollment(c_int(fmd_type))
        if res != DPFJ_SUCCESS:
            raise RuntimeError(f"dpfj_start_enrollment failed: {error_text(res)}")

    def enrollment_add(self, fmd_data: bytes, fmd_type: int = DPFJ_FMD_ANSI_378_2004, view_idx: int = 0) -> bool:
        """Add one FMD to enrollment pool. Returns True when ready."""
        if not fmd_data:
            raise ValueError("fmd_data must not be empty")

        fmd = (c_ubyte * len(fmd_data)).from_buffer_copy(fmd_data)
        res = self.lib.dll.dpfj_add_to_enrollment(
            c_int(fmd_type),
            fmd,
            c_uint(len(fmd_data)),
            c_uint(view_idx),
        )

        if res == DPFJ_SUCCESS:
            return True
        if res == DPFJ_E_MORE_DATA:
            return False
        raise RuntimeError(f"dpfj_add_to_enrollment failed: {error_text(res)}")

    def enrollment_create_fmd(self) -> bytes:
        """Finalize enrollment and return enrollment FMD."""
        out_buf = (c_ubyte * MAX_FMD_SIZE)()
        out_size = c_uint(MAX_FMD_SIZE)

        res = self.lib.dll.dpfj_create_enrollment_fmd(out_buf, byref(out_size))
        if res != DPFJ_SUCCESS:
            raise RuntimeError(f"dpfj_create_enrollment_fmd failed: {error_text(res)}")

        return bytes(out_buf[: out_size.value])

    def enrollment_finish(self):
        """Finish enrollment and release enrollment resources."""
        res = self.lib.dll.dpfj_finish_enrollment()
        if res != DPFJ_SUCCESS:
            raise RuntimeError(f"dpfj_finish_enrollment failed: {error_text(res)}")


if __name__ == "__main__":
    engine = FingerJetEngine("./dpfj.dll")
    info = engine.version()
    print("FingerJet wrapper loaded")
    print(f"Library version: {info['library']}")
    print(f"API version: {info['api']}")
