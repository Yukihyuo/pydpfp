#!/usr/bin/env python3
"""
Fingerprint enrollment script.

Uses dpfpdd_wrapper.py for device control/capture and dpfj_wrapper.py
for enrollment (FMD consolidation).
"""

import argparse
import base64
import os
import time
import uuid

from pydpfp.dpfj_wrapper import FingerJetEngine
from pydpfp.dpfpdd_wrapper import (
    DPFPDD_PRIORITY_COOPERATIVE,
    DPFPDD_PRIORITY_EXCLUSIVE,
    FingerPrintReader,
)


def wait_for_finger_state(reader: FingerPrintReader, target_present: bool, timeout_s: float = 12.0, poll_s: float = 0.12) -> bool:
    """Wait until reader reports finger present/absent state."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        status = reader.get_status()
        if status is not None and bool(status.get("finger_detected")) == target_present:
            return True
        time.sleep(poll_s)
    return False


def open_reader(reader: FingerPrintReader) -> tuple[bool, str, str]:
    """Initialize SDK and open reader using resilient fallbacks."""
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

    print("[*] Initializing capture SDK...")
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
    else:
        print("[!] Enumeration returned no devices, using fallback names...")

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


def enroll_same_finger(
    reader: FingerPrintReader,
    engine: FingerJetEngine,
    takes_required: int,
    dpi: int,
) -> bytes:
    """Capture multiple samples of the same finger and build a master FMD."""
    print(f"[*] Starting enrollment context (required takes: {takes_required})")
    engine.enrollment_start()

    ready = False
    take = 0
    final_fmd = b""

    try:
        while take < takes_required and not ready:
            take += 1
            print(f"\n[>>>] Take {take}/{takes_required}: place the SAME finger")

            if not wait_for_finger_state(reader, True, timeout_s=20.0):
                print("[!] Finger not detected in time. Try again for this take.")
                take -= 1
                continue

            success, result, image_data = reader.capture(timeout_ms=12000, retries=3)
            if not success:
                print("[!] Capture failed, repeating this take...")
                take -= 1
                continue

            width = int(result.get("width", 0) or 0)
            height = int(result.get("height", 0) or 0)
            if width <= 0 or height <= 0:
                print("[!] Invalid image dimensions from capture result. Repeating this take...")
                take -= 1
                continue

            try:
                fmd = engine.create_fmd_from_raw(
                    image_data=image_data,
                    image_width=width,
                    image_height=height,
                    image_dpi=dpi,
                )
            except Exception as ex:
                print(f"[!] Failed to extract FMD for this take: {ex}")
                take -= 1
                continue

            try:
                ready = engine.enrollment_add(fmd)
            except Exception as ex:
                print(f"[!] Failed to add FMD to enrollment: {ex}")
                take -= 1
                continue

            if ready:
                print("[+] Enrollment pool is ready. Creating consolidated master FMD...")
                final_fmd = engine.enrollment_create_fmd()
                break

            print("[*] Enrollment needs more samples.")
            print("[*] Lift finger to arm next take...")
            wait_for_finger_state(reader, False, timeout_s=8.0)

        if not final_fmd:
            # If SDK still needs more data after configured takes, this will raise,
            # which is useful feedback to the user.
            print("[*] Attempting to finalize enrollment with collected samples...")
            final_fmd = engine.enrollment_create_fmd()

        return final_fmd
    finally:
        try:
            engine.enrollment_finish()
        except Exception as ex:
            print(f"[!] Warning: enrollment_finish returned error: {ex}")


def main():
    parser = argparse.ArgumentParser(description="Enroll one finger and save consolidated FMD as Base64 text")
    parser.add_argument("--captures-dir", default="captures", help="Output folder")
    parser.add_argument("--takes", type=int, default=4, help="Number of takes for same finger")
    parser.add_argument("--dpi", type=int, default=500, help="Image DPI used for raw->FMD extraction")
    parser.add_argument("--output-name", default="", help="Optional output filename (without extension)")
    args = parser.parse_args()

    captures_dir = args.captures_dir
    os.makedirs(captures_dir, exist_ok=True)

    engine = FingerJetEngine("./dpfj.dll")
    ver = engine.version()
    print(f"[*] FingerJet ready - Library {ver['library']}, API {ver['api']}")

    with FingerPrintReader("./dpfpdd.dll") as reader:
        ok, dev_name, mode = open_reader(reader)
        if not ok:
            return

        print(f"[+] Reader opened: {dev_name} ({mode})")
        print("[*] Starting stream and calibration...")
        reader.start_stream()
        reader.calibrate()

        try:
            master_fmd = enroll_same_finger(
                reader=reader,
                engine=engine,
                takes_required=max(1, args.takes),
                dpi=args.dpi,
            )
        except KeyboardInterrupt:
            print("\n[*] Enrollment canceled by user")
            return
        except Exception as ex:
            print(f"[!] Enrollment failed: {ex}")
            return

        b64_text = base64.b64encode(master_fmd).decode("ascii")

        if args.output_name:
            base_name = args.output_name
        else:
            ts = time.strftime("%Y%m%d_%H%M%S")
            base_name = f"enroll_{ts}_{uuid.uuid4().hex[:8]}"

        out_path = os.path.join(captures_dir, f"{base_name}.fmd")
        with open(out_path, "w", encoding="ascii") as f:
            f.write(b64_text)

        print("\n[+] Enrollment completed")
        print(f"[*] Master FMD bytes: {len(master_fmd)}")
        print(f"[*] Saved Base64 template: {out_path}")


if __name__ == "__main__":
    main()
