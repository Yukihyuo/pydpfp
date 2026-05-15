#!/usr/bin/env python3
"""
Capture one live fingerprint and compare it against .fmd files in captures/.

Prints the filename with the best match score and whether it passes threshold.
"""

import argparse
import base64
import glob
import os
import time
import uuid

from pydpfp.dpfj_wrapper import FingerJetEngine
from pydpfp.dpfj_wrapper import (
    DPFJ_FMD_ANSI_378_2004,
    DPFJ_FMD_DP_REG_FEATURES,
    DPFJ_FMD_DP_VER_FEATURES,
    DPFJ_FMD_ISO_19794_2_2005,
)
from pydpfp.dpfpdd_wrapper import (
    DPFPDD_PRIORITY_COOPERATIVE,
    DPFPDD_PRIORITY_EXCLUSIVE,
    FingerPrintReader,
)


def infer_dimensions(data_len: int) -> tuple[int, int]:
    """Infer image dimensions from raw size (8bpp, no padding)."""
    side = int(data_len ** 0.5)
    if side * side == data_len:
        return side, side
    raise ValueError(f"Cannot infer width/height from {data_len} bytes")


def wait_for_finger_state(reader: FingerPrintReader, target_present: bool, timeout_s: float = 10.0, poll_s: float = 0.12) -> bool:
    """Wait until reader reports finger present/absent state."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        st = reader.get_status()
        if st is not None and bool(st.get("finger_detected")) == target_present:
            return True
        time.sleep(poll_s)
    return False


def open_reader(reader: FingerPrintReader) -> tuple[bool, str, str]:
    """Initialize and open first available reader with resilient fallback."""
    default_device_names = [
        "\\\\?\\usb#vid_05ba&pid_0007#5&2a23e537&0&1",
        "\\\\.\\UAREU$1",
        "\\\\.\\UAREU$0",
        "\\\\.\\UareU",
        "\\\\.\\UareU0",
        "\\\\.\\UareU1",
        "U.are.U 5100",
        "U.are.U 4500",
        "DigitalPersona U.are.U",
    ]

    open_candidates = [
        {"use_ext": True, "priority": DPFPDD_PRIORITY_COOPERATIVE, "label": "open_ext/cooperative"},
        {"use_ext": True, "priority": DPFPDD_PRIORITY_EXCLUSIVE, "label": "open_ext/exclusive"},
        {"use_ext": False, "priority": DPFPDD_PRIORITY_COOPERATIVE, "label": "open/exclusive(default)"},
    ]

    print("[*] Initializing SDK...")
    if not reader.init():
        return False, "", ""

    print("[*] Enumerating readers...")
    devices = reader.list_devices()

    candidate_names = []
    if devices:
        print(f"[+] Found {len(devices)} device(s)")
        for idx, dev in enumerate(devices, 1):
            print(f"    {idx}. {dev.get('name', '<unknown>')}")
        candidate_names.extend([d["name"] for d in devices if d.get("name")])

    for fallback in default_device_names:
        if fallback not in candidate_names:
            candidate_names.append(fallback)

    selected_name = ""
    selected_mode = ""

    for device_name in candidate_names:
        print(f"[*] Trying device: {device_name}")
        for mode in open_candidates:
            print(f"    -> {mode['label']}")
            ok = reader.open(device_name, use_ext=mode["use_ext"], priority=mode["priority"])
            if ok:
                selected_name = device_name
                selected_mode = mode["label"]
                break
        if selected_name:
            break

    if not selected_name:
        print("[!] Could not open any reader")
        return False, "", ""

    return True, selected_name, selected_mode


def load_capture_candidates(captures_dir: str) -> list[str]:
    """Load all .fmd candidates from captures folder."""
    pattern = os.path.join(captures_dir, "*.fmd")
    files = sorted(glob.glob(pattern))
    return [f for f in files if os.path.isfile(f)]


def read_fmd_base64_file(path: str) -> bytes:
    """Read Base64 text from .fmd and decode to raw FMD bytes."""
    with open(path, "r", encoding="ascii") as f:
        b64_text = f.read().strip()
    if not b64_text:
        raise ValueError("empty .fmd file")
    try:
        return base64.b64decode(b64_text, validate=True)
    except Exception as ex:
        raise ValueError(f"invalid Base64 template: {ex}") from ex


def best_effort_compare(engine: FingerJetEngine, probe_fmd: bytes, candidate_fmd: bytes) -> tuple[int | None, tuple[int, int, int, int] | None]:
    """Try multiple format/view combinations and return the best score found."""
    fmd_types = [
        DPFJ_FMD_ANSI_378_2004,
        DPFJ_FMD_ISO_19794_2_2005,
        DPFJ_FMD_DP_VER_FEATURES,
        DPFJ_FMD_DP_REG_FEATURES,
    ]

    best_score = None
    best_cfg = None

    for probe_type in fmd_types:
        for candidate_type in fmd_types:
            for view_idx1 in (0, 1):
                for view_idx2 in (0, 1):
                    try:
                        score = engine.compare(
                            probe_fmd,
                            candidate_fmd,
                            fmd1_type=probe_type,
                            fmd2_type=candidate_type,
                            view_idx1=view_idx1,
                            view_idx2=view_idx2,
                        )
                    except Exception:
                        continue

                    if best_score is None or score < best_score:
                        best_score = score
                        best_cfg = (probe_type, candidate_type, view_idx1, view_idx2)

    return best_score, best_cfg


def main():
    parser = argparse.ArgumentParser(description="Capture fingerprint and compare against captures/*.fmd")
    parser.add_argument("--captures-dir", default="captures", help="Folder with enrolled .fmd files (Base64)")
    parser.add_argument("--dpi", type=int, default=500, help="Image DPI for raw processing")
    parser.add_argument("--width", type=int, default=500, help="Fallback raw image width")
    parser.add_argument("--height", type=int, default=500, help="Fallback raw image height")
    parser.add_argument("--threshold", type=int, default=800000, help="Match threshold (lower score is better)")
    parser.add_argument("--top", type=int, default=5, help="How many top scores to print")
    parser.add_argument("--save-probe", action="store_true", help="Save live probe capture to captures directory")
    args = parser.parse_args()

    captures_dir = args.captures_dir
    os.makedirs(captures_dir, exist_ok=True)

    candidate_files = load_capture_candidates(captures_dir)
    if not candidate_files:
        print(f"[!] No .fmd files found in: {captures_dir}")
        print("[*] First enroll samples with enroll_fingerprint.py")
        return

    print(f"[*] Loaded {len(candidate_files)} enrolled templates from {captures_dir}")

    engine = FingerJetEngine("./dpfj.dll")
    versions = engine.version()
    print(f"[*] FingerJet loaded - Library {versions['library']}, API {versions['api']}")

    with FingerPrintReader("./dpfpdd.dll") as reader:
        ok, selected_name, selected_mode = open_reader(reader)
        if not ok:
            return

        print(f"[+] Reader opened: {selected_name} ({selected_mode})")
        print("[*] Starting stream and calibration...")
        reader.start_stream()
        reader.calibrate()

        print("[>>>] Place your finger on the reader for probe capture...")
        if not wait_for_finger_state(reader, True, timeout_s=15.0):
            print("[!] Finger not detected in time")
            return

        success, result, probe_raw = reader.capture(timeout_ms=10000, retries=3)
        if not success:
            print("[!] Probe capture failed")
            return

        print("[+] Probe captured")
        print(
            f"    Image: {result.get('width', 'N/A')}x{result.get('height', 'N/A')} @ {result.get('resolution', 'N/A')} DPI"
        )

        if args.save_probe:
            probe_name = f"probe_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}.raw"
            probe_path = os.path.join(captures_dir, probe_name)
            with open(probe_path, "wb") as f:
                f.write(probe_raw)
            print(f"[*] Probe saved to: {probe_path}")

        probe_w = int(result.get("width", 0) or 0)
        probe_h = int(result.get("height", 0) or 0)

        if probe_w <= 0 or probe_h <= 0:
            probe_w = args.width
            probe_h = args.height

        expected_probe_size = probe_w * probe_h
        if len(probe_raw) < expected_probe_size:
            try:
                probe_w, probe_h = infer_dimensions(len(probe_raw))
                print(f"[*] Auto-inferred probe dimensions: {probe_w}x{probe_h}")
            except ValueError:
                print(
                    f"[!] Probe raw size ({len(probe_raw)}) does not match configured dimensions ({probe_w}x{probe_h})"
                )
                return
        elif len(probe_raw) > expected_probe_size:
            # Common with dpfpdd: padded buffer bigger than image raster.
            # Keep SDK-reported width/height; dpfj_wrapper trims to width*height.
            print(
                f"[*] Probe buffer has padding: {len(probe_raw)} bytes, using raster {probe_w}x{probe_h} ({expected_probe_size} bytes)"
            )

        try:
            probe_fmd = engine.create_fmd_from_raw(
                image_data=probe_raw,
                image_width=probe_w,
                image_height=probe_h,
                image_dpi=args.dpi,
            )
        except Exception as ex:
            print(f"[!] Could not create FMD from probe: {ex}")
            return

        # Quick sanity check: probe vs itself should be near-perfect and never maxed out.
        self_score, self_cfg = best_effort_compare(engine, probe_fmd, probe_fmd)
        if self_score is None:
            print("[!] Could not compare probe template even against itself")
            return
        print(f"[*] Probe self-check score: {self_score} (cfg={self_cfg})")

        scores = []
        for path in candidate_files:
            name = os.path.basename(path)
            try:
                candidate_fmd = read_fmd_base64_file(path)

                cand_self_score, cand_self_cfg = best_effort_compare(engine, candidate_fmd, candidate_fmd)
                if cand_self_score is None:
                    raise RuntimeError("candidate template cannot be compared to itself")
                if cand_self_score == 2147483647:
                    raise RuntimeError(
                        f"candidate self-check is max score ({cand_self_score}), likely invalid enrollment/template format"
                    )

                score, cfg = best_effort_compare(engine, probe_fmd, candidate_fmd)
                if score is None:
                    raise RuntimeError("no valid compare combination found")
                scores.append((score, name, cfg))
            except Exception as ex:
                print(f"[i] Skipped {name}: {ex}")

        if not scores:
            print("[!] No candidate could be processed")
            return

        scores.sort(key=lambda item: item[0])

        print("\n[*] Top matches (lower is better):")
        for idx, (score, name, cfg) in enumerate(scores[: max(1, args.top)], 1):
            print(f"    {idx}. score={score} file={name} cfg={cfg}")

        best_score, best_name, best_cfg = scores[0]
        print("\n[*] Best candidate:")
        print(f"    file: {best_name}")
        print(f"    score: {best_score}")
        print(f"    cfg: {best_cfg}")
        print(f"    threshold: {args.threshold}")

        if best_score <= args.threshold:
            print(f"[MATCH] {best_name}")
        else:
            print("[NO MATCH] Best score did not pass threshold")


if __name__ == "__main__":
    main()
