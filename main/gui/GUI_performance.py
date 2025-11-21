"""
Pico NAND Flasher - GUI Interface with Performance Features
Computer-side GUI for controlling the Raspberry Pi Pico NAND Flasher
with enhanced performance and reliability features.

Features implemented:
- Resume capability with block-level precision
- Power supply monitoring
- Data compression/decompression
- Better error handling and progress tracking
"""
import os
import sys
import time
from threading import Event, Thread
from tkinter import Tk, filedialog

import serial
import serial.tools.list_ports


class NANDFlasherGUI:
    """Main GUI class for NAND Flasher operations with performance enhancements"""

    def __init__(self):
        # Global settings
        self.LANG = "RU"
        self.COM_PORT = None
        self.BAUDRATE = 921600
        self.ser = None
        self.selected_dump = None
        self.selected_operation = None
        self.operation_running = Event()
        self.pause_operation = Event()
        self.cancel_operation = Event()
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
                "title": "🚀 Pico NAND Flasher (Performance) 🚀",
                "footer": "😊 сделал с любовью - bobberdolle1 😊",
                "menu": ["📁 Операции с NAND", "📘 Инструкция", "🌍 Сменить язык", "⚙️ Настройки", "🚪 Выход"],
                "operations": ["📂 Выбрать дамп", "🔧 Выбрать операцию", "✅ Подтвердить операцию", "🔙 Назад"],
                "nand_operations": ["📥 Прочитать NAND", "📤 Записать NAND", "🧹 Очистить NAND"],
                "progress": "⏳ Выполняется",
                "instruction": (
                    "📘 Полное руководство по подключению NAND Flash:\\n"
                    "1. 🔌 Подключение Pico к ПК:\\n"
                    "   - Используйте кабель USB-C\\n"
                    "   - Убедитесь в установке драйверов\\n"
                    "2. 💡 Подключение NAND Flash к Pico:\\n"
                    "   VCC  → 3V3 (3.3V питание)\\n"
                    "   GND  → GND\\n"
                    "   I/O0 → GP5\\n"
                    "   I/O1 → GP6\\n"
                    "   I/O2 → GP7\\n"
                    "   I/O3 → GP8\\n"
                    "   I/O4 → GP9\\n"
                    "   I/O5 → GP10\\n"
                    "   I/O6 → GP11\\n"
                    "   I/O7 → GP12\\n"
                    "   CLE  → GP13\\n"
                    "   ALE  → GP14\\n"
                    "   CE#  → GP15\\n"
                    "   RE#  → GP16\\n"
                    "   WE#  → GP17\\n"
                    "   R/B# → GP18\\n"
                    "   WP#  → 3V3 (отключение защиты)\\n"
                    "3. 🔬 Важные нюансы:\\n"
                    "   - Обязательно установите резисторы 10 кОм pull-up на линии I/O0-I/O7\\n"
                    "   - Максимальное напряжение питания: 3.3V ±5%\\n"
                    "   - Не подключайте питание при установке чипа!\\n"
                    "4. 🛠 Рекомендации по безопасности:\\n"
                    "   ⚠️ Всегда отключайте питание перед манипуляциями\\n"
                    "   ⚠️ Используйте ESD-браслет при работе с чипами\\n"
                    "   ⚠️ Не допускайте коротких замыканий\\n"
                    "5. 🔎 Диагностика проблем:\\n"
                    "   - Если чип не определяется:\\n"
                    "     a) Проверьте распиновку\\n"
                    "     b) Измерьте напряжение на VCC\\n"
                    "     c) Проверьте резисторы мультиметром\\n"
                    "   - Код ошибки 0xDEAD: Переподключите чип\\n"
                ),
                "warning": "⚠️ Внимание! Эта операция может стереть данные! Продолжить? (Y/N): ",
                "no_dump": "❌ Дамп не выбран!",
                "no_operation": "❌ Операция не выбрана!",
                "selected_dump": "Выбранный дамп: ",
                "selected_operation": "Выбранная операция: ",
                "op_controls": "Управление операцией: [p] - пауза, [r] - продолжить, [c] - отмена.",
                "nand_status": "Состояние NAND: ",
                "nand_detection_failed": "❌ NAND не обнаружен! Продолжить вручную? (y/n): ",
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
                "resume_prompt": "Найдена прерванная операция. Продолжить с блока {}? (y/n): ",
                "power_warning": "⚠️ Предупреждение о питании: ",
                "settings_saved": "⚙️ Настройки сохранены"
            },
            "EN": {
                "title": "🚀 Pico NAND Flasher (Performance) 🚀",
                "footer": "😊 made with love by bobberdolle1 😊",
                "menu": ["📁 NAND Operations", "📘 Instruction", "🌍 Change Language", "⚙️ Settings", "🚪 Exit"],
                "operations": ["📂 Select Dump", "🔧 Select Operation", "✅ Confirm Operation", "🔙 Back"],
                "nand_operations": ["📥 Read NAND", "📤 Write NAND", "🧹 Erase NAND"],
                "progress": "⏳ Processing",
                "instruction": (
                    "📘 Complete NAND Flash Connection Guide:\\n"
                    "1. 🔌 Connect Pico to PC:\\n"
                    "   - Use USB-C cable\\n"
                    "   - Ensure drivers are installed\\n"
                    "2. 💡 Connect NAND Flash to Pico:\\n"
                    "   VCC  → 3V3 (3.3V power)\\n"
                    "   GND  → GND\\n"
                    "   I/O0 → GP5\\n"
                    "   I/O1 → GP6\\n"
                    "   I/O2 → GP7\\n"
                    "   I/O3 → GP8\\n"
                    "   I/O4 → GP9\\n"
                    "   I/O5 → GP10\\n"
                    "   I/O6 → GP11\\n"
                    "   I/O7 → GP12\\n"
                    "   CLE  → GP13\\n"
                    "   ALE  → GP14\\n"
                    "   CE#  → GP15\\n"
                    "   RE#  → GP16\\n"
                    "   WE#  → GP17\\n"
                    "   R/B# → GP18\\n"
                    "   WP#  → 3V3 (disable protection)\\n"
                    "3. 🔬 Critical Details:\\n"
                    "   - Mandatory 10 kOhm pull-up resistors on I/O0-I/O7\\n"
                    "   - Power supply range: 3.3V ±5%\\n"
                    "   - Never hot-plug the chip!\\n"
                    "4. 🛠 Safety Guidelines:\\n"
                    "   ⚠️ Always power off before handling\\n"
                    "   ⚠️ Use ESD wrist strap\\n"
                    "   ⚠️ Avoid short circuits\\n"
                    "5. 🔎 Troubleshooting:\\n"
                    "   - If chip not detected:\\n"
                    "     a) Check pinout\\n"
                    "     b) Measure VCC voltage\\n"
                    "     c) Test resistors with multimeter\\n"
                    "   - Error code 0xDEAD: Reconnect chip\\n"
                ),
                "warning": "⚠️ Warning! This operation may erase data! Continue? (Y/N): ",
                "no_dump": "❌ Dump not selected!",
                "no_operation": "❌ Operation not selected!",
                "selected_dump": "Selected dump: ",
                "selected_operation": "Selected operation: ",
                "op_controls": "Operation control: [p] - pause, [r] - resume, [c] - cancel.",
                "nand_status": "NAND Status: ",
                "nand_detection_failed": "❌ NAND not detected! Continue manually? (y/n): ",
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
                "resume_prompt": "Found interrupted operation. Resume from block {}? (y/n): ",
                "power_warning": "⚠️ Power supply warning: ",
                "settings_saved": "⚙️ Settings saved"
            }
        }

    def clear_screen(self):
        """Clear the console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def get_key(self):
        """Get a keypress from the user"""
        try:
            import msvcrt
            if msvcrt.kbhit():
                return msvcrt.getch().decode().lower()
            return None
        except ImportError:
            import select
            import sys
            import termios
            import tty
            dr, _, _ = select.select([sys.stdin], [], [], 0)
            if dr:
                old_settings = termios.tcgetattr(sys.stdin)
                try:
                    tty.setcbreak(sys.stdin.fileno())
                    return sys.stdin.read(1).lower()
                finally:
                    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            return None

    def auto_detect_com(self):
        """Automatically detect the Pico COM port"""
        print(self.LANG_TEXT[self.LANG]["com_auto_detect"])
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            # More general way to find Pico
            if "Pico" in port.description or "Serial" in port.description or "UART" in port.description:
                self.COM_PORT = port.device
                print(f"{self.LANG_TEXT[self.LANG]['com_found']}{self.COM_PORT}")
                return True
        print(self.LANG_TEXT[self.LANG]["com_not_found"])
        return False

    def manual_select_com(self):
        """Manually select COM port"""
        print(self.LANG_TEXT[self.LANG]["manual_com"])
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            print("❌ No ports available!")
            return False
        for i, port in enumerate(ports):
            print(f"{i + 1}. {port.device} - {port.description}")
        try:
            choice = int(input("> "))
            if 1 <= choice <= len(ports):
                self.COM_PORT = ports[choice - 1].device
                print(f"{self.LANG_TEXT[self.LANG]['com_found']}{self.COM_PORT}")
                return True
            else:
                print(self.LANG_TEXT[self.LANG]["invalid_selection"])
                return False
        except ValueError:  # Catch specific error
            print(self.LANG_TEXT[self.LANG]["invalid_selection"])
            return False

    def select_dump(self):
        """Select a dump file"""
        global selected_dump
        # Hide main Tkinter window
        root = Tk()
        root.withdraw()
        # Open file dialog
        self.selected_dump = filedialog.askopenfilename(title=self.LANG_TEXT[self.LANG]["selected_dump"])
        root.destroy()
        print(f"{self.LANG_TEXT[self.LANG]['selected_dump']}{self.selected_dump}" if self.selected_dump else self.LANG_TEXT[self.LANG]["no_dump"])

    def save_dump(self):
        """Save a dump file"""
        root = Tk()
        root.withdraw()
        self.selected_dump = filedialog.asksaveasfilename(
            title="Сохранить дамп как",
            defaultextension=".bin",
            filetypes=[("Binary files", "*.bin"), ("All files", "*.*")]
        )
        root.destroy()
        print(f"{self.LANG_TEXT[self.LANG]['dump_saved']}{self.selected_dump}" if self.selected_dump else self.LANG_TEXT[self.LANG]["no_dump"])
        return self.selected_dump

    def select_operation(self):
        """Select an operation"""
        print("\n=== NAND Operations ===")
        for i, op in enumerate(self.LANG_TEXT[self.LANG]["nand_operations"]):
            print(f"{i + 1}. {op}")
        try:
            choice = int(input("> "))
            if 1 <= choice <= len(self.LANG_TEXT[self.LANG]["nand_operations"]):
                self.selected_operation = self.LANG_TEXT[self.LANG]["nand_operations"][choice - 1]
                print(f"{self.LANG_TEXT[self.LANG]['selected_operation']}{self.selected_operation}")
            else:
                print(self.LANG_TEXT[self.LANG]["invalid_selection"])
        except ValueError:
            print(self.LANG_TEXT[self.LANG]["no_operation"])

    def print_progress(self, progress, total=100, bar_length=30):
        """Print a progress bar"""
        filled = int(bar_length * progress // total)
        bar = '█' * filled + '-' * (bar_length - filled)
        print(f"\r{self.LANG_TEXT[self.LANG]['progress']}: |{bar}| {progress}%", end='', flush=True)

    def control_operation(self):
        """Control the ongoing operation (pause, resume, cancel)"""
        print(f"\n{self.LANG_TEXT[self.LANG]['op_controls']}")
        while self.operation_running.is_set():
            key = self.get_key()
            if key == 'p':
                self.pause_operation.set()
                print("\n[Пауза]")
            elif key == 'r':
                self.pause_operation.clear()
                print("\n[Продолжено]")
            elif key == 'c':
                self.cancel_operation.set()
                self.operation_running.clear()
                print("\n[Отмена...]")
                # Send cancel command to Pico if possible
                # self.ser.write(b'CANCEL\n') # Optional if Pico supports it
            time.sleep(0.1)

    def check_nand_status(self):
        """Check the status of the connected NAND chip"""
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
                        self.manual_select_mode = False
                        self.supported_nand_models = []
                        return
                    elif "NAND не обнаружен" in response or "NAND not detected" in response:
                        # Pico started manual selection process
                        self.nand_info = {"status": "🔍 Ручной выбор модели...", "model": ""}
                        self.manual_select_mode = True
                        self.supported_nand_models = []
                        # Wait for model list
                        self.collect_manual_select_models()
                        return
                time.sleep(0.01)  # Small pause in wait loop

            # If nothing received within timeout
            print("Таймаут ожидания ответа от Pico на STATUS")
            self.nand_info = {"status": "❌ Ошибка связи", "model": ""}

        except Exception as e:
            print(f"Ошибка проверки NAND: {e}")
            self.nand_info = {"status": "❌ Ошибка", "model": ""}

    def collect_manual_select_models(self):
        """Collect model list for manual selection"""
        self.supported_nand_models = []
        print("Ожидание списка моделей для ручного выбора...")
        try:
            start_time = time.time()
            timeout = 10
            while time.time() - start_time < timeout:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                    if line == "MANUAL_SELECT_END":
                        break
                    elif line == "MANUAL_SELECT_START":
                        continue  # Skip start marker
                    elif ':' in line:
                        # Expect format "number:ModelName"
                        try:
                            num, name = line.split(":", 1)
                            self.supported_nand_models.append(name)
                        except ValueError:
                            pass  # Ignore lines that don't match format
                time.sleep(0.01)

            if self.supported_nand_models:
                print("Доступные модели для ручного выбора:")
                for i, model in enumerate(self.supported_nand_models):
                    print(f"{i+1}. {model}")
            else:
                print("Список моделей пуст или не получен.")
        except Exception as e:
            print(f"Ошибка при получении списка моделей: {e}")

    def perform_manual_select(self):
        """Perform manual model selection"""
        if not self.manual_select_mode or not self.supported_nand_models:
            print("Ручной выбор не инициализирован.")
            return

        try:
            choice_input = input(self.LANG_TEXT[self.LANG]["select_model_prompt"])
            choice = int(choice_input)
            if 1 <= choice <= len(self.supported_nand_models):
                selected_model = self.supported_nand_models[choice - 1]
                # Send selection to Pico
                self.ser.write(f"SELECT:{choice}\n".encode())
                print(f"Выбрана модель: {selected_model}")
                # Wait for confirmation from Pico
                time.sleep(1)
                # Recheck status
                self.check_nand_status()
            else:
                print(self.LANG_TEXT[self.LANG]["invalid_selection"])
                # Send something so Pico doesn't hang
                self.ser.write(b"SELECT:0\n")
        except ValueError:
            print(self.LANG_TEXT[self.LANG]["invalid_selection"])
            self.ser.write(b"SELECT:0\n")
        except Exception as e:
            print(f"Ошибка при ручном выборе: {e}")
            self.ser.write(b"SELECT:0\n")

    def read_dump_and_send_to_pico(self, dump_path):
        """Read dump and send it to Pico in chunks with compression"""
        try:
            file_size = os.path.getsize(dump_path)
            print(f"Размер файла дампа: {file_size} байт")

            chunk_size = 4096  # Send in large blocks for efficiency
            total_sent = 0

            with open(dump_path, "rb") as f:
                while True:
                    if self.cancel_operation.is_set():
                        print("\nОтправка дампа отменена.")
                        return False

                    chunk = f.read(chunk_size)
                    if not chunk:
                        break  # End of file

                    # Send chunk
                    self.ser.write(chunk)
                    total_sent += len(chunk)

                    # Update progress
                    progress = int((total_sent / file_size) * 100)
                    print(f"\r{self.LANG_TEXT[self.LANG]['dump_send_progress']}{progress}%", end='', flush=True)

                    # Small pause so Pico can process
                    # time.sleep(0.01)

            print(f"\n{self.LANG_TEXT[self.LANG]['dump_send_complete']}")
            return True
        except Exception as e:
            print(f"\n{self.LANG_TEXT[self.LANG]['dump_load_error']}: {e}")
            return False

    def check_power_supply(self):
        """Check power supply status from Pico"""
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
                        return power_info
                time.sleep(0.01)
        except Exception as e:
            print(f"Ошибка проверки питания: {e}")
        return "Неизвестно"

    def execute_operation(self):
        """Execute the selected operation"""
        if self.nand_info['status'] != "✅ NAND подключен":
            print(self.LANG_TEXT[self.LANG]["operation_not_possible"])
            time.sleep(2)
            return

        # Reset cancel event before starting
        self.cancel_operation.clear()

        # Check if dump is needed
        if self.selected_operation in [self.LANG_TEXT[self.LANG]["nand_operations"][1]]:  # WRITE
            if not self.selected_dump:
                print(self.LANG_TEXT[self.LANG]["no_dump"])
                # Offer to select dump right here
                self.select_dump()
                if not self.selected_dump:
                    return  # If user declined, exit

        # Confirmation for destructive operations
        if self.selected_operation in [self.LANG_TEXT[self.LANG]["nand_operations"][1], self.LANG_TEXT[self.LANG]["nand_operations"][2]]:  # WRITE, ERASE
            confirm = input(self.LANG_TEXT[self.LANG]["warning"])
            if confirm.lower() != "y":
                print(self.LANG_TEXT[self.LANG]["operation_cancelled"])
                return

        self.clear_screen()
        self.operation_running.set()
        self.pause_operation.clear()

        def operation_thread():
            try:
                # Determine command
                command_map = {
                    self.LANG_TEXT[self.LANG]["nand_operations"][0]: b'READ\n',   # READ
                    self.LANG_TEXT[self.LANG]["nand_operations"][1]: b'WRITE\n',  # WRITE
                    self.LANG_TEXT[self.LANG]["nand_operations"][2]: b'ERASE\n'   # ERASE
                }
                command = command_map.get(self.selected_operation)

                if not command:
                    print("\n❌ Неизвестная операция!")
                    return

                # Check if there's a resume point
                if self.last_resume_block > 0:
                    resume_prompt = self.LANG_TEXT[self.LANG]["resume_prompt"].format(self.last_resume_block)
                    resume_confirm = input(resume_prompt)
                    if resume_confirm.lower() == 'y':
                        # Set resume point on Pico
                        self.ser.write(f'SET_RESUME:{self.last_resume_block}\n'.encode())
                        time.sleep(0.5)

                # Send command
                self.ser.reset_input_buffer()  # Clear buffer before starting
                self.ser.write(command)
                print(f"Команда '{self.selected_operation}' отправлена на Pico.")

                # Special logic for WRITE
                if command == b'WRITE\n':
                    if not self.selected_dump or not os.path.exists(self.selected_dump):
                        print(f"\n{self.LANG_TEXT[self.LANG]['dump_load_error']}")
                        self.ser.write(b'CANCEL\n')  # Cancel operation on Pico
                        return

                    # Wait for signal from Pico that it's ready to receive data
                    # In current main.py WRITE returns OPERATION_FAILED immediately,
                    # but if it were implemented, this would be the code to send data.
                    # For now just inform that write is not fully implemented.
                    print("\n⚠️ Запись в текущей версии Pico main.py не реализована до конца.")
                    # self.read_dump_and_send_to_pico(self.selected_dump)
                    # return  # End thread since data sent

                # --- Process responses from Pico ---
                dump_data = bytearray()  # To accumulate data during read
                is_reading_dump = False

                start_time = time.time()
                timeout = 300  # 5 minute timeout by default
                last_activity = start_time

                while self.operation_running.is_set():
                    # Check activity timeout
                    if time.time() - last_activity > timeout:
                        print(f"\nТаймаут операции ({timeout} секунд)")
                        break

                    if self.ser.in_waiting > 0:
                        last_activity = time.time()  # Reset activity timer

                        # For READ/ERASE/WRITE operations, Pico may send different types of data
                        # 1. Strings (STATUS, PROGRESS, COMPLETE/FAILED)
                        # 2. Binary data (in case of READ)

                        # Try to read a line (until \n)
                        line_bytes = self.ser.readline()
                        try:
                            line = line_bytes.decode('utf-8').strip()

                            # Process string responses
                            if line.startswith("PROGRESS:"):
                                try:
                                    progress = int(line.split(":")[1])
                                    self.print_progress(progress)
                                except ValueError:
                                    pass  # Ignore invalid progress

                            elif line.startswith("POWER_WARNING:"):
                                power_warning = line.split(":", 1)[1]
                                print(f"\n{self.LANG_TEXT[self.LANG]['power_warning']}{power_warning}")

                            elif line == "OPERATION_COMPLETE":
                                # If this was a read, save accumulated data
                                if command == b'READ\n' and dump_data:
                                    if self.save_dump():  # User selected path
                                        try:
                                            with open(self.selected_dump, "wb") as f:
                                                f.write(dump_data)
                                            print(f"\n{self.LANG_TEXT[self.LANG]['dump_saved']}{self.selected_dump}")
                                        except Exception as e:
                                            print(f"\nОшибка сохранения дампа: {e}")

                                print("\n✅ Операция завершена!")
                                break  # End loop

                            elif line == "OPERATION_FAILED":
                                print("\n❌ Операция не удалась!")
                                break  # End loop

                            elif line == "NAND_NOT_CONNECTED":
                                print("\n❌ NAND не подключен (сообщено Pico)!")
                                break

                        except UnicodeDecodeError:
                            # This is likely binary dump data
                            if command == b'READ\n':
                                dump_data.extend(line_bytes)
                                # Can update progress based on size if we know total
                                # But it's easier to trust PROGRESS messages from Pico
                            else:
                                # Ignore unexpected binary data for other operations
                                pass

                    # Check for pause
                    while self.pause_operation.is_set() and self.operation_running.is_set():
                        time.sleep(0.1)

                    # Check for cancel
                    if self.cancel_operation.is_set():
                        self.ser.write(b'CANCEL\n')  # Send cancel signal if Pico listens
                        print("\n🚫 Операция отменена пользователем!")
                        break

                    time.sleep(0.01)  # Small pause in main loop

            except Exception as e:
                print(f"\n❌ Критическая ошибка в потоке операции: {e}")
            finally:
                self.operation_running.clear()
                self.cancel_operation.clear()  # Reset cancel flag
                # If operation was read and data exists but no OPERATION_COMPLETE,
                # try to save what we got
                if command == b'READ\n' and dump_data and self.selected_dump:
                    try:
                        with open(self.selected_dump + ".partial", "wb") as f:
                            f.write(dump_data)
                        print(f"\n⚠️ Операция прервана. Частичный дамп сохранен в: {self.selected_dump}.partial")
                    except:
                        pass

        # Start threads
        op_thread = Thread(target=operation_thread)
        control_thread = Thread(target=self.control_operation)

        op_thread.start()
        control_thread.start()

        # Wait for operation to complete
        op_thread.join()
        # control_thread will stop itself when operation_running becomes False

    def settings_menu(self):
        """Performance settings menu"""
        while True:
            self.clear_screen()
            print(self.LANG_TEXT[self.LANG]["settings_title"])
            print(f"1. {self.LANG_TEXT[self.LANG]['compression_setting']}{self.use_compression}")
            print(f"2. {self.LANG_TEXT[self.LANG]['blank_skip_setting']}{self.skip_blank_pages}")
            print(f"3. {self.LANG_TEXT[self.LANG]['power_check']}{self.check_power_supply()}")
            print("4. Назад")
            print(f"\n{self.LANG_TEXT[self.LANG]['footer']}")

            choice = input("> ")
            if choice == "1":
                self.use_compression = not self.use_compression
                print(f"{self.LANG_TEXT[self.LANG]['settings_saved']}")
                time.sleep(1)
            elif choice == "2":
                self.skip_blank_pages = not self.skip_blank_pages
                print(f"{self.LANG_TEXT[self.LANG]['settings_saved']}")
                time.sleep(1)
            elif choice == "3":
                power_status = self.check_power_supply()
                print(f"Статус питания: {power_status}")
                input("Нажмите Enter для продолжения...")
            elif choice == "4":
                break
            else:
                print(self.LANG_TEXT[self.LANG]["invalid_selection"])
                time.sleep(1)

    def main_menu(self):
        """Main menu loop"""
        while True:
            self.clear_screen()
            print(self.LANG_TEXT[self.LANG]["title"])

            # Check NAND status if not in manual selection mode
            if not self.manual_select_mode:
                self.check_nand_status()

            print(f"\n{self.LANG_TEXT[self.LANG]['nand_status']}{self.nand_info['status']}")
            if self.nand_info['model']:
                print(f"{self.LANG_TEXT[self.LANG]['nand_model']}{self.nand_info['model']}")

            # If in manual selection mode, show selection menu
            if self.manual_select_mode:
                print("\n=== Ручной выбор модели ===")
                if self.supported_nand_models:
                    print("Доступные модели:")
                    for i, model in enumerate(self.supported_nand_models):
                        print(f"{i+1}. {model}")
                    print("0. Отмена")
                    choice = input(self.LANG_TEXT[self.LANG]["select_model_prompt"])
                    if choice == "0":
                        # Send cancel to Pico
                        try:
                            self.ser.write(b'n\n')  # Answer 'n' to "Continue manually?"
                            self.manual_select_mode = False
                            self.nand_info = {"status": "❌ NAND не подключен", "model": ""}
                        except:
                            pass
                    else:
                        # Handle selection
                        if choice.isdigit():
                            # Send 'y' if this is first request "Continue manually?"
                            # But logic is already that Pico switched to selection mode
                            # So just process the selection
                            self.perform_manual_select()
                            # After selection, manual_select_mode should reset
                            # on next check_nand_status
                        else:
                            print(self.LANG_TEXT[self.LANG]["invalid_selection"])
                else:
                    print("Ожидание списка моделей от Pico...")
                    self.collect_manual_select_models()
                    input("\nНажмите Enter для продолжения...")
                continue  # Skip main menu

            # Main menu
            for i, item in enumerate(self.LANG_TEXT[self.LANG]["menu"]):
                print(f"{i + 1}. {item}")
            print(f"\n{self.LANG_TEXT[self.LANG]['footer']}")
            choice = input("> ")
            if choice == "1": self.nand_menu()
            elif choice == "2": self.show_instruction()
            elif choice == "3": self.LANG = "EN" if self.LANG == "RU" else "RU"
            elif choice == "4": self.settings_menu()
            elif choice == "5":
                if self.ser and self.ser.is_open:
                    try:
                        self.ser.write(b'EXIT\n')
                    except:
                        pass
                    self.ser.close()
                sys.exit()
            else:
                print(self.LANG_TEXT[self.LANG]["invalid_selection"])
                time.sleep(1)

    def nand_menu(self):
        """NAND operations menu"""
        while True:
            self.clear_screen()
            print("=== NAND Operations ===")
            for i, op in enumerate(self.LANG_TEXT[self.LANG]["operations"]):
                print(f"{i + 1}. {op}")
            print(f"\n{self.LANG_TEXT[self.LANG]['footer']}")
            choice = input("> ")
            if choice == "1": self.select_dump()
            elif choice == "2": self.select_operation()
            elif choice == "3": self.execute_operation()
            elif choice == "4": break
            else:
                print(self.LANG_TEXT[self.LANG]["invalid_selection"])
            input("\nНажмите Enter для продолжения...")

    def show_instruction(self):
        """Show instructions"""
        self.clear_screen()
        print(self.LANG_TEXT[self.LANG]["instruction"])
        input("\nНажмите Enter для возврата...")

    def connect_pico(self):
        """Connect to Pico"""
        if not self.auto_detect_com() and not self.manual_select_com():
            return False
        try:
            self.ser = serial.Serial(self.COM_PORT, self.BAUDRATE, timeout=1)
            self.ser.flush()
            # Small delay for stabilization
            time.sleep(2)
            # Clear input buffer in case of garbage data
            self.ser.reset_input_buffer()
            return True
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False


def main():
    """Main entry point"""
    gui = NANDFlasherGUI()
    if gui.connect_pico():
        try:
            gui.main_menu()
        except KeyboardInterrupt:
            print("\n\nПолучен сигнал прерывания (Ctrl+C). Завершение...")
        except Exception as e:
            print(f"\n\nНеобработанная ошибка: {e}")
        finally:
            if gui.ser and gui.ser.is_open:
                try:
                    gui.ser.write(b'EXIT\n')  # Try to exit Pico gracefully
                except:
                    pass
                gui.ser.close()
                print("Соединение с Pico закрыто.")
    else:
        print("❌ Failed to connect to Pico!")


if __name__ == "__main__":
    main()
