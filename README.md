# DualSense for Assassin’s Creed 1 & 2 (Linux)

**Language / Язык:** [Русский](#русская-версия) · [English](#english-version)

---

<a id="русская-версия"></a>

# 🎮 DualSense для Assassin’s Creed 1 & 2 (Linux)

Утилита для полноценной работы геймпада **PlayStation 5 (DualSense)** в **Assassin’s Creed 1** и **Assassin’s Creed 2** на Linux (Steam / Proton).

Она транслирует сигналы DualSense в виртуальный контроллер Xbox 360, чинит баги старых движков (неработающие LB, RB, триггеры LT/RT), устраняет дикую чувствительность камеры и добавляет виброотклик.

---

## ⚡ Быстрый старт за 2 минуты

### Шаг 1. Установи зависимости (один раз)
Открой терминал в этой папке и выполни:
```bash
pip install -r requirements.txt
chmod +x *.sh
```

### Шаг 2. Установи мод в игру (один раз)
Запусти автоматический установщик:
```bash
./install_eaglepatch.sh
```
*Скрипт автоматически найдет установленные **Assassin’s Creed 1** и/или **Assassin’s Creed 2**, скачает правильный EaglePatch + ASI Loader и настроит нативную поддержку геймпада.*

### Шаг 3. Настрой Steam (один раз)
1. В Steam: ПКМ по игре (**Assassin's Creed** / **Assassin's Creed 2**) → **Свойства** (*Properties*).
2. Во вкладке **Общие** (*General*) в поле **«Параметры запуска»** вставь:
   ```bash
   WINEDLLOVERRIDES="dinput8=n,b" %command%
   ```
3. Во вкладке **Контроллер** (*Controller*) выбери: **«Отключить систему ввода Steam»** (*Disable Steam Input*).

---

## 🚀 Как играть

1. **Подключи DualSense** по проводу или Bluetooth.
2. В терминале папки проекта запусти маппер:
   ```bash
   ./ac1-gamepad.sh
   ```
   *(В терминале появится `[ACTIVE] Connected & Active`, а подсветка на DualSense загорится цветом уровня заряда).*
3. **Запусти Assassin’s Creed в Steam и играй!**
4. Когда закончил играть — нажми `Ctrl + C` в терминале.

---

## ⚙️ Настройка чувствительности и кнопок (UI)

Если хочешь сделать камеру медленнее/быстрее, подкрутить мёртвые зоны или поменять кнопки:

Запусти компактную панель настроек:
```bash
./ac1-settings.sh
```
В ней доступны:
- **Camera Sensitivity** — плавный ползунок скорости обзора (по умолчанию комфортные 0.65x);
- **Stick Deadzone** — мёртвая зона стиков (на случай дрифта);
- **Trigger Threshold** — порог срабатывания курков;
- **Touchpad Speed** — скорость курсора мыши;
- Переключатели вибрации, подсветки и режима мыши.

Нажми **Save Settings** — изменения сохранятся в `config.json` и сразу применятся.

---

## 🕹️ Базовое управление (из коробки)

По умолчанию выставлена классическая консольная раскладка:

| Кнопка DualSense | Действие в игре |
| :--- | :--- |
| **Левый стик** | Передвижение |
| **Правый стик** | Обзор / Камера (плавная, без рывков) |
| **R1** | Стойка бега (High Profile) |
| **✕ (Крест)** | Ноги (зажать **R1 + ✕** = спринт и паркур) |
| **□ (Квадрат)** | Атака / Оружие |
| **○ (Круг)** | Взаимодействие / Толчок / Захват |
| **△ (Треугольник)** | Орлиное зрение (Eagle Vision) |
| **L1** | Захват цели (Lock-on) / Левый бампер |
| **L2** | Центрирование камеры / Сброс вида |
| **Create (Share)** | Карта |
| **Options** | Пауза / Меню |
| **Крестовина (D-Pad)** | Быстрый выбор оружия |
| **Тачпад** | Перемещение курсора мыши в меню (клик = ЛКМ) |

---

## ✨ Что умеет этот инструмент
- 🔄 **Авто-реконнект (Hotplug)**: геймпад можно отключать или усыплять во время игры — маппер сам восстановит связь.
- 🎯 **Исправление багов AC1 & AC2**: лечит неработающие LB, RB, LT в Assassin's Creed 2 и нормализует скорость камеры.
- 📳 **Вибрация (Force Feedback / Rumble)**: полная отдача в игре.
- 🔋 **Индикация заряда батареи**: подсветка DualSense меняет цвет в зависимости от батареи (зеленый > 75%, желтый 40–75%, оранжевый 15–40%, красный < 15%).
- 🖱️ **Тачпад как мышь**: трекпад для удобной навигации в игровых меню.

---

## ❓ Частые вопросы (FAQ)

**В Assassin's Creed 2 не работают LB, RB или LT:**  
Запусти `./install_eaglepatch.sh` — он установит `EaglePatchAC2` и настроит XInput. Обязательно проверь, что в параметрах запуска Steam прописано `WINEDLLOVERRIDES="dinput8=n,b" %command%`, а Steam Input выключен.

**Камера крутится слишком быстро или слишком медленно:**  
Запусти `./ac1-settings.sh` и настрой ползунок **Camera Sensitivity** под себя.

---
---

<a id="english-version"></a>

# 🎮 DualSense for Assassin’s Creed 1 & 2 (Linux)

A plug-and-play tool for using the **PlayStation 5 (DualSense)** controller in **Assassin’s Creed 1** and **Assassin’s Creed 2** on Linux (Steam / Proton).

It emulates an Xbox 360 controller via `uinput`, fixes classic engine bugs (unresponsive LB, RB, LT/RT triggers in AC2), solves camera over-sensitivity, and adds rumble feedback.

---

## ⚡ Quick Start in 2 Minutes

### Step 1. Install dependencies (once)
Open a terminal in this folder and run:
```bash
pip install -r requirements.txt
chmod +x *.sh
```

### Step 2. Install the game mod (once)
Run the automated installer:
```bash
./install_eaglepatch.sh
```
*Automatically detects **Assassin’s Creed 1** and/or **Assassin’s Creed 2**, downloads the appropriate EaglePatch + ASI Loader, and configures native controller support.*

### Step 3. Configure Steam (once)
1. In Steam: Right-click the game (**Assassin's Creed** / **Assassin's Creed 2**) → **Properties**.
2. Under **General**, set **Launch Options** to:
   ```bash
   WINEDLLOVERRIDES="dinput8=n,b" %command%
   ```
3. Under **Controller**, select: **Disable Steam Input**.

---

## 🚀 How to Play

1. **Connect your DualSense** (USB or Bluetooth).
2. In the terminal, run the mapper:
   ```bash
   ./ac1-gamepad.sh
   ```
   *(Terminal will show `[ACTIVE] Connected & Active`, and the lightbar will reflect the current battery level).*
3. **Launch the game from Steam and enjoy!**
4. When finished, press `Ctrl + C` in the terminal to stop.

---

## ⚙️ Settings & Sensitivity UI

To adjust camera speed, stick deadzones, or change buttons:
```bash
./ac1-settings.sh
```
Includes:
- **Camera Sensitivity** slider (smooth scaling, default 0.65x);
- **Stick Deadzone** (anti-drift calibration);
- **Trigger Threshold**;
- **Touchpad Speed**;
- Rumble, Battery LED, and Touchpad toggles.

Click **Save Settings** to write to `config.json`.

---

## 🕹️ Default Controls

Matched to the original console experience:

| DualSense Button | In-Game Action |
| :--- | :--- |
| **Left Stick** | Movement |
| **Right Stick** | Camera (smooth & controlled) |
| **R1** | High Profile stance |
| **✕ (Cross)** | Legs (Hold **R1 + ✕** to Sprint / Parkour) |
| **□ (Square)** | Attack / Weapon |
| **○ (Circle)** | Free Hand / Grab / Push |
| **△ (Triangle)** | Head / Eagle Vision |
| **L1** | Target Lock / Left Bumper |
| **L2** | Reset Camera |
| **Create** | Map |
| **Options** | Pause Menu |
| **D-Pad** | Weapon Selection |
| **Touchpad** | Virtual mouse cursor in menus (click = LMB) |

---

## ✨ Features
- 🔄 **Auto-Reconnect (Hotplug)**: Controller sleeps or disconnects? Reconnects automatically without restarting the game.
- 🎯 **AC1 & AC2 Fixes**: Resolves missing LB, RB, LT buttons in AC2 and tunes down camera sensitivity.
- 📳 **Full Rumble**: Complete force feedback vibration support.
- 🔋 **Battery RGB Lightbar**: Real-time battery indicator (Green > 75%, Yellow 40–75%, Orange 15–40%, Red < 15%).
- 🖱️ **Touchpad as Mouse**: Trackpad navigation in game menus.
