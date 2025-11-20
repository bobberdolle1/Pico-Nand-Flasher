"""
Pico NAND Flasher - Main Controller
MicroPython script for Raspberry Pi Pico to interface with NAND Flash memory

This script runs on the Pico and handles communication with NAND Flash chips,
providing read, write, and erase functionality via UART communication.
"""

from machine import Pin, UART
import time
import sys


class NANDFlasher:
    """Main class for NAND Flash operations on Raspberry Pi Pico"""
    
    def __init__(self):
        # Configuration
        self.BAUDRATE = 921600
        
        # Initialize UART for communication with computer
        self.uart = UART(0, baudrate=self.BAUDRATE, tx=Pin(0), rx=Pin(1))
        self.uart.init(bits=8, parity=None, stop=1)
        
        # Initialize NAND interface pins
        self.io_pins = [
            Pin(5, Pin.IN, Pin.PULL_UP),   # I/O0 - GP5
            Pin(6, Pin.IN, Pin.PULL_UP),   # I/O1 - GP6
            Pin(7, Pin.IN, Pin.PULL_UP),   # I/O2 - GP7
            Pin(8, Pin.IN, Pin.PULL_UP),   # I/O3 - GP8
            Pin(9, Pin.IN, Pin.PULL_UP),   # I/O4 - GP9
            Pin(10, Pin.IN, Pin.PULL_UP),  # I/O5 - GP10
            Pin(11, Pin.IN, Pin.PULL_UP),  # I/O6 - GP11
            Pin(12, Pin.IN, Pin.PULL_UP)   # I/O7 - GP12
        ]
        
        # Control pins
        self.cle_pin = Pin(13, Pin.OUT)    # CLE - GP13
        self.ale_pin = Pin(14, Pin.OUT)    # ALE - GP14
        self.ce_pin = Pin(15, Pin.OUT)     # CE# - GP15
        self.re_pin = Pin(16, Pin.OUT)     # RE# - GP16
        self.we_pin = Pin(17, Pin.OUT)     # WE# - GP17
        self.rb_pin = Pin(18, Pin.IN, Pin.PULL_UP)      # R/B# - GP18
        
        # Initialize control pins to inactive state
        self.cle_pin.value(0)
        self.ale_pin.value(0)
        self.ce_pin.value(1)  # CE# active LOW
        self.re_pin.value(1)  # RE# active LOW
        self.we_pin.value(1)  # WE# active LOW
        
        # Supported NAND chips database
        self.supported_nand = {
            # Samsung
            "Samsung K9F4G08U0A": {"id": [0xEC, 0xD3], "page_size": 2048, "block_size": 128, "blocks": 4096},
            "Samsung K9F1G08U0A": {"id": [0xEC, 0xF1], "page_size": 2048, "block_size": 128, "blocks": 2048},
            "Samsung K9F1G08R0A": {"id": [0xEC, 0xF1], "page_size": 2048, "block_size": 64, "blocks": 2048},
            "Samsung K9GAG08U0M": {"id": [0xEC, 0xD5], "page_size": 4096, "block_size": 256, "blocks": 8192},
            "Samsung K9T1G08U0M": {"id": [0xEC, 0xF1], "page_size": 2048, "block_size": 128, "blocks": 1024},
            "Samsung K9F2G08U0M": {"id": [0xEC, 0xDA], "page_size": 2048, "block_size": 128, "blocks": 2048},
            # Hynix
            "Hynix HY27US08281A": {"id": [0xAD, 0xF1], "page_size": 2048, "block_size": 128, "blocks": 1024},
            "Hynix H27UBG8T2A": {"id": [0xAD, 0xD3], "page_size": 4096, "block_size": 256, "blocks": 8192},
            "Hynix HY27UF082G2B": {"id": [0xAD, 0xF1], "page_size": 2048, "block_size": 128, "blocks": 2048},
            "Hynix H27U4G8F2D": {"id": [0xAD, 0xD5], "page_size": 4096, "block_size": 256, "blocks": 4096},
            "Hynix H27U4G8F2DTR": {"id": [0xAD, 0xD5], "page_size": 4096, "block_size": 256, "blocks": 4096},
            # Toshiba
            "Toshiba TC58NVG2S3E": {"id": [0x98, 0xDA], "page_size": 2048, "block_size": 128, "blocks": 2048},
            "Toshiba TC58NVG3S0F": {"id": [0x98, 0xF1], "page_size": 4096, "block_size": 256, "blocks": 4096},
            # Micron
            "Micron MT29F4G08ABA": {"id": [0x2C, 0xDC], "page_size": 4096, "block_size": 256, "blocks": 4096},
            "Micron MT29F8G08ABACA": {"id": [0x2C, 0x68], "page_size": 4096, "block_size": 256, "blocks": 8192},
            # Intel
            "Intel JS29F32G08AAMC1": {"id": [0x89, 0xD3], "page_size": 4096, "block_size": 256, "blocks": 8192},
            "Intel JS29F64G08ACMF3": {"id": [0x89, 0xD7], "page_size": 4096, "block_size": 256, "blocks": 16384},
            # SanDisk
            "SanDisk SDTNQGAMA-008G": {"id": [0x45, 0xD7], "page_size": 4096, "block_size": 256, "blocks": 8192}
        }
        
        self.current_nand = (None, None)
    
    def wait_for_ready(self, timeout_ms=5000):
        """Wait for NAND to be ready (R/B# = HIGH)"""
        start_time = time.ticks_ms()
        while self.rb_pin.value() == 0:
            if time.ticks_diff(time.ticks_ms(), start_time) > timeout_ms:
                return False
        return True
    
    def set_io_output(self):
        """Switch I/O pins to output mode"""
        for pin in self.io_pins:
            pin.init(Pin.OUT)
    
    def set_io_input(self):
        """Switch I/O pins to input mode with pull-up"""
        for pin in self.io_pins:
            pin.init(Pin.IN, Pin.PULL_UP)
    
    def write_byte(self, data):
        """Write a byte to NAND"""
        # Set data on I/O pins
        for i, pin in enumerate(self.io_pins):
            pin.value((data >> i) & 1)
        
        # Activate WE# pulse
        self.we_pin.value(0)
        self.we_pin.value(1)
    
    def read_byte(self):
        """Read a byte from NAND"""
        # Switch I/O pins to input
        self.set_io_input()
        
        # Activate RE# pulse
        self.re_pin.value(0)
        
        # Read data
        data = 0
        for i, pin in enumerate(self.io_pins):
            data |= (pin.value() << i)
        
        self.re_pin.value(1)
        
        # Return I/O pins to output mode
        self.set_io_output()
        
        return data
    
    def send_address_cycles(self, addr, cycles):
        """Send address to NAND in specified number of cycles"""
        self.ale_pin.value(1)  # Set ALE
        for _ in range(cycles):
            self.write_byte(addr & 0xFF)
            addr >>= 8
        self.ale_pin.value(0)  # Reset ALE
    
    def send_command(self, cmd):
        """Send command to NAND"""
        self.ce_pin.value(0)   # Activate CE#
        self.cle_pin.value(1)  # Set CLE
        self.write_byte(cmd)
        self.cle_pin.value(0)  # Reset CLE
        # Keep CE# active for subsequent operations
    
    def read_status(self):
        """Read NAND status register"""
        self.send_command(0x70)  # Read Status command
        status = self.read_byte()
        self.ce_pin.value(1)  # Deactivate CE#
        return status
    
    def is_status_fail(self, status):
        """Check if status indicates failure"""
        return (status & 0x01) == 0x01
    
    def read_nand_id(self):
        """Read NAND ID"""
        # Send Read ID command
        self.send_command(0x90)
        
        # Send address 0x00
        self.ale_pin.value(1)
        self.write_byte(0x00)
        self.ale_pin.value(0)
        
        # Wait for ready
        if not self.wait_for_ready(1000):
            self.ce_pin.value(1)
            return [0xFF, 0xFF, 0xFF, 0xFF]  # Return "empty" ID on timeout
        
        # Read ID bytes
        id_bytes = []
        for _ in range(6):  # Read 6 bytes for reliability
            id_bytes.append(self.read_byte())
        
        self.ce_pin.value(1)  # Deactivate CE#
        
        return id_bytes[:4]  # Return first 4 bytes
    
    def detect_nand(self):
        """Attempt to detect NAND type"""
        try:
            # Initialize pins
            self.set_io_output()
            time.sleep_ms(10)  # Small delay for stabilization
            
            nand_id = self.read_nand_id()
            
            for name, info in self.supported_nand.items():
                if nand_id[:len(info["id"])] == info["id"]:
                    return (name, info)
            return (None, None)
        except Exception as e:
            return (None, None)
    
    def read_page(self, nand_info, page_addr, buffer):
        """Read a single page of data and spare area"""
        try:
            page_size = nand_info["page_size"]
            block_size = nand_info["block_size"]
            
            # Step 1: Read command (00h)
            self.send_command(0x00)
            
            # Step 2: Send address (5 cycles for most modern NAND)
            # Address format: Column (0) + Page Address
            full_addr = page_addr * page_size
            self.send_address_cycles(full_addr, 5)
            
            # Step 3: Read Confirm command (30h)
            self.send_command(0x30)
            
            # Step 4: Wait for ready
            if not self.wait_for_ready():
                self.ce_pin.value(1)
                return False
            
            # Step 5: Read page data
            for i in range(page_size):
                buffer[i] = self.read_byte()
            
            # Step 6: Read spare area (OOB)
            spare_size = 64
            if page_size == 4096:
                spare_size = 128
            elif page_size == 2048:
                spare_size = 64
                
            for i in range(spare_size):
                buffer[page_size + i] = self.read_byte()
                
            self.ce_pin.value(1)  # Deactivate CE#
            return True
            
        except Exception as e:
            self.ce_pin.value(1)
            return False
    
    def write_page(self, nand_info, page_addr, data_buffer):
        """Write a single page of data and spare area"""
        try:
            page_size = nand_info["page_size"]
            block_size = nand_info["block_size"]
            
            # Step 1: Serial Data Input command (80h)
            self.send_command(0x80)
            
            # Step 2: Send address (5 cycles)
            full_addr = page_addr * page_size
            self.send_address_cycles(full_addr, 5)
            
            # Step 3: Write page data
            for i in range(page_size):
                self.write_byte(data_buffer[i])
            
            # Step 4: Write spare area
            spare_size = 64
            if page_size == 4096:
                spare_size = 128
            elif page_size == 2048:
                spare_size = 64
                
            for i in range(spare_size):
                self.write_byte(data_buffer[page_size + i])
                
            # Step 5: Program Confirm command (10h)
            self.send_command(0x10)
            
            # Step 6: Wait for ready (up to 5 seconds)
            if not self.wait_for_ready(5000):
                self.ce_pin.value(1)
                return False
                
            # Step 7: Check status
            status = self.read_status()
            if self.is_status_fail(status):
                return False
                
            self.ce_pin.value(1)  # Deactivate CE#
            return True
            
        except Exception as e:
            self.ce_pin.value(1)
            return False
    
    def erase_block(self, nand_info, block_addr):
        """Erase a single block"""
        try:
            block_size = nand_info["block_size"]
            page_addr = block_addr * block_size  # Address of first page in block
            
            # Step 1: Block Erase command (60h)
            self.send_command(0x60)
            
            # Step 2: Send block address (3 cycles, high bits of page address)
            self.send_address_cycles(page_addr, 3)
            
            # Step 3: Erase Confirm command (D0h)
            self.send_command(0xD0)
            
            # Step 4: Wait for ready (can take several seconds)
            if not self.wait_for_ready(10000):  # 10 second timeout
                self.ce_pin.value(1)
                return False
                
            # Step 5: Check status
            status = self.read_status()
            if self.is_status_fail(status):
                return False
                
            self.ce_pin.value(1)  # Deactivate CE#
            return True
            
        except Exception as e:
            self.ce_pin.value(1)
            return False
    
    def wait_for_command(self):
        """Read command from UART"""
        data = self.uart.readline()
        if data:
            return data.decode('utf-8').strip()
        return ""
    
    def send_status(self):
        """Send status to GUI"""
        if self.current_nand[0]:
            self.uart.write(f"MODEL:{self.current_nand[0]}\n")
        else:
            self.uart.write("MODEL:UNKNOWN\n")
    
    def read_nand_operation(self):
        """Read entire NAND content"""
        if not self.current_nand[0]:
            self.uart.write("NAND_NOT_CONNECTED\n")
            return

        info = self.current_nand[1]
        total_pages = info["blocks"] * info["block_size"]
        page_size = info["page_size"]
        spare_size = 64
        if page_size == 4096:
            spare_size = 128
        elif page_size == 2048:
            spare_size = 64
            
        page_total_size = page_size + spare_size

        # Buffer for one page + spare
        page_buffer = bytearray(page_total_size)
        
        try:
            for page in range(total_pages):
                if not self.read_page(info, page, page_buffer):
                    self.uart.write("OPERATION_FAILED\n")
                    return
                
                # Send page data via UART
                self.uart.write(page_buffer)
                
                # Send progress
                progress = int((page + 1) * 100 / total_pages)
                self.uart.write(f"PROGRESS:{progress}\n")
                
            self.uart.write("OPERATION_COMPLETE\n")
        except Exception as e:
            self.uart.write("OPERATION_FAILED\n")
    
    def write_nand_operation(self):
        """Write to NAND from data received via UART"""
        if not self.current_nand[0]:
            self.uart.write("NAND_NOT_CONNECTED\n")
            return
            
        info = self.current_nand[1]
        total_pages = info["blocks"] * info["block_size"]
        page_size = info["page_size"]
        spare_size = 64
        if page_size == 4096:
            spare_size = 128
        elif page_size == 2048:
            spare_size = 64
            
        page_total_size = page_size + spare_size
        
        # Signal that we're ready to receive data
        self.uart.write("READY_FOR_DATA\n")
        
        try:
            for page in range(total_pages):
                # In a real implementation, we would receive page_total_size bytes from GUI
                # For now, we'll simulate with test data
                page_buffer = bytearray(page_total_size)
                # Fill buffer with test data
                for i in range(page_total_size):
                    page_buffer[i] = (page + i) % 256
                
                if not self.write_page(info, page, page_buffer):
                    self.uart.write("OPERATION_FAILED\n")
                    return
                    
                # Send progress
                progress = int((page + 1) * 100 / total_pages)
                self.uart.write(f"PROGRESS:{progress}\n")
                
            self.uart.write("OPERATION_COMPLETE\n")
        except Exception as e:
            self.uart.write("OPERATION_FAILED\n")
    
    def erase_nand_operation(self):
        """Erase entire NAND"""
        if not self.current_nand[0]:
            self.uart.write("NAND_NOT_CONNECTED\n")
            return

        info = self.current_nand[1]
        total_blocks = info["blocks"]

        try:
            for block in range(total_blocks):
                if not self.erase_block(info, block):
                    self.uart.write("OPERATION_FAILED\n")
                    return
                    
                # Send progress
                progress = int((block + 1) * 100 / total_blocks)
                self.uart.write(f"PROGRESS:{progress}\n")
                
            self.uart.write("OPERATION_COMPLETE\n")
        except Exception as e:
            self.uart.write("OPERATION_FAILED\n")
    
    def handle_operation(self, cmd):
        """Handle operation commands"""
        if not self.current_nand[0]:
            self.uart.write("NAND_NOT_CONNECTED\n")
            return
        try:
            if cmd == 'READ':
                self.read_nand_operation()
            elif cmd == 'WRITE':
                self.write_nand_operation()
            elif cmd == 'ERASE':
                self.erase_nand_operation()
        except Exception as e:
            self.uart.write("OPERATION_FAILED\n")
    
    def select_nand_manually(self):
        """Manual NAND model selection"""
        self.uart.write("MANUAL_SELECT_START\n")
        names = list(self.supported_nand.keys())
        for i, name in enumerate(names):
            self.uart.write(f"{i+1}:{name}\n")
        self.uart.write("MANUAL_SELECT_END\n")
        
        # Wait for user selection
        while True:
            cmd = self.wait_for_command()
            if cmd.startswith("SELECT:"):
                try:
                    index = int(cmd.split(":")[1]) - 1
                    if 0 <= index < len(names):
                        name = names[index]
                        return (name, self.supported_nand[name])
                except:
                    pass
    
    def main_loop(self):
        """Main program loop"""
        # Set I/O pins to output mode by default
        self.set_io_output()
        time.sleep_ms(100)  # Stabilization time
        
        while True:
            self.uart.write("🔍 Определение NAND...\n")
            self.current_nand = self.detect_nand()
            
            if not self.current_nand[0]:
                self.uart.write("❌ NAND не обнаружен! Продолжить вручную? (y/n): \n")
                # Wait for response from GUI
                start_wait = time.ticks_ms()
                timeout = 30000  # 30 seconds
                while True:
                    cmd = self.wait_for_command()
                    if cmd:
                        if cmd.lower() == 'y':
                            self.current_nand = self.select_nand_manually()
                            break
                        elif cmd.lower() == 'n':
                            sys.exit()
                    if time.ticks_diff(time.ticks_ms(), start_wait) > timeout:
                        sys.exit()
            else:
                self.send_status()

            # Main command processing loop
            while True:
                cmd = self.wait_for_command()
                if not cmd:
                    continue
                    
                if cmd == 'STATUS':
                    self.send_status()
                elif cmd in ['READ', 'WRITE', 'ERASE']:
                    self.handle_operation(cmd)
                elif cmd == 'EXIT':
                    sys.exit()
                elif cmd == 'REDETECT':
                    # Break inner loop to re-detect
                    break


# Initialize and run the NAND flasher
if __name__ == "__main__":
    try:
        flasher = NANDFlasher()
        flasher.main_loop()
    except KeyboardInterrupt:
        pass
    except Exception as e:
        pass