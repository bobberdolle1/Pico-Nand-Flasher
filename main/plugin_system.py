"""
Plugin System for Pico NAND Flasher
Implements a plugin architecture for supporting different NAND chip types
"""
import os
import sys
import importlib.util
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class NANDChipPlugin(ABC):
    """Base class for NAND chip plugins"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the NAND chip"""
        pass
    
    @property
    @abstractmethod
    def manufacturer(self) -> str:
        """Manufacturer of the NAND chip"""
        pass
    
    @property
    @abstractmethod
    def chip_id(self) -> List[int]:
        """Chip ID bytes for identification"""
        pass
    
    @property
    @abstractmethod
    def page_size(self) -> int:
        """Page size in bytes"""
        pass
    
    @property
    @abstractmethod
    def block_size(self) -> int:
        """Block size in pages"""
        pass
    
    @property
    @abstractmethod
    def total_blocks(self) -> int:
        """Total number of blocks"""
        pass
    
    @property
    def total_size(self) -> int:
        """Total size in bytes"""
        return self.page_size * self.block_size * self.total_blocks
    
    @property
    def spare_size(self) -> int:
        """Spare area size per page"""
        if self.page_size == 512:
            return 16
        elif self.page_size <= 2048:
            return 64
        else:
            return 128
    
    @property
    def address_cycles(self) -> int:
        """Number of address cycles needed"""
        # Calculate based on total size
        total_pages = self.block_size * self.total_blocks
        if total_pages <= 65536:  # 2^16
            return 4
        else:
            return 5
    
    @abstractmethod
    def get_timing_params(self) -> Dict[str, int]:
        """Get timing parameters for this chip"""
        pass
    
    def get_description(self) -> str:
        """Get a human-readable description of the chip"""
        size_mb = self.total_size / (1024 * 1024)
        return f"{self.manufacturer} {self.name} - {size_mb:.0f}MB ({self.page_size}B x {self.block_size} x {self.total_blocks})"


class PluginManager:
    """Manages NAND chip plugins"""
    
    def __init__(self):
        self.plugins = {}
        self._load_default_plugins()
    
    def _load_default_plugins(self):
        """Load built-in plugins"""
        # Add some default plugins as examples
        self.plugins["default_samsung_k9f4g08u0a"] = SamsungK9F4G08U0A()
        self.plugins["default_hynix_hy27uf082g2b"] = HynixHY27UF082G2B()
        self.plugins["default_toshiba_tc58nvg2s3e"] = ToshibaTC58NVG2S3E()
    
    def load_plugin_from_file(self, file_path: str) -> bool:
        """Load a plugin from a Python file"""
        try:
            spec = importlib.util.spec_from_file_location("plugin", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Look for classes that inherit from NANDChipPlugin
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, NANDChipPlugin) and 
                    attr != NANDChipPlugin):
                    plugin_instance = attr()
                    plugin_key = f"file_{os.path.basename(file_path)}_{plugin_instance.name.lower().replace(' ', '_')}"
                    self.plugins[plugin_key] = plugin_instance
                    return True
            
            return False
        except Exception as e:
            print(f"Error loading plugin from {file_path}: {e}")
            return False
    
    def load_plugins_from_directory(self, directory: str):
        """Load all plugins from a directory"""
        if not os.path.exists(directory):
            return
            
        for filename in os.listdir(directory):
            if filename.endswith('.py') and not filename.startswith('__'):
                file_path = os.path.join(directory, filename)
                self.load_plugin_from_file(file_path)
    
    def get_all_plugins(self) -> List[NANDChipPlugin]:
        """Get all loaded plugins"""
        return list(self.plugins.values())
    
    def find_plugin_by_id(self, chip_id: List[int]) -> Optional[NANDChipPlugin]:
        """Find a plugin that matches the given chip ID"""
        for plugin in self.plugins.values():
            if plugin.chip_id == chip_id[:len(plugin.chip_id)]:
                return plugin
        return None
    
    def get_plugin_by_name(self, name: str) -> Optional[NANDChipPlugin]:
        """Get a plugin by its name"""
        for plugin in self.plugins.values():
            if plugin.name.lower() == name.lower():
                return plugin
        return None


# Default implementations for common NAND chips

class SamsungK9F4G08U0A(NANDChipPlugin):
    """Samsung K9F4G08U0A - 512MB NAND Flash"""
    
    @property
    def name(self) -> str:
        return "K9F4G08U0A"
    
    @property
    def manufacturer(self) -> str:
        return "Samsung"
    
    @property
    def chip_id(self) -> List[int]:
        return [0xEC, 0xD3]  # Samsung K9F4G08U0A ID
    
    @property
    def page_size(self) -> int:
        return 2048
    
    @property
    def block_size(self) -> int:
        return 64  # 64 pages per block
    
    @property
    def total_blocks(self) -> int:
        return 4096  # 4096 blocks
    
    def get_timing_params(self) -> Dict[str, int]:
        return {
            "tWC": 25,   # Write cycle time (ns)
            "tRC": 25,   # Read cycle time (ns)
            "tREA": 15,  # Access time to read (ns)
            "tRP": 12,   # Read pulse width (ns)
            "tWP": 12,   # Write pulse width (ns)
            "tBERS": 3000,  # Block erase time (ms, typical)
            "tPROG": 700    # Page program time (µs, typical)
        }


class HynixHY27UF082G2B(NANDChipPlugin):
    """Hynix HY27UF082G2B - 256MB NAND Flash"""
    
    @property
    def name(self) -> str:
        return "HY27UF082G2B"
    
    @property
    def manufacturer(self) -> str:
        return "Hynix"
    
    @property
    def chip_id(self) -> List[int]:
        return [0xAD, 0xF1]  # Hynix HY27UF082G2B ID
    
    @property
    def page_size(self) -> int:
        return 2048
    
    @property
    def block_size(self) -> int:
        return 64  # 64 pages per block
    
    @property
    def total_blocks(self) -> int:
        return 2048  # 2048 blocks
    
    def get_timing_params(self) -> Dict[str, int]:
        return {
            "tWC": 30,   # Write cycle time (ns)
            "tRC": 30,   # Read cycle time (ns)
            "tREA": 20,  # Access time to read (ns)
            "tRP": 15,   # Read pulse width (ns)
            "tWP": 15,   # Write pulse width (ns)
            "tBERS": 2000,  # Block erase time (ms, typical)
            "tPROG": 600    # Page program time (µs, typical)
        }


class ToshibaTC58NVG2S3E(NANDChipPlugin):
    """Toshiba TC58NVG2S3E - 256MB NAND Flash"""
    
    @property
    def name(self) -> str:
        return "TC58NVG2S3E"
    
    @property
    def manufacturer(self) -> str:
        return "Toshiba"
    
    @property
    def chip_id(self) -> List[int]:
        return [0x98, 0xDA]  # Toshiba TC58NVG2S3E ID
    
    @property
    def page_size(self) -> int:
        return 2048
    
    @property
    def block_size(self) -> int:
        return 64  # 64 pages per block
    
    @property
    def total_blocks(self) -> int:
        return 2048  # 2048 blocks
    
    def get_timing_params(self) -> Dict[str, int]:
        return {
            "tWC": 20,   # Write cycle time (ns)
            "tRC": 20,   # Read cycle time (ns)
            "tREA": 12,  # Access time to read (ns)
            "tRP": 10,   # Read pulse width (ns)
            "tWP": 10,   # Write pulse width (ns)
            "tBERS": 2500,  # Block erase time (ms, typical)
            "tPROG": 500    # Page program time (µs, typical)
        }


# Example of how to create a custom plugin
class CustomNANDChip(NANDChipPlugin):
    """Example of a custom NAND chip plugin"""
    
    def __init__(self, name: str, manufacturer: str, chip_id: List[int], 
                 page_size: int, block_size: int, total_blocks: int):
        self._name = name
        self._manufacturer = manufacturer
        self._chip_id = chip_id
        self._page_size = page_size
        self._block_size = block_size
        self._total_blocks = total_blocks
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def manufacturer(self) -> str:
        return self._manufacturer
    
    @property
    def chip_id(self) -> List[int]:
        return self._chip_id
    
    @property
    def page_size(self) -> int:
        return self._page_size
    
    @property
    def block_size(self) -> int:
        return self._block_size
    
    @property
    def total_blocks(self) -> int:
        return self._total_blocks
    
    def get_timing_params(self) -> Dict[str, int]:
        # Default conservative timings
        return {
            "tWC": 30,
            "tRC": 30,
            "tREA": 20,
            "tRP": 15,
            "tWP": 15,
            "tBERS": 3000,
            "tPROG": 700
        }


def main():
    """Example usage of the plugin system"""
    print("=== NAND Flash Plugin System Demo ===\n")
    
    # Create plugin manager
    pm = PluginManager()
    
    # List all available plugins
    print("Available NAND chip plugins:")
    for i, plugin in enumerate(pm.get_all_plugins(), 1):
        print(f"  {i}. {plugin.get_description()}")
        print(f"     ID: {plugin.chip_id}")
        print(f"     Timing: {plugin.get_timing_params()}")
        print()
    
    # Test chip ID matching
    print("Testing chip ID matching:")
    test_ids = [
        [0xEC, 0xD3, 0x90, 0x95, 0x46],  # Samsung K9F4G08U0A
        [0xAD, 0xF1, 0x00, 0x1D, 0x7E],  # Hynix HY27UF082G2B
        [0x98, 0xDA, 0x10, 0x95, 0x56],  # Toshiba TC58NVG2S3E
        [0xFF, 0xFF, 0xFF, 0xFF, 0xFF],  # Unknown
    ]
    
    for chip_id in test_ids:
        plugin = pm.find_plugin_by_id(chip_id)
        if plugin:
            print(f"  ID {chip_id[:2]} -> {plugin.get_description()}")
        else:
            print(f"  ID {chip_id[:2]} -> Unknown chip")
    
    print("\n=== Plugin System Demo Complete ===")


if __name__ == "__main__":
    main()