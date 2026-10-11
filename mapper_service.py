#!/usr/bin/env python3
"""
Mapper background worker and controller that can be driven via CLI,
imported as a thread/service in the GUI, or executed standalone.
"""

from __future__ import annotations

import select
import sys
import threading
import time
from pathlib import Path
from typing import Callable

from evdev import AbsInfo, InputDevice, UInput, ecodes, ff, list_devices

from config_lib import (
    DUALSENSE_TO_EVDEV,
    XBOX_LABEL_TO_CODE,
    load_config,
)

TARGET_NAME = "DualSense Wireless Controller"
POLL_DT = 0.004
AXIS_MAX = 32767
TRIG_MAX = 255


def find_dualsense() -> InputDevice | None:
    for path in list_devices():
        try:
            dev = InputDevice(path)
            if dev.name == TARGET_NAME:
                return dev
        except (OSError, FileNotFoundError):
            continue
    return None


def find_all_dualsense_nodes() -> list[InputDevice]:
    nodes: list[InputDevice] = []
    for path in list_devices():
        try:
            dev = InputDevice(path)
            if "DualSense Wireless Controller" in dev.name:
                nodes.append(dev)
        except (OSError, FileNotFoundError):
            continue
    return nodes


def build_xbox_pad(enable_rumble: bool = True) -> UInput:
    abs_info_stick = AbsInfo(
        value=0, min=-AXIS_MAX, max=AXIS_MAX, fuzz=16, flat=128, resolution=0
    )
    abs_info_trig = AbsInfo(value=0, min=0, max=TRIG_MAX, fuzz=0, flat=0, resolution=0)
    abs_info_hat = AbsInfo(value=0, min=-1, max=1, fuzz=0, flat=0, resolution=0)
    cap = {
        ecodes.EV_KEY: [
            ecodes.BTN_A,
            ecodes.BTN_B,
            ecodes.BTN_X,
            ecodes.BTN_Y,
            ecodes.BTN_TL,
            ecodes.BTN_TR,
            ecodes.BTN_SELECT,
            ecodes.BTN_START,
            ecodes.BTN_MODE,
            ecodes.BTN_THUMBL,
            ecodes.BTN_THUMBR,
        ],
        ecodes.EV_ABS: [
            (ecodes.ABS_X, abs_info_stick),
            (ecodes.ABS_Y, abs_info_stick),
            (ecodes.ABS_RX, abs_info_stick),
            (ecodes.ABS_RY, abs_info_stick),
            (ecodes.ABS_Z, abs_info_trig),
            (ecodes.ABS_RZ, abs_info_trig),
            (ecodes.ABS_HAT0X, abs_info_hat),
            (ecodes.ABS_HAT0Y, abs_info_hat),
        ],
    }
    if enable_rumble:
        cap[ecodes.EV_FF] = [ecodes.FF_RUMBLE]

    return UInput(
        cap,
        name="Microsoft X-Box 360 pad",
        vendor=0x045E,
        product=0x028E,
        version=0x0110,
        bustype=ecodes.BUS_USB,
    )


def build_mouse() -> UInput:
    cap = {
        ecodes.EV_REL: [ecodes.REL_X, ecodes.REL_Y],
        ecodes.EV_KEY: [ecodes.BTN_LEFT, ecodes.BTN_RIGHT],
    }
    return UInput(
        cap,
        name="DualSense Virtual Mouse",
        bustype=ecodes.BUS_USB,
    )


def set_btn(ui: UInput, code: int, pressed: bool, state: dict[int, bool]) -> None:
    now = bool(pressed)
    if state.get(code) == now:
        return
    state[code] = now
    ui.write(ecodes.EV_KEY, code, 1 if now else 0)
    ui.syn()


def set_abs(ui: UInput, code: int, value: int, state: dict[int, int]) -> None:
    if state.get(code) == value:
        return
    state[code] = value
    ui.write(ecodes.EV_ABS, code, value)
    ui.syn()


def make_stick_normalizer(deadzone: float, sensitivity: float = 1.0):
    def norm_stick(value: int, info: AbsInfo) -> int:
        mid = (info.min + info.max) / 2.0
        half = max((info.max - info.min) / 2.0, 1.0)
        v = (value - mid) / half
        if abs(v) < deadzone:
            return 0
        sign = 1.0 if v > 0 else -1.0
        mag = (abs(v) - deadzone) / (1.0 - deadzone)
        # Apply sensitivity scaling smoothly
        scaled = sign * min(1.0, mag * sensitivity)
        return int(max(-AXIS_MAX, min(AXIS_MAX, scaled * AXIS_MAX)))

    return norm_stick


def make_trigger_normalizer(threshold: float):
    def norm_trigger(value: int, info: AbsInfo) -> int:
        span = max(info.max - info.min, 1)
        t = (value - info.min) / span
        if t < threshold:
            return 0
        t = (t - threshold) / (1.0 - threshold)
        return int(max(0, min(TRIG_MAX, t * TRIG_MAX)))

    return norm_trigger


def build_btn_map(buttons: dict[str, str]) -> dict[int, int]:
    mapping: dict[int, int] = {}
    for dual_key, xbox_label in buttons.items():
        dual_name = DUALSENSE_TO_EVDEV.get(dual_key)
        xbox_name = XBOX_LABEL_TO_CODE.get(xbox_label)
        if not dual_name or not xbox_name:
            continue
        dual_code = getattr(ecodes, dual_name)
        xbox_code = getattr(ecodes, xbox_name)
        mapping[dual_code] = xbox_code
    return mapping


class BatteryLedManager:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.last_update = 0.0
        self.last_color: tuple[int, int, int] | None = None
        self.led_nodes = self._find_led_nodes()

    def _find_led_nodes(self) -> dict[str, Path]:
        base = Path("/sys/class/leds")
        if not base.is_dir():
            return {}
        nodes: dict[str, Path] = {}
        for entry in base.glob("*dualsense*"):
            name = entry.name.lower()
            if ":red" in name or name.endswith("red"):
                nodes["red"] = entry / "brightness"
            elif ":green" in name or name.endswith("green"):
                nodes["green"] = entry / "brightness"
            elif ":blue" in name or name.endswith("blue"):
                nodes["blue"] = entry / "brightness"
        return nodes

    def get_battery_capacity(self) -> int | None:
        base = Path("/sys/class/power_supply")
        if not base.is_dir():
            return None
        for entry in base.glob("*dualsense*"):
            cap_file = entry / "capacity"
            if cap_file.exists():
                try:
                    return int(cap_file.read_text(encoding="utf-8").strip())
                except (ValueError, OSError):
                    pass
        return None

    def update(self, force: bool = False) -> None:
        if not self.enabled:
            return
        now = time.time()
        if not force and (now - self.last_update < 10.0):
            return
        self.last_update = now

        capacity = self.get_battery_capacity()
        if capacity is None:
            color = (0, 100, 255)
        elif capacity <= 15:
            color = (255, 0, 0)
        elif capacity <= 40:
            color = (255, 120, 0)
        elif capacity <= 75:
            color = (200, 220, 0)
        else:
            color = (0, 255, 60)

        if color == self.last_color and not force:
            return

        self.last_color = color
        if not self.led_nodes:
            self.led_nodes = self._find_led_nodes()
        if not self.led_nodes:
            return
        for channel, val in zip(("red", "green", "blue"), color):
            p = self.led_nodes.get(channel)
            if p and p.exists():
                try:
                    p.write_text(str(val), encoding="utf-8")
                except OSError:
                    pass


class TouchpadHandler:
    def __init__(self, mouse: UInput | None, sensitivity: float = 1.2, enabled: bool = True) -> None:
        self.mouse = mouse
        self.sensitivity = sensitivity
        self.enabled = enabled and (mouse is not None)
        self.last_x: int | None = None
        self.last_y: int | None = None
        self.is_touching = False

    def handle_event(self, event) -> None:
        if not self.enabled or not self.mouse:
            return
        if event.type == ecodes.EV_KEY:
            if event.code == ecodes.BTN_TOUCH:
                self.is_touching = (event.value != 0)
                if not self.is_touching:
                    self.last_x = None
                    self.last_y = None
            elif event.code == ecodes.BTN_TOOL_FINGER:
                if event.value == 0:
                    self.last_x = None
                    self.last_y = None
            elif event.code == ecodes.BTN_LEFT:
                self.mouse.write(ecodes.EV_KEY, ecodes.BTN_LEFT, event.value)
                self.mouse.syn()
        elif event.type == ecodes.EV_ABS:
            if event.code in (ecodes.ABS_X, ecodes.ABS_MT_POSITION_X):
                cur_x = event.value
                if self.last_x is not None:
                    dx = int((cur_x - self.last_x) * self.sensitivity * 0.15)
                    if dx != 0:
                        self.mouse.write(ecodes.EV_REL, ecodes.REL_X, dx)
                        self.mouse.syn()
                self.last_x = cur_x
            elif event.code in (ecodes.ABS_Y, ecodes.ABS_MT_POSITION_Y):
                cur_y = event.value
                if self.last_y is not None:
                    dy = int((cur_y - self.last_y) * self.sensitivity * 0.15)
                    if dy != 0:
                        self.mouse.write(ecodes.EV_REL, ecodes.REL_Y, dy)
                        self.mouse.syn()
                self.last_y = cur_y
            elif event.code == ecodes.ABS_MT_TRACKING_ID and event.value == -1:
                self.last_x = None
                self.last_y = None


class RumbleRelay:
    def __init__(self, real_pad: InputDevice | None, enabled: bool = True) -> None:
        self.real_pad = real_pad
        self.enabled = enabled and (real_pad is not None)
        self.active_effect_id = -1
        self.ff_supported = False
        if self.real_pad and self.enabled:
            caps = self.real_pad.capabilities()
            if ecodes.EV_FF in caps:
                self.ff_supported = True

    def set_rumble(self, strong_magnitude: int, weak_magnitude: int) -> None:
        if not self.ff_supported or not self.real_pad:
            return
        try:
            if strong_magnitude == 0 and weak_magnitude == 0:
                if self.active_effect_id >= 0:
                    self.real_pad.erase_effect(self.active_effect_id)
                    self.active_effect_id = -1
                return

            rumble = ff.Rumble(strong_magnitude=strong_magnitude, weak_magnitude=weak_magnitude)
            effect = ff.Effect(
                ecodes.FF_RUMBLE,
                -1,
                0,
                ff.Trigger(0, 0),
                ff.Replay(1000, 0),
                ff.EffectType(ff_rumble_effect=rumble),
            )
            new_id = self.real_pad.upload_effect(effect)
            self.real_pad.write(ecodes.EV_FF, new_id, 1)

            if self.active_effect_id >= 0 and self.active_effect_id != new_id:
                try:
                    self.real_pad.erase_effect(self.active_effect_id)
                except OSError:
                    pass
            self.active_effect_id = new_id
        except OSError:
            pass

    def stop(self) -> None:
        if self.active_effect_id >= 0 and self.real_pad:
            try:
                self.real_pad.erase_effect(self.active_effect_id)
            except OSError:
                pass
            self.active_effect_id = -1


class MapperService:
    """Threaded controller for the DualSense to Xbox mapper."""

    def __init__(
        self,
        on_status_change: Callable[[str, bool, int | None], None] | None = None,
        on_input_event: Callable[[str, any], None] | None = None,
    ) -> None:
        self.on_status_change = on_status_change
        self.on_input_event = on_input_event
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.is_running = False
        self.controller_connected = False
        self.current_battery: int | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._worker, daemon=True, name="MapperWorker")
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        self.is_running = False
        self.controller_connected = False
        self._notify_status("Stopped", False)

    def _notify_status(self, msg: str, connected: bool) -> None:
        self.controller_connected = connected
        if self.on_status_change:
            try:
                self.on_status_change(msg, connected, self.current_battery)
            except Exception:
                pass

    def _worker(self) -> None:
        self.is_running = True
        self._notify_status("Starting...", False)

        while not self._stop_event.is_set():
            cfg = load_config()
            stick_deadzone = float(cfg["stick_deadzone"])
            trigger_threshold = float(cfg["trigger_threshold"])
            camera_sensitivity = float(cfg["camera_sensitivity"])
            touchpad_mouse_enabled = bool(cfg.get("touchpad_mouse", True))
            touchpad_sens = float(cfg.get("touchpad_sensitivity", 1.2))
            rumble_enabled = bool(cfg.get("rumble_enabled", True))
            battery_led_enabled = bool(cfg.get("battery_led", True))

            norm_stick = make_stick_normalizer(stick_deadzone, 1.0)
            norm_camera = make_stick_normalizer(stick_deadzone, camera_sensitivity)
            norm_trigger = make_trigger_normalizer(trigger_threshold)
            btn_map = build_btn_map(cfg["buttons"])

            self._notify_status("Waiting for DualSense...", False)
            pad: InputDevice | None = None
            while not self._stop_event.is_set() and pad is None:
                pad = find_dualsense()
                if pad is None:
                    time.sleep(0.5)

            if self._stop_event.is_set() or pad is None:
                break

            nodes = find_all_dualsense_nodes()
            for node in nodes:
                try:
                    node.grab()
                except OSError:
                    pass

            abs_caps: dict[int, AbsInfo] = {}
            for item in pad.capabilities(absinfo=True).get(ecodes.EV_ABS, []):
                if isinstance(item, tuple):
                    code, info = item[0], item[1]
                    abs_caps[int(code)] = (
                        info if isinstance(info, AbsInfo) else pad.absinfo(int(code))
                    )
                else:
                    abs_caps[int(item)] = pad.absinfo(int(item))

            axis_names = {code: ecodes.ABS[code] for code in abs_caps}

            def axis_by(*names: str) -> int | None:
                for code, name in axis_names.items():
                    if name in names:
                        return code
                return None

            def rest_value(code: int) -> int:
                return int(pad.absinfo(code).value)

            def is_centered(code: int | None) -> bool:
                if code is None:
                    return False
                info = abs_caps[code]
                mid = (info.min + info.max) / 2.0
                return abs(rest_value(code) - mid) <= (info.max - info.min) * 0.20

            def is_trigger_rest(code: int | None) -> bool:
                if code is None:
                    return False
                info = abs_caps[code]
                span = max(info.max - info.min, 1)
                return (rest_value(code) - info.min) / span <= 0.12

            lx, ly = axis_by("ABS_X"), axis_by("ABS_Y")
            rx = ry = None
            for a, b in (
                (axis_by("ABS_RX"), axis_by("ABS_RY")),
                (axis_by("ABS_Z"), axis_by("ABS_RZ")),
            ):
                if is_centered(a) and is_centered(b):
                    rx, ry = a, b
                    break
            if rx is None:
                rx, ry = axis_by("ABS_RX"), axis_by("ABS_RY")

            triggers = sorted(
                {
                    c
                    for c in (
                        axis_by("ABS_Z"),
                        axis_by("ABS_RZ"),
                        axis_by("ABS_RX"),
                        axis_by("ABS_RY"),
                    )
                    if c is not None and c not in (lx, ly, rx, ry) and is_trigger_rest(c)
                }
            )
            lt = triggers[0] if len(triggers) > 0 else None
            rt = triggers[1] if len(triggers) > 1 else None

            ui = build_xbox_pad(enable_rumble=rumble_enabled)
            mouse = build_mouse() if touchpad_mouse_enabled else None
            touchpad_handler = TouchpadHandler(
                mouse, sensitivity=touchpad_sens, enabled=touchpad_mouse_enabled
            )
            rumble_relay = RumbleRelay(pad, enabled=rumble_enabled)
            battery_led = BatteryLedManager(enabled=battery_led_enabled)
            battery_led.update(force=True)

            self.current_battery = battery_led.get_battery_capacity()
            self._notify_status("Connected & Active", True)

            btn_state: dict[int, bool] = {}
            abs_state: dict[int, int] = {}
            axis_values = {code: int(pad.absinfo(code).value) for code in abs_caps}

            select_fds = [n.fd for n in nodes]
            if rumble_enabled:
                select_fds.append(ui.fd)

            disconnected = False
            last_bat_check = time.time()

            try:
                while not self._stop_event.is_set() and not disconnected:
                    now = time.time()
                    if now - last_bat_check > 5.0:
                        last_bat_check = now
                        battery_led.update()
                        bat = battery_led.get_battery_capacity()
                        if bat != self.current_battery:
                            self.current_battery = bat
                            self._notify_status("Connected & Active", True)

                    try:
                        readable, _, _ = select.select(select_fds, [], [], POLL_DT)
                    except (OSError, ValueError):
                        disconnected = True
                        break

                    if readable:
                        if ui.fd in readable:
                            try:
                                for event in ui.read():
                                    if event.type == ecodes.EV_FF:
                                        rumble_relay.set_rumble(event.value, event.value)
                            except (OSError, BlockingIOError):
                                pass

                        for node in nodes:
                            if node.fd not in readable:
                                continue
                            try:
                                events = list(node.read())
                            except OSError:
                                disconnected = True
                                break

                            for event in events:
                                if node.path == pad.path:
                                    if event.type == ecodes.EV_KEY and event.value != 2:
                                        mapped = btn_map.get(event.code)
                                        if mapped is not None:
                                            set_btn(ui, mapped, event.value != 0, btn_state)
                                        if self.on_input_event:
                                            self.on_input_event("button", (event.code, event.value != 0))
                                    elif event.type == ecodes.EV_ABS:
                                        axis_values[event.code] = event.value
                                        if event.code == ecodes.ABS_HAT0X:
                                            set_abs(ui, ecodes.ABS_HAT0X, int(event.value), abs_state)
                                        elif event.code == ecodes.ABS_HAT0Y:
                                            set_abs(ui, ecodes.ABS_HAT0Y, int(event.value), abs_state)
                                        if self.on_input_event:
                                            self.on_input_event("axis", (event.code, event.value))
                                else:
                                    touchpad_handler.handle_event(event)

                    if disconnected:
                        break

                    if lx is not None and ly is not None:
                        set_abs(ui, ecodes.ABS_X, norm_stick(axis_values[lx], abs_caps[lx]), abs_state)
                        set_abs(ui, ecodes.ABS_Y, norm_stick(axis_values[ly], abs_caps[ly]), abs_state)
                    if rx is not None and ry is not None:
                        set_abs(
                            ui, ecodes.ABS_RX, norm_camera(axis_values[rx], abs_caps[rx]), abs_state
                        )
                        set_abs(
                            ui, ecodes.ABS_RY, norm_camera(axis_values[ry], abs_caps[ry]), abs_state
                        )
                    if lt is not None:
                        set_abs(ui, ecodes.ABS_Z, norm_trigger(axis_values[lt], abs_caps[lt]), abs_state)
                    if rt is not None:
                        set_abs(ui, ecodes.ABS_RZ, norm_trigger(axis_values[rt], abs_caps[rt]), abs_state)

            finally:
                rumble_relay.stop()
                for node in nodes:
                    try:
                        node.ungrab()
                    except OSError:
                        pass
                ui.close()
                if mouse:
                    mouse.close()

            if disconnected:
                self._notify_status("Disconnected. Retrying...", False)
                time.sleep(1.0)

        self.is_running = False
        self._notify_status("Stopped", False)
