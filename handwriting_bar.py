#!/usr/bin/env python3
"""
Handwriting Bar - Wayland Stylus Handwriting to Text for Hyprland / Omarchy.
Uses GTK4 + Gtk4LayerShell, Cairo canvas, Google Digital Ink API + Tesseract offline fallback, and wtype.
"""

import os
import sys
import time
import json
import tempfile
import subprocess
import shutil
import urllib.request
import urllib.error

# Gtk4LayerShell requires being loaded before libwayland-client
if "libgtk4-layer-shell.so" not in os.environ.get("LD_PRELOAD", ""):
    layer_so = "/usr/lib/libgtk4-layer-shell.so"
    if os.path.exists(layer_so):
        env = os.environ.copy()
        cur = env.get("LD_PRELOAD", "")
        env["LD_PRELOAD"] = f"{layer_so}:{cur}" if cur else layer_so
        os.execvpe(sys.executable, [sys.executable] + sys.argv, env)

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Gdk', '4.0')
gi.require_version('Gtk4LayerShell', '1.0')

from gi.repository import Gtk, Gdk, GLib, Gtk4LayerShell
import cairo

CSS = """
window.handwriting-window {
    background-color: transparent;
}

.main-container {
    background-color: rgba(24, 24, 37, 0.96);
    border: 1.5px solid rgba(255, 255, 255, 0.15);
    border-radius: 18px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
    padding: 10px 14px;
}

.canvas-frame {
    background-color: rgba(17, 17, 27, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
}

.btn-action {
    background-color: rgba(49, 50, 68, 0.8);
    color: #cdd6f4;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 8px 12px;
    font-size: 14px;
    font-weight: bold;
    min-width: 48px;
}

.btn-action:hover {
    background-color: rgba(69, 71, 90, 0.9);
    color: #ffffff;
}

.btn-action:active {
    background-color: #89b4fa;
    color: #11111b;
}

.btn-send {
    background-color: #89b4fa;
    color: #11111b;
    border: none;
    font-size: 15px;
    font-weight: bold;
}

.btn-send:hover {
    background-color: #b4befe;
}

.btn-clear {
    background-color: rgba(243, 139, 168, 0.2);
    color: #f38ba8;
    border: 1px solid rgba(243, 139, 168, 0.3);
}

.btn-clear:hover {
    background-color: #f38ba8;
    color: #11111b;
}

.candidate-chip {
    background-color: rgba(49, 50, 68, 0.85);
    color: #cdd6f4;
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 8px;
    padding: 4px 10px;
    font-size: 13px;
    font-weight: 500;
}

.candidate-chip:hover {
    background-color: #89b4fa;
    color: #11111b;
}

.candidate-primary {
    background-color: rgba(137, 180, 250, 0.22);
    border-color: #89b4fa;
    color: #89b4fa;
    font-weight: bold;
}

.status-label {
    color: #a6adc8;
    font-size: 12px;
    font-style: italic;
    padding-left: 6px;
}
"""

class HandwritingBar(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        
        self.set_title("Handwriting Bar")
        self.add_css_class("handwriting-window")
        self.set_default_size(920, 240)
        
        # Configure Wayland Layer Shell
        Gtk4LayerShell.init_for_window(self)
        Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.TOP)
        Gtk4LayerShell.set_namespace(self, "handwriting-bar")
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.BOTTOM, True)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.LEFT, True)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.RIGHT, True)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.BOTTOM, 14)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.LEFT, 40)
        Gtk4LayerShell.set_margin(self, Gtk4LayerShell.Edge.RIGHT, 40)
        
        # Critical: DO NOT take keyboard focus so wtype inputs directly into active app!
        Gtk4LayerShell.set_keyboard_mode(self, Gtk4LayerShell.KeyboardMode.NONE)

        # Drawing state
        self.strokes = []             # List of strokes: [ [(x, y, t), ...], ... ]
        self.current_stroke = []      # Stroke currently being drawn
        self.stroke_start_time = 0
        self.auto_send_timer_id = None
        self.auto_send_delay = 1400   # ms after pen lift before auto-recognition
        self.last_sent_word = ""

        # Build UI
        self.build_ui()

    def build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        main_box.add_css_class("main-container")
        self.set_child(main_box)

        # Top Bar: Status + Candidate Suggestion Chips
        top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        self.status_lbl = Gtk.Label(label="Pisz odręcznie rysikiem lub dotykiem...", xalign=0.0)
        self.status_lbl.add_css_class("status-label")
        top_bar.append(self.status_lbl)

        # Candidates horizontal box for suggestion chips
        self.candidates_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        top_bar.append(self.candidates_box)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        top_bar.append(spacer)

        # Close button
        btn_close = Gtk.Button(label="✕ Schowaj")
        btn_close.add_css_class("btn-action")
        btn_close.connect("clicked", lambda _: self.close())
        top_bar.append(btn_close)

        main_box.append(top_bar)

        # Center Area: Canvas + Action Buttons
        center_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        center_box.set_vexpand(True)

        # Canvas Frame & DrawingArea
        canvas_frame = Gtk.Frame()
        canvas_frame.add_css_class("canvas-frame")
        canvas_frame.set_hexpand(True)
        canvas_frame.set_vexpand(True)

        self.canvas = Gtk.DrawingArea()
        self.canvas.set_hexpand(True)
        self.canvas.set_vexpand(True)
        self.canvas.set_draw_func(self.on_draw)
        canvas_frame.set_child(self.canvas)
        center_box.append(canvas_frame)

        # Setup Drawing Gestures
        self.setup_canvas_gestures()

        # Action Buttons Column
        btn_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        btn_col.set_valign(Gtk.Align.CENTER)

        btn_send = Gtk.Button(label="✓ Wyślij")
        btn_send.add_css_class("btn-action")
        btn_send.add_css_class("btn-send")
        btn_send.connect("clicked", lambda _: self.process_recognition_and_send())
        btn_col.append(btn_send)

        btn_space = Gtk.Button(label="␣ Spacja")
        btn_space.add_css_class("btn-action")
        btn_space.connect("clicked", lambda _: self.send_key("space"))
        btn_col.append(btn_space)

        btn_backspace = Gtk.Button(label="⌫ Cofnij")
        btn_backspace.add_css_class("btn-action")
        btn_backspace.connect("clicked", lambda _: self.send_key("BackSpace"))
        btn_col.append(btn_backspace)

        btn_enter = Gtk.Button(label="↵ Enter")
        btn_enter.add_css_class("btn-action")
        btn_enter.connect("clicked", lambda _: self.send_key("Return"))
        btn_col.append(btn_enter)

        btn_clear = Gtk.Button(label="✕ Wyczyść")
        btn_clear.add_css_class("btn-action")
        btn_clear.add_css_class("btn-clear")
        btn_clear.connect("clicked", lambda _: self.clear_canvas())
        btn_col.append(btn_clear)

        center_box.append(btn_col)
        main_box.append(center_box)

    def setup_canvas_gestures(self):
        # GestureDrag in GTK4 captures Stylus, Touch, and Mouse seamlessly
        self.drag = Gtk.GestureDrag()
        self.drag.connect("drag-begin", self.on_drag_begin)
        self.drag.connect("drag-update", self.on_drag_update)
        self.drag.connect("drag-end", self.on_drag_end)
        self.canvas.add_controller(self.drag)

    def on_drag_begin(self, gesture, start_x, start_y):
        self.cancel_auto_send()
        self.stroke_start_time = time.time() * 1000
        self.drag_start_x = start_x
        self.drag_start_y = start_y
        self.current_stroke = [(start_x, start_y, 0)]
        self.canvas.queue_draw()

    def on_drag_update(self, gesture, offset_x, offset_y):
        if self.current_stroke:
            px = self.drag_start_x + offset_x
            py = self.drag_start_y + offset_y
            last = self.current_stroke[-1]
            if abs(px - last[0]) >= 1.2 or abs(py - last[1]) >= 1.2:
                t = int(time.time() * 1000 - self.stroke_start_time)
                self.current_stroke.append((px, py, t))
                self.canvas.queue_draw()

    def on_drag_end(self, gesture, offset_x, offset_y):
        if self.current_stroke and len(self.current_stroke) >= 2:
            self.strokes.append(list(self.current_stroke))
        self.current_stroke = []
        self.canvas.queue_draw()
        if self.strokes:
            self.schedule_auto_send()

    # Drawing
    def on_draw(self, area, cr, width, height):
        # Draw background guidelines
        cr.set_source_rgba(1.0, 1.0, 1.0, 0.05)
        cr.set_line_width(1.0)
        
        y_center = height * 0.55
        cr.move_to(20, y_center)
        cr.line_to(width - 20, y_center)
        cr.stroke()

        cr.set_source_rgba(1.0, 1.0, 1.0, 0.02)
        y_top = height * 0.28
        cr.move_to(20, y_top)
        cr.line_to(width - 20, y_top)
        cr.stroke()

        # Render Ink Strokes
        cr.set_source_rgb(0.537, 0.706, 0.980)  # #89b4fa
        cr.set_line_width(4.5)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)

        for stroke in self.strokes:
            if not stroke:
                continue
            cr.move_to(stroke[0][0], stroke[0][1])
            for pt in stroke[1:]:
                cr.line_to(pt[0], pt[1])
            cr.stroke()

        # Render ongoing stroke
        if self.current_stroke:
            cr.move_to(self.current_stroke[0][0], self.current_stroke[0][1])
            for pt in self.current_stroke[1:]:
                cr.line_to(pt[0], pt[1])
            cr.stroke()

    # Auto-send Management
    def schedule_auto_send(self):
        self.cancel_auto_send()
        self.status_lbl.set_text("Rozpoznawanie...")
        self.auto_send_timer_id = GLib.timeout_add(self.auto_send_delay, self._on_auto_send_timeout)

    def cancel_auto_send(self):
        if self.auto_send_timer_id:
            GLib.source_remove(self.auto_send_timer_id)
            self.auto_send_timer_id = None
        self.status_lbl.set_text("Pisanie...")

    def _on_auto_send_timeout(self):
        self.auto_send_timer_id = None
        self.process_recognition_and_send()
        return False

    def clear_canvas(self):
        self.cancel_auto_send()
        self.strokes = []
        self.current_stroke = []
        self.canvas.queue_draw()
        self.clear_candidates()
        self.status_lbl.set_text("Płótno wyczyszczone.")

    def clear_candidates(self):
        child = self.candidates_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.candidates_box.remove(child)
            child = next_child

    def show_candidates(self, candidates):
        self.clear_candidates()
        for idx, word in enumerate(candidates):
            btn = Gtk.Button(label=word)
            btn.add_css_class("candidate-chip")
            if idx == 0:
                btn.add_css_class("candidate-primary")
            btn.connect("clicked", lambda _, w=word: self.select_candidate(w))
            self.candidates_box.append(btn)

    def select_candidate(self, word):
        # Backspace out previous word and replace with selected candidate
        if self.last_sent_word:
            backspaces = ["BackSpace"] * (len(self.last_sent_word) + 1)
            for _ in backspaces:
                subprocess.Popen(["wtype", "-k", "BackSpace"])
        subprocess.Popen(["wtype", word + " "])
        self.last_sent_word = word
        self.status_lbl.set_text(f"Zmieniono na: \"{word}\"")

    def send_key(self, key_name):
        try:
            if key_name == "space":
                subprocess.Popen(["wtype", " "])
                self.last_sent_word = ""
            else:
                subprocess.Popen(["wtype", "-k", key_name])
            self.status_lbl.set_text(f"Klawisz: {key_name}")
        except Exception as e:
            self.status_lbl.set_text(f"Błąd wtype: {e}")

    # Digital Ink Recognition Engine
    def recognize_google_ink(self, strokes, width, height):
        ink = []
        for s in strokes:
            if len(s) < 2:
                continue
            xs = [int(p[0]) for p in s]
            ys = [int(p[1]) for p in s]
            ts = [int(p[2]) if len(p) > 2 else idx * 20 for idx, p in enumerate(s)]
            ink.append([xs, ys, ts])

        if not ink:
            return []

        payload = {
            "app_version": 0.4,
            "api_level": "537.36",
            "device": "537.36",
            "input_type": "0",
            "options": "enable_pre_space",
            "requests": [{
                "writing_guide": {"writing_area_width": int(width), "writing_area_height": int(height)},
                "pre_context": "",
                "max_num_results": 6,
                "max_completions": 0,
                "language": "pl",
                "ink": ink
            }]
        }

        req = urllib.request.Request(
            "https://www.google.com/inputtools/request?ime=handwriting&app=mobilesearch&cs=1&oe=UTF-8",
            data=json.dumps(payload).encode('utf-8'),
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=3.5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data[0] == "SUCCESS" and len(data) > 1 and len(data[1]) > 0:
                results = data[1][0][1]
                return results
        return []

    # Local Tesseract Fallback
    def recognize_tesseract_fallback(self):
        all_points = [p for s in self.strokes for p in s]
        if len(all_points) < 4:
            return ""

        min_x = min(p[0] for p in all_points)
        max_x = max(p[0] for p in all_points)
        min_y = min(p[1] for p in all_points)
        max_y = max(p[1] for p in all_points)

        w = max(20.0, float(max_x - min_x))
        h = max(20.0, float(max_y - min_y))
        scale = max(1.0, min(3.0, 95.0 / h))
        pad_x, pad_y = 55, 45

        img_w = int(w * scale + pad_x * 2)
        img_h = int(h * scale + pad_y * 2)

        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, img_w, img_h)
        cr = cairo.Context(surface)
        cr.set_source_rgb(1.0, 1.0, 1.0)
        cr.paint()
        cr.set_source_rgb(0.0, 0.0, 0.0)
        cr.set_line_width(4.5)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.set_line_join(cairo.LINE_JOIN_ROUND)

        for stroke in self.strokes:
            cr.move_to(pad_x + (stroke[0][0] - min_x) * scale, pad_y + (stroke[0][1] - min_y) * scale)
            for pt in stroke[1:]:
                cr.line_to(pad_x + (pt[0] - min_x) * scale, pad_y + (pt[1] - min_y) * scale)
            cr.stroke()

        tmp_path = os.path.join(tempfile.gettempdir(), f"handwriting_{os.getpid()}.png")
        try:
            surface.write_to_png(tmp_path)
            shutil.copyfile(tmp_path, "/tmp/handwriting_last.png")

            for psm in ["7", "8", "6"]:
                cmd = ["tesseract", tmp_path, "stdout", "--psm", psm, "--oem", "1", "-c", "tessedit_char_blacklist=(|)[]{}~^\\_§"]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
                cand = proc.stdout.strip()
                if cand and (len(cand) >= 2 or cand.isalnum()):
                    return cand.replace("\n", " ").strip()
        except Exception:
            pass
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        return ""

    def process_recognition_and_send(self):
        self.cancel_auto_send()
        if not self.strokes:
            self.status_lbl.set_text("Brak tekstu.")
            return

        w = self.canvas.get_width() or 800
        h = self.canvas.get_height() or 220

        candidates = []
        try:
            # 1. Primary: High-accuracy Digital Ink Recognition
            candidates = self.recognize_google_ink(self.strokes, w, h)
        except Exception as e:
            # 2. Fallback: Offline Tesseract OCR
            pass

        if not candidates:
            offline_word = self.recognize_tesseract_fallback()
            if offline_word:
                candidates = [offline_word]

        if candidates:
            primary = candidates[0]
            self.last_sent_word = primary
            self.status_lbl.set_text(f"Wysłano: \"{primary}\"")
            self.show_candidates(candidates[:5])
            # Send word followed by space into active window
            subprocess.Popen(["wtype", primary + " "])
        else:
            self.status_lbl.set_text("Nie rozpoznano (spróbuj ponownie)")

        self.strokes = []
        self.canvas.queue_draw()


class HandwritingApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.omarchy.handwriting_bar")

    def do_startup(self):
        Gtk.Application.do_startup(self)
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS.encode('utf-8'))
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def do_activate(self):
        for win in self.get_windows():
            if win.is_visible():
                win.close()
                return
            else:
                win.present()
                return

        win = HandwritingBar(self)
        win.present()


def main():
    app = HandwritingApp()
    app.run(sys.argv)


if __name__ == "__main__":
    main()
