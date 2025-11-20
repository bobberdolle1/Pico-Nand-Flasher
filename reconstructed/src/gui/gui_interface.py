"""
GUI interface for Pico NAND Flasher
Provides a graphical user interface for NAND operations
"""
import os
import sys
import time
import serial
import serial.tools.list_ports
from tkinter import Tk, filedialog, messagebox
import tkinter.ttk as ttk
import threading
from typing import Optional, Callable

from ..hardware.nand_controller import NANDController
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


class NANDFlasherGUI:
    """Main GUI class for NAND Flasher operations"""
    
    def __init__(self):
        self.logger = get_logger()
        self.controller = NANDController()
        
        # GUI elements
        self.root = Tk()
        self.root.title("Pico NAND Flasher")
        self.root.geometry("800x600")
        
        # Variables
        self.selected_dump_path = ""
        self.selected_operation = ""
        self.is_connected = False
        self.is_operation_running = False
        
        # Create GUI elements
        self.create_widgets()
        
        # Setup logging
        self.logger.info("GUI initialized")
    
    def create_widgets(self):
        """Create and layout GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Connection frame
        conn_frame = ttk.LabelFrame(main_frame, text="Connection", padding="5")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(conn_frame, text="Connect", command=self.connect).grid(row=0, column=0, padx=5)
        ttk.Button(conn_frame, text="Disconnect", command=self.disconnect).grid(row=0, column=1, padx=5)
        self.conn_status_label = ttk.Label(conn_frame, text="Disconnected")
        self.conn_status_label.grid(row=0, column=2, padx=10)
        
        # NAND info frame
        nand_frame = ttk.LabelFrame(main_frame, text="NAND Information", padding="5")
        nand_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.nand_info_label = ttk.Label(nand_frame, text="NAND: Not detected")
        self.nand_info_label.grid(row=0, column=0, sticky=tk.W)
        
        # File operations frame
        file_frame = ttk.LabelFrame(main_frame, text="File Operations", padding="5")
        file_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(file_frame, text="Select Dump File", command=self.select_dump).grid(row=0, column=0, padx=5)
        self.dump_label = ttk.Label(file_frame, text="No file selected")
        self.dump_label.grid(row=0, column=1, padx=5, sticky=tk.W)
        
        # Operations frame
        op_frame = ttk.LabelFrame(main_frame, text="Operations", padding="5")
        op_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(op_frame, text="Read NAND", command=self.read_nand).grid(row=0, column=0, padx=5, pady=2)
        ttk.Button(op_frame, text="Write NAND", command=self.write_nand).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(op_frame, text="Erase NAND", command=self.erase_nand).grid(row=0, column=2, padx=5, pady=2)
        
        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        self.progress_label = ttk.Label(progress_frame, text="Ready")
        self.progress_label.grid(row=0, column=1, padx=5)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
    
    def connect(self):
        """Connect to the Pico device"""
        self.logger.info("Attempting to connect to Pico...")
        
        # Try to auto-detect port
        ports = list(serial.tools.list_ports.comports())
        pico_port = None
        for port in ports:
            if ("Pico" in port.description or 
                "Serial" in port.description or 
                "UART" in port.description):
                pico_port = port.device
                break
        
        if not pico_port:
            # If auto-detect fails, ask user
            messagebox.showinfo("Connection", "Pico not found automatically. Please select port manually.")
            return
        
        try:
            if self.controller.connect(pico_port):
                self.is_connected = True
                self.conn_status_label.config(text=f"Connected to {pico_port}")
                self.status_label.config(text="Connected to Pico")
                
                # Try to detect NAND
                self.detect_nand()
            else:
                messagebox.showerror("Connection Error", f"Failed to connect to {pico_port}")
                self.conn_status_label.config(text="Connection failed")
        except ConnectionException as e:
            self.logger.error(f"Connection failed: {e}")
            messagebox.showerror("Connection Error", f"Failed to connect to {pico_port}: {e}")
            self.conn_status_label.config(text="Connection failed")
        except Exception as e:
            self.logger.error(f"Unexpected error during connection: {e}")
            messagebox.showerror("Connection Error", f"Unexpected error: {e}")
            self.conn_status_label.config(text="Connection error")
    
    def disconnect(self):
        """Disconnect from the Pico device"""
        if self.is_connected:
            self.controller.disconnect()
            self.is_connected = False
            self.conn_status_label.config(text="Disconnected")
            self.nand_info_label.config(text="NAND: Not detected")
            self.status_label.config(text="Disconnected")
            self.logger.info("Disconnected from Pico")
    
    def detect_nand(self):
        """Detect connected NAND chip"""
        if not self.is_connected:
            return
        
        detected, model, info = self.controller.detect_nand()
        if detected and model:
            info_text = f"NAND: {model}"
            if info:
                info_text += f" ({info['page_size']*info['block_size']*info['blocks']//(1024*1024)} MB)"
            self.nand_info_label.config(text=info_text)
            self.status_label.config(text=f"NAND detected: {model}")
            self.logger.info(f"NAND detected: {model}")
        else:
            self.nand_info_label.config(text="NAND: Not detected")
            self.status_label.config(text="NAND not detected")
    
    def select_dump(self):
        """Select a dump file"""
        file_path = filedialog.askopenfilename(
            title="Select NAND dump file",
            filetypes=[("Binary files", "*.bin"), ("All files", "*.*")]
        )
        
        if file_path:
            self.selected_dump_path = file_path
            self.dump_label.config(text=os.path.basename(file_path))
            self.logger.info(f"Selected dump file: {file_path}")
    
    def save_dump(self) -> Optional[str]:
        """Prompt to save dump file"""
        file_path = filedialog.asksaveasfilename(
            title="Save NAND dump as",
            defaultextension=".bin",
            filetypes=[("Binary files", "*.bin"), ("All files", "*.*")]
        )
        
        if file_path:
            self.selected_dump_path = file_path
            self.dump_label.config(text=os.path.basename(file_path))
            self.logger.info(f"Selected save location: {file_path}")
        
        return file_path
    
    def update_progress(self, value: int):
        """Update progress bar and label"""
        self.progress_var.set(value)
        self.progress_label.config(text=f"{value}%")
        self.root.update_idletasks()
    
    def set_operation_running(self, running: bool):
        """Set operation running state and update UI accordingly"""
        self.is_operation_running = running
        
        # Disable/enable buttons based on operation state
        for child in self.root.winfo_children():
            for widget in child.winfo_children():
                if isinstance(widget, ttk.Button):
                    if running:
                        if widget.cget('text') in ['Read NAND', 'Write NAND', 'Erase NAND']:
                            widget.config(state='disabled')
                    else:
                        if widget.cget('text') in ['Read NAND', 'Write NAND', 'Erase NAND']:
                            widget.config(state='normal')
    
    def read_nand(self):
        """Start NAND read operation"""
        if not self.is_connected:
            messagebox.showerror("Error", "Not connected to Pico")
            return
        
        if not self.controller.current_nand_info:
            messagebox.showwarning("Warning", "No NAND chip detected")
            return
        
        # Ask for save location
        save_path = self.save_dump()
        if not save_path:
            return
        
        # Confirm operation
        if not messagebox.askyesno("Confirm Read", "This will read the entire NAND content. Continue?"):
            return
        
        # Start operation in separate thread
        self.set_operation_running(True)
        self.status_label.config(text="Reading NAND...")
        
        def read_thread():
            try:
                data = self.controller.read_nand(progress_callback=self.update_progress)
                if data:
                    with open(save_path, 'wb') as f:
                        f.write(data)
                    self.status_label.config(text=f"Read completed: {len(data)} bytes saved")
                    messagebox.showinfo("Success", f"NAND read completed successfully. {len(data)} bytes saved to {save_path}")
                else:
                    self.status_label.config(text="Read operation failed")
                    messagebox.showerror("Error", "NAND read operation failed")
            except Exception as e:
                self.logger.error(f"Error during read operation: {e}")
                self.status_label.config(text=f"Read operation failed: {e}")
                messagebox.showerror("Error", f"Read operation failed: {e}")
            finally:
                self.set_operation_running(False)
                self.progress_var.set(0)
                self.progress_label.config(text="Ready")
        
        threading.Thread(target=read_thread, daemon=True).start()
    
    def write_nand(self):
        """Start NAND write operation"""
        if not self.is_connected:
            messagebox.showerror("Error", "Not connected to Pico")
            return
        
        if not self.controller.current_nand_info:
            messagebox.showwarning("Warning", "No NAND chip detected")
            return
        
        if not self.selected_dump_path or not os.path.exists(self.selected_dump_path):
            messagebox.showerror("Error", "Please select a valid dump file first")
            return
        
        # Confirm operation
        if not messagebox.askyesno("Confirm Write", f"This will write {self.selected_dump_path} to NAND and erase existing data. Continue?"):
            return
        
        # Start operation in separate thread
        self.set_operation_running(True)
        self.status_label.config(text="Writing to NAND...")
        
        def write_thread():
            try:
                with open(self.selected_dump_path, 'rb') as f:
                    data = f.read()
                
                success = self.controller.write_nand(data, progress_callback=self.update_progress)
                if success:
                    self.status_label.config(text="Write completed successfully")
                    messagebox.showinfo("Success", "NAND write completed successfully")
                else:
                    self.status_label.config(text="Write operation failed")
                    messagebox.showerror("Error", "NAND write operation failed")
            except Exception as e:
                self.logger.error(f"Error during write operation: {e}")
                self.status_label.config(text=f"Write operation failed: {e}")
                messagebox.showerror("Error", f"Write operation failed: {e}")
            finally:
                self.set_operation_running(False)
                self.progress_var.set(0)
                self.progress_label.config(text="Ready")
        
        threading.Thread(target=write_thread, daemon=True).start()
    
    def erase_nand(self):
        """Start NAND erase operation"""
        if not self.is_connected:
            messagebox.showerror("Error", "Not connected to Pico")
            return
        
        if not self.controller.current_nand_info:
            messagebox.showwarning("Warning", "No NAND chip detected")
            return
        
        # Confirm operation
        if not messagebox.askyesno("Confirm Erase", "This will erase ALL data on the NAND chip. Continue?"):
            return
        
        # Start operation in separate thread
        self.set_operation_running(True)
        self.status_label.config(text="Erasing NAND...")
        
        def erase_thread():
            try:
                success = self.controller.erase_nand(progress_callback=self.update_progress)
                if success:
                    self.status_label.config(text="Erase completed successfully")
                    messagebox.showinfo("Success", "NAND erase completed successfully")
                else:
                    self.status_label.config(text="Erase operation failed")
                    messagebox.showerror("Error", "NAND erase operation failed")
            except Exception as e:
                self.logger.error(f"Error during erase operation: {e}")
                self.status_label.config(text=f"Erase operation failed: {e}")
                messagebox.showerror("Error", f"Erase operation failed: {e}")
            finally:
                self.set_operation_running(False)
                self.progress_var.set(0)
                self.progress_label.config(text="Ready")
        
        threading.Thread(target=erase_thread, daemon=True).start()
    
    def run(self):
        """Start the GUI main loop"""
        self.logger.info("Starting GUI main loop")
        self.root.mainloop()


def main():
    """Main GUI entry point"""
    gui = NANDFlasherGUI()
    gui.run()


if __name__ == "__main__":
    main()