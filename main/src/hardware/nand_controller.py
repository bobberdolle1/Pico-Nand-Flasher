"""
Hardware abstraction layer for NAND Flash operations
Provides a clean interface between the application logic and hardware communication
"""
import time
import serial
from typing import Optional, Tuple, Dict, List
from pathlib import Path
from ..utils.logging_config import get_logger
from ..config.settings import config_manager
from ..utils.exceptions import (
    ConnectionException, 
    NANDDetectionException, 
    ReadException, 
    WriteException, 
    EraseException,
    OperationException
)


class NANDController:
    """Hardware abstraction layer for NAND Flash operations"""
    
    def __init__(self):
        self.logger = get_logger()
        self.ser: Optional[serial.Serial] = None
        self.is_connected = False
        self.current_nand_info = None
        self.baudrate = config_manager.get('default_baudrate')
        self.timeout = config_manager.get('connection_timeout')
        
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
    
    def connect(self, port: str) -> bool:
        """
        Connect to the Pico device
        
        Args:
            port: Serial port to connect to
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.logger.info(f"Attempting to connect to {port} at {self.baudrate} baud")
            self.ser = serial.Serial(port, self.baudrate, timeout=self.timeout)
            self.ser.flush()
            
            # Small delay for stabilization
            time.sleep(2)
            # Clear input buffer in case of garbage data
            self.ser.reset_input_buffer()
            
            self.is_connected = True
            self.logger.info(f"Successfully connected to {port}")
            return True
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            self.is_connected = False
            raise ConnectionException(f"Failed to connect to {port}: {e}") from e
    
    def disconnect(self) -> None:
        """Disconnect from the Pico device"""
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b'EXIT\n')
            except:
                pass
            self.ser.close()
            self.is_connected = False
            self.logger.info("Disconnected from device")
    
    def send_command(self, command: str) -> None:
        """
        Send a command to the Pico device
        
        Args:
            command: Command string to send
        """
        if not self.is_connected or not self.ser:
            self.logger.error("Not connected to device")
            return
        
        try:
            command_bytes = f"{command}\n".encode('utf-8')
            self.ser.write(command_bytes)
            self.logger.debug(f"Sent command: {command}")
        except Exception as e:
            self.logger.error(f"Error sending command: {e}")
    
    def read_response(self, timeout: Optional[float] = None) -> Optional[str]:
        """
        Read a response from the Pico device
        
        Args:
            timeout: Optional timeout override
            
        Returns:
            Response string or None if timeout/error
        """
        if not self.is_connected or not self.ser:
            self.logger.error("Not connected to device")
            return None
        
        try:
            start_time = time.time()
            timeout = timeout or self.timeout
            
            while time.time() - start_time < timeout:
                if self.ser.in_waiting > 0:
                    response = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    self.logger.debug(f"Received response: {response}")
                    return response
                time.sleep(0.01)
            
            self.logger.warning("Timeout waiting for response")
            return None
        except Exception as e:
            self.logger.error(f"Error reading response: {e}")
            return None
    
    def detect_nand(self) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Detect connected NAND chip
        
        Returns:
            Tuple of (detected, model_name, nand_info)
        """
        self.logger.info("Detecting NAND chip...")
        
        if not self.is_connected:
            return False, None, None
        
        # Send STATUS command to check NAND status
        self.send_command("STATUS")
        
        response = self.read_response()
        if response and response.startswith("MODEL:"):
            model_name = response.split(":", 1)[1]
            nand_info = self.supported_nand.get(model_name)
            self.current_nand_info = nand_info
            self.logger.info(f"NAND detected: {model_name}")
            return True, model_name, nand_info
        
        self.logger.info("NAND not detected, manual selection may be required")
        return False, None, None
    
    def read_nand(self, progress_callback=None) -> Optional[bytes]:
        """
        Read data from NAND
        
        Args:
            progress_callback: Optional callback function for progress updates
            
        Returns:
            NAND data as bytes or None if failed
        """
        self.logger.info("Starting NAND read operation...")
        
        if not self.is_connected or not self.current_nand_info:
            self.logger.error("No connected NAND chip")
            return None
        
        self.send_command("READ")
        
        # Collect data and progress updates
        nand_data = bytearray()
        total_size = (self.current_nand_info["blocks"] * 
                     self.current_nand_info["block_size"] * 
                     self.current_nand_info["page_size"])
        
        self.logger.info(f"Reading {total_size} bytes from NAND")
        
        try:
            while True:
                response = self.read_response()
                if not response:
                    self.logger.error("No response from device")
                    return None
                
                if response.startswith("PROGRESS:"):
                    try:
                        progress = int(response.split(":")[1])
                        self.logger.debug(f"Read progress: {progress}%")
                        if progress_callback:
                            progress_callback(progress)
                    except ValueError:
                        pass
                elif response == "OPERATION_COMPLETE":
                    self.logger.info("NAND read completed successfully")
                    break
                elif response == "OPERATION_FAILED":
                    self.logger.error("NAND read operation failed")
                    return None
                elif response == "NAND_NOT_CONNECTED":
                    self.logger.error("NAND not connected")
                    return None
                else:
                    # This might be binary data
                    try:
                        # Add the response as binary data
                        nand_data.extend(response.encode('utf-8'))
                    except:
                        # If it's already binary, try to add it directly
                        nand_data.extend(response.encode('utf-8', errors='ignore'))
        
        except Exception as e:
            self.logger.error(f"Error during NAND read: {e}")
            return None
        
        return bytes(nand_data)
    
    def write_nand(self, data: bytes, progress_callback=None) -> bool:
        """
        Write data to NAND
        
        Args:
            data: Data to write
            progress_callback: Optional callback function for progress updates
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info(f"Starting NAND write operation with {len(data)} bytes...")
        
        if not self.is_connected or not self.current_nand_info:
            self.logger.error("No connected NAND chip")
            return False
        
        self.send_command("WRITE")
        
        # Wait for ready signal
        ready_response = self.read_response()
        if ready_response != "READY_FOR_DATA":
            self.logger.error(f"Device not ready for data: {ready_response}")
            return False
        
        # Send data in chunks
        chunk_size = config_manager.get('chunk_size')
        total_size = len(data)
        
        for i in range(0, total_size, chunk_size):
            chunk = data[i:i + chunk_size]
            try:
                self.ser.write(chunk)
            except Exception as e:
                self.logger.error(f"Error sending data chunk: {e}")
                return False
            
            # Calculate and report progress
            progress = int((i + len(chunk)) / total_size * 100)
            if progress_callback:
                progress_callback(progress)
        
        # Wait for completion
        while True:
            response = self.read_response()
            if not response:
                self.logger.error("No response from device")
                return False
            
            if response.startswith("PROGRESS:"):
                try:
                    progress = int(response.split(":")[1])
                    self.logger.debug(f"Write progress: {progress}%")
                    if progress_callback:
                        progress_callback(progress)
                except ValueError:
                    pass
            elif response == "OPERATION_COMPLETE":
                self.logger.info("NAND write completed successfully")
                return True
            elif response == "OPERATION_FAILED":
                self.logger.error("NAND write operation failed")
                return False
            elif response == "NAND_NOT_CONNECTED":
                self.logger.error("NAND not connected")
                return False
    
    def erase_nand(self, progress_callback=None) -> bool:
        """
        Erase NAND chip
        
        Args:
            progress_callback: Optional callback function for progress updates
            
        Returns:
            True if successful, False otherwise
        """
        self.logger.info("Starting NAND erase operation...")
        
        if not self.is_connected or not self.current_nand_info:
            self.logger.error("No connected NAND chip")
            return False
        
        self.send_command("ERASE")
        
        try:
            while True:
                response = self.read_response()
                if not response:
                    self.logger.error("No response from device")
                    return False
                
                if response.startswith("PROGRESS:"):
                    try:
                        progress = int(response.split(":")[1])
                        self.logger.debug(f"Erase progress: {progress}%")
                        if progress_callback:
                            progress_callback(progress)
                    except ValueError:
                        pass
                elif response == "OPERATION_COMPLETE":
                    self.logger.info("NAND erase completed successfully")
                    return True
                elif response == "OPERATION_FAILED":
                    self.logger.error("NAND erase operation failed")
                    return False
                elif response == "NAND_NOT_CONNECTED":
                    self.logger.error("NAND not connected")
                    return False
        except Exception as e:
            self.logger.error(f"Error during NAND erase: {e}")
            return False