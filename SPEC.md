# Technical Specification: Handwriting Bar

## 1. Overview
Handwriting Bar is a modern, lightweight digital ink handwriting recognition panel for Linux / Wayland (Hyprland, Omarchy, Sway). It bridges the gap on Linux for 2-in-1 flip convertibles and tablet devices with stylus support, delivering an Apple Scribble / Windows Ink-style experience.
It enables freeform handwriting with an active or passive stylus, automatically transcribing strokes into text and injecting them directly into the currently focused input field of any application without focus-stealing issues.

---

## 2. Architecture & Tech Stack

### 2.1 UI Layer & Wayland Integration
* **Toolkit:** GTK4 via PyGObject (`gi.repository.Gtk`, `Gdk`).
* **Wayland Layer Shell:** `gtk4-layer-shell`.
  * **Anchoring:** Bottom screen edge (`Gtk4LayerShell.Edge.BOTTOM`).
  * **Layer:** `Layer.TOP` or `Layer.OVERLAY`.
  * **Focus Management:** `Gtk4LayerShell.KeyboardMode.NONE` — ensures drawing actions and UI interactions never steal keyboard focus from the target application (browser, terminal, editor).
* **Rendering Engine:** Cairo 2D vector graphics with antialiasing, round line caps (`LINE_CAP_ROUND`), and round line joins (`LINE_JOIN_ROUND`).
* **Input Gestures:** `Gtk.GestureDrag` tracking stroke coordinates `(x, y)` and millisecond timestamps `t`.

### 2.2 Recognition Pipeline
1. **Primary Engine (Digital Ink Recognition):**
   * Processes vector stroke trajectories `[[xs, ys, ts], ...]` with temporal data.
   * Recognizes cursive handwriting, print letters, numbers, math formulas, and accented characters with sub-100ms latency.
   * Generates candidate word completions for interactive correction chips.
2. **Offline Fallback Engine (Tesseract OCR):**
   * Activates seamlessly when offline.
   * Renders high-contrast rasterized black ink on white background with stroke height normalization (~90px) and padding.
   * Evaluates multiple page segmentation modes (`PSM 7`, `PSM 8`, `PSM 6`).

### 2.3 Text Injection
* **Protocol:** Wayland `virtual-keyboard-v1`.
* **Utility:** `wtype` simulating native keypress events into the compositor.

---

## 3. Definition of Done (DoD)
1. **Operational UI Component:**
   * Floating bottom panel anchored smoothly without interfering with status bars.
   * High-framerate drawing response to stylus and touch input with dark Omarchy aesthetic.
2. **Accurate Recognition:**
   * Accurately transcribes letters, numbers, and math formulas (e.g. `1+1`).
   * Provides real-time candidate suggestion chips for user correction.
3. **Seamless Input Injection:**
   * Text is inserted into the active focused window using `wtype` followed by an auto-space separator.
4. **Desktop Environment Integration:**
   * Single-instance toggle support (`./handwriting_bar.py toggle`).
   * Clean status bar widget integration and Hyprland keybinding support.

---

## 4. Acceptance Criteria (AC)
* **AC1:** Launching `handwriting-bar` presents a responsive bottom writing canvas without stealing active keyboard focus.
* **AC2:** Stylus strokes render continuous smooth lines without coordinate jitter or duplicate stroke artifacts.
* **AC3:** Upon pen lift pause (1.4s) or clicking `✓ Send`, the handwritten input is transcribed and typed directly into the active application.
* **AC4:** Control buttons (`Space`, `Backspace`, `Enter`, `Clear`, `Hide`) work immediately via touch/stylus.
* **AC5:** Clicking alternative candidate chips replaces the typed text with the selected candidate.
