"""
Configuration management module for Pico NAND Flasher
Handles application settings, defaults, and configuration persistence.
"""
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class AppSettings:
    """Application settings dataclass"""
    # Connection settings
    default_baudrate: int = 921600
    connection_timeout: int = 10
    auto_detect_port: bool = True
    use_binary_protocol: bool = True  # Toggle for framed binary UART protocol (default on in v2.5)

    # Operation settings
    default_operation_timeout: int = 300  # 5 minutes
    chunk_size: int = 4096
    verify_after_write: bool = True
    include_oob: bool = False  # Include OOB (spare) area in dumps
    enable_ecc: bool = False   # Enable ECC verification/correction when possible
    ecc_scheme: str = "crc16"  # none|crc16|hamming_512_3byte (future)
    ecc_sector_size: int = 512
    ecc_bytes_per_sector: int = 2
    ecc_oob_offset: int = 0  # offset within OOB where ECC for first sector starts

    # UI settings
    default_language: str = "EN"
    show_progress_bar: bool = True
    enable_logging: bool = True
    log_level: str = "INFO"
    log_file_path: str = "logs/nand_flasher.log"

    # Hardware settings
    pullup_resistor_value: int = 10  # kOhm
    power_supply_voltage: float = 3.3  # Volts

    # File settings
    default_dump_extension: str = ".bin"
    max_recent_files: int = 10


class ConfigManager:
    """Configuration manager for handling persistent settings"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file. If None, uses default location
        """
        self.config_path = Path(config_path) if config_path else Path.home() / ".pico_nand_flasher" / "config.json"
        self.settings = AppSettings()
        self.load_config()

    def load_config(self) -> bool:
        """
        Load configuration from file
        
        Returns:
            True if configuration was loaded successfully, False otherwise
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, encoding='utf-8') as f:
                    config_data = json.load(f)

                # Update settings with loaded data
                for key, value in config_data.items():
                    if hasattr(self.settings, key):
                        setattr(self.settings, key, value)

                return True
            else:
                # Create default config if it doesn't exist
                self.save_config()
                return False
        except Exception as e:
            print(f"Warning: Could not load configuration: {e}")
            return False

    def save_config(self) -> bool:
        """
        Save current configuration to file
        
        Returns:
            True if configuration was saved successfully, False otherwise
        """
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.settings), f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            print(f"Warning: Could not save configuration: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        return getattr(self.settings, key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
        else:
            raise AttributeError(f"'{key}' is not a valid configuration setting")

    def reset_to_defaults(self) -> None:
        """Reset all settings to default values"""
        self.settings = AppSettings()
        self.save_config()


# Global configuration instance
config_manager = ConfigManager()
