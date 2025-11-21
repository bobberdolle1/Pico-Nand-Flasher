"""
Custom exception classes for Pico NAND Flasher
Provides specific exception types for different error conditions
"""


class NANDFlasherException(Exception):
    """Base exception class for Pico NAND Flasher"""
    pass


class HardwareException(NANDFlasherException):
    """Exception raised when hardware-related errors occur"""
    pass


class ConnectionException(HardwareException):
    """Exception raised when connection to Pico fails"""
    pass


class NANDDetectionException(HardwareException):
    """Exception raised when NAND chip detection fails"""
    pass


class OperationException(NANDFlasherException):
    """Exception raised when NAND operations fail"""
    pass


class ReadException(OperationException):
    """Exception raised when NAND read operation fails"""
    pass


class WriteException(OperationException):
    """Exception raised when NAND write operation fails"""
    pass


class EraseException(OperationException):
    """Exception raised when NAND erase operation fails"""
    pass


class DataIntegrityException(NANDFlasherException):
    """Exception raised when data integrity verification fails"""
    pass


class ConfigurationException(NANDFlasherException):
    """Exception raised when configuration errors occur"""
    pass


class FileException(NANDFlasherException):
    """Exception raised when file operations fail"""
    pass
