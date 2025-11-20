# Pico NAND Flasher

A Raspberry Pi Pico based NAND Flash programmer with multilingual support.

## Project Structure

```
reconstructed/
├── __init__.py          # Package initialization
├── i18n.py             # Internationalization module (Russian/English)
├── setup.py            # Package setup configuration
├── requirements.txt    # Python dependencies
├── LICENSE            # MIT License
├── README.md          # Project documentation
├── docs/              # Documentation files
│   ├── USAGE.md       # Usage instructions
│   └── DEVELOPMENT.md # Development guidelines
├── gui/               # GUI application code
│   └── GUI.py         # Main GUI application
└── pico/              # Raspberry Pi Pico code
    └── main.py        # Pico-side implementation
```

## Features

- Read, write, and erase NAND Flash memory
- Multilingual support (Russian and English)
- Cross-platform compatibility
- Professional packaging and distribution

## Installation

```bash
pip install -e .
```

## Usage

```bash
pico-nand-flasher
```

For detailed usage instructions, see [USAGE.md](reconstructed/docs/USAGE.md).

## Languages

The application supports both Russian and English languages with seamless switching capabilities. The i18n module provides a centralized translation system for all UI elements and messages.

## Development

For development guidelines, see [DEVELOPMENT.md](reconstructed/docs/DEVELOPMENT.md).