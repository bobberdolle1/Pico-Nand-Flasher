# Pico NAND Flasher - Development Documentation

## Project Structure

```
reconstructed/
├── pico/           # MicroPython code for Raspberry Pi Pico
│   └── main.py     # Main controller for NAND operations
├── gui/            # Computer-side GUI application
│   └── GUI.py      # Main GUI interface
├── docs/           # Documentation files
│   ├── DEVELOPMENT.md   # This file
│   └── USAGE.md         # Usage instructions
├── tests/          # Test files (if any)
├── README.md       # Main project documentation
├── requirements.txt # Python dependencies
└── LICENSE         # License information
```

## Architecture Overview

### Pico Code (main.py)
The Pico code handles direct communication with the NAND Flash chip using GPIO pins. It implements the low-level NAND commands:

- Read ID: `0x90`
- Read: `0x00` + address + `0x30`
- Write: `0x80` + address + data + `0x10`
- Erase: `0x60` + address + `0xD0`
- Status read: `0x70`

### GUI Code (GUI.py)
The computer-side GUI provides a user-friendly interface that:
- Automatically detects the Pico via USB
- Communicates with the Pico via UART
- Provides NAND chip detection and manual selection
- Offers operations: Read, Write, Erase
- Includes progress tracking and operation controls

## Supported NAND Chips

The project supports many popular NAND Flash chips including:
- Samsung: K9F1G08U0A, K9F2G08U0A, K9F4G08U0A, K9GAG08U0M, K9T1G08U0M, etc.
- Micron: MT29F4G08ABA, MT29F8G08ABACA, etc.
- Hynix: HY27US08281A, HY27UF082G2B, H27UBG8T2A, H27U4G8F2D, etc.
- Toshiba: TC58NVG2S3E, TC58NVG3S0F, etc.
- Intel, SanDisk and others

## Key Features

### Pico Code
- Automatic chip detection using ID bytes
- Manual chip selection option
- Page-level read/write operations
- Block-level erase operations
- Status checking and error handling
- Progress reporting

### GUI
- Multi-language support (Russian/English)
- Auto-detection of Pico COM port
- Manual COM port selection
- Operation controls (pause, resume, cancel)
- Progress visualization
- File selection dialogs
- Safety confirmations for destructive operations

## Pin Mapping

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

## Communication Protocol

The GUI and Pico communicate via UART at 921600 baud rate. Commands and responses:

### Commands from GUI to Pico:
- `STATUS` - Get current NAND status and model
- `READ` - Start reading NAND content
- `WRITE` - Start writing to NAND
- `ERASE` - Start erasing NAND
- `EXIT` - Exit the Pico program
- `REDETECT` - Redetect NAND chip
- `SELECT:n` - Select chip model n (for manual selection)

### Responses from Pico to GUI:
- `MODEL:chip_name` - Current chip model
- `PROGRESS:n` - Operation progress (0-100%)
- `OPERATION_COMPLETE` - Operation finished successfully
- `OPERATION_FAILED` - Operation failed
- `NAND_NOT_CONNECTED` - No NAND detected
- `MANUAL_SELECT_START` - Start of manual selection list
- `n:chip_name` - Chip model n for manual selection
- `MANUAL_SELECT_END` - End of manual selection list

## Safety Considerations

1. Always ensure proper power supply (3.3V) before connecting the chip
2. Install 10kΩ pull-up resistors on all I/O lines
3. Use ESD protection when handling chips
4. Never hot-swap the NAND chip
5. Verify wiring before powering on
6. Use caution with write and erase operations as they permanently modify data

## Troubleshooting

### Common Issues:
- **NAND not detected**: Check wiring, verify pull-up resistors, ensure 3.3V power
- **Communication errors**: Verify baud rate, check USB connection
- **Data corruption**: Check signal integrity, verify proper pull-ups
- **Operation timeouts**: Reduce baud rate, check wiring quality

## Adding New NAND Support

To add support for a new NAND chip:
1. Find the chip's datasheet and note ID bytes, page size, block size, and total blocks
2. Add an entry to the `supported_nand` dictionary in `pico/main.py`
3. Format: `"Chip Name": {"id": [ID1, ID2], "page_size": size, "block_size": pages_per_block, "blocks": total_blocks}`

## Development Notes

The project uses object-oriented design in both the Pico and GUI code for better maintainability. The GUI code is structured as a class with separate methods for each functionality area, making it easier to maintain and extend.

The Pico code includes proper error handling and cleanup to prevent hanging operations and ensure reliable operation.