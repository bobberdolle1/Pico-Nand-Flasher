### Binary Protocol / Firmware Mismatch
1. Ensure you uploaded `main/pico/main_performance.py` to the Pico.
2. If the GUI cannot communicate, try setting `use_binary_protocol` to `False` in `settings.py` (legacy text mode).

# Pico NAND Flasher - Usage Guide

> Version 2.5 introduces a new framed binary UART protocol with CRC32 (enabled by default) and a resume feature for long operations.

## Getting Started

### Prerequisites
- Raspberry Pi Pico with MicroPython firmware
- NAND Flash chip
- 8x 10kΩ resistors for pull-up
- USB-C cable
- Computer with Python 3.6+

### Installation
1. Install MicroPython on your Raspberry Pi Pico
2. Connect your NAND Flash chip to the Pico according to the pin mapping
3. Install required Python packages: `pip install -r requirements.txt`
4. Upload the Pico firmware file to your device:
   - For v2.5 use: `main/pico/main_performance.py`
   - Open it in Thonny (or another MicroPython tool) and save to the Pico
5. Run the GUI via console entry point (recommended) or directly:
   - `pico-nand-flasher-gui`
   - or `python -m src.gui.gui_interface` from `main/`

## Hardware Setup

### Wiring Diagram
Connect your NAND Flash chip to the Raspberry Pi Pico as follows:

| NAND Pin | Pico GPIO | Function |
|----------|-----------|----------|
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
| WP#      | 3V3       | Write Protect (disable) |

### Important Notes
- Install 10kΩ pull-up resistors between each I/O line (I/O0-I/O7) and the Pico's 3V3 pin
- Ensure stable 3.3V power supply
- Never hot-swap the NAND chip while powered
- Use ESD protection when handling chips

## Using the GUI

### Main Menu
When you start the application, you'll see the main menu:
1. **📁 Операции с NAND** - Access NAND operations (Read, Write, Erase)
2. **📘 Инструкция** - View detailed connection instructions
3. **🌍 Сменить язык** - Switch between Russian and English
4. **🚪 Выход** - Exit the application

### NAND Operations Menu
This menu provides access to all NAND operations:
1. **📂 Выбрать дамп** - Select a dump file for write operations or save location for read operations
2. **🔧 Выбрать операцию** - Choose between Read, Write, or Erase
3. **✅ Подтвердить операцию** - Execute the selected operation
4. **🔙 Назад** - Return to main menu

### Operation Types

#### Read NAND
- Creates a binary dump of the entire NAND chip
- Select a save location for the dump file
- Operation preserves existing NAND data
- Progress is shown with a progress bar

#### Write NAND
- Writes a previously created dump to the NAND chip
- **Warning**: This operation permanently erases all data on the NAND chip
- Select the dump file to write
- Progress is shown with a progress bar
- Requires confirmation before proceeding

#### Erase NAND
- Performs a full chip erase, setting all bytes to 0xFF
- **Warning**: This operation permanently erases all data on the NAND chip
- Progress is shown with a progress bar
- Requires confirmation before proceeding

## v2.5 Binary Protocol

- The application now uses a framed binary UART protocol by default for robust communication:
  - Frame: `MAGIC (PF)` + `CMD (1 byte)` + `LEN (4 bytes, LE)` + `PAYLOAD` + `CRC32 (4 bytes, LE)`.
  - This improves reliability vs. plain text mode and enables streaming binary data safely.
- To switch off (for legacy Pico firmware), set `use_binary_protocol` to `False` in `main/src/config/settings.py`.

## Resume Feature

- Long operations (READ/WRITE/ERASE) can be resumed after interruption.
- The host side stores checkpoints in `resume.json` near `config.json` (e.g., `~/.pico_nand_flasher/resume.json`).
- Behavior:
  - READ: previously read pages are skipped on resume (in binary mode). Data appended from the next page.
  - WRITE: transmission continues from last confirmed byte; a CRC check of the last chunk ensures safety — if mismatch, restart from zero.
  - ERASE: progress is tracked and approximated by percentage; resume continues from the next blocks.
- The GUI will prompt whether to continue from resume or start over (which clears `resume.json`).

## Operation Controls

During operations, you can use keyboard controls:
- **P** - Pause the operation
- **R** - Resume the operation
- **C** - Cancel the operation

## Troubleshooting

### NAND Not Detected
1. Verify all connections according to the wiring diagram
2. Ensure 10kΩ pull-up resistors are installed on all I/O lines
3. Check that the NAND chip is properly powered (3.3V)
4. Try the manual selection option if automatic detection fails

### Communication Issues
1. Verify USB connection between Pico and computer
2. Check that MicroPython is properly installed on the Pico
3. Ensure no other applications are using the COM port
4. Try selecting the COM port manually if auto-detection fails

### Data Corruption
1. Check signal integrity and wiring quality
2. Verify proper pull-up resistors are installed
3. Try reducing the baud rate if communication errors occur
4. Ensure stable power supply

## Safety Guidelines

1. **Always power off** before connecting or disconnecting the NAND chip
2. Use **ESD protection** when handling chips
3. **Never hot-swap** the NAND chip while powered
4. Be **extremely careful** with write and erase operations as they permanently modify data
5. **Always backup** important data before performing operations
6. Verify **correct wiring** before powering on

## Supported NAND Chips

The application supports many popular NAND Flash chips including:
- Samsung: K9F1G08U0A, K9F2G08U0A, K9F4G08U0A, K9GAG08U0M, K9T1G08U0M, etc.
- Micron: MT29F4G08ABA, MT29F8G08ABACA, etc.
- Hynix: HY27US08281A, HY27UF082G2B, H27UBG8T2A, H27U4G8F2D, etc.
- Toshiba: TC58NVG2S3E, TC58NVG3S0F, etc.
- Intel, SanDisk and others

If your chip is not automatically detected, you can use the manual selection feature to choose from the supported models.