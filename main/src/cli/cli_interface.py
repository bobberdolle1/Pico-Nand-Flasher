"""
CLI interface for Pico NAND Flasher
Provides command-line interface without GUI dependencies
"""
import argparse
import sys
from pathlib import Path
from typing import Optional

import serial.tools.list_ports

from ..hardware.nand_controller import NANDController
from ..utils.exceptions import (
    ConnectionException,
)
from ..utils.logging_config import get_logger, setup_logging


class CLIInterface:
    """Command-line interface for NAND operations"""

    def __init__(self):
        self.logger = get_logger()
        self.controller = NANDController()
        self.port = None

    def auto_detect_port(self) -> Optional[str]:
        """
        Automatically detect the Pico COM port
        
        Returns:
            Port name if found, None otherwise
        """
        self.logger.info("Auto-detecting Pico COM port...")

        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            # Look for Pico or common identifiers
            if ("Pico" in port.description or
                "Serial" in port.description or
                "UART" in port.description or
                "CDC" in port.description):
                self.logger.info(f"Pico detected on {port.device}")
                return port.device

        self.logger.warning("Pico not found automatically")
        return None

    def list_ports(self) -> None:
        """List available serial ports"""
        print("Available serial ports:")
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            print("  No ports available")
            return

        for i, port in enumerate(ports):
            print(f"  {i+1}. {port.device} - {port.description}")

    def connect_to_device(self, port: Optional[str] = None) -> bool:
        """
        Connect to the Pico device
        
        Args:
            port: Port to connect to. If None, auto-detect
            
        Returns:
            True if connection successful, False otherwise
        """
        if not port:
            port = self.auto_detect_port()
            if not port:
                print("❌ Pico not found! Please specify a port manually.")
                self.list_ports()
                return False

        try:
            if self.controller.connect(port):
                self.port = port
                return True
        except ConnectionException as e:
            self.logger.error(f"Connection failed: {e}")
            print(f"❌ Connection failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during connection: {e}")
            print(f"❌ Unexpected error: {e}")
            return False

        return False

    def detect_nand(self) -> bool:
        """Detect connected NAND chip"""
        detected, model, info = self.controller.detect_nand()
        if detected and model:
            print(f"✅ NAND detected: {model}")
            if info:
                print(f"   Page size: {info['page_size']} bytes")
                print(f"   Block size: {info['block_size']} pages")
                print(f"   Total blocks: {info['blocks']}")
                total_size = (info['blocks'] * info['block_size'] * info['page_size']) / (1024*1024)  # MB
                print(f"   Total size: ~{total_size:.2f} MB")
            return True
        else:
            print("❌ NAND not detected")
            return False

    def read_operation(self, output_file: str) -> bool:
        """
        Perform read operation
        
        Args:
            output_file: Path to save the dump
            
        Returns:
            True if successful, False otherwise
        """
        def progress_callback(progress: int):
            print(f"\rRead progress: {progress}%", end='', flush=True)

        print(f"Reading NAND to {output_file}...")
        data = self.controller.read_nand(progress_callback=progress_callback)

        if data:
            print(f"\nSaving {len(data)} bytes to {output_file}")
            try:
                with open(output_file, 'wb') as f:
                    f.write(data)
                print(f"✅ NAND read completed successfully. Data saved to {output_file}")
                return True
            except Exception as e:
                print(f"❌ Error saving file: {e}")
                return False
        else:
            print("❌ NAND read failed")
            return False

    def write_operation(self, input_file: str) -> bool:
        """
        Perform write operation
        
        Args:
            input_file: Path to file to write to NAND
            
        Returns:
            True if successful, False otherwise
        """
        if not Path(input_file).exists():
            print(f"❌ Input file does not exist: {input_file}")
            return False

        try:
            with open(input_file, 'rb') as f:
                data = f.read()
            print(f"Loaded {len(data)} bytes from {input_file}")
        except Exception as e:
            print(f"❌ Error reading input file: {e}")
            return False

        # Confirm write operation
        response = input("⚠️  This will overwrite NAND contents. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Write operation cancelled")
            return False

        def progress_callback(progress: int):
            print(f"\rWrite progress: {progress}%", end='', flush=True)

        print("Writing data to NAND...")
        success = self.controller.write_nand(data, progress_callback=progress_callback)

        if success:
            print("\n✅ NAND write completed successfully")
            return True
        else:
            print("\n❌ NAND write failed")
            return False

    def erase_operation(self) -> bool:
        """Perform erase operation"""
        # Confirm erase operation
        response = input("⚠️  This will erase all data on NAND. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Erase operation cancelled")
            return False

        def progress_callback(progress: int):
            print(f"\rErase progress: {progress}%", end='', flush=True)

        print("Erasing NAND...")
        success = self.controller.erase_nand(progress_callback=progress_callback)

        if success:
            print("\n✅ NAND erase completed successfully")
            return True
        else:
            print("\n❌ NAND erase failed")
            return False

    def run_cli(self, args):
        """Run CLI with parsed arguments"""
        # Setup logging based on verbosity
        log_level = 'DEBUG' if args.verbose else 'INFO'
        setup_logging(level=getattr(sys.modules['logging'], log_level))

        # Connect to device
        if not self.connect_to_device(args.port):
            return False

        # Detect NAND
        if not self.detect_nand():
            if not args.force:
                self.controller.disconnect()
                return False

        # Perform requested operation
        success = False
        if args.command == 'read':
            success = self.read_operation(args.output)
        elif args.command == 'write':
            success = self.write_operation(args.input)
        elif args.command == 'erase':
            success = self.erase_operation()
        elif args.command == 'info':
            success = True  # Just detection was already done

        # Disconnect
        self.controller.disconnect()
        return success


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description='Pico NAND Flasher - Command Line Interface')
    parser.add_argument('--port', type=str, help='Serial port to connect to (e.g., COM3, /dev/ttyUSB0)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--force', action='store_true', help='Force operation even if NAND not detected')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Read command
    read_parser = subparsers.add_parser('read', help='Read NAND content to file')
    read_parser.add_argument('output', type=str, help='Output file path')

    # Write command
    write_parser = subparsers.add_parser('write', help='Write file to NAND')
    write_parser.add_argument('input', type=str, help='Input file path')

    # Erase command
    erase_parser = subparsers.add_parser('erase', help='Erase NAND content')

    # Info command
    info_parser = subparsers.add_parser('info', help='Show NAND information')

    # List command
    list_parser = subparsers.add_parser('list', help='List available serial ports')

    args = parser.parse_args()

    if args.command == 'list':
        cli = CLIInterface()
        cli.list_ports()
        return

    if not args.command:
        parser.print_help()
        return

    cli = CLIInterface()
    success = cli.run_cli(args)

    if success:
        print("Operation completed successfully")
        sys.exit(0)
    else:
        print("Operation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
