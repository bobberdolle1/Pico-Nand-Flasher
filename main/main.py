"""
Pico NAND Flasher - Main Entry Point
This file serves as the main entry point for the application
"""

import os
import sys

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src import main as app_main

if __name__ == "__main__":
    app_main()
