#!/usr/bin/env python3
"""
CLI entry point for the AC1 DualSense Mapper.
Uses the unified mapper_service backend.
"""

from __future__ import annotations

import sys
import time

from mapper_service import MapperService


def on_status(msg: str, connected: bool, battery: int | None) -> None:
    bat_str = f" [Battery: {battery}%]" if battery is not None else ""
    status_str = "ACTIVE" if connected else "WAITING"
    print(f"[*] [{status_str}] {msg}{bat_str}")


def main() -> int:
    print("==================================================")
    print("      Assassin's Creed 1 - DualSense Mapper       ")
    print("==================================================")
    service = MapperService(on_status_change=on_status)
    service.start()
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nStopping DualSense mapper...")
        service.stop()
    print("Mapper stopped successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
