"""
Pico NAND Flasher - Main entry point
Handles CLI and GUI mode selection
"""
import argparse
import sys

from .cli.cli_interface import main as cli_main
from .gui.gui_interface import main as gui_main


def main():
    """Main entry point that handles mode selection"""
    # Check if we're running in CLI mode
    if len(sys.argv) > 1:
        # If the first argument is not a GUI-specific flag, use CLI
        if sys.argv[1] in ['-h', '--help', 'read', 'write', 'erase', 'info', 'list']:
            cli_main()
            return
        elif sys.argv[1] in ['--cli', '--command-line']:
            cli_main()
            return

    # Default to GUI mode if no specific CLI arguments
    try:
        gui_main()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error running GUI: {e}")
        # Fallback to CLI mode
        cli_main()


if __name__ == "__main__":
    main()
