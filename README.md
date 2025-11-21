# 🚀 Pico NAND Flasher — Professional NAND Flash Programmer for Raspberry Pi Pico

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Raspberry Pi Pico](https://img.shields.io/badge/Raspberry%20Pi-Pico-orange)](https://www.raspberrypi.org/)

Turn your Raspberry Pi Pico into a powerful, cross‑platform NAND Flash programmer with a modern, user‑friendly GUI.

## Highlights

- ✅ Protocol‑level PAUSE / RESUME / CANCEL (GUI ↔ Pico)
- ✅ Real WRITE on Pico with page+spare streaming over UART
- ✅ Modern PyQt6 GUI with toolbar, RU/EN localization, theme switch (System/Light/Dark)
- ✅ Dump Analyzer: Hex view, OOB overlay, bad‑block scan, ECC verify, diff, Markdown report
- ✅ Cross‑platform builds (Windows / macOS / Linux) via GitHub Actions

## Hardware at a Glance

- Raspberry Pi Pico (MicroPython firmware)
- NAND flash chip (Samsung / Micron / Hynix / Toshiba / Intel / …)
- 8 × 10 kΩ pull‑ups (I/O0–I/O7 → 3V3), wiring jumpers

### Wiring

| NAND Pin | Pico GPIO | Purpose |
|:---------|:----------|:--------|
| VCC      | 3V3       | Power (3.3V) |
| GND      | GND       | Ground |
| I/O0     | GP5       | Data 0 |
| I/O1     | GP6       | Data 1 |
| I/O2     | GP7       | Data 2 |
| I/O3     | GP8       | Data 3 |
| I/O4     | GP9       | Data 4 |
| I/O5     | GP10      | Data 5 |
| I/O6     | GP11      | Data 6 |
| I/O7     | GP12      | Data 7 |
| CLE      | GP13      | Command Latch Enable |
| ALE      | GP14      | Address Latch Enable |
| CE#      | GP15      | Chip Enable |
| RE#      | GP16      | Read Enable |
| WE#      | GP17      | Write Enable |
| R/B#     | GP18      | Ready / Busy |
| WP#      | 3V3       | Write Protect (disabled) |

Pro tip: add 10 kΩ pull‑ups between I/O0–I/O7 and 3V3.

## Quick Start

1) Flash MicroPython to Pico
```bash
# Download latest MicroPython for RP2040 from micropython.org
# Hold BOOTSEL, plug USB, copy .uf2 to RPI-RP2 drive
```

2) Upload Pico firmware (v2.5)
```bash
# Use Thonny → File → Save to MicroPython
main/pico/main.py
```

3) Install desktop dependencies
```bash
pip install -r main/requirements.txt
```

4) Launch the GUI
```bash
python main/gui/main_app.py
```

The launcher starts the Modern GUI and the Dump Analyzer.

## Using the GUI

- Language: Settings → RU/EN
- Theme: Settings → System / Light / Dark (applies instantly)
- Write OOB (spare): enabled by default; toggle in Settings
- Toolbar: quick actions for Refresh / Connect / Disconnect / Read / Write / Erase / About
- After a successful READ you can open the dump in the Analyzer with one click

## Releases (Prebuilt Binaries)

- Tagged pushes `v*` produce artifacts for Windows, macOS and Linux (GitHub Actions)
- Download the latest release and run the launcher executable

## Notes on WRITE

- Default mode streams page + spare (OOB). You can disable OOB in Settings.
- The GUI streams data after Pico reports `READY_FOR_DATA`.
- Progress and power warnings are shown in the GUI.

## Troubleshooting

- "Connection Error": check USB cable and MicroPython
- "NAND not detected": verify wiring, pull‑ups, 3.3V supply
- Corrupted data: ensure correct NAND model selection
- Hangs: ensure WP# is tied to 3V3

## License

MIT — use it, modify it, share it. 🎉