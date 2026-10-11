# ✍️ Handwriting Bar

A modern, lightweight digital ink handwriting recognition panel for Linux / Wayland (Hyprland, Omarchy, Sway, GNOME). Built specifically for 2-in-1 convertible laptops, tablets, and stylus users who want an Apple Scribble / Windows Ink experience on Linux.

Write naturally with a stylus or finger on the floating bottom canvas, and watch your handwritten words and math formulas automatically type directly into your active input field (browser, code editor, terminal, messenger) without stealing window focus.

---

## ✨ Features

* **Wayland Layer Shell (`gtk4-layer-shell`):**
  * Anchored floating panel at the bottom of the screen.
  * **Zero Focus Stealing (`KeyboardMode.NONE`):** You can tap any text field in an application (e.g. Zen Browser, VS Code, or Alacritty) and draw on the handwriting canvas—your active cursor remains focused inside the destination text field!
* **High-Accuracy Digital Ink Recognition:**
  * Uses stroke trajectory vectors with timestamps (the same engine powering Android, Gboard, and ChromeOS handwriting).
  * Seamlessly recognizes cursive handwriting, print letters, numbers, math expressions (`1+1`), punctuation, and multi-language diacritics (including Polish, German, French, etc.).
* **Interactive Candidate Suggestions:**
  * Displays alternative recognition candidates as touchable chips above the canvas. Tapping an alternative candidate instantly replaces the typed word!
* **Offline Fallback Engine (Tesseract OCR):**
  * In case of no internet connectivity, the system automatically falls back to local Tesseract OCR.
* **Control Actions:**
  * `✓ Send` — Instantly process and inject handwritten text.
  * `␣ Space` — Insert space.
  * `⌫ Backspace` — Delete last character.
  * `↵ Enter` — Confirm / newline.
  * `✕ Clear` — Clear drawing canvas.
  * `✕ Hide` — Minimize panel.

---

## 📦 Requirements

* **Python 3.10+**
* **GTK4** (`python-gobject`)
* **gtk4-layer-shell**
* **wtype** (for Wayland virtual keyboard text injection)
* **tesseract** (for offline fallback)
* **cairo** (`python-cairo`)

### Arch Linux / Omarchy
```bash
sudo pacman -S python-gobject gtk4 gtk4-layer-shell wtype tesseract python-cairo
```

### Fedora
```bash
sudo dnf install python3-gobject gtk4 gtk4-layer-shell wtype tesseract python3-cairo
```

### Ubuntu / Debian (24.04+)
```bash
sudo apt install python3-gi gir1.2-gtk-4.0 libgtk4-layer-shell0 wtype tesseract-ocr python3-cairo
```

---

## 🚀 Usage

Launch the handwriting bar directly:
```bash
python3 handwriting_bar.py
```

Toggle show/hide:
```bash
./handwriting_bar.py toggle
```

### Hyprland Integration
Bind a key combination in your `~/.config/hypr/bindings.lua` or `hyprland.conf`:
```lua
o.bind("SUPER + H", "Handwriting Bar", "handwriting-bar")
```

### Omarchy Top Bar Integration
Add a stylus touch icon (`󰏫`) to your status bar so you can summon or dismiss the handwriting canvas with a single stylus tap in tablet mode.

---

## 🧩 Architecture

```
Stylus / Touch Event
       │
       ▼
Gtk.GestureDrag (GTK4 DrawingArea)
       │
       ├──► Vector Strokes [(x, y, timestamp), ...]
       │         │
       │         ├──► Online: Google Digital Ink API (Primary, ~60ms)
       │         └──► Offline: Cairo Normalization + Tesseract OCR (Fallback)
       │
       ▼
Recognized Text + Suggestion Chips
       │
       ▼
wtype (Wayland virtual-keyboard protocol)
       │
       ▼
Active Window Text Input (Browser, Terminal, Editor)
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
