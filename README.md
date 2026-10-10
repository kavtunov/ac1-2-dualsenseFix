# DualSense for Assassin’s Creed 1 (Linux)

**Language / Язык:** [Русский](#русская-версия) · [English](#english-version)

---

<a id="русская-версия"></a>

# 🎮 DualSense для Assassin’s Creed 1 (Linux)

Утилита для нормальной работы геймпада **PlayStation 5 (DualSense)** в игре **Assassin’s Creed 1** на Linux (через Steam / Proton).

Она транслирует сигналы DualSense в виртуальный контроллер Xbox 360, добавляет виброотклик, авто-реконнект и выставляет правильную раскладку кнопок, которую понимает старая игра.

---

## ⚡ Быстрый старт за 2 минуты

### Шаг 1. Установи зависимости (один раз)
Открой терминал в этой папке и выполни:
```bash
pip install -r requirements.txt
chmod +x *.sh
```

### Шаг 2. Установи мод в игру (один раз)
Запусти автоматический установщик EaglePatch:
```bash
./install_eaglepatch.sh
```
*Скрипт сам найдёт Assassin's Creed в библиотеке Steam, скачает и распакует файлы мода и включит поддержку геймпада.*

### Шаг 3. Настрой Steam (один раз)
1. В Steam: ПКМ по **Assassin's Creed** → **Свойства** (*Properties*).
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
   *(Терминал напишет `[ACTIVE] Connected & Active`, а подсветка на DualSense загорится цветом уровня заряда).*
3. **Запусти Assassin’s Creed в Steam и играй!**
4. Когда закончил играть — нажми `Ctrl + C` в терминале.

---

## 🕹️ Базовое управление (из коробки)

По умолчанию уже выставлена оригинальная консольная раскладка AC1:

| Кнопка DualSense | Действие в игре |
| :--- | :--- |
| **Левый стик** | Передвижение |
| **Правый стик** | Обзор / Камера |
| **R1** | Стойка бега (High Profile) |
| **✕ (Крест)** | Ноги (зажать **R1 + ✕** = спринт и паркур) |
| **□ (Квадрат)** | Атака / Оружие |
| **○ (Круг)** | Взаимодействие / Толчок / Захват |
| **△ (Треугольник)** | Орлиное зрение (Eagle Vision) |
| **L1** | Захват цели (Lock-on) |
| **L2** | Центрирование камеры |
| **Create (Share)** | Карта |
| **Options** | Пауза / Меню |
| **Крестовина (D-Pad)** | Быстрый выбор оружия |
| **Тачпад** | Перемещение курсора мыши в меню (клик = ЛКМ) |

> 💡 **Хочешь поменять кнопки под себя?**  
> Запусти `./ac1-settings.sh` — откроется простое окно настроек чувствительности и кнопок.

---

## ✨ Что умеет этот инструмент
- 🔄 **Авто-реконнект (Hotplug)**: геймпад можно отключать, переподключать по проводу/Bluetooth прямо во время игры — связь восстановится сама.
- 📳 **Вибрация (Force Feedback / Rumble)**: эффекты ударов и синхронизации передаются на моторы DualSense.
- 🔋 **Индикация заряда батареи**: светодиодная полоса DualSense меняет цвет в зависимости от процента заряда (зеленый > 75%, желтый 40–75%, оранжевый 15–40%, красный < 15%).
- 🖱️ **Тачпад как мышь**: сенсорная панель работает как трекпад для удобного кликанья в меню игры.

---

## ❓ Частые вопросы (FAQ)

**Игра не видит геймпад:**  
1. Убедись, что выполнил `./install_eaglepatch.sh` и прописал параметры запуска в Steam.
2. Проверь, отключен ли Steam Input в свойствах игры.
3. Запускай `./ac1-gamepad.sh` **до** запуска игры.

**Двойные нажатия кнопок:**  
Отключи сторонние эмуляторы (AntiMicroX, SC-Controller) и обязательно выключи Steam Input.

---
---

<a id="english-version"></a>

# 🎮 DualSense for Assassin’s Creed 1 (Linux)

A plug-and-play tool for using the **PlayStation 5 (DualSense)** controller in **Assassin’s Creed 1** on Linux (Steam / Proton).

It emulates a native Xbox 360 controller via `uinput`, adds rumble, auto-reconnect, and configures the classic console layout out of the box.

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
*Automatically finds Assassin's Creed in Steam, downloads EaglePatch + ASI Loader, and configures XInput support.*

### Step 3. Configure Steam (once)
1. In Steam: Right-click **Assassin's Creed** → **Properties**.
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
3. **Launch Assassin’s Creed from Steam and enjoy!**
4. When finished, press `Ctrl + C` in the terminal to stop.

---

## 🕹️ Default Controls

Configured to match the original console layout:

| DualSense Button | In-Game Action |
| :--- | :--- |
| **Left Stick** | Movement |
| **Right Stick** | Camera |
| **R1** | High Profile stance |
| **✕ (Cross)** | Legs (Hold **R1 + ✕** to Sprint / Parkour) |
| **□ (Square)** | Attack / Weapon |
| **○ (Circle)** | Free Hand / Grab / Push |
| **△ (Triangle)** | Head / Eagle Vision |
| **L1** | Target Lock |
| **L2** | Reset Camera |
| **Create** | Map |
| **Options** | Pause Menu |
| **D-Pad** | Weapon Selection |
| **Touchpad** | Virtual mouse cursor in menus (click = LMB) |

> 💡 **Want to customize bindings or deadzones?**  
> Run `./ac1-settings.sh` anytime.

---

## ✨ Features
- 🔄 **Auto-Reconnect (Hotplug)**: Controller sleeps or disconnects? Pick it up again without restarting the game or terminal.
- 📳 **Full Rumble (Force Feedback)**: Complete vibration feedback support.
- 🔋 **Battery RGB Lightbar**: Real-time battery indicator (Green > 75%, Yellow 40–75%, Orange 15–40%, Red < 15%).
- 🖱️ **Touchpad as Mouse**: Use the touchpad as a trackpad for menu navigation.
