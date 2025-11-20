# Pico NAND Flasher - Reconstructed

This is a reconstructed and improved version of the NAND Flasher project for Raspberry Pi Pico using MicroPython. This tool allows you to use a Raspberry Pi Pico as a programmer (flasher) to read, write, and erase NAND Flash memory.

## Table of Contents
- [About](#about)
- [Features](#features)
- [Hardware Requirements](#hardware-requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Supported Chips](#supported-chips)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## About

This project consists of two main components:
- **Pico Code**: Runs on the Raspberry Pi Pico and handles direct communication with the NAND flash
- **GUI**: Runs on a computer and provides a user-friendly interface for operations

## Features

- Read NAND flash content (create dumps)
- Write dumps to NAND flash
- Erase NAND flash blocks
- Automatic chip detection
- Manual chip selection
- Progress tracking
- Multi-language support (Russian/English)
- Safety controls (pause, resume, cancel)

## Hardware Requirements

- **Raspberry Pi Pico** with MicroPython firmware
- **NAND Flash chip** (various models supported)
- **8x 10 kΩ resistors** for pull-up on data lines
- **Wires/breadboard** for connections

### Wiring Diagram

| NAND Pin | Pico GPIO | Function            |
| :------- | :-------- | :------------------ |
| VCC      | 3V3       | Power (3.3V)        |
| GND      | GND       | Ground              |
| I/O0     | GP5       | Data Line 0         |
| I/O1     | GP6       | Data Line 1         |
| I/O2     | GP7       | Data Line 2         |
| I/O3     | GP8       | Data Line 3         |
| I/O4     | GP9       | Data Line 4         |
| I/O5     | GP10      | Data Line 5         |
| I/O6     | GP11      | Data Line 6         |
| I/O7     | GP12      | Data Line 7         |
| CLE      | GP13      | Command Latch Enable|
| ALE      | GP14      | Address Latch Enable|
| CE#      | GP15      | Chip Enable         |
| RE#      | GP16      | Read Enable         |
| WE#      | GP17      | Write Enable        |
| R/B#     | GP18      | Ready/Busy          |
| WP#      | 3V3       | Write Protect (disable) |

**Important**: Install 10 kΩ pull-up resistors between each I/O line (I/O0-I/O7) and the Pico's 3V3 pin.

## Installation

### 1. Flash MicroPython to Pico
1. Download the latest [MicroPython for RP2040](https://micropython.org/download/rp2-pico/)
2. Hold down the **BOOTSEL** button on the Pico and plug it into your computer via USB
3. Copy the downloaded `.uf2` file to the appearing USB drive `RPI-RP2`

### 2. Upload Pico Code
1. Open `pico/main.py` in an editor (e.g., Thonny)
2. Connect to the Pico via Thonny
3. Save `main.py` to the Pico (File -> Save As -> MicroPython Device)

### 3. Install Computer Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the GUI
```bash
python gui/GUI.py
```

## Supported Chips

The project supports many popular NAND Flash chips including:
- Samsung: K9F1G08U0A, K9F2G08U0A, K9F4G08U0A, K9GAG08U0M, K9T1G08U0M, etc.
- Micron: MT29F4G08ABA, MT29F8G08ABACA, etc.
- Hynix: HY27US08281A, HY27UF082G2B, H27UBG8T2A, H27U4G8F2D, etc.
- Toshiba: TC58NVG2S3E, TC58NVG3S0F, etc.
- Intel, SanDisk and others

## Troubleshooting

- **"Connection Error"**: Check USB cable, ensure MicroPython firmware is installed
- **"NAND not detected"**: Verify wiring, check pull-up resistors, confirm 3.3V power
- **Incorrect data**: Ensure correct NAND model selection
- **Hangs**: Confirm WP# pin is connected to 3V3

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.