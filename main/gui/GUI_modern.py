"""
Pico NAND Flasher - Modern GUI with PyQt6
Computer-side GUI for controlling the Raspberry Pi Pico NAND Flasher
with enhanced performance and reliability features.
"""
import sys
import os
import time
import serial
import serial.tools.list_ports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QProgressBar, QGroupBox, QFileDialog,
                            QMessageBox, QComboBox, QCheckBox, QTextEdit, QTabWidget)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QFont, QIcon

class NANDFlasherGUI(QMainWindow):
    """Modern GUI class for NAND Flasher operations with PyQt6"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🚀 Pico NAND Flasher (Modern)")
        self.setGeometry(100, 100, 800, 600)
        
        # Global settings
        self.LANG = "RU"
        self.COM_PORT = None
        self.BAUDRATE = 921600
        self.ser = None
        self.selected_dump = None
        self.selected_operation = None
        self.operation_running = False
        self.pause_operation = False
        self.cancel_operation = False
        self.nand_info = {"status": "❌ NAND не подключен", "model": ""}
        self.manual_select_mode = False
        self.supported_nand_models = []
        
        # Performance settings
        self.use_compression = True
        self.skip_blank_pages = True
        self.last_resume_block = 0
        
        # Localization
        self.LANG_TEXT = {
            "RU": {
                "title": "🚀 Pico NAND Flasher (Modern) 🚀",
                "footer": "😊 сделал с любовью - bobberdolle1 😊",
                "menu": ["📁 Операции с NAND", "📘 Инструкция", "🌍 Сменить язык", "⚙️ Настройки", "🚪 Выход"],
                "operations": ["📂 Выбрать дамп", "🔧 Выбрать операцию", "✅ Подтвердить операцию", "🔙 Назад"],
                "nand_operations": ["📥 Прочитать NAND", "📤 Записать NAND", "🧹 Очистить NAND"],
                "progress": "⏳ Выполняется",
                "warning": "⚠️ Внимание! Эта операция может стереть данные! Продолжить?",
                "no_dump": "❌ Дамп не выбран!",
                "no_operation": "❌ Операция не выбрана!",
                "selected_dump": "Выбранный дамп: ",
                "selected_operation": "Выбранная операция: ",
                "nand_status": "Состояние NAND: ",
                "nand_detection_failed": "❌ NAND не обнаружен! Продолжить вручную?",
                "operation_not_possible": "⚠️ Невозможно выполнить операцию: NAND не подключен!",
                "com_auto_detect": "🔌 Автоопределение COM-порта...",
                "com_found": "✅ Подключено к ",
                "com_not_found": "❌ Pico не найден!",
                "manual_com": "🖥 Выберите COM-порт вручную:",
                "nand_model": "📝 Модель: ",
                "operation_cancelled": "🚫 Операция отменена!",
                "dump_saved": "💾 Дамп сохранен в: ",
                "dump_load_error": "❌ Ошибка загрузки дампа!",
                "dump_send_progress": "📤 Отправка дампа: ",
                "dump_send_complete": "✅ Дамп отправлен.",
                "invalid_selection": "❌ Неверный выбор!",
                "select_model_prompt": "Введите номер модели: ",
                "settings_title": "⚙️ Настройки производительности",
                "compression_setting": "Использовать сжатие данных: ",
                "blank_skip_setting": "Пропускать пустые страницы: ",
                "power_check": "Проверка питания: ",
                "resume_operation": "Продолжить прерванную операцию: ",
                "resume_prompt": "Найдена прерванная операция. Продолжить с блока {}?",
                "power_warning": "⚠️ Предупреждение о питании: ",
                "settings_saved": "⚙️ Настройки сохранены",
                "connect_button": "🔌 Подключиться",
                "disconnect_button": "🔌 Отключиться",
                "refresh_button": "🔄 Обновить",
                "log_tab": "Лог",
                "settings_tab": "Настройки",
                "info_tab": "Информация",
                "operation_control": "Управление операцией",
                "pause_button": "⏸️ Пауза",
                "resume_button": "▶️ Продолжить",
                "cancel_button": "❌ Отмена",
                "read_button": "📥 Прочитать",
                "write_button": "📤 Записать",
                "erase_button": "🧹 Стереть",
                "save_dump_button": "💾 Сохранить дамп",
                "load_dump_button": "📂 Загрузить дамп",
                "operation_status": "Статус операции: ",
                "power_status": "Статус питания: ",
                "operation_progress": "Прогресс операции: ",
                "operation_log": "Лог операций: "
            },
            "EN": {
                "title": "🚀 Pico NAND Flasher (Modern) 🚀",
                "footer": "😊 made with love by bobberdolle1 😊",
                "menu": ["📁 NAND Operations", "📘 Instruction", "🌍 Change Language", "⚙️ Settings", "🚪 Exit"],
                "operations": ["📂 Select Dump", "🔧 Select Operation", "✅ Confirm Operation", "🔙 Back"],
                "nand_operations": ["📥 Read NAND", "📤 Write NAND", "🧹 Erase NAND"],
                "progress": "⏳ Processing",
                "warning": "⚠️ Warning! This operation may erase data! Continue?",
                "no_dump": "❌ Dump not selected!",
                "no_operation": "❌ Operation not selected!",
                "selected_dump": "Selected dump: ",
                "selected_operation": "Selected operation: ",
                "nand_status": "NAND Status: ",
                "nand_detection_failed": "❌ NAND not detected! Continue manually?",
                "operation_not_possible": "⚠️ Operation not possible: NAND not connected!",
                "com_auto_detect": "🔌 Auto-detecting COM port...",
                "com_found": "✅ Connected to ",
                "com_not_found": "❌ Pico not found!",
                "manual_com": "🖥 Select COM port manually:",
                "nand_model": "📝 Model: ",
                "operation_cancelled": "🚫 Operation cancelled!",
                "dump_saved": "💾 Dump saved to: ",
                "dump_load_error": "❌ Error loading dump!",
                "dump_send_progress": "📤 Sending dump: ",
                "dump_send_complete": "✅ Dump sent.",
                "invalid_selection": "❌ Invalid selection!",
                "select_model_prompt": "Enter model number: ",
                "settings_title": "⚙️ Performance Settings",
                "compression_setting": "Use data compression: ",
                "blank_skip_setting": "Skip blank pages: ",
                "power_check": "Power supply check: ",
                "resume_operation": "Resume interrupted operation: ",
                "resume_prompt": "Found interrupted operation. Resume from block {}?",
                "power_warning": "⚠️ Power supply warning: ",
                "settings_saved": "⚙️ Settings saved",
                "connect_button": "🔌 Connect",
                "disconnect_button": "🔌 Disconnect",
                "refresh_button": "🔄 Refresh",
                "log_tab": "Log",
                "settings_tab": "Settings",
                "info_tab": "Info",
                "operation_control": "Operation Control",
                "pause_button": "⏸️ Pause",
                "resume_button": "▶️ Resume",
                "cancel_button": "❌ Cancel",
                "read_button": "📥 Read",
                "write_button": "📤 Write",
                "erase_button": "🧹 Erase",
                "save_dump_button": "💾 Save Dump",
                "load_dump_button": "📂 Load Dump",
                "operation_status": "Operation Status: ",
                "power_status": "Power Status: ",
                "operation_progress": "Operation Progress: ",
                "operation_log": "Operation Log: "
            }
        }
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tabs
        self.tabs = QTabWidget()
        
        # Main tab
        self.main_tab = QWidget()
        self.setup_main_tab()
        
        # Log tab
        self.log_tab = QWidget()
        self.setup_log_tab()
        
        # Settings tab
        self.settings_tab = QWidget()
        self.setup_settings_tab()
        
        # Add tabs
        self.tabs.addTab(self.main_tab, self.LANG_TEXT[self.LANG]["log_tab"])
        self.tabs.addTab(self.log_tab, self.LANG_TEXT[self.LANG]["log_tab"])
        self.tabs.addTab(self.settings_tab, self.LANG_TEXT[self.LANG]["settings_tab"])
        
        main_layout.addWidget(self.tabs)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage(self.LANG_TEXT[self.LANG]["nand_status"] + self.nand_info["status"])
        
        # Timer for checking NAND status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_nand_status)
        self.status_timer.start(5000)  # Check every 5 seconds
        
    def setup_main_tab(self):
        """Setup the main tab"""
        layout = QVBoxLayout(self.main_tab)
        
        # Connection group
        conn_group = QGroupBox("🔌 Подключение")
        conn_layout = QHBoxLayout(conn_group)
        
        self.com_ports_combo = QComboBox()
        self.refresh_ports_button = QPushButton(self.LANG_TEXT[self.LANG]["refresh_button"])
        self.connect_button = QPushButton(self.LANG_TEXT[self.LANG]["connect_button"])
        self.disconnect_button = QPushButton(self.LANG_TEXT[self.LANG]["disconnect_button"])
        self.disconnect_button.setEnabled(False)
        
        conn_layout.addWidget(QLabel("COM Порт:"))
        conn_layout.addWidget(self.com_ports_combo)
        conn_layout.addWidget(self.refresh_ports_button)
        conn_layout.addWidget(self.connect_button)
        conn_layout.addWidget(self.disconnect_button)
        
        layout.addWidget(conn_group)
        
        # NAND Info group
        nand_group = QGroupBox("📝 Информация о NAND")
        nand_layout = QVBoxLayout(nand_group)
        
        self.nand_status_label = QLabel(self.nand_info["status"])
        self.nand_model_label = QLabel(self.nand_info["model"])
        
        nand_layout.addWidget(self.nand_status_label)
        nand_layout.addWidget(self.nand_model_label)
        
        layout.addWidget(nand_group)
        
        # Operation group
        op_group = QGroupBox("⚙️ Операции")
        op_layout = QVBoxLayout(op_group)
        
        self.read_button = QPushButton(self.LANG_TEXT[self.LANG]["read_button"])
        self.write_button = QPushButton(self.LANG_TEXT[self.LANG]["write_button"])
        self.erase_button = QPushButton(self.LANG_TEXT[self.LANG]["erase_button"])
        
        op_layout.addWidget(self.read_button)
        op_layout.addWidget(self.write_button)
        op_layout.addWidget(self.erase_button)
        
        layout.addWidget(op_group)
        
        # Progress group
        progress_group = QGroupBox("📊 Прогресс")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("0%")
        
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        
        layout.addWidget(progress_group)
        
        # Control group
        control_group = QGroupBox(self.LANG_TEXT[self.LANG]["operation_control"])
        control_layout = QHBoxLayout(control_group)
        
        self.pause_button = QPushButton(self.LANG_TEXT[self.LANG]["pause_button"])
        self.resume_button = QPushButton(self.LANG_TEXT[self.LANG]["resume_button"])
        self.cancel_button = QPushButton(self.LANG_TEXT[self.LANG]["cancel_button"])
        
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.resume_button)
        control_layout.addWidget(self.cancel_button)
        
        layout.addWidget(control_group)
        
        # Dump selection
        dump_group = QGroupBox("💾 Выбор дампа")
        dump_layout = QHBoxLayout(dump_group)
        
        self.dump_path_label = QLabel(self.LANG_TEXT[self.LANG]["no_dump"])
        self.load_dump_button = QPushButton(self.LANG_TEXT[self.LANG]["load_dump_button"])
        self.save_dump_button = QPushButton(self.LANG_TEXT[self.LANG]["save_dump_button"])
        
        dump_layout.addWidget(self.dump_path_label)
        dump_layout.addWidget(self.load_dump_button)
        dump_layout.addWidget(self.save_dump_button)
        
        layout.addWidget(dump_group)
        
    def setup_log_tab(self):
        """Setup the log tab"""
        layout = QVBoxLayout(self.log_tab)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        layout.addWidget(self.log_text)
        
    def setup_settings_tab(self):
        """Setup the settings tab"""
        layout = QVBoxLayout(self.settings_tab)
        
        # Performance settings
        perf_group = QGroupBox("⚙️ Настройки производительности")
        perf_layout = QVBoxLayout(perf_group)
        
        self.compression_checkbox = QCheckBox(self.LANG_TEXT[self.LANG]["compression_setting"])
        self.compression_checkbox.setChecked(self.use_compression)
        
        self.blank_skip_checkbox = QCheckBox(self.LANG_TEXT[self.LANG]["blank_skip_setting"])
        self.blank_skip_checkbox.setChecked(self.skip_blank_pages)
        
        perf_layout.addWidget(self.compression_checkbox)
        perf_layout.addWidget(self.blank_skip_checkbox)
        
        layout.addWidget(perf_group)
        
        # Power settings
        power_group = QGroupBox("⚡ Настройки питания")
        power_layout = QVBoxLayout(power_group)
        
        self.power_check_button = QPushButton(self.LANG_TEXT[self.LANG]["power_check"])
        self.power_status_label = QLabel("Неизвестно")
        
        power_layout.addWidget(self.power_check_button)
        power_layout.addWidget(self.power_status_label)
        
        layout.addWidget(power_group)
        
    def setup_connections(self):
        """Setup signal connections"""
        self.connect_button.clicked.connect(self.connect_pico)
        self.disconnect_button.clicked.connect(self.disconnect_pico)
        self.refresh_ports_button.clicked.connect(self.refresh_com_ports)
        
        self.read_button.clicked.connect(self.read_nand)
        self.write_button.clicked.connect(self.write_nand)
        self.erase_button.clicked.connect(self.erase_nand)
        
        self.pause_button.clicked.connect(self.pause_operation)
        self.resume_button.clicked.connect(self.resume_operation)
        self.cancel_button.clicked.connect(self.cancel_operation)
        
        self.load_dump_button.clicked.connect(self.select_dump)
        self.save_dump_button.clicked.connect(self.save_dump)
        
        self.compression_checkbox.stateChanged.connect(self.toggle_compression)
        self.blank_skip_checkbox.stateChanged.connect(self.toggle_blank_skip)
        self.power_check_button.clicked.connect(self.check_power_supply)
        
        # Populate COM ports
        self.refresh_com_ports()
        
    def refresh_com_ports(self):
        """Refresh available COM ports"""
        self.com_ports_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.com_ports_combo.addItems(ports)
        
        # Try to auto-select Pico if available
        for port in ports:
            if "Pico" in port or "Serial" in port or "UART" in port:
                self.com_ports_combo.setCurrentText(port)
                break
    
    def log_message(self, message):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        
    def connect_pico(self):
        """Connect to Pico"""
        port = self.com_ports_combo.currentText()
        if not port:
            QMessageBox.warning(self, "Ошибка", self.LANG_TEXT[self.LANG]["com_not_found"])
            return
            
        try:
            self.ser = serial.Serial(port, self.BAUDRATE, timeout=1)
            self.COM_PORT = port
            self.log_message(f"{self.LANG_TEXT[self.LANG]['com_found']}{port}")
            
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.status_bar.showMessage(f"{self.LANG_TEXT[self.LANG]['com_found']}{port}")
            
            # Start checking NAND status
            self.check_nand_status()
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка подключения", f"Ошибка: {str(e)}")
            self.log_message(f"Ошибка подключения: {str(e)}")
    
    def disconnect_pico(self):
        """Disconnect from Pico"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            
        self.ser = None
        self.COM_PORT = None
        self.connect_button.setEnabled(True)
        self.disconnect_button.setEnabled(False)
        self.nand_status_label.setText("❌ NAND не подключен")
        self.nand_model_label.setText("")
        self.status_bar.showMessage("Отключено")
        self.log_message("Отключено от Pico")
    
    def check_nand_status(self):
        """Check the status of the connected NAND chip"""
        if not self.ser or not self.ser.is_open:
            return
            
        try:
            # Clear buffer before sending request
            self.ser.reset_input_buffer()
            self.ser.write(b'STATUS\n')
            
            start_time = time.time()
            timeout = 5  # 5 second timeout
            while time.time() - start_time < timeout:
                if self.ser.in_waiting > 0:
                    response = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    
                    if response.startswith("MODEL:"):
                        model_name = response.split(":", 1)[1]
                        self.nand_info = {"status": "✅ NAND подключен", "model": model_name}
                        self.nand_status_label.setText(self.nand_info["status"])
                        self.nand_model_label.setText(f"{self.LANG_TEXT[self.LANG]['nand_model']}{model_name}")
                        self.status_bar.showMessage(f"{self.LANG_TEXT[self.LANG]['nand_status']}{self.nand_info['status']}")
                        self.read_button.setEnabled(True)
                        self.write_button.setEnabled(True)
                        self.erase_button.setEnabled(True)
                        self.log_message(f"Обнаружена модель NAND: {model_name}")
                        return
                    elif response == "MODEL:UNKNOWN":
                        self.nand_info = {"status": "❌ NAND не обнаружен", "model": ""}
                        self.nand_status_label.setText(self.nand_info["status"])
                        self.nand_model_label.setText("")
                        self.status_bar.showMessage(f"{self.LANG_TEXT[self.LANG]['nand_status']}{self.nand_info['status']}")
                        self.read_button.setEnabled(False)
                        self.write_button.setEnabled(False)
                        self.erase_button.setEnabled(False)
                        return
                        
                time.sleep(0.01)  # Small pause in wait loop
            
        except Exception as e:
            self.log_message(f"Ошибка проверки NAND: {str(e)}")
    
    def read_nand(self):
        """Start reading NAND operation"""
        if not self.ser or not self.ser.is_open:
            QMessageBox.warning(self, "Ошибка", self.LANG_TEXT[self.LANG]["operation_not_possible"])
            return
            
        # Ask for dump file location
        dump_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Сохранить дамп как", 
            "", 
            "Binary files (*.bin);;All files (*)"
        )
        
        if not dump_path:
            return
            
        self.selected_dump = dump_path
        self.dump_path_label.setText(f"{self.LANG_TEXT[self.LANG]['selected_dump']}{dump_path}")
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            "Подтверждение", 
            self.LANG_TEXT[self.LANG]["warning"],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            self.log_message(self.LANG_TEXT[self.LANG]["operation_cancelled"])
            return
            
        # Start operation
        self.start_operation("READ")
    
    def write_nand(self):
        """Start writing NAND operation"""
        if not self.ser or not self.ser.is_open:
            QMessageBox.warning(self, "Ошибка", self.LANG_TEXT[self.LANG]["operation_not_possible"])
            return
            
        if not self.selected_dump:
            QMessageBox.warning(self, "Ошибка", self.LANG_TEXT[self.LANG]["no_dump"])
            return
            
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            "Подтверждение", 
            self.LANG_TEXT[self.LANG]["warning"],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            self.log_message(self.LANG_TEXT[self.LANG]["operation_cancelled"])
            return
            
        # Start operation
        self.start_operation("WRITE")
    
    def erase_nand(self):
        """Start erasing NAND operation"""
        if not self.ser or not self.ser.is_open:
            QMessageBox.warning(self, "Ошибка", self.LANG_TEXT[self.LANG]["operation_not_possible"])
            return
            
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            "Подтверждение", 
            self.LANG_TEXT[self.LANG]["warning"],
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            self.log_message(self.LANG_TEXT[self.LANG]["operation_cancelled"])
            return
            
        # Start operation
        self.start_operation("ERASE")
    
    def start_operation(self, operation):
        """Start the specified operation"""
        self.operation_running = True
        self.operation_type = operation
        
        # Enable control buttons
        self.pause_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        
        # Disable operation buttons
        self.read_button.setEnabled(False)
        self.write_button.setEnabled(False)
        self.erase_button.setEnabled(False)
        
        # Reset progress
        self.progress_bar.setValue(0)
        self.progress_label.setText("0%")
        
        self.log_message(f"Начало операции: {operation}")
        
        # Send command to Pico
        self.ser.write(f'{operation}\n'.encode('utf-8'))
        
        # Start monitoring thread
        self.operation_thread = OperationThread(self.ser, operation)
        self.operation_thread.progress.connect(self.update_progress)
        self.operation_thread.status.connect(self.update_status)
        self.operation_thread.power_warning.connect(self.handle_power_warning)
        self.operation_thread.finished.connect(self.operation_finished)
        self.operation_thread.start()
    
    def update_progress(self, progress):
        """Update progress bar"""
        self.progress_bar.setValue(progress)
        self.progress_label.setText(f"{progress}%")
    
    def update_status(self, status):
        """Update status"""
        self.log_message(status)
    
    def handle_power_warning(self, warning):
        """Handle power supply warning"""
        self.log_message(f"{self.LANG_TEXT[self.LANG]['power_warning']}{warning}")
        QMessageBox.warning(self, "Предупреждение о питании", f"{self.LANG_TEXT[self.LANG]['power_warning']}{warning}")
    
    def operation_finished(self, success):
        """Handle operation completion"""
        self.operation_running = False
        
        # Disable control buttons
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        
        # Enable operation buttons
        self.read_button.setEnabled(True)
        self.write_button.setEnabled(True)
        self.erase_button.setEnabled(True)
        
        if success:
            self.log_message("Операция завершена успешно")
            QMessageBox.information(self, "Успех", "Операция завершена успешно")
        else:
            self.log_message("Операция не удалась")
            QMessageBox.critical(self, "Ошибка", "Операция не удалась")
    
    def pause_operation(self):
        """Pause the current operation"""
        self.pause_operation = True
        self.log_message("Операция приостановлена")
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(True)
    
    def resume_operation(self):
        """Resume the paused operation"""
        self.pause_operation = False
        self.log_message("Операция возобновлена")
        self.pause_button.setEnabled(True)
        self.resume_button.setEnabled(False)
    
    def cancel_operation(self):
        """Cancel the current operation"""
        if self.ser and self.ser.is_open:
            self.ser.write(b'CANCEL\n')
            
        self.cancel_operation = True
        self.operation_running = False
        self.log_message("Операция отменена")
        
        # Disable control buttons
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        
        # Enable operation buttons
        self.read_button.setEnabled(True)
        self.write_button.setEnabled(True)
        self.erase_button.setEnabled(True)
    
    def select_dump(self):
        """Select a dump file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выбрать дамп", 
            "", 
            "Binary files (*.bin);;All files (*)"
        )
        
        if file_path:
            self.selected_dump = file_path
            self.dump_path_label.setText(f"{self.LANG_TEXT[self.LANG]['selected_dump']}{file_path}")
            self.log_message(f"Выбран дамп: {file_path}")
    
    def save_dump(self):
        """Save a dump file"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Сохранить дамп как", 
            "", 
            "Binary files (*.bin);;All files (*)"
        )
        
        if file_path:
            self.selected_dump = file_path
            self.dump_path_label.setText(f"{self.LANG_TEXT[self.LANG]['selected_dump']}{file_path}")
            self.log_message(f"Дамп будет сохранен в: {file_path}")
            return file_path
            
        return None
    
    def toggle_compression(self, state):
        """Toggle compression setting"""
        self.use_compression = bool(state)
        self.log_message(f"Сжатие данных: {'включено' if self.use_compression else 'отключено'}")
    
    def toggle_blank_skip(self, state):
        """Toggle blank page skipping setting"""
        self.skip_blank_pages = bool(state)
        self.log_message(f"Пропуск пустых страниц: {'включено' if self.skip_blank_pages else 'отключено'}")
    
    def check_power_supply(self):
        """Check power supply status from Pico"""
        if not self.ser or not self.ser.is_open:
            return
            
        try:
            self.ser.reset_input_buffer()
            self.ser.write(b'POWER_CHECK\n')

            start_time = time.time()
            timeout = 3  # 3 second timeout
            while time.time() - start_time < timeout:
                if self.ser.in_waiting > 0:
                    response = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if response.startswith("POWER:"):
                        power_info = response.split(":", 1)[1]
                        self.power_status_label.setText(power_info)
                        self.log_message(f"Статус питания: {power_info}")
                        return power_info
                time.sleep(0.01)
                
            self.power_status_label.setText("Неизвестно")
            return "Неизвестно"
        except Exception as e:
            self.log_message(f"Ошибка проверки питания: {str(e)}")
            return "Ошибка"


class OperationThread(QThread):
    """Thread for handling NAND operations"""
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    power_warning = pyqtSignal(str)
    finished = pyqtSignal(bool)
    
    def __init__(self, ser, operation_type):
        super().__init__()
        self.ser = ser
        self.operation_type = operation_type
        self.dump_data = bytearray()
        
    def run(self):
        """Run the operation in the thread"""
        try:
            success = False
            timeout = 300  # 5 minutes timeout
            start_time = time.time()
            last_activity = start_time
            
            while True:
                # Check for timeout
                if time.time() - last_activity > timeout:
                    self.status.emit("Таймаут операции")
                    break
                    
                if self.ser.in_waiting > 0:
                    last_activity = time.time()
                    
                    # Read line from Pico
                    line_bytes = self.ser.readline()
                    try:
                        line = line_bytes.decode('utf-8').strip()
                        
                        # Process string responses
                        if line.startswith("PROGRESS:"):
                            try:
                                progress = int(line.split(":")[1])
                                self.progress.emit(progress)
                            except ValueError:
                                pass  # Ignore invalid progress
                        
                        elif line.startswith("POWER_WARNING:"):
                            power_warning = line.split(":", 1)[1]
                            self.power_warning.emit(power_warning)
                        
                        elif line == "OPERATION_COMPLETE":
                            success = True
                            # If this was a read operation, save the accumulated data
                            if self.operation_type == "READ" and self.dump_data and hasattr(self, 'dump_path'):
                                with open(self.dump_path, "wb") as f:
                                    f.write(self.dump_data)
                                self.status.emit(f"Дамп сохранен в: {self.dump_path}")
                            
                            self.status.emit("Операция завершена успешно")
                            break
                        
                        elif line == "OPERATION_FAILED":
                            self.status.emit("Операция не удалась")
                            break
                        
                        elif line == "NAND_NOT_CONNECTED":
                            self.status.emit("NAND не подключен")
                            break
                            
                    except UnicodeDecodeError:
                        # This is likely binary dump data (for READ operations)
                        if self.operation_type == "READ":
                            self.dump_data.extend(line_bytes)
                
                # Small delay to prevent high CPU usage
                self.msleep(10)
                
            self.finished.emit(success)
            
        except Exception as e:
            self.status.emit(f"Ошибка в потоке операции: {str(e)}")
            self.finished.emit(False)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application font
    font = QFont("Arial", 9)
    app.setFont(font)
    
    window = NANDFlasherGUI()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()