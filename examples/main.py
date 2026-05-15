﻿#!/usr/bin/env python3
"""
Fingerprint Capture Example using DigitalPersona U.are.U SDK

This script demonstrates fingerprint capture using the dpfpdd_wrapper module.

Note: Device enumeration (list_devices) may not work on all systems due to SDK 
limitations. If it doesn't work, the script will try common default device names.
"""

import os
import time
import uuid

from pydpfp.dpfpdd_wrapper import (
    FingerPrintReader,
    DPFPDD_PRIORITY_COOPERATIVE,
    DPFPDD_PRIORITY_EXCLUSIVE,
)


def main():
    """Main example: initialize, list devices, open reader, capture."""
    output_dir = "captures"
    os.makedirs(output_dir, exist_ok=True)
    
    # Common default device names to try if enumeration fails
    DEFAULT_DEVICE_NAMES = [
        "\\\\?\\usb#vid_05ba&pid_0007#5&2a23e537&0&1",  # Common format
        "\\\\.\\UAREU$1",
        "\\\\.\\UAREU$0",
        "\\\\.\\UareU",
        "\\\\.\\UareU0",
        "\\\\.\\UareU1",
        "U.are.U 5100",
        "U.are.U 4500",
        "DigitalPersona U.are.U",
    ]

    OPEN_CANDIDATES = [
        # Cooperative mode is usually safer if other software/services are present.
        {"use_ext": True, "priority": DPFPDD_PRIORITY_COOPERATIVE, "label": "open_ext/cooperative"},
        {"use_ext": True, "priority": DPFPDD_PRIORITY_EXCLUSIVE, "label": "open_ext/exclusive"},
        {"use_ext": False, "priority": DPFPDD_PRIORITY_COOPERATIVE, "label": "open/exclusive(default)"},
    ]
    
    # Use context manager for automatic cleanup
    with FingerPrintReader() as reader:
        
        # Initialize SDK
        print("[*] Initializing SDK...")
        if not reader.init():
            print("[!] Failed to initialize SDK")
            return
        
        # List connected readers
        print("[*] Attempting to enumerate devices...")
        devices = reader.list_devices()
        
        if devices:
            print(f"\n[+] Found {len(devices)} device(s):")
            for i, dev in enumerate(devices, 1):
                print(f"  {i}. {dev['product']} (by {dev['vendor']})")
                print(f"     Serial: {dev['serial']}")
                print(f"     Name: {dev['name']}")
            candidate_names = [d["name"] for d in devices if d.get("name")]
        else:
            print("[!] Device enumeration failed or no devices found")
            candidate_names = []

        # Keep order stable and avoid duplicated retries.
        for fallback in DEFAULT_DEVICE_NAMES:
            if fallback not in candidate_names:
                candidate_names.append(fallback)

        print("[*] Device open candidates:")
        for i, name in enumerate(candidate_names, 1):
            print(f"    {i}. {name}")
        
        # Try every name with multiple open modes.
        selected_name = None
        selected_mode = None
        for device_name in candidate_names:
            print(f"\n[*] Trying device: {device_name}")
            for mode in OPEN_CANDIDATES:
                print(f"    -> {mode['label']}")
                ok = reader.open(
                    device_name,
                    use_ext=mode["use_ext"],
                    priority=mode["priority"],
                )
                if ok:
                    selected_name = device_name
                    selected_mode = mode["label"]
                    break
            if selected_name:
                break

        if not selected_name:
            print("[!] Failed to open device with all candidates/modes")
            print("[*] Troubleshooting tips:")
            print("    1. Check if the device is connected and powered")
            print("    2. Close other fingerprint apps/services that may own the reader")
            print("    3. Try running this script as Administrator")
            print("    4. Verify SDK/driver architecture matches Python (x64 vs x86)")
            return
        
        print(f"[+] Device opened successfully: {selected_name} via {selected_mode}")
        
        # Check device status
        status = reader.get_status()
        if status:
            print(f"[*] Device status: {status.get('status_text', 'Unknown')}")
            if status.get('finger_detected'):
                print("[*] Finger already detected on reader")
        
        # Optional: Start streaming and calibrate
        print("[*] Starting stream and calibration...")
        try:
            reader.start_stream()
            reader.calibrate()
        except Exception as e:
            print(f"[!] Warning: {e}")
        
        # Continuous capture loop
        print("\n[>>>] Continuous capture mode enabled")
        print(f"[*] Saved files folder: {output_dir}")
        print("[*] Place finger, wait for capture, lift finger, and repeat")
        print("[*] Press Ctrl+C to stop")

        capture_count = 0

        def wait_for_finger_state(target_present: bool, timeout_s: float = 10.0, poll_s: float = 0.12) -> bool:
            """Wait until reader reports finger present/absent state."""
            deadline = time.time() + timeout_s
            while time.time() < deadline:
                st = reader.get_status()
                if st is not None and bool(st.get("finger_detected")) == target_present:
                    return True
                time.sleep(poll_s)
            return False

        try:
            while True:
                print("\n[>>>] Waiting for finger...")
                if not wait_for_finger_state(True, timeout_s=15.0):
                    print("[i] No finger detected yet. Still waiting...")
                    continue

                success, result, image_data = reader.capture(timeout_ms=10000, retries=3)

                if success:
                    capture_count += 1
                    rand_id = uuid.uuid4().hex[:10]
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    output_file = os.path.join(output_dir, f"fp_{timestamp}_{rand_id}.raw")

                    with open(output_file, "wb") as f:
                        f.write(image_data)

                    print("[+] Capture successful!")
                    print(f"    # {capture_count}")
                    print(f"    Image: {result.get('width', 'N/A')}x{result.get('height', 'N/A')} @ {result.get('resolution', 'N/A')} DPI")
                    print(f"    Quality: {result.get('quality', 'N/A')}, Score: {result.get('score', 'N/A')}")
                    print(f"    Data: {len(image_data)} bytes")
                    print(f"    Saved: {output_file}")

                    print("[*] Lift finger to arm next capture...")
                    wait_for_finger_state(False, timeout_s=8.0)
                else:
                    print("[!] No valid capture this cycle (timeout/quality). Retrying...")
        except KeyboardInterrupt:
            print("\n[*] Capture stopped by user (Ctrl+C)")
            print(f"[*] Total captures saved: {capture_count}")
        
        # Cleanup is automatic when exiting context manager
        print("\n[*] Cleaning up...")


if __name__ == "__main__":
    main()
