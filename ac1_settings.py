#!/usr/bin/env python3
"""
AC DualSense Settings - Compact & Modern Control Panel
Allows tweaking camera sensitivity, stick deadzone, triggers, and button bindings.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from config_lib import (
    DEFAULT_CONFIG,
    DUALSENSE_KEYS,
    XBOX_ACTIONS,
    load_config,
    save_config,
)


class SettingsApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Assassin's Creed DualSense Settings")
        self.geometry("520x640")
        self.minsize(480, 560)
        self.configure(bg="#181a20")

        self.config_data = load_config()
        self.button_vars: dict[str, tk.StringVar] = {}
        self.label_to_code = {label: code for code, label in XBOX_ACTIONS}
        self.code_to_label = {code: label for code, label in XBOX_ACTIONS}

        self.deadzone_var = tk.DoubleVar(value=float(self.config_data.get("stick_deadzone", 0.18)))
        self.trigger_var = tk.DoubleVar(value=float(self.config_data.get("trigger_threshold", 0.12)))
        self.camera_var = tk.DoubleVar(value=float(self.config_data.get("camera_sensitivity", 0.75)))
        self.touchpad_mouse_var = tk.BooleanVar(value=bool(self.config_data.get("touchpad_mouse", True)))
        self.touchpad_sens_var = tk.DoubleVar(value=float(self.config_data.get("touchpad_sensitivity", 1.2)))
        self.rumble_var = tk.BooleanVar(value=bool(self.config_data.get("rumble_enabled", True)))
        self.battery_led_var = tk.BooleanVar(value=bool(self.config_data.get("battery_led", True)))

        self._apply_styles()
        self._build()

    def _apply_styles(self) -> None:
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.style.configure(".", background="#181a20", foreground="#e2e8f0", font=("Segoe UI", 10))
        self.style.configure("TFrame", background="#181a20")
        self.style.configure("TLabelframe", background="#1f232b", foreground="#38bdf8", font=("Segoe UI", 10, "bold"))
        self.style.configure("TLabelframe.Label", background="#1f232b", foreground="#38bdf8")

        self.style.configure("TLabel", background="#1f232b", foreground="#e2e8f0")
        self.style.configure("Header.TLabel", background="#181a20", foreground="#38bdf8", font=("Segoe UI", 13, "bold"))
        self.style.configure("Value.TLabel", background="#1f232b", foreground="#38bdf8", font=("Segoe UI", 10, "bold"))

        self.style.configure("TCheckbutton", background="#1f232b", foreground="#e2e8f0")
        self.style.map("TCheckbutton", background=[("active", "#1f232b")])

        self.style.configure("TCombobox", fieldbackground="#262c37", background="#262c37", foreground="#ffffff")
        self.style.map("TCombobox", fieldbackground=[("readonly", "#262c37")], selectbackground=[("readonly", "#0284c7")])

        self.style.configure("TScale", background="#1f232b", troughcolor="#2b323f")

        self.style.configure("Primary.TButton", background="#0284c7", foreground="#ffffff", font=("Segoe UI", 10, "bold"), borderwidth=0, padding=6)
        self.style.map("Primary.TButton", background=[("active", "#0369a1")])

        self.style.configure("Secondary.TButton", background="#2b323f", foreground="#e2e8f0", font=("Segoe UI", 10), borderwidth=0, padding=6)
        self.style.map("Secondary.TButton", background=[("active", "#384152")])

    def _build(self) -> None:
        container = ttk.Frame(self, padding=16)
        container.pack(fill="both", expand=True)

        # Header title
        header_frame = ttk.Frame(container)
        header_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(header_frame, text="DualSense Controller Settings", style="Header.TLabel").pack(side="left")

        # Sensitivity card
        sens_box = ttk.LabelFrame(container, text="  Sensitivity & Deadzones  ", padding=12)
        sens_box.pack(fill="x", pady=(0, 10))

        self._add_slider(sens_box, "Camera Sensitivity", self.camera_var, 0.1, 2.0, 0, unit="x")
        self._add_slider(sens_box, "Stick Deadzone", self.deadzone_var, 0.0, 0.5, 1, percent=True)
        self._add_slider(sens_box, "Trigger Threshold", self.trigger_var, 0.0, 0.5, 2, percent=True)
        self._add_slider(sens_box, "Touchpad Speed", self.touchpad_sens_var, 0.2, 3.0, 3, unit="x")

        # Feature Toggles card
        feat_box = ttk.LabelFrame(container, text="  Features  ", padding=12)
        feat_box.pack(fill="x", pady=(0, 10))

        ttk.Checkbutton(feat_box, text="Touchpad as Virtual Mouse in Menus", variable=self.touchpad_mouse_var).pack(anchor="w", pady=2)
        ttk.Checkbutton(feat_box, text="Force Feedback (Vibration / Rumble)", variable=self.rumble_var).pack(anchor="w", pady=2)
        ttk.Checkbutton(feat_box, text="Battery LED Indicator (Lightbar)", variable=self.battery_led_var).pack(anchor="w", pady=2)

        # Buttons Mapping card
        btn_box = ttk.LabelFrame(container, text="  Button Mapping (DualSense -> Xbox 360)  ", padding=12)
        btn_box.pack(fill="both", expand=True, pady=(0, 12))

        xbox_labels = [label for _code, label in XBOX_ACTIONS]

        for idx, (key, dual_label) in enumerate(DUALSENSE_KEYS):
            row = idx // 2
            col = (idx % 2) * 3

            lbl = ttk.Label(btn_box, text=f"{dual_label}:")
            lbl.grid(row=row, column=col, sticky="w", padx=(6, 2), pady=3)

            current = self.config_data.get("buttons", {}).get(key, "None")
            var = tk.StringVar(value=self.code_to_label.get(current, self.code_to_label.get("None", "None")))
            self.button_vars[key] = var

            combo = ttk.Combobox(
                btn_box,
                textvariable=var,
                values=xbox_labels,
                state="readonly",
                width=8,
            )
            combo.grid(row=row, column=col + 1, sticky="w", padx=(2, 14), pady=3)

        btn_box.columnconfigure(1, weight=1)
        btn_box.columnconfigure(4, weight=1)

        # Bottom buttons
        bottom = ttk.Frame(container)
        bottom.pack(fill="x", pady=(4, 0))

        ttk.Button(bottom, text="Reset Defaults", style="Secondary.TButton", command=self.reset_defaults).pack(side="left")
        ttk.Button(bottom, text="Save Settings", style="Primary.TButton", command=self.save).pack(side="right")

    def _add_slider(
        self,
        parent: ttk.LabelFrame,
        title: str,
        variable: tk.DoubleVar,
        low: float,
        high: float,
        row: int,
        unit: str = "",
        percent: bool = False,
    ) -> None:
        ttk.Label(parent, text=title).grid(row=row, column=0, sticky="w", padx=6, pady=4)

        def format_val() -> str:
            v = variable.get()
            if percent:
                return f"{int(v * 100)}%"
            return f"{v:.2f}{unit}"

        value_label = ttk.Label(parent, text=format_val(), style="Value.TLabel", width=7, anchor="e")
        value_label.grid(row=row, column=2, sticky="e", padx=6)

        def on_change(_event: object | None = None) -> None:
            value_label.configure(text=format_val())

        scale = ttk.Scale(
            parent,
            from_=low,
            to=high,
            variable=variable,
            command=lambda _v: on_change(),
        )
        scale.grid(row=row, column=1, sticky="ew", padx=8, pady=4)
        parent.columnconfigure(1, weight=1)

    def _collect(self) -> dict:
        buttons = {}
        for key, var in self.button_vars.items():
            buttons[key] = self.label_to_code.get(var.get(), "None")
        return {
            "stick_deadzone": round(float(self.deadzone_var.get()), 3),
            "trigger_threshold": round(float(self.trigger_var.get()), 3),
            "camera_sensitivity": round(float(self.camera_var.get()), 3),
            "touchpad_mouse": bool(self.touchpad_mouse_var.get()),
            "touchpad_sensitivity": round(float(self.touchpad_sens_var.get()), 3),
            "rumble_enabled": bool(self.rumble_var.get()),
            "battery_led": bool(self.battery_led_var.get()),
            "buttons": buttons,
        }

    def save(self) -> None:
        save_config(self._collect())
        messagebox.showinfo("Saved", "Settings saved successfully! Mapper will use updated values.")

    def reset_defaults(self) -> None:
        self.config_data = dict(DEFAULT_CONFIG)
        self.config_data["buttons"] = dict(DEFAULT_CONFIG["buttons"])
        for key, var in self.button_vars.items():
            var.set(self.code_to_label[self.config_data["buttons"][key]])
        self.deadzone_var.set(DEFAULT_CONFIG["stick_deadzone"])
        self.trigger_var.set(DEFAULT_CONFIG["trigger_threshold"])
        self.camera_var.set(DEFAULT_CONFIG["camera_sensitivity"])
        self.touchpad_mouse_var.set(DEFAULT_CONFIG.get("touchpad_mouse", True))
        self.touchpad_sens_var.set(DEFAULT_CONFIG.get("touchpad_sensitivity", 1.2))
        self.rumble_var.set(DEFAULT_CONFIG.get("rumble_enabled", True))
        self.battery_led_var.set(DEFAULT_CONFIG.get("battery_led", True))


def main() -> None:
    app = SettingsApp()
    app.mainloop()


if __name__ == "__main__":
    main()
