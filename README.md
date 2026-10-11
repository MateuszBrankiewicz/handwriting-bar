# ✍️ Handwriting Bar

Nowoczesny, minimalistyczny panel pisma odręcznego (digital ink canvas) dla systemu Linux/Wayland (Hyprland / Omarchy / Sway), stworzony z myślą o laptopach 2-in-1, tabletach oraz użytkownikach rysików aktywnych (stylus) i ekranów dotykowych.

Pozwala pisać odręcznie rysikiem lub palcem u dołu ekranu i automatycznie wprowadza rozpoznany tekst w dowolne aktywne pole tekstowe (przeglądarka, terminal, edytor kodu, komunikator).

---

## ✨ Funkcje

* **Warstwa Wayland Layer Shell (`gtk4-layer-shell`):**
  * Pływający dolny panel dokowany do dołu ekranu.
  * **Brak kradzieży fokusu (`KeyboardMode.NONE`):** Możesz kliknąć w dowolne pole tekstowe (np. w Zen Browser czy Alacritty), a następnie pisać na panelu rysika – kursor tekstowy cały czas pozostaje w edytowanym oknie!
* **Ultra-precyzyjny silnik Digital Ink Recognition:**
  * Wektory pociągnięć ze znacznikami czasu przesyłane do silnika Digital Ink (tego samego co w Android/Gboard/ChromeOS).
  * Rozpoznaje kursywę (pismo łączone), pojedyncze litery, cyfry, działania matematyczne (`1+1`), znaki specjalne i polskie znaki diakrytyczne.
* **Kafelki z alternatywnymi podpowiedziami:**
  * Wyświetla alternatywne warianty rozpoznania. Dotknięcie kafelka rysikiem natychmiast podmienia słowo w edytowanym polu!
* **Tryb Offline (Tesseract Fallback):**
  * W razie braku połączenia sieciowego automatycznie przełącza się na lokalny silnik OCR (Tesseract).
* **Przyciski szybkiej kontroli:**
  * `✓ Wyślij` – natychmiastowe zatwierdzenie tekstu bez czekania na automatyczny timer.
  * `␣ Spacja` – dodanie spacji.
  * `⌫ Cofnij` – usunięcie ostatniego znaku (Backspace).
  * `↵ Enter` – zatwierdzenie/nowa linia.
  * `✕ Wyczyść` – wyczyszczenie płótna.
  * `✕ Schowaj` – schowanie panelu.

---

## 🚀 Wymagania

* **Python 3**
* **GTK4** (`python-gobject`)
* **gtk4-layer-shell**
* **wtype** (do emulacji klawiatury w Waylandzie)
* **tesseract** (jako silnik awaryjny offline)
* **cairo** (`python-cairo`)

Na Arch Linux / Omarchy:
```bash
sudo pacman -S python-gobject gtk4 gtk4-layer-shell wtype tesseract python-cairo
```

---

## 🛠️ Uruchomienie

W terminalu:
```bash
python3 handwriting_bar.py
# lub z parametrem:
./handwriting-bar.py toggle
```

### Integracja z Hyprland / Omarchy
Możesz przypisać skrót klawiszowy w `~/.config/hypr/bindings.lua`:
```lua
o.bind("SUPER + H", "Handwriting Bar", "handwriting-bar")
```
LUB dodać dotykową ikonę pióra (`󰏫`) bezpośrednio do paska zadań Omarchy (`omarchy-shell`).

---

## 📄 Licencja
Projekt udostępniany na licencji [MIT](LICENSE).
