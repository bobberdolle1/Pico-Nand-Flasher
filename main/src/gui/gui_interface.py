"""
GUI interface for Pico NAND Flasher
Provides a graphical user interface for NAND operations
"""

import os
import threading
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import Tk, filedialog, messagebox

import serial
import serial.tools.list_ports

from ..config.settings import config_manager
from ..hardware.nand_controller import NANDController
from ..utils.exceptions import (
    ConnectionException,
)
from ..utils.i18n import i18n
from ..utils.logging_config import get_logger


class NANDFlasherGUI:
    """Main GUI class for NAND Flasher operations"""

    def __init__(self):
        self.logger = get_logger()
        self.controller = NANDController()

        # GUI elements
        self.root = Tk()
        # Set language from config (defaults to English)
        try:
            lang = (config_manager.get("default_language") or "EN").lower()
            if lang in ("en", "ru"):
                i18n.set_language(lang)
        except Exception:
            pass

        title = "Pico NAND Flasher"
        if i18n:
            title = i18n.t("title") or title
        self.root.title(title)
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
        # Menu bar
        menubar = tk.Menu(self.root)
        settings_menu = tk.Menu(menubar, tearoff=0)
        # Language submenu
        lang_menu = tk.Menu(settings_menu, tearoff=0)
        lang_menu.add_command(label=i18n.t("english"), command=lambda: self._set_language("en"))
        lang_menu.add_command(label=i18n.t("russian"), command=lambda: self._set_language("ru"))
        settings_menu.add_cascade(label=i18n.t("language"), menu=lang_menu)
        # Binary protocol toggle
        self.binary_var = tk.BooleanVar(value=bool(config_manager.get("use_binary_protocol", True)))

        def _toggle_protocol():
            try:
                config_manager.set("use_binary_protocol", bool(self.binary_var.get()))
                config_manager.save_config()
                messagebox.showinfo(i18n.t("settings"), i18n.t("protocol_change_notice"))
            except Exception:
                pass

        settings_menu.add_checkbutton(
            label=i18n.t("binary_protocol"),
            onvalue=True,
            offvalue=False,
            variable=self.binary_var,
            command=_toggle_protocol,
        )

        # Include OOB toggle
        self.oob_var = tk.BooleanVar(value=bool(config_manager.get("include_oob", False)))

        def _toggle_oob():
            try:
                config_manager.set("include_oob", bool(self.oob_var.get()))
                config_manager.save_config()
                messagebox.showinfo(i18n.t("settings"), "OOB setting saved")
            except Exception:
                pass

        settings_menu.add_checkbutton(
            label="Include OOB in dumps",
            onvalue=True,
            offvalue=False,
            variable=self.oob_var,
            command=_toggle_oob,
        )

        # Enable ECC toggle
        self.ecc_var = tk.BooleanVar(value=bool(config_manager.get("enable_ecc", False)))

        def _toggle_ecc():
            try:
                config_manager.set("enable_ecc", bool(self.ecc_var.get()))
                config_manager.save_config()
                messagebox.showinfo(i18n.t("settings"), "ECC setting saved")
            except Exception:
                pass

        settings_menu.add_checkbutton(
            label="Enable ECC verification",
            onvalue=True,
            offvalue=False,
            variable=self.ecc_var,
            command=_toggle_ecc,
        )

        # ECC parameters dialog
        def _open_ecc_params():
            win = tk.Toplevel(self.root)
            win.title("ECC Parameters")
            tk.Label(win, text="ECC scheme (none|crc16|hamming_512_3byte)").grid(
                row=0, column=0, sticky="w"
            )
            scheme_var = tk.StringVar(value=str(config_manager.get("ecc_scheme", "crc16")))
            tk.Entry(win, textvariable=scheme_var).grid(row=0, column=1)
            tk.Label(win, text="ECC sector size").grid(row=1, column=0, sticky="w")
            sector_var = tk.StringVar(value=str(config_manager.get("ecc_sector_size", 512)))
            tk.Entry(win, textvariable=sector_var).grid(row=1, column=1)
            tk.Label(win, text="ECC bytes per sector").grid(row=2, column=0, sticky="w")
            bytes_var = tk.StringVar(value=str(config_manager.get("ecc_bytes_per_sector", 2)))
            tk.Entry(win, textvariable=bytes_var).grid(row=2, column=1)
            tk.Label(win, text="ECC OOB offset").grid(row=3, column=0, sticky="w")
            oob_off_var = tk.StringVar(value=str(config_manager.get("ecc_oob_offset", 0)))
            tk.Entry(win, textvariable=oob_off_var).grid(row=3, column=1)

            def _save():
                try:
                    config_manager.set("ecc_scheme", scheme_var.get())
                    config_manager.set("ecc_sector_size", int(sector_var.get()))
                    config_manager.set("ecc_bytes_per_sector", int(bytes_var.get()))
                    config_manager.set("ecc_oob_offset", int(oob_off_var.get()))
                    config_manager.save_config()
                    messagebox.showinfo("ECC", "ECC parameters saved")
                    win.destroy()
                except Exception as e:
                    messagebox.showerror("ECC", f"Error saving ECC params: {e}")

            tk.Button(win, text="Save", command=_save).grid(row=4, column=0, columnspan=2)

        settings_menu.add_command(label="ECC Parameters…", command=_open_ecc_params)

        # Clear resume state
        def _clear_resume():
            try:
                self.controller.clear_resume_state()
                messagebox.showinfo(i18n.t("settings"), i18n.t("resume_cleared"))
            except Exception:
                pass

        settings_menu.add_command(label=i18n.t("clear_resume"), command=_clear_resume)
        menubar.add_cascade(label=i18n.t("settings"), menu=settings_menu)
        self.root.config(menu=menubar)
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Connection frame
        conn_label = i18n.t("connection")
        conn_frame = ttk.LabelFrame(main_frame, text=conn_label, padding="5")
        conn_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        btn_connect = i18n.t("connect_button")
        btn_disconnect = i18n.t("disconnect_button")
        status_disconnected = i18n.t("status_disconnected")
        ttk.Button(conn_frame, text=btn_connect, command=self.connect).grid(row=0, column=0, padx=5)
        ttk.Button(conn_frame, text=btn_disconnect, command=self.disconnect).grid(
            row=0, column=1, padx=5
        )
        self.conn_status_label = ttk.Label(conn_frame, text=status_disconnected)
        self.conn_status_label.grid(row=0, column=2, padx=10)

        # NAND info frame
        nand_frame = ttk.LabelFrame(main_frame, text=i18n.t("nand_information"), padding="5")
        nand_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.nand_info_label = ttk.Label(nand_frame, text=i18n.t("nand_not_detected"))
        self.nand_info_label.grid(row=0, column=0, sticky=tk.W)

        # File operations frame
        file_frame = ttk.LabelFrame(main_frame, text=i18n.t("file_operations"), padding="5")
        file_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        btn_select_dump = i18n.t("operations_select_dump")
        ttk.Button(file_frame, text=btn_select_dump, command=self.select_dump).grid(
            row=0, column=0, padx=5
        )
        self.dump_label = ttk.Label(file_frame, text=i18n.t("no_file_selected"))
        self.dump_label.grid(row=0, column=1, padx=5, sticky=tk.W)

        # Operations frame
        op_frame = ttk.LabelFrame(main_frame, text=i18n.t("operations"), padding="5")
        op_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        btn_read = i18n.t("nand_operations_read")
        btn_write = i18n.t("nand_operations_write")
        btn_erase = i18n.t("nand_operations_erase")
        ttk.Button(op_frame, text=btn_read, command=self.read_nand).grid(
            row=0, column=0, padx=5, pady=2
        )
        ttk.Button(op_frame, text=btn_write, command=self.write_nand).grid(
            row=0, column=1, padx=5, pady=2
        )
        ttk.Button(op_frame, text=btn_erase, command=self.erase_nand).grid(
            row=0, column=2, padx=5, pady=2
        )

        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=5)
        self.progress_label = ttk.Label(progress_frame, text=i18n.t("ready"))
        self.progress_label.grid(row=0, column=1, padx=5)

        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        self.status_label = ttk.Label(status_frame, text=i18n.t("ready"))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        # Resume status label
        self.resume_label = ttk.Label(status_frame, text="")
        self.resume_label.grid(row=0, column=1, sticky=tk.W, padx=10)

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

    def _set_language(self, lang_code: str):
        try:
            i18n.set_language(lang_code)
            # Persist to config
            config_manager.set("default_language", lang_code.upper())
            config_manager.save_config()
            messagebox.showinfo(i18n.t("settings"), i18n.t("language_applied"))
        except Exception:
            pass

    def connect(self):
        """Connect to the Pico device"""
        self.logger.info("Attempting to connect to Pico...")

        # Try to auto-detect port
        ports = list(serial.tools.list_ports.comports())
        pico_port = None
        for port in ports:
            if (
                "Pico" in port.description
                or "Serial" in port.description
                or "UART" in port.description
            ):
                pico_port = port.device
                break

        if not pico_port:
            # If auto-detect fails, ask user
            messagebox.showinfo(i18n.t("connection_title"), i18n.t("connection_manual_select"))
            return

        try:
            if self.controller.connect(pico_port):
                self.is_connected = True
                self.conn_status_label.config(text=f"Connected to {pico_port}")
                self.status_label.config(text=i18n.t("status_connected"))

                # Try to detect NAND
                self.detect_nand()
            else:
                messagebox.showerror(i18n.t("connection_error_title"), i18n.t("connection_failed"))
                self.conn_status_label.config(text=i18n.t("connection_failed"))
        except ConnectionException as e:
            self.logger.error(f"Connection failed: {e}")
            messagebox.showerror(i18n.t("connection_error_title"), i18n.t("connection_failed"))
            self.conn_status_label.config(text=i18n.t("connection_failed"))
        except Exception as e:
            self.logger.error(f"Unexpected error during connection: {e}")
            messagebox.showerror(i18n.t("connection_error_title"), i18n.t("connection_error"))
            self.conn_status_label.config(text=i18n.t("connection_error"))

    def disconnect(self):
        """Disconnect from the Pico device"""
        if self.is_connected:
            self.controller.disconnect()
            self.is_connected = False
            self.conn_status_label.config(text=i18n.t("status_disconnected"))
            self.nand_info_label.config(text=i18n.t("nand_not_detected"))
            self.status_label.config(text=i18n.t("status_disconnected"))
            self.logger.info("Disconnected from Pico")

    def detect_nand(self):
        """Detect connected NAND chip"""
        if not self.is_connected:
            return

        detected, model, info = self.controller.detect_nand()
        if detected and model:
            info_text = f"NAND: {model}"
            if info:
                info_text += (
                    f" ({info['page_size']*info['block_size']*info['blocks']//(1024*1024)} MB)"
                )
            self.nand_info_label.config(text=info_text)
            self.status_label.config(text=f"NAND detected: {model}")
            self.logger.info(f"NAND detected: {model}")
            # Show resume mode if exists
            try:
                resume = self.controller.get_resume_state()
                op = resume.get("operation")
                if op == "READ":
                    self.resume_label.config(
                        text=i18n.t("resume_mode_read").replace(
                            "{page}", str(resume.get("last_page", 0))
                        )
                    )
                elif op == "WRITE":
                    self.resume_label.config(
                        text=i18n.t("resume_mode_write").replace(
                            "{bytes}", str(resume.get("bytes_sent", 0))
                        )
                    )
                elif op == "ERASE":
                    self.resume_label.config(
                        text=i18n.t("resume_mode_erase").replace(
                            "{block}", str(resume.get("erase_block", 0))
                        )
                    )
                else:
                    self.resume_label.config(text="")
            except Exception:
                self.resume_label.config(text="")
        else:
            self.nand_info_label.config(text=i18n.t("nand_not_detected"))
            self.status_label.config(text=i18n.t("nand_not_detected"))
            self.resume_label.config(text="")

    def select_dump(self):
        """Select a dump file"""
        file_path = filedialog.askopenfilename(
            title=i18n.t("select_dump_title"),
            filetypes=[("Binary files", "*.bin"), ("All files", "*.*")],
        )

        if file_path:
            self.selected_dump_path = file_path
            self.dump_label.config(text=os.path.basename(file_path))
            self.logger.info(f"Selected dump file: {file_path}")

    def save_dump(self) -> str | None:
        """Prompt to save dump file"""
        file_path = filedialog.asksaveasfilename(
            title=i18n.t("save_dump_title"),
            defaultextension=".bin",
            filetypes=[("Binary files", "*.bin"), ("All files", "*.*")],
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
                        if widget.cget("text") in ["Read NAND", "Write NAND", "Erase NAND"]:
                            widget.config(state="disabled")
                    else:
                        if widget.cget("text") in ["Read NAND", "Write NAND", "Erase NAND"]:
                            widget.config(state="normal")

    def read_nand(self):
        """Start NAND read operation"""
        if not self.is_connected:
            messagebox.showerror(i18n.t("error_title"), i18n.t("not_connected_to_pico"))
            return

        if not self.controller.current_nand_info:
            messagebox.showwarning(i18n.t("warning_title"), i18n.t("no_nand_detected"))
            return

        # Ask for save location
        save_path = self.save_dump()
        if not save_path:
            return

        # Confirm operation
        if not messagebox.askyesno(i18n.t("confirm_read_title"), i18n.t("confirm_read_text")):
            return

        # Resume prompt (if applicable)
        try:
            resume = self.controller.get_resume_state()
            if resume.get("operation") == "READ":
                if not messagebox.askyesno(
                    i18n.t("resume_found_title"), i18n.t("resume_read_text")
                ):
                    self.controller.clear_resume_state()
        except Exception:
            pass

        # Start operation in separate thread
        self.set_operation_running(True)
        self.status_label.config(text=i18n.t("reading_nand"))

        def read_thread():
            try:
                data = self.controller.read_nand(progress_callback=self.update_progress)
                if data:
                    with open(save_path, "wb") as f:
                        f.write(data)
                    self.status_label.config(text=i18n.t("read_completed"))
                    messagebox.showinfo(i18n.t("success_title"), i18n.t("read_completed"))
                else:
                    self.status_label.config(text=i18n.t("read_failed"))
                    messagebox.showerror(i18n.t("error_title"), i18n.t("read_failed"))
            except Exception as e:
                self.logger.error(f"Error during read operation: {e}")
                self.status_label.config(text=i18n.t("read_failed"))
                messagebox.showerror(i18n.t("error_title"), i18n.t("read_failed"))
            finally:
                self.set_operation_running(False)
                self.progress_var.set(0)
                self.progress_label.config(text=i18n.t("ready"))

        threading.Thread(target=read_thread, daemon=True).start()

    def write_nand(self):
        """Start NAND write operation"""
        if not self.is_connected:
            messagebox.showerror(i18n.t("error_title"), i18n.t("not_connected_to_pico"))
            return

        if not self.controller.current_nand_info:
            messagebox.showwarning(i18n.t("warning_title"), i18n.t("no_nand_detected"))
            return

        if not self.selected_dump_path or not os.path.exists(self.selected_dump_path):
            messagebox.showerror(i18n.t("error_title"), i18n.t("please_select_dump"))
            return

        # Confirm operation
        if not messagebox.askyesno(i18n.t("confirm_write_title"), i18n.t("confirm_write_text")):
            return

        # Resume prompt (if applicable)
        try:
            resume = self.controller.get_resume_state()
            if resume.get("operation") == "WRITE":
                if not messagebox.askyesno(
                    i18n.t("resume_found_title"), i18n.t("resume_write_text")
                ):
                    self.controller.clear_resume_state()
        except Exception:
            pass

        # Start operation in separate thread
        self.set_operation_running(True)
        self.status_label.config(text=i18n.t("writing_nand"))

        def write_thread():
            try:
                with open(self.selected_dump_path, "rb") as f:
                    data = f.read()

                success = self.controller.write_nand(data, progress_callback=self.update_progress)
                if success:
                    self.status_label.config(text=i18n.t("write_completed"))
                    messagebox.showinfo(i18n.t("success_title"), i18n.t("write_completed"))
                else:
                    self.status_label.config(text=i18n.t("write_failed"))
                    messagebox.showerror(i18n.t("error_title"), i18n.t("write_failed"))
            except Exception as e:
                self.logger.error(f"Error during write operation: {e}")
                self.status_label.config(text=i18n.t("write_failed"))
                messagebox.showerror(i18n.t("error_title"), i18n.t("write_failed"))
            finally:
                self.set_operation_running(False)
                self.progress_var.set(0)
                self.progress_label.config(text=i18n.t("ready"))

        threading.Thread(target=write_thread, daemon=True).start()

    def erase_nand(self):
        """Start NAND erase operation"""
        if not self.is_connected:
            messagebox.showerror(i18n.t("error_title"), i18n.t("not_connected_to_pico"))
            return

        if not self.controller.current_nand_info:
            messagebox.showwarning("Warning", "No NAND chip detected")
            return

        # Confirm operation
        if not messagebox.askyesno(i18n.t("confirm_erase_title"), i18n.t("confirm_erase_text")):
            return

        # Resume prompt (if applicable)
        try:
            resume = self.controller.get_resume_state()
            if resume.get("operation") == "ERASE":
                if not messagebox.askyesno(
                    i18n.t("resume_found_title"), i18n.t("resume_erase_text")
                ):
                    self.controller.clear_resume_state()
        except Exception:
            pass

        # Start operation in separate thread
        self.set_operation_running(True)
        self.status_label.config(text=i18n.t("erasing_nand"))

        def erase_thread():
            try:
                success = self.controller.erase_nand(progress_callback=self.update_progress)
                if success:
                    self.status_label.config(text=i18n.t("erase_completed"))
                    messagebox.showinfo(i18n.t("success_title"), i18n.t("erase_completed"))
                else:
                    self.status_label.config(text=i18n.t("erase_failed"))
                    messagebox.showerror(i18n.t("error_title"), i18n.t("erase_failed"))
            except Exception as e:
                self.logger.error(f"Error during erase operation: {e}")
                self.status_label.config(text=i18n.t("erase_failed"))
                messagebox.showerror(i18n.t("error_title"), i18n.t("erase_failed"))
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
