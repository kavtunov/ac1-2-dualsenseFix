#!/usr/bin/env python3
"""
Automated installer for EaglePatch and Ultimate ASI Loader for Assassin's Creed 1.
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

EAGLEPATCH_API = "https://api.github.com/repos/Sergeanur/EaglePatch/releases/latest"
ASI_LOADER_API = "https://api.github.com/repos/ThirteenAG/Ultimate-ASI-Loader/releases/latest"

FALLBACK_EAGLEPATCH_ZIP = "https://github.com/Sergeanur/EaglePatch/releases/download/v1.1/EaglePatchAC1.zip"
FALLBACK_ASI_ZIP = "https://github.com/ThirteenAG/Ultimate-ASI-Loader/releases/download/v4.68/Ultimate-ASI-Loader.zip"


def find_steam_libraries() -> list[Path]:
    candidates = [
        Path.home() / ".local/share/Steam",
        Path.home() / ".steam/steam",
        Path.home() / ".steam/root",
    ]
    steam_roots = [p for p in candidates if p.is_dir()]
    lib_paths: set[Path] = set()

    for root in steam_roots:
        lib_paths.add(root)
        vdf = root / "steamapps/libraryfolders.vdf"
        if vdf.exists():
            try:
                content = vdf.read_text(encoding="utf-8", errors="ignore")
                for match in re.finditer(r'"path"\s+"([^"]+)"', content):
                    p = Path(match.group(1))
                    if p.is_dir():
                        lib_paths.add(p)
            except OSError:
                pass

    # Common mounted paths
    for media_root in Path("/run/media").glob("*/*"):
        if media_root.is_dir():
            for sub in ("SteamLibrary", "Steam", "steamapps"):
                candidate = media_root / sub
                if candidate.is_dir():
                    lib_paths.add(candidate if sub != "steamapps" else media_root)

    return list(lib_paths)


def find_ac1_dir() -> Path | None:
    libs = find_steam_libraries()
    for lib in libs:
        common = lib / "steamapps/common"
        if not common.is_dir():
            continue
        for child in common.iterdir():
            if child.is_dir() and "assassin" in child.name.lower():
                if (child / "AssassinsCreed_Dx9.exe").exists() or (child / "AssassinsCreed_Dx10.exe").exists():
                    return child
    return None


def fetch_json(url: str) -> dict | None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AC1-DualSense-Installer"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"[!] Warning: failed to fetch release metadata ({exc})")
        return None


def download_zip(url: str) -> zipfile.ZipFile:
    print(f"[*] Downloading {url} ...")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AC1-DualSense-Installer"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    return zipfile.ZipFile(io.BytesIO(data))


def install(target_dir: Path | None = None) -> int:
    ac1 = target_dir or find_ac1_dir()
    if not ac1 or not ac1.is_dir():
        print("[-] Could not find Assassin's Creed 1 directory automatically.")
        path_input = input("Enter path to AC1 game folder manually: ").strip()
        ac1 = Path(path_input)
        if not ac1.is_dir() or not ((ac1 / "AssassinsCreed_Dx9.exe").exists() or (ac1 / "AssassinsCreed_Game.exe").exists()):
            print("[-] Invalid game folder. Aborting.")
            return 1

    print(f"[+] Found Assassin's Creed 1 at: {ac1}")

    # 1. Download ASI Loader
    asi_url = None
    asi_data = fetch_json(ASI_LOADER_API)
    if asi_data:
        for asset in asi_data.get("assets", []):
            name = asset.get("name", "").lower()
            if "ultimate-asi-loader" in name and "x64" not in name and name.endswith(".zip"):
                asi_url = asset.get("browser_download_url")
                break
    if not asi_url:
        asi_url = FALLBACK_ASI_ZIP

    try:
        zf_asi = download_zip(asi_url)
        dinput8_extracted = False
        for item in zf_asi.namelist():
            if Path(item).name.lower() == "dinput8.dll":
                out_path = ac1 / "dinput8.dll"
                out_path.write_bytes(zf_asi.read(item))
                print(f"[+] Extracted dinput8.dll -> {out_path}")
                dinput8_extracted = True
                break
        if not dinput8_extracted:
            print("[-] Could not find dinput8.dll in ASI loader zip!")
            return 1
    except Exception as exc:
        print(f"[-] Error installing ASI Loader: {exc}")
        return 1

    # 2. Download EaglePatch
    ep_url = None
    ep_data = fetch_json(EAGLEPATCH_API)
    if ep_data:
        for asset in ep_data.get("assets", []):
            name = asset.get("name", "").lower()
            if "eaglepatchac1" in name and name.endswith(".zip"):
                ep_url = asset.get("browser_download_url")
                break
    if not ep_url:
        ep_url = FALLBACK_EAGLEPATCH_ZIP

    scripts_dir = ac1 / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    try:
        zf_ep = download_zip(ep_url)
        for item in zf_ep.namelist():
            filename = Path(item).name
            if filename in ("EaglePatchAC1.asi", "EaglePatchAC1.ini"):
                out_path = scripts_dir / filename
                out_path.write_bytes(zf_ep.read(item))
                print(f"[+] Extracted {filename} -> {out_path}")
    except Exception as exc:
        print(f"[-] Error installing EaglePatch: {exc}")
        return 1

    # 3. Configure EaglePatchAC1.ini
    ini_path = scripts_dir / "EaglePatchAC1.ini"
    if ini_path.exists():
        try:
            content = ini_path.read_text(encoding="utf-8", errors="ignore")
            # Enable XInput / Gamepad
            content = re.sub(r"(?i)EnableGamepad\s*=\s*\d+", "EnableGamepad = 1", content)
            ini_path.write_text(content, encoding="utf-8")
            print("[+] Configured EaglePatchAC1.ini (EnableGamepad = 1)")
        except Exception as exc:
            print(f"[!] Warning: failed to auto-edit EaglePatchAC1.ini: {exc}")

    print("\n" + "=" * 60)
    print("SUCCESS! EaglePatch & ASI Loader installed successfully.")
    print("Important for Steam/Proton on Linux:")
    print("Make sure your Steam Launch Options for Assassin's Creed 1 include:")
    print('  WINEDLLOVERRIDES="dinput8=n,b" %command%')
    print("=" * 60 + "\n")
    return 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    sys.exit(install(target))
