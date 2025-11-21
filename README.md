# 🔥 Pico NAND Flasher - The Ultimate NAND Flash Programmer 🔥

> Transform your Raspberry Pi Pico into a powerful NAND Flash programming beast! 🚀

[![Awesome](https://cdn.rawgit.com/sindresorhus/awesome/d7305f38d29fed78fa85652e3a63e154dd8e8829/media/badge.svg)](https://github.com/sindresorhus/awesome)
[![Python](https://img.shields.io/badge/Python-3.7%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](https://opensource.org/licenses/MIT)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-Pico-orange)](https://www.raspberrypi.org/)

## 🌟 What Makes This Project Insanely Cool?

This isn't just another NAND flasher - it's a **revolutionary tool** that turns your humble Raspberry Pi Pico into a professional-grade NAND Flash programmer! With cutting-edge features like PIO acceleration, data compression, and integrity verification, you'll have the power of expensive commercial programmers in your pocket.

## ⚡ Key Features That'll Blow Your Mind

- 📡 **Lightning-Fast Operations**: Leveraging Pico's PIO (Programmable I/O) and DMA for maximum performance
- 🗜️ **Smart Compression**: RLE (Run-Length Encoding) dramatically reduces data transfer times
- 🔒 **Military-Grade Integrity**: CRC32 checksums ensure data accuracy
- 🛡️ **Safety-First Design**: Pause, resume, and cancel operations with confidence
- 🌍 **Bilingual Interface**: Seamless Russian/English switching
- 🧩 **Plugin Architecture**: Extend functionality with custom NAND chip support
- 📊 **Advanced Analytics**: Built-in dump analysis tools with hex view and search
- ⚡ **Power Monitoring**: VSYS voltage monitoring prevents corruption during operations
- 🔄 **Smart Skipping**: Automatically bypass blank pages for faster operations
- 🛠️ **Operation Resumption**: Pick up where you left off after interruptions

## 🛠️ Hardware Requirements (Dead Simple!)

- **Raspberry Pi Pico** with MicroPython firmware
- **Your NAND Flash chip** (supports Samsung, Micron, Hynix, Toshiba, Intel & more!)
- **8x 10kΩ resistors** (pull-ups for data lines)
- **Some wires** and a breadboard

### 🔧 Wiring Made Stupid Simple

| NAND Pin | Pico GPIO | Purpose |
|:---------|:----------|:--------|
| VCC      | 3V3       | Power (3.3V) |
| GND      | GND       | Ground |
| I/O0     | GP5       | Data Line 0 |
| I/O1     | GP6       | Data Line 1 |
| I/O2     | GP7       | Data Line 2 |
| I/O3     | GP8       | Data Line 3 |
| I/O4     | GP9       | Data Line 4 |
| I/O5     | GP10      | Data Line 5 |
| I/O6     | GP11      | Data Line 6 |
| I/O7     | GP12      | Data Line 7 |
| CLE      | GP13      | Command Latch Enable |
| ALE      | GP14      | Address Latch Enable |
| CE#      | GP15      | Chip Enable |
| RE#      | GP16      | Read Enable |
| WE#      | GP17      | Write Enable |
| R/B#     | GP18      | Ready/Busy |
| WP#      | 3V3       | Write Protect (disabled) |

**💡 Pro Tip**: Install 10kΩ pull-up resistors between each I/O line (I/O0-I/O7) and 3V3!

## 🚀 Getting Started - Zero to Hero!

### 1. Flash MicroPython to Your Pico
```bash
# Download latest MicroPython for RP2040 from micropython.org
# Hold BOOTSEL, plug in USB, copy .uf2 file to RPI-RP2 drive
```

### 2. Upload Pico Code
```bash
# Open main.py in Thonny or your favorite editor
# Connect to Pico and upload main.py to device
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the Beast!
```bash
python gui/GUI.py
```

## 🧰 Supported NAND Chips (The Collection!)

This beast supports tons of popular chips:
- **Samsung**: K9F1G08U0A, K9F2G08U0A, K9F4G08U0A, K9GAG08U0M, K9T1G08U0M, and more!
- **Micron**: MT29F4G08ABA, MT29F8G08ABACA, etc.
- **Hynix**: HY27US08281A, HY27UF082G2B, H27UBG8T2A, H27U4G8F2D, etc.
- **Toshiba**: TC58NVG2S3E, TC58NVG3S0F, etc.
- **Intel, SanDisk** and many others!

## 🛡️ Troubleshooting (When Things Get Tricky)

- **"Connection Error"**: Check USB cable and MicroPython firmware
- **"NAND not detected"**: Verify wiring, check pull-up resistors, confirm 3.3V power
- **Corrupted data**: Ensure correct NAND model selection
- **System hangs**: Confirm WP# pin is connected to 3V3

## 📄 License

MIT License - Use it, modify it, share it! 🎉