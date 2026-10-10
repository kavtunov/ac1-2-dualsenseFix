#!/usr/bin/env python3

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
        self.title("AC1 DualSense")
        self.minsize(480, 560)
        self.geometry("520x620")

        self.config_data = load_config()
        self.button_vars: dict[str, tk.StringVar] = {}
        self.label_to_code = {label: code for code, label in XBOX_ACTIONS}
        self.code_to_label = {code: label for code, label in XBOX_ACTIONS}
        self.deadzone_var = tk.DoubleVar(value=self.config_data["stick_deadzone"])
        self.trigger_var = tk.DoubleVar(value=self.config_data["trigger_threshold"])
        self.camera_var = tk.DoubleVar(value=self.config_data["camera_sensitivity"])
        self.touchpad_mouse_var = tk.BooleanVar(value=self.config_data.get("touchpad_mouse", True))
        self.touchpad_sens_var = tk.DoubleVar(value=self.config_data.get("touchpad_sensitivity", 1.2))
        self.rumble_var = tk.BooleanVar(value=self.config_data.get("rumble_enabled", True))
        self.battery_led_var = tk.BooleanVar(value=self.config_data.get("battery_led", True))

        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=16, pady=16)

        xbox_labels = [label for _code, label in XBOX_ACTIONS]

        for row, (key, dual_label) in enumerate(DUALSENSE_KEYS):
            ttk.Label(frame, text=dual_label).grid(row=row, column=0, sticky="w", pady=4)
            current = self.config_data["buttons"].get(key, "None")
            var = tk.StringVar(value=self.code_to_label.get(current, self.code_to_label["None"]))
            self.button_vars[key] = var
            combo = ttk.Combobox(
                frame,
                textvariable=var,
                values=xbox_labels,
                state="readonly",
                width=12,
            )
            combo.grid(row=row, column=1, sticky="ew", pady=4, padx=(12, 0))

        frame.columnconfigure(1, weight=1)

        sens = ttk.LabelFrame(self, text="Sensitivity")
        sens.pack(fill="x", padx=16, pady=(0, 12))

        self._add_scale(sens, "Deadzone", self.deadzone_var, 0.0, 0.6, 0)
        self._add_scale(sens, "Triggers", self.trigger_var, 0.0, 0.7, 1)
        self._add_scale(sens, "Camera", self.camera_var, 0.2, 2.5, 2)
        self._add_scale(sens, "Touchpad", self.touchpad_sens_var, 0.2, 3.0, 3)

        feat = ttk.LabelFrame(self, text="Features")
        feat.pack(fill="x", padx=16, pady=(0, 12))

        ttk.Checkbutton(feat, text="Enable Touchpad as Mouse", variable=self.touchpad_mouse_var).pack(
            anchor="w", padx=8, pady=4
        )
        ttk.Checkbutton(feat, text="Enable Rumble (Force Feedback)", variable=self.rumble_var).pack(
            anchor="w", padx=8, pady=4
        )
        ttk.Checkbutton(feat, text="DualSense Battery LED Indicator", variable=self.battery_led_var).pack(
            anchor="w", padx=8, pady=4
        )

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=16, pady=(0, 16))

        ttk.Button(buttons, text="Reset", command=self.reset_defaults).pack(side="left")
        ttk.Button(buttons, text="Save", command=self.save).pack(side="right")

    def _add_scale(
        self,
        parent: ttk.LabelFrame,
        title: str,
        variable: tk.DoubleVar,
        low: float,
        high: float,
        row: int,
    ) -> None:
        ttk.Label(parent, text=title).grid(row=row, column=0, sticky="w", padx=8, pady=6)
        value_label = ttk.Label(parent, text=f"{variable.get():.2f}")
        value_label.grid(row=row, column=2, sticky="e", padx=8)

        def on_change(_event: object | None = None) -> None:
            value_label.configure(text=f"{variable.get():.2f}")

        scale = ttk.Scale(
            parent,
            from_=low,
            to=high,
            variable=variable,
            command=lambda _v: on_change(),
        )
        scale.grid(row=row, column=1, sticky="ew", padx=8, pady=6)
        parent.columnconfigure(1, weight=1)

    def _collect(self) -> dict:
        buttons = {}
        for key, var in self.button_vars.items():
            buttons[key] = self.label_to_code[var.get()]
        return {
            "stick_deadzone": float(self.deadzone_var.get()),
            "trigger_threshold": float(self.trigger_var.get()),
            "camera_sensitivity": float(self.camera_var.get()),
            "touchpad_mouse": bool(self.touchpad_mouse_var.get()),
            "touchpad_sensitivity": float(self.touchpad_sens_var.get()),
            "rumble_enabled": bool(self.rumble_var.get()),
            "battery_led": bool(self.battery_led_var.get()),
            "buttons": buttons,
        }

    def save(self) -> None:
        save_config(self._collect())
        messagebox.showinfo("Saved", "OK")

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
