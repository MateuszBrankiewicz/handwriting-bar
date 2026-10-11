# Handwriting Bar (Tablet Stylus Handwriting to Text)

## 1. Overview
Handwriting Bar to lekki, nowoczesny panel pisma odręcznego (canvas) dla systemu Linux/Wayland (Hyprland / Omarchy), przeznaczony dla laptopów 2-in-1 i tabletów z rysikiem aktywnym/pasywnym.
Umożliwia pisanie odręczne rysikiem na ekranie w trybie tableta i automatyczne wprowadzanie rozpoznanego tekstu do aktywnego pola tekstowego w dowolnej aplikacji (przeglądarka, edytor, komunikator, terminal).

## 2. Architecture & Tech Stack
- **Warstwa UI / Canvas:** Python (GTK4 / PyGObject z Cairo Canvas lub Quickshell Layer-Shell).
  - Płynne śledzenie pociągnięć rysika (stylus events, nacisk / pressure).
  - Pływający dolny panel lub dokowana warstwa Wayland u dołu ekranu.
  - Przyciski funkcyjne: Spacja, Backspace, Enter, Czyść (Clear), Ukryj (Hide).
- **Silnik rozpoznawania (OCR Engine):**
  - Tesseract OCR (`--psm 7` / `--psm 8`, silnik LSTM) dla trybu offline / zero-dependency.
  - Możliwość rozszerzenia o lekki model ONNX / TrOCR dla jeszcze wyższej dokładności pisma odręcznego.
- **Wstrzykiwanie tekstu (Text Injection):**
  - `wtype` (Wayland virtual-keyboard protocol) – natychmiastowe wpisanie tekstu w aktywne pole tekstowe.

## 3. Definition of Done (DoD)
1. **Działający komponent UI:**
   - Panel wyświetla się u dołu ekranu bez kolizji z górnym paskiem Omarchy.
   - Posiada płynne pole do rysowania rysikiem (i palcem) o odpowiedniej czułości i estetycznym wyglądzie (ciemny motyw spójny z Omarchy).
2. **Rozpoznawanie tekstu:**
   - Po napisaniu słowa/zdania i pauzie w rysowaniu (lub kliknięciu przycisku 'Zatwierdź' / spacja), pismo ręczne jest poprawnie przetwarzane na tekst.
3. **Wstrzykiwanie do aplikacji:**
   - Rozpoznany tekst jest wprowadzany do aktywnego okna przez `wtype`.
4. **Integracja z systemem:**
   - Skrót klawiszowy lub integracja z panelem tableta (`omarchy-tablet-mode`).
   - Brak blokad czy błędów pamięci.

## 4. Acceptance Criteria (AC)
- **AC1:** Użytkownik może uruchomić `handwriting-bar` i na ekranie pojawia się estetyczny pasek do pisania.
- **AC2:** Pociągnięcia rysikiem po obszarze rysowania natychmiast rysują gładkie linie (ink strokes).
- **AC3:** Po narysowaniu słowa (np. "test") i naciśnięciu wyślij / po opóźnieniu (debounce), tekst zostaje wysłany do aplikacji z fokusem.
- **AC4:** Dostępne są przyciski szybkiej edycji: [Spacja], [Cofnij / Backspace], [Enter], [Wyczyść], [Zamknij].
