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
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt, QSettings
from PyQt6.QtGui import QFont, QIcon, QAction

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
        # Flags: avoid name conflicts with handler methods
        self.is_paused = False
        self.is_cancelled = False
        # Theme setting: System, Light, Dark
        self.theme = "System"
        # Write options
        self.write_with_oob = True  # default enabled
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
        
        # Settings storage (org/app names affect platform-specific storage locations)
        self.settings = QSettings("PicoNAND", "FlasherGUI")

        self.init_ui()
        self.setup_connections()
        self.load_settings()
        
    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Toolbar (professional quick actions)
        self.toolbar = self.addToolBar("Main")
        self.action_refresh = QAction("🔄", self)
        self.action_refresh.setToolTip(self.LANG_TEXT[self.LANG]["refresh_button"])
        self.action_connect = QAction("🔌", self)
        self.action_connect.setToolTip(self.LANG_TEXT[self.LANG]["connect_button"])
        self.action_disconnect = QAction("⛔", self)
        self.action_disconnect.setToolTip(self.LANG_TEXT[self.LANG]["disconnect_button"])
        self.action_read = QAction("📥", self)
        self.action_read.setToolTip(self.LANG_TEXT[self.LANG]["read_button"])
        self.action_write = QAction("📤", self)
        self.action_write.setToolTip(self.LANG_TEXT[self.LANG]["write_button"])
        self.action_erase = QAction("🧹", self)
        self.action_erase.setToolTip(self.LANG_TEXT[self.LANG]["erase_button"])
        self.action_about = QAction("ℹ️", self)
        self.action_about.setToolTip("About")
        for act in [self.action_refresh, self.action_connect, self.action_disconnect, self.action_read, self.action_write, self.action_erase, self.action_about]:
            self.toolbar.addAction(act)
        
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
        
        # Add tabs with correct titles
        self._apply_language_to_tabs()
        
        main_layout.addWidget(self.tabs)
        
        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage(self.LANG_TEXT[self.LANG]["nand_status"] + self.nand_info["status"])
        
        # Timer for checking NAND status
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_nand_status)
        self.status_timer.start(5000)  # Check every 5 seconds

        # Apply theme at startup
        self.apply_theme()
        # Apply app icon if exists
        try:
            assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, "assets"))
            for name in ("app.ico", "app.png"):  # prefer .ico on Windows
                icon_path = os.path.join(assets_dir, name)
                if os.path.exists(icon_path):
                    self.setWindowIcon(QIcon(icon_path))
                    break
            else:
                # No asset found: generate a simple icon dynamically
                try:
                    from PyQt6.QtGui import QPixmap, QPainter, QColor
                    pm = QPixmap(256, 256)
                    pm.fill(QColor("#1e1e1e"))
                    p = QPainter(pm)
                    p.setRenderHint(QPainter.RenderHint.Antialiasing)
                    # Accent circle
                    p.setBrush(QColor("#2a82da"))
                    p.setPen(QColor("#2a82da"))
                    p.drawEllipse(28, 28, 200, 200)
                    # Text PNF
                    p.setPen(QColor("white"))
                    font = QFont("Arial", 56, QFont.Weight.Bold)
                    p.setFont(font)
                    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "PNF")
                    p.end()
                    self.setWindowIcon(QIcon(pm))
                except Exception:
                    pass
        except Exception:
            pass

    def on_write_oob_changed(self, state):
        self.write_with_oob = bool(state)
        # Persist as 1/0 for portability
        self.settings.setValue("write_with_oob", 1 if self.write_with_oob else 0)
        # Restore window geometry/position
        self.restore_window_state()
        
    def setup_main_tab(self):
        """Setup the main tab"""
        layout = QVBoxLayout(self.main_tab)
        
        # Connection group
        conn_group = QGroupBox("🔌 Подключение" if self.LANG == "RU" else "🔌 Connection")
        conn_layout = QHBoxLayout(conn_group)
        
        self.com_ports_combo = QComboBox()
        self.refresh_ports_button = QPushButton(self.LANG_TEXT[self.LANG]["refresh_button"])
        self.connect_button = QPushButton(self.LANG_TEXT[self.LANG]["connect_button"])
        self.disconnect_button = QPushButton(self.LANG_TEXT[self.LANG]["disconnect_button"])
        self.disconnect_button.setEnabled(False)
        
        conn_layout.addWidget(QLabel("COM Порт:" if self.LANG == "RU" else "COM Port:"))
        conn_layout.addWidget(self.com_ports_combo)
        conn_layout.addWidget(self.refresh_ports_button)
        conn_layout.addWidget(self.connect_button)
        conn_layout.addWidget(self.disconnect_button)
        
        layout.addWidget(conn_group)
        
        # NAND Info group
        nand_group = QGroupBox("📝 Информация о NAND" if self.LANG == "RU" else "📝 NAND Info")
        nand_layout = QVBoxLayout(nand_group)
        
        self.nand_status_label = QLabel(self.nand_info["status"])
        self.nand_model_label = QLabel(self.nand_info["model"])
        
        nand_layout.addWidget(self.nand_status_label)
        nand_layout.addWidget(self.nand_model_label)
        
        layout.addWidget(nand_group)
        
        # Operation group
        op_group = QGroupBox("⚙️ Операции" if self.LANG == "RU" else "⚙️ Operations")
        op_layout = QVBoxLayout(op_group)
        
        self.read_button = QPushButton(self.LANG_TEXT[self.LANG]["read_button"])
        self.write_button = QPushButton(self.LANG_TEXT[self.LANG]["write_button"])
        self.erase_button = QPushButton(self.LANG_TEXT[self.LANG]["erase_button"])
        
        op_layout.addWidget(self.read_button)
        op_layout.addWidget(self.write_button)
        op_layout.addWidget(self.erase_button)
        
        layout.addWidget(op_group)
        
        # Progress group
        progress_group = QGroupBox("📊 Прогресс" if self.LANG == "RU" else "📊 Progress")
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
        dump_group = QGroupBox("💾 Выбор дампа" if self.LANG == "RU" else "💾 Dump selection")
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
        perf_group = QGroupBox(self.LANG_TEXT[self.LANG]["settings_title"])
        perf_layout = QVBoxLayout(perf_group)
        
        self.compression_checkbox = QCheckBox(self.LANG_TEXT[self.LANG]["compression_setting"])
        self.compression_checkbox.setChecked(self.use_compression)
        
        self.blank_skip_checkbox = QCheckBox(self.LANG_TEXT[self.LANG]["blank_skip_setting"])
        self.blank_skip_checkbox.setChecked(self.skip_blank_pages)
        # Write OOB option
        self.write_oob_checkbox = QCheckBox("Записывать OOB (spare)" if self.LANG == "RU" else "Write OOB (spare)")
        self.write_oob_checkbox.setChecked(self.write_with_oob)
        
        perf_layout.addWidget(self.compression_checkbox)
        perf_layout.addWidget(self.blank_skip_checkbox)
        perf_layout.addWidget(self.write_oob_checkbox)
        
        layout.addWidget(perf_group)
        
        # Power settings
        power_group = QGroupBox("⚡ Настройки питания" if self.LANG == "RU" else "⚡ Power settings")
        power_layout = QVBoxLayout(power_group)
        
        self.power_check_button = QPushButton(self.LANG_TEXT[self.LANG]["power_check"])
        self.power_status_label = QLabel("Неизвестно")
        
        power_layout.addWidget(self.power_check_button)
        power_layout.addWidget(self.power_status_label)
        
        layout.addWidget(power_group)

        # Language switch
        lang_group = QGroupBox("🌍 Язык / Language")
        lang_layout = QHBoxLayout(lang_group)
        self.lang_toggle_button = QPushButton("EN" if self.LANG == "RU" else "RU")
        lang_layout.addWidget(QLabel("Текущий язык:" if self.LANG == "RU" else "Current language:"))
        self.current_lang_label = QLabel(self.LANG)
        lang_layout.addWidget(self.current_lang_label)
        lang_layout.addWidget(self.lang_toggle_button)
        lang_layout.addStretch()
        layout.addWidget(lang_group)

        # Theme switch
        theme_group = QGroupBox("🎨 Тема / Theme")
        theme_layout = QHBoxLayout(theme_group)
        self.theme_label = QLabel("Текущая тема:" if self.LANG == "RU" else "Current theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["System", "Light", "Dark"])
        self.theme_combo.setCurrentText(self.theme)
        theme_layout.addWidget(self.theme_label)
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        layout.addWidget(theme_group)
        
    def setup_connections(self):
        """Setup signal connections"""
        self.connect_button.clicked.connect(self.connect_pico)
        self.disconnect_button.clicked.connect(self.disconnect_pico)
        self.refresh_ports_button.clicked.connect(self.refresh_com_ports)
        # Toolbar actions
        self.action_refresh.triggered.connect(self.refresh_com_ports)
        self.action_connect.triggered.connect(self.connect_pico)
        self.action_disconnect.triggered.connect(self.disconnect_pico)
        self.action_read.triggered.connect(self.read_nand)
        self.action_write.triggered.connect(self.write_nand)
        self.action_erase.triggered.connect(self.erase_nand)
        self.action_about.triggered.connect(self.show_about)
        
        self.read_button.clicked.connect(self.read_nand)
        self.write_button.clicked.connect(self.write_nand)
        self.erase_button.clicked.connect(self.erase_nand)
        
        self.pause_button.clicked.connect(self.on_pause_clicked)
        self.resume_button.clicked.connect(self.on_resume_clicked)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        
        self.load_dump_button.clicked.connect(self.select_dump)
        self.save_dump_button.clicked.connect(self.save_dump)
        
        self.compression_checkbox.stateChanged.connect(self.toggle_compression)
        self.blank_skip_checkbox.stateChanged.connect(self.toggle_blank_skip)
        self.power_check_button.clicked.connect(self.check_power_supply)
        self.lang_toggle_button.clicked.connect(self.toggle_language)
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        self.write_oob_checkbox.stateChanged.connect(self.on_write_oob_changed)
        
        # Populate COM ports
        self.refresh_com_ports()
        
    def refresh_com_ports(self):
        """Refresh available COM ports"""
        self.com_ports_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.com_ports_combo.addItems(ports)
        # Restore last selected port if present
        last_port = self.settings.value("last_com_port", "")
        if last_port and last_port in ports:
            self.com_ports_combo.setCurrentText(last_port)
        
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
            # Persist selected port
            self.settings.setValue("last_com_port", port)
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
            
        # Start operation, choose protocol based on OOB option
        op = "WRITE" if self.write_with_oob else "WRITE_NO_OOB"
        self.start_operation(op)
    
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
        
        # Start monitoring thread (pass dump path for all operations)
        dump_path = self.selected_dump
        self.operation_thread = OperationThread(self.ser, operation, dump_path=dump_path)
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
            # If READ completed, offer to open analyzer
            try:
                if getattr(self, 'operation_type', None) == "READ" and self.selected_dump:
                    reply = QMessageBox.question(
                        self,
                        "Dump Analyzer",
                        "Открыть дамп в анализаторе?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply == QMessageBox.StandardButton.Yes:
                        from main.gui.dump_analyzer import DumpAnalyzer
                        self.analyzer_window = DumpAnalyzer()
                        self.analyzer_window.show()
                        # Auto-load the dump we just saved
                        try:
                            self.analyzer_window.load_dump_from_path(self.selected_dump)
                        except Exception:
                            pass
            except Exception:
                pass
        else:
            self.log_message("Операция не удалась")
            QMessageBox.critical(self, "Ошибка", "Операция не удалась")
    
    def show_about(self):
        text = (
            "<b>Pico NAND Flasher</b><br>"
            "Современный GUI для чтения/записи/стирания NAND через Raspberry Pi Pico." 
            "<br>Поддержка тем, локализации RU/EN, паузы/отмены операции, и анализатора дампов."
        )
        QMessageBox.about(self, "About", text)
    
    def on_pause_clicked(self):
        """Pause the current operation"""
        self.is_paused = True
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b'PAUSE\n')
            except Exception:
                pass
        self.log_message("Операция приостановлена")
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(True)
    
    def on_resume_clicked(self):
        """Resume the paused operation"""
        self.is_paused = False
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(b'RESUME\n')
            except Exception:
                pass
        self.log_message("Операция возобновлена")
        self.pause_button.setEnabled(True)
        self.resume_button.setEnabled(False)
    
    def on_cancel_clicked(self):
        """Cancel the current operation"""
        if self.ser and self.ser.is_open:
            self.ser.write(b'CANCEL\n')
            
        self.is_cancelled = True
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

    def toggle_language(self):
        """Toggle UI language and reapply labels"""
        self.LANG = "EN" if self.LANG == "RU" else "RU"
        self.settings.setValue("language", self.LANG)
        self.current_lang_label.setText(self.LANG)
        # Update dynamic labels/buttons
        self.refresh_ports_button.setText(self.LANG_TEXT[self.LANG]["refresh_button"])
        self.connect_button.setText(self.LANG_TEXT[self.LANG]["connect_button"])
        self.disconnect_button.setText(self.LANG_TEXT[self.LANG]["disconnect_button"])
        self.read_button.setText(self.LANG_TEXT[self.LANG]["read_button"])
        self.write_button.setText(self.LANG_TEXT[self.LANG]["write_button"])
        self.erase_button.setText(self.LANG_TEXT[self.LANG]["erase_button"])
        self.pause_button.setText(self.LANG_TEXT[self.LANG]["pause_button"])
        self.resume_button.setText(self.LANG_TEXT[self.LANG]["resume_button"])
        self.cancel_button.setText(self.LANG_TEXT[self.LANG]["cancel_button"])
        self.load_dump_button.setText(self.LANG_TEXT[self.LANG]["load_dump_button"])
        self.save_dump_button.setText(self.LANG_TEXT[self.LANG]["save_dump_button"])
        self.dump_path_label.setText(self.LANG_TEXT[self.LANG]["no_dump"]) if not self.selected_dump else None
        self._apply_language_to_tabs()
        self.status_bar.showMessage(self.LANG_TEXT[self.LANG]["nand_status"] + self.nand_info["status"])
        # Update group titles by recreating main tab minimal texts
        # (For simplicity, leave static group titles as they don't change often)
        # Update theme group labels
        self.theme_label.setText("Текущая тема:" if self.LANG == "RU" else "Current theme:")
        self.lang_toggle_button.setText("EN" if self.LANG == "RU" else "RU")
        self.write_oob_checkbox.setText("Записывать OOB (spare)" if self.LANG == "RU" else "Write OOB (spare)")

    def _apply_language_to_tabs(self):
        """Set tab titles based on current language"""
        try:
            self.tabs.clear()
        except Exception:
            pass
        main_title = "Главная" if self.LANG == "RU" else "Main"
        self.tabs.addTab(self.main_tab, main_title)
        self.tabs.addTab(self.log_tab, self.LANG_TEXT[self.LANG]["log_tab"])
        self.tabs.addTab(self.settings_tab, self.LANG_TEXT[self.LANG]["settings_tab"])

    def on_theme_changed(self, value: str):
        """Apply selected theme"""
        self.theme = value
        self.settings.setValue("theme", self.theme)
        self.apply_theme()

    def apply_theme(self):
        """Apply theme palette (System/Light/Dark)."""
        app = QApplication.instance()
        if not app:
            return
        if self.theme == "System":
            # Reset to system defaults
            app.setStyle("Fusion")  # Fusion is consistent across OS; still keep palette default
            app.setPalette(app.style().standardPalette())
            return
        # Start with Fusion for better cross-platform consistency
        app.setStyle("Fusion")
        from PyQt6.QtGui import QPalette, QColor
        palette = QPalette()
        if self.theme == "Dark":
            # Dark palette
            palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
            palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(220, 220, 220))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(220, 220, 220))
            palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
            palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
            palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
        else:
            # Light palette (near default)
            palette = app.style().standardPalette()
        app.setPalette(palette)

    def load_settings(self):
        """Load persistent settings and apply basic ones (language/theme/last paths)."""
        # Language
        lang = self.settings.value("language", self.LANG)
        if lang in ("RU", "EN") and lang != self.LANG:
            self.LANG = lang
            # Reapply tabs & labels
            self._apply_language_to_tabs()
        # Theme
        theme = self.settings.value("theme", self.theme)
        if theme in ("System", "Light", "Dark"):
            self.theme = theme
            if hasattr(self, "theme_combo"):
                self.theme_combo.setCurrentText(self.theme)
        # Last dump path (used as initial path in dialogs)
        last_dump = self.settings.value("last_dump_path", "")
        if last_dump:
            self.selected_dump = last_dump
            self.dump_path_label.setText(f"{self.LANG_TEXT[self.LANG]['selected_dump']}{last_dump}")
        # Write with OOB option
        oob = self.settings.value("write_with_oob")
        if oob is not None:
            try:
                self.write_with_oob = bool(int(oob)) if isinstance(oob, str) else bool(oob)
            except Exception:
                self.write_with_oob = True
        if hasattr(self, 'write_oob_checkbox'):
            self.write_oob_checkbox.setChecked(self.write_with_oob)

    def closeEvent(self, event):
        """Persist window state on close."""
        try:
            self.settings.setValue("window_geometry", self.saveGeometry())
            self.settings.setValue("window_state", self.saveState())
        except Exception:
            pass
        super().closeEvent(event)

    def restore_window_state(self):
        """Restore window geometry/state if saved."""
        try:
            geom = self.settings.value("window_geometry")
            if geom is not None:
                self.restoreGeometry(geom)
            st = self.settings.value("window_state")
            if st is not None:
                self.restoreState(st)
        except Exception:
            pass
    
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
            # Persist last dump path
            self.settings.setValue("last_dump_path", file_path)
    
    def save_dump(self):
        """Save a dump file"""
        initial = self.settings.value("last_dump_path", "")
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Сохранить дамп как", 
            initial, 
            "Binary files (*.bin);;All files (*)"
        )
        
        if file_path:
            self.selected_dump = file_path
            self.dump_path_label.setText(f"{self.LANG_TEXT[self.LANG]['selected_dump']}{file_path}")
            self.log_message(f"Дамп будет сохранен в: {file_path}")
            self.settings.setValue("last_dump_path", file_path)
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
    
    def __init__(self, ser, operation_type, dump_path=None):
        super().__init__()
        self.ser = ser
        self.operation_type = operation_type
        self.dump_data = bytearray()
        self.dump_path = dump_path
        
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
                        
                        elif line == "READY_FOR_DATA" and self.operation_type == "WRITE":
                            # Stream dump file to Pico
                            if not self.dump_path:
                                self.status.emit("Нет файла дампа для записи")
                                self.ser.write(b'CANCEL\n')
                            else:
                                try:
                                    total_size = os.path.getsize(self.dump_path)
                                    sent = 0
                                    with open(self.dump_path, 'rb') as f:
                                        chunk = f.read(4096)
                                        while chunk:
                                            # Check for pause/cancel from GUI sending through serial is handled by Pico
                                            self.ser.write(chunk)
                                            sent += len(chunk)
                                            pct = int(sent * 100 / total_size) if total_size else 0
                                            self.progress.emit(min(pct, 99))
                                            chunk = f.read(4096)
                                    self.status.emit("Дамп отправлен на Pico")
                                except Exception as e:
                                    self.status.emit(f"Ошибка отправки дампа: {e}")
                                    self.ser.write(b'CANCEL\n')
                        
                        elif line == "PAUSED":
                            self.status.emit("Пауза на устройстве")
                        
                        elif line == "OPERATION_CANCELLED":
                            self.status.emit("Операция отменена устройством")
                            break
                        
                        elif line.startswith("POWER_WARNING:"):
                            power_warning = line.split(":", 1)[1]
                            self.power_warning.emit(power_warning)
                        
                        elif line == "OPERATION_COMPLETE":
                            success = True
                            # If this was a read operation, save the accumulated data
                            if self.operation_type == "READ" and self.dump_data and self.dump_path:
                                try:
                                    with open(self.dump_path, "wb") as f:
                                        f.write(self.dump_data)
                                    self.status.emit(f"Дамп сохранен в: {self.dump_path}")
                                except Exception as e:
                                    self.status.emit(f"Ошибка сохранения дампа: {e}")
                            
                            self.status.emit("Операция завершена успешно")
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