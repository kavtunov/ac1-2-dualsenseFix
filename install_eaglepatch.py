#!/usr/bin/env python3
"""
Automated installer for EaglePatch and Ultimate ASI Loader for Assassin's Creed 1 and 2.
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

FALLBACK_ASI_ZIP = "https://github.com/ThirteenAG/Ultimate-ASI-Loader/releases/download/v9.7.4/Ultimate-ASI-Loader-NoPDB.zip"
FALLBACK_EAGLEPATCH_AC1 = "https://github.com/Sergeanur/EaglePatch/releases/download/v1.1/EaglePatchAC1.zip"
FALLBACK_EAGLEPATCH_AC2 = "https://github.com/Sergeanur/EaglePatch/releases/download/v1.1/EaglePatchAC2.zip"


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


def find_games() -> dict[str, Path]:
    """Find installed Assassin's Creed games."""
    games: dict[str, Path] = {}
    libs = find_steam_libraries()
    for lib in libs:
        common = lib / "steamapps/common"
        if not common.is_dir():
            continue
        for child in common.iterdir():
            if not child.is_dir():
                continue
            name_lower = child.name.lower()
            if "assassin" in name_lower:
                if (child / "AssassinsCreedIIGame.exe").exists() or (child / "AssassinsCreedII.exe").exists() or "creed 2" in name_lower or "creed ii" in name_lower:
                    games["AC2"] = child
                elif (child / "AssassinsCreed_Dx9.exe").exists() or (child / "AssassinsCreed_Dx10.exe").exists():
                    games["AC1"] = child
    return games


def detect_game_version(game_dir: Path) -> str:
    """Detect whether directory is AC1 or AC2."""
    dir_name = game_dir.name.lower()
    if (game_dir / "AssassinsCreedIIGame.exe").exists() or (game_dir / "AssassinsCreedII.exe").exists() or "creed 2" in dir_name or "creed ii" in dir_name:
        return "AC2"
    return "AC1"


def fetch_json(url: str) -> dict | None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AC-DualSense-Installer"},
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
        headers={"User-Agent": "AC-DualSense-Installer"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    return zipfile.ZipFile(io.BytesIO(data))


def install(target_dir: Path | None = None) -> int:
    detected_games = find_games()

    if target_dir:
        game_path = target_dir
        game_ver = detect_game_version(game_path)
    else:
        # Prompt user or default to available
        if "AC2" in detected_games and "AC1" in detected_games:
            print("Found multiple games:")
            print(f"1) Assassin's Creed 1: {detected_games['AC1']}")
            print(f"2) Assassin's Creed 2: {detected_games['AC2']}")
            print("3) Install for both")
            choice = input("Select [1/2/3] (default 2): ").strip()
            if choice == "1":
                return _install_for_game(detected_games["AC1"], "AC1")
            elif choice == "3":
                rc1 = _install_for_game(detected_games["AC1"], "AC1")
                rc2 = _install_for_game(detected_games["AC2"], "AC2")
                return 0 if (rc1 == 0 and rc2 == 0) else 1
            else:
                return _install_for_game(detected_games["AC2"], "AC2")
        elif "AC2" in detected_games:
            game_path = detected_games["AC2"]
            game_ver = "AC2"
        elif "AC1" in detected_games:
            game_path = detected_games["AC1"]
            game_ver = "AC1"
        else:
            print("[-] Could not find Assassin's Creed 1 or 2 directory automatically.")
            path_input = input("Enter path to game folder manually: ").strip()
            game_path = Path(path_input)
            if not game_path.is_dir():
                print("[-] Invalid game folder. Aborting.")
                return 1
            game_ver = detect_game_version(game_path)

    return _install_for_game(game_path, game_ver)


def _install_for_game(game_path: Path, game_ver: str) -> int:
    print(f"[+] Installing for {game_ver} at: {game_path}")

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
                out_path = game_path / "dinput8.dll"
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

    # 2. Download EaglePatch for AC1 or AC2
    ep_zip_name = f"eaglepatch{game_ver.lower()}.zip"
    ep_url = None
    ep_data = fetch_json(EAGLEPATCH_API)
    if ep_data:
        for asset in ep_data.get("assets", []):
            name = asset.get("name", "").lower()
            if ep_zip_name in name and name.endswith(".zip"):
                ep_url = asset.get("browser_download_url")
                break
    if not ep_url:
        ep_url = FALLBACK_EAGLEPATCH_AC2 if game_ver == "AC2" else FALLBACK_EAGLEPATCH_AC1

    scripts_dir = game_path / "scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    # Clean old wrong ASI if switching
    if game_ver == "AC2":
        old_ac1_asi = scripts_dir / "EaglePatchAC1.asi"
        old_ac1_ini = scripts_dir / "EaglePatchAC1.ini"
        if old_ac1_asi.exists():
            old_ac1_asi.unlink()
        if old_ac1_ini.exists():
            old_ac1_ini.unlink()

    try:
        zf_ep = download_zip(ep_url)
        for item in zf_ep.namelist():
            filename = Path(item).name
            if filename in (f"EaglePatch{game_ver}.asi", f"EaglePatch{game_ver}.ini"):
                out_path = scripts_dir / filename
                out_path.write_bytes(zf_ep.read(item))
                print(f"[+] Extracted {filename} -> {out_path}")
    except Exception as exc:
        print(f"[-] Error installing EaglePatch: {exc}")
        return 1

    # 3. Configure ini
    ini_path = scripts_dir / f"EaglePatch{game_ver}.ini"
    if ini_path.exists():
        try:
            content = ini_path.read_text(encoding="utf-8", errors="ignore")
            content = re.sub(r"(?i)DisableXInputPatch\s*=\s*\d+", "DisableXInputPatch=0", content)
            content = re.sub(r"(?i)EnableGamepad\s*=\s*\d+", "EnableGamepad=1", content)
            ini_path.write_text(content, encoding="utf-8")
            print(f"[+] Configured EaglePatch{game_ver}.ini (XInput support enabled)")
        except Exception as exc:
            print(f"[!] Warning: failed to auto-edit {ini_path.name}: {exc}")

    print("\n" + "=" * 60)
    print(f"SUCCESS! EaglePatch {game_ver} & ASI Loader installed successfully.")
    print("Important for Steam/Proton on Linux:")
    print("Make sure your Steam Launch Options for the game include:")
    print('  WINEDLLOVERRIDES="dinput8=n,b" %command%')
    print("And ensure 'Steam Input' is set to 'Disable Steam Input'.")
    print("=" * 60 + "\n")
    return 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    sys.exit(install(target))
