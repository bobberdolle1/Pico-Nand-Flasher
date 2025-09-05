# GUI.py для NAND Flasher (доработанный)
import os
import sys
import time
import serial
import serial.tools.list_ports
from tkinter import Tk, filedialog
from threading import Event, Thread
import hashlib # Для проверки целостности (опционально)

# Глобальные настройки
LANG = "RU"
COM_PORT = None
BAUDRATE = 921600

# Константы для операций
SERIAL_TIMEOUT = 1
CONNECTION_RETRY_DELAY = 2
OPERATION_CHECK_INTERVAL = 0.1
RESPONSE_TIMEOUT = 30

# Статусы операций
STATUS_NAND_NOT_CONNECTED = "❌ NAND не подключен"
STATUS_NAND_CONNECTED = "✅ NAND подключен"
STATUS_NAND_DETECTED = "🔍 NAND обнаружен"

ser = None
selected_dump = None
selected_operation = None
operation_running = Event()
pause_operation = Event()
cancel_operation = Event() # Новое событие для отмены
nand_info = {"status": STATUS_NAND_NOT_CONNECTED, "model": ""}
manual_select_mode = False
supported_nand_models = [] # Для хранения списка моделей при ручном выборе

# Локализация
LANG_TEXT = {
    "RU": {
        "title": "🚀 Pico NAND Flasher 🚀",
        "footer": "😊 сделал с любовью - bobberdolle1 😊",
        "menu": ["📁 Операции с NAND", "📘 Инструкция", "🌍 Сменить язык", "🚪 Выход"],
        "operations": ["📂 Выбрать дамп", "🔧 Выбрать операцию", "✅ Подтвердить операцию", "🔙 Назад"],
        "nand_operations": ["📥 Прочитать NAND", "📤 Записать NAND", "🧹 Очистить NAND"],
        "progress": "⏳ Выполняется",
        "instruction": (
            "📘 Полное руководство по подключению NAND Flash:\n"
            "1. 🔌 Подключение Pico к ПК:\n"
            "   - Используйте кабель USB-C\n"
            "   - Убедитесь в установке драйверов\n"
            "2. 💡 Подключение NAND Flash к Pico:\n"
            "   VCC  → 3V3 (3.3V питание)\n"
            "   GND  → GND\n"
            "   I/O0 → GP5\n"
            "   I/O1 → GP6\n"
            "   I/O2 → GP7\n"
            "   I/O3 → GP8\n"
            "   I/O4 → GP9\n"
            "   I/O5 → GP10\n"
            "   I/O6 → GP11\n"
            "   I/O7 → GP12\n"
            "   CLE  → GP13\n"
            "   ALE  → GP14\n"
            "   CE#  → GP15\n"
            "   RE#  → GP16\n"
            "   WE#  → GP17\n"
            "   R/B# → GP18\n"
            "   WP#  → 3V3 (отключение защиты)\n"
            "3. 🔬 Важные нюансы:\n"
            "   - Обязательно установите резисторы 10 кОм pull-up на линии I/O0-I/O7\n"
            "   - Максимальное напряжение питания: 3.3V ±5%\n"
            "   - Не подключайте питание при установке чипа!\n"
            "4. 🛠 Рекомендации по безопасности:\n"
            "   ⚠️ Всегда отключайте питание перед манипуляциями\n"
            "   ⚠️ Используйте ESD-браслет при работе с чипами\n"
            "   ⚠️ Не допускайте коротких замыканий\n"
            "5. 🔎 Диагностика проблем:\n"
            "   - Если чип не определяется:\n"
            "     a) Проверьте распиновку\n"
            "     b) Измерьте напряжение на VCC\n"
            "     c) Проверьте резисторы мультиметром\n"
            "   - Код ошибки 0xDEAD: Переподключите чип\n"
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
        "select_model_prompt": "Введите номер модели: "
    },
    "EN": {
        "title": "🚀 Pico NAND Flasher 🚀",
        "footer": "😊 made with love by bobberdolle1 😊",
        "menu": ["📁 NAND Operations", "📘 Instruction", "🌍 Change Language", "🚪 Exit"],
        "operations": ["📂 Select Dump", "🔧 Select Operation", "✅ Confirm Operation", "🔙 Back"],
        "nand_operations": ["📥 Read NAND", "📤 Write NAND", "🧹 Erase NAND"],
        "progress": "⏳ Processing",
        "instruction": (
            "📘 Complete NAND Flash Connection Guide:\n"
            "1. 🔌 Connect Pico to PC:\n"
            "   - Use USB-C cable\n"
            "   - Ensure drivers are installed\n"
            "2. 💡 Connect NAND Flash to Pico:\n"
            "   VCC  → 3V3 (3.3V power)\n"
            "   GND  → GND\n"
            "   I/O0 → GP5\n"
            "   I/O1 → GP6\n"
            "   I/O2 → GP7\n"
            "   I/O3 → GP8\n"
            "   I/O4 → GP9\n"
            "   I/O5 → GP10\n"
            "   I/O6 → GP11\n"
            "   I/O7 → GP12\n"
            "   CLE  → GP13\n"
            "   ALE  → GP14\n"
            "   CE#  → GP15\n"
            "   RE#  → GP16\n"
            "   WE#  → GP17\n"
            "   R/B# → GP18\n"
            "   WP#  → 3V3 (disable protection)\n"
            "3. 🔬 Critical Details:\n"
            "   - Mandatory 10 kOhm pull-up resistors on I/O0-I/O7\n"
            "   - Power supply range: 3.3V ±5%\n"
            "   - Never hot-plug the chip!\n"
            "4. 🛠 Safety Guidelines:\n"
            "   ⚠️ Always power off before handling\n"
            "   ⚠️ Use ESD wrist strap\n"
            "   ⚠️ Avoid short circuits\n"
            "5. 🔎 Troubleshooting:\n"
            "   - If chip not detected:\n"
            "     a) Check pinout\n"
            "     b) Measure VCC voltage\n"
            "     c) Test resistors with multimeter\n"
            "   - Error code 0xDEAD: Reconnect chip\n"
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
        "select_model_prompt": "Enter model number: "
    }
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def safe_serial_write(data):
    """Безопасная запись в серийный порт"""
    try:
        if ser and ser.is_open:
            ser.write(data if isinstance(data, bytes) else data.encode())
            return True
    except (serial.SerialException, OSError) as e:
        print(f"❌ Serial write error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error during write: {e}")
    return False

def safe_serial_read(timeout=RESPONSE_TIMEOUT):
    """Безопасное чтение из серийного порта"""
    try:
        if ser and ser.is_open:
            ser.timeout = timeout
            response = ser.readline()
            if response:
                return response.decode('utf-8').strip()
    except (serial.SerialException, OSError) as e:
        print(f"❌ Serial read error: {e}")
    except UnicodeDecodeError as e:
        print(f"❌ Decode error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error during read: {e}")
    return ""

def get_key():
    try:
        import msvcrt
        if msvcrt.kbhit():
            return msvcrt.getch().decode().lower()
        return None
    except ImportError:
        import sys, select, tty, termios
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if dr:
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setcbreak(sys.stdin.fileno())
                return sys.stdin.read(1).lower()
            finally:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        return None

def auto_detect_com():
    global COM_PORT
    print(LANG_TEXT[LANG]["com_auto_detect"])
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        # Более общий способ поиска Pico
        if "Pico" in port.description or "Serial" in port.description or "UART" in port.description:
            COM_PORT = port.device
            print(f"{LANG_TEXT[LANG]['com_found']}{COM_PORT}")
            return True
    print(LANG_TEXT[LANG]["com_not_found"])
    return False

def manual_select_com():
    global COM_PORT
    print(LANG_TEXT[LANG]["manual_com"])
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("❌ No ports available!")
        return False
    for i, port in enumerate(ports):
        print(f"{i + 1}. {port.device} - {port.description}")
    try:
        choice = int(input("> "))
        if 1 <= choice <= len(ports):
            COM_PORT = ports[choice - 1].device
            print(f"{LANG_TEXT[LANG]['com_found']}{COM_PORT}")
            return True
        else:
            print(LANG_TEXT[LANG]["invalid_selection"])
            return False
    except ValueError: # Ловим конкретную ошибку
        print(LANG_TEXT[LANG]["invalid_selection"])
        return False

def select_dump():
    global selected_dump
    # Скрыть главное окно Tkinter
    root = Tk()
    root.withdraw()
    # Открыть диалог выбора файла
    selected_dump = filedialog.askopenfilename(title=LANG_TEXT[LANG]["selected_dump"])
    root.destroy() # Уничтожить корневое окно
    print(f"{LANG_TEXT[LANG]['selected_dump']}{selected_dump}" if selected_dump else LANG_TEXT[LANG]["no_dump"])

def save_dump():
    global selected_dump
    root = Tk()
    root.withdraw()
    selected_dump = filedialog.asksaveasfilename(title="Сохранить дамп как", defaultextension=".bin", filetypes=[("Binary files", "*.bin"), ("All files", "*.*")])
    root.destroy()
    print(f"{LANG_TEXT[LANG]['dump_saved']}{selected_dump}" if selected_dump else LANG_TEXT[LANG]["no_dump"])
    return selected_dump

def select_operation():
    global selected_operation
    print("\n=== NAND Operations ===")
    for i, op in enumerate(LANG_TEXT[LANG]["nand_operations"]):
        print(f"{i + 1}. {op}")
    try:
        choice = int(input("> "))
        if 1 <= choice <= len(LANG_TEXT[LANG]["nand_operations"]):
            selected_operation = LANG_TEXT[LANG]["nand_operations"][choice - 1]
            print(f"{LANG_TEXT[LANG]['selected_operation']}{selected_operation}")
        else:
             print(LANG_TEXT[LANG]["invalid_selection"])
    except ValueError:
        print(LANG_TEXT[LANG]["no_operation"])

def print_progress(progress, total=100, bar_length=30):
    filled = int(bar_length * progress // total)
    bar = '█' * filled + '-' * (bar_length - filled)
    print(f"\r{LANG_TEXT[LANG]['progress']}: |{bar}| {progress}%", end='', flush=True)

def control_operation():
    global cancel_operation
    print("\n" + LANG_TEXT[LANG]["op_controls"])
    while operation_running.is_set():
        key = get_key()
        if key == 'p': 
            pause_operation.set()
            print("\n[Пауза]")
        elif key == 'r': 
            pause_operation.clear()
            print("\n[Продолжено]")
        elif key == 'c': 
            cancel_operation.set()
            operation_running.clear()
            print("\n[Отмена...]")
            # Отправить команду отмены на Pico, если возможно
            # ser.write(b'CANCEL\n') # Опционально, если Pico поддерживает
        time.sleep(0.1)

def check_nand_status():
    global nand_info # <-- Добавьте эту строку
    try:
        ser.write(b'STATUS\n')
        time.sleep(0.5)
        response = ser.readline().decode().strip()
        if response.startswith("MODEL:"):
            nand_info = {"status": STATUS_NAND_CONNECTED, "model": response.split(":")[1]}
        else:
            nand_info = {"status": STATUS_NAND_NOT_CONNECTED, "model": ""}
    except Exception as e:
        print("Ошибка проверки NAND:", e)
    global manual_select_mode, supported_nand_models
    try:
        # Очистка буфера перед отправкой запроса
        ser.reset_input_buffer()
        ser.write(b'STATUS\n')
        # time.sleep(0.5) # Небольшая пауза
        
        start_time = time.time()
        timeout = 5 # 5 секунд таймаут
        while time.time() - start_time < timeout:
            if ser.in_waiting > 0:
                response = ser.readline().decode('utf-8', errors='ignore').strip()
                # print(f"Debug: Получен ответ от Pico: '{response}'") # Для отладки
                
                if response.startswith("MODEL:"):
                    model_name = response.split(":", 1)[1]
                    nand_info = {"status": "✅ NAND подключен", "model": model_name}
                    manual_select_mode = False
                    supported_nand_models = []
                    return
                elif "NAND не обнаружен" in response or "NAND not detected" in response:
                    # Pico начал процесс ручного выбора
                    nand_info = {"status": "🔍 Ручной выбор модели...", "model": ""}
                    manual_select_mode = True
                    supported_nand_models = []
                    # Ждем список моделей
                    collect_manual_select_models()
                    return
            time.sleep(0.01) # Небольшая пауза в цикле ожидания
            
        # Если за таймаут ничего не получено
        print("Таймаут ожидания ответа от Pico на STATUS")
        nand_info = {"status": "❌ Ошибка связи", "model": ""}
        
    except Exception as e:
        print("Ошибка проверки NAND:", e)
        nand_info = {"status": "❌ Ошибка", "model": ""}

def collect_manual_select_models():
    """Собирает список моделей для ручного выбора"""
    global supported_nand_models
    supported_nand_models = []
    print("Ожидание списка моделей для ручного выбора...")
    try:
        start_time = time.time()
        timeout = 10
        while time.time() - start_time < timeout:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line == "MANUAL_SELECT_END":
                    break
                elif line == "MANUAL_SELECT_START":
                    continue # Пропускаем начальный маркер
                elif ':' in line:
                    # Ожидаем формат "номер:НазваниеМодели"
                    try:
                        num, name = line.split(":", 1)
                        supported_nand_models.append(name)
                    except ValueError:
                        pass # Игнорируем строки, которые не соответствуют формату
            time.sleep(0.01)
            
        if supported_nand_models:
            print("Доступные модели для ручного выбора:")
            for i, model in enumerate(supported_nand_models):
                print(f"{i+1}. {model}")
        else:
            print("Список моделей пуст или не получен.")
    except Exception as e:
        print(f"Ошибка при получении списка моделей: {e}")

def perform_manual_select():
    """Выполняет ручной выбор модели"""
    global nand_info, manual_select_mode, supported_nand_models
    if not manual_select_mode or not supported_nand_models:
        print("Ручной выбор не инициализирован.")
        return

    try:
        choice_input = input(LANG_TEXT[LANG]["select_model_prompt"])
        choice = int(choice_input)
        if 1 <= choice <= len(supported_nand_models):
            selected_model = supported_nand_models[choice - 1]
            # Отправляем выбор на Pico
            ser.write(f"SELECT:{choice}\n".encode('utf-8'))
            print(f"Выбрана модель: {selected_model}")
            # Ждем подтверждения от Pico
            time.sleep(1)
            # Перепроверим статус
            check_nand_status()
        else:
            print(LANG_TEXT[LANG]["invalid_selection"])
            # Отправляем что-то, чтобы Pico не висел
            ser.write(b"SELECT:0\n") 
    except ValueError:
        print(LANG_TEXT[LANG]["invalid_selection"])
        ser.write(b"SELECT:0\n") 
    except Exception as e:
        print(f"Ошибка при ручном выборе: {e}")
        ser.write(b"SELECT:0\n") 

def read_dump_and_send_to_pico(dump_path):
    """Читает дамп и отправляет его на Pico по частям"""
    try:
        file_size = os.path.getsize(dump_path)
        print(f"Размер файла дампа: {file_size} байт")
        
        chunk_size = 4096 # Отправляем крупными блоками для эффективности
        total_sent = 0
        
        with open(dump_path, "rb") as f:
            while True:
                if cancel_operation.is_set():
                    print("\nОтправка дампа отменена.")
                    return False
                
                chunk = f.read(chunk_size)
                if not chunk:
                    break # Конец файла
                
                # Отправляем чанк
                ser.write(chunk)
                total_sent += len(chunk)
                
                # Обновляем прогресс отправки
                progress = int((total_sent / file_size) * 100)
                print(f"\r{LANG_TEXT[LANG]['dump_send_progress']}{progress}%", end='', flush=True)
                
                # Небольшая пауза, чтобы Pico успевал обрабатывать
                # time.sleep(0.01) 

        print(f"\n{LANG_TEXT[LANG]['dump_send_complete']}")
        return True
    except Exception as e:
        print(f"\n{LANG_TEXT[LANG]['dump_load_error']}: {e}")
        return False

def execute_operation():
    global selected_operation, selected_dump, cancel_operation
    if nand_info['status'] != "✅ NAND подключен":
        print(LANG_TEXT[LANG]["operation_not_possible"])
        time.sleep(2)
        return

    # Сброс события отмены перед началом
    cancel_operation.clear()

    # Проверка на необходимость дампа
    if selected_operation in [LANG_TEXT[LANG]["nand_operations"][1]]: # WRITE
        if not selected_dump:
            print(LANG_TEXT[LANG]["no_dump"])
            # Предложить выбрать дамп прямо здесь
            select_dump()
            if not selected_dump:
                 return # Если пользователь отказался, выходим

    # Подтверждение для разрушительных операций
    if selected_operation in [LANG_TEXT[LANG]["nand_operations"][1], LANG_TEXT[LANG]["nand_operations"][2]]: # WRITE, ERASE
        confirm = input(LANG_TEXT[LANG]["warning"])
        if confirm.lower() != "y":
            print(LANG_TEXT[LANG]["operation_cancelled"])
            return

    clear_screen()
    operation_running.set()
    pause_operation.clear()
    
    def operation_thread():
        global selected_dump, cancel_operation
        try:
            # Определение команды
            command_map = {
                LANG_TEXT[LANG]["nand_operations"][0]: b'READ\n',   # READ
                LANG_TEXT[LANG]["nand_operations"][1]: b'WRITE\n',  # WRITE
                LANG_TEXT[LANG]["nand_operations"][2]: b'ERASE\n'   # ERASE
            }
            command = command_map.get(selected_operation)

            if not command:
                print("\n❌ Неизвестная операция!")
                return

            # Отправка команды
            ser.reset_input_buffer() # Очистить буфер перед началом
            ser.write(command)
            print(f"Команда '{selected_operation}' отправлена на Pico.")

            # Специальная логика для WRITE
            if command == b'WRITE\n':
                if not selected_dump or not os.path.exists(selected_dump):
                    print(f"\n{LANG_TEXT[LANG]['dump_load_error']}")
                    ser.write(b'CANCEL\n') # Отменить операцию на Pico
                    return
                
                # Ждем сигнала от Pico, что он готов принять данные
                # В текущей реализации main.py WRITE возвращает OPERATION_FAILED сразу,
                # но если бы оно было реализовано, здесь был бы код для отправки данных.
                # Пока просто сообщаем, что запись не поддерживается полностью.
                print("\n⚠️ Запись в текущей версии Pico main.py не реализована до конца.")
                # read_dump_and_send_to_pico(selected_dump)
                # return # Завершаем поток, так как данные отправлены

            # --- Обработка ответов от Pico ---
            dump_data = bytearray() # Для накопления данных при чтении
            is_reading_dump = False
            
            start_time = time.time()
            timeout = 300  # 5 минут таймаут по умолчанию
            last_activity = start_time
            
            while operation_running.is_set():
                # Проверка таймаута активности
                if time.time() - last_activity > timeout:
                    print(f"\nТаймаут операции ({timeout} секунд)")
                    break

                if ser.in_waiting > 0:
                    last_activity = time.time() # Сброс таймера активности
                    
                    # Для операций READ/ERASE/WRITE Pico может отправлять разные типы данных
                    # 1. Строки (STATUS, PROGRESS, COMPLETE/FAILED)
                    # 2. Бинарные данные (в случае READ)
                    
                    # Попробуем прочитать строку (до \n)
                    line_bytes = ser.readline()
                    try:
                        line = line_bytes.decode('utf-8').strip()
                        
                        # Обработка строковых ответов
                        if line.startswith("PROGRESS:"):
                            try:
                                progress = int(line.split(":")[1])
                                print_progress(progress)
                            except ValueError:
                                pass # Игнорировать некорректный прогресс
                        
                        elif line == "OPERATION_COMPLETE":
                            # Если это было чтение, сохраним накопленные данные
                            if command == b'READ\n' and dump_data:
                                if save_dump(): # Пользователь выбрал путь
                                    try:
                                        with open(selected_dump, "wb") as f:
                                            f.write(dump_data)
                                        print(f"\n{LANG_TEXT[LANG]['dump_saved']}{selected_dump}")
                                    except Exception as e:
                                        print(f"\nОшибка сохранения дампа: {e}")
                            
                            print("\n✅ Операция завершена!")
                            break # Завершить цикл
                        
                        elif line == "OPERATION_FAILED":
                            print("\n❌ Операция не удалась!")
                            break # Завершить цикл
                        
                        elif line == "NAND_NOT_CONNECTED":
                            print("\n❌ NAND не подключен (сообщено Pico)!")
                            break
                        
                        # Если строка не распознана как команда, это могут быть данные
                        # Но для простоты будем считать, что основные данные - это байты
                        # которые не декодируются в utf-8 или не соответствуют формату.
                        # Поэтому проверим, не являются ли полученные байты данными дампа.
                        # В текущем main.py данные отправляются напрямую через uart.write(buffer),
                        # что означает, что они будут в буфере порта, а не в виде строк.
                        # Нужно переписать логику чтения.

                    except UnicodeDecodeError:
                        # Это, скорее всего, бинарные данные дампа
                        if command == b'READ\n':
                            dump_data.extend(line_bytes)
                            # Можно обновлять прогресс на основе размера, если знать общий
                            # Но проще довериться сообщениям PROGRESS от Pico
                        else:
                           # Игнорируем неожиданные бинарные данные для других операций
                           pass

                # Проверка паузы
                while pause_operation.is_set() and operation_running.is_set():
                    time.sleep(0.1)
                
                # Проверка отмены
                if cancel_operation.is_set():
                    ser.write(b'CANCEL\n') # Отправить сигнал отмены, если Pico слушает
                    print("\n🚫 Операция отменена пользователем!")
                    break
                    
                time.sleep(0.01) # Небольшая пауза в основном цикле

        except Exception as e:
            print(f"\n❌ Критическая ошибка в потоке операции: {e}")
        finally:
            operation_running.clear()
            cancel_operation.clear() # Сбросить флаг отмены
            # Если операция была чтением и данные есть, но не было OPERATION_COMPLETE,
            # попробуем сохранить то, что успели получить
            if command == b'READ\n' and dump_data and selected_dump:
                 try:
                     with open(selected_dump + ".partial", "wb") as f:
                         f.write(dump_data)
                     print(f"\n⚠️ Операция прервана. Частичный дамп сохранен в: {selected_dump}.partial")
                 except:
                     pass

    # Запуск потоков
    op_thread = Thread(target=operation_thread)
    control_thread = Thread(target=control_operation)
    
    op_thread.start()
    control_thread.start()
    
    # Ожидание завершения операции
    op_thread.join()
    # control_thread остановится сам, когда operation_running станет False

def main_menu():
    global LANG, manual_select_mode, nand_info
    while True:
        clear_screen()
        print(LANG_TEXT[LANG]["title"])
        
        # Проверка статуса NAND, если не в режиме ручного выбора
        if not manual_select_mode:
            check_nand_status()
        
        print(f"\n{LANG_TEXT[LANG]['nand_status']}{nand_info['status']}")
        if nand_info['model']: 
            print(f"{LANG_TEXT[LANG]['nand_model']}{nand_info['model']}")
        
        # Если в режиме ручного выбора, показываем меню выбора
        if manual_select_mode:
            print("\n=== Ручной выбор модели ===")
            if supported_nand_models:
                print("Доступные модели:")
                for i, model in enumerate(supported_nand_models):
                    print(f"{i+1}. {model}")
                print("0. Отмена")
                choice = input(LANG_TEXT[LANG]["select_model_prompt"])
                if choice == "0":
                    # Отправить отмену на Pico
                    try:
                        ser.write(b'n\n') # Ответ 'n' на запрос "Продолжить вручную?"
                        manual_select_mode = False
                        nand_info = {"status": "❌ NAND не подключен", "model": ""}
                    except:
                        pass
                else:
                    # Передаем управление функции ручного выбора
                    # Но сначала проверим, не является ли это числом
                    if choice.isdigit():
                         # Отправим 'y' если это первый запрос "Продолжить вручную?"
                         # Но логика уже в том, что Pico сам перешел в режим выбора
                         # Поэтому просто обработаем выбор
                         perform_manual_select()
                         # После выбора manual_select_mode должен сброситься
                         # при следующем check_nand_status
                    else:
                         print(LANG_TEXT[LANG]["invalid_selection"])
            else:
                print("Ожидание списка моделей от Pico...")
                collect_manual_select_models()
                input("\nНажмите Enter для продолжения...")
            continue # Пропустить основное меню
            
        # Основное меню
        for i, item in enumerate(LANG_TEXT[LANG]["menu"]):
            print(f"{i + 1}. {item}")
        print("\n" + LANG_TEXT[LANG]["footer"])
        choice = input("> ")
        if choice == "1": nand_menu()
        elif choice == "2": show_instruction()
        elif choice == "3": LANG = "EN" if LANG == "RU" else "RU"
        elif choice == "4": 
            if ser and ser.is_open:
                try:
                    ser.write(b'EXIT\n')
                except:
                    pass
                ser.close()
            sys.exit()
        else:
            print(LANG_TEXT[LANG]["invalid_selection"])
            time.sleep(1)

def nand_menu():
    while True:
        clear_screen()
        print("=== NAND Operations ===")
        for i, op in enumerate(LANG_TEXT[LANG]["operations"]):
            print(f"{i + 1}. {op}")
        print("\n" + LANG_TEXT[LANG]["footer"])
        choice = input("> ")
        if choice == "1": select_dump()
        elif choice == "2": select_operation()
        elif choice == "3": execute_operation()
        elif choice == "4": break
        else:
            print(LANG_TEXT[LANG]["invalid_selection"])
        input("\nНажмите Enter для продолжения...")

def show_instruction():
    clear_screen()
    print(LANG_TEXT[LANG]["instruction"])
    input("\nНажмите Enter для возврата...")

def connect_pico():
    """Подключение к Raspberry Pi Pico"""
    global ser
    if not auto_detect_com() and not manual_select_com():
        return False
    try:
        ser = serial.Serial(COM_PORT, BAUDRATE, timeout=SERIAL_TIMEOUT)
        ser.flush()
        # Небольшая пауза для стабилизации
        time.sleep(CONNECTION_RETRY_DELAY)
        # Очистка входного буфера на случай мусорных данных
        ser.reset_input_buffer()
        return True
    except serial.SerialException as e:
        print(f"❌ Serial connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected connection error: {e}")
        return False

if __name__ == "__main__":
    if connect_pico():
        try:
            main_menu()
        except KeyboardInterrupt:
            print("\n\nПолучен сигнал прерывания (Ctrl+C). Завершение...")
        except Exception as e:
            print(f"\n\nНеобработанная ошибка: {e}")
        finally:
            if ser and ser.is_open:
                try:
                    ser.write(b'EXIT\n') # Попытка корректного завершения на Pico
                except:
                    pass
                ser.close()
                print("Соединение с Pico закрыто.")
    else:
        print("❌ Failed to connect to Pico!")
