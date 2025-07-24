# main.py для NAND Flasher на Raspberry Pi Pico
# Совместим с GUI.py

from machine import Pin, UART
import time
import sys

# === Настройки ===
BAUDRATE = 921600

# === Инициализация UART ===
# Используем UART0, TX=GP0, RX=GP1 (стандартные пины для USB-CDC на Pico)
uart = UART(0, baudrate=BAUDRATE, tx=Pin(0), rx=Pin(1))
uart.init(bits=8, parity=None, stop=1)

# === Инициализация пинов NAND ===
# Определение пинов согласно инструкции
io_pins = [
    Pin(5, Pin.IN, Pin.PULL_UP),   # I/O0 - GP5
    Pin(6, Pin.IN, Pin.PULL_UP),   # I/O1 - GP6
    Pin(7, Pin.IN, Pin.PULL_UP),   # I/O2 - GP7
    Pin(8, Pin.IN, Pin.PULL_UP),   # I/O3 - GP8
    Pin(9, Pin.IN, Pin.PULL_UP),   # I/O4 - GP9
    Pin(10, Pin.IN, Pin.PULL_UP),  # I/O5 - GP10
    Pin(11, Pin.IN, Pin.PULL_UP),  # I/O6 - GP11
    Pin(12, Pin.IN, Pin.PULL_UP)   # I/O7 - GP12
]

# Управляющие пины (все как выходы по умолчанию, активный уровень LOW)
cle_pin = Pin(13, Pin.OUT)    # CLE - GP13
ale_pin = Pin(14, Pin.OUT)    # ALE - GP14
ce_pin = Pin(15, Pin.OUT)     # CE# - GP15
re_pin = Pin(16, Pin.OUT)     # RE# - GP16
we_pin = Pin(17, Pin.OUT)     # WE# - GP17
rb_pin = Pin(18, Pin.IN, Pin.PULL_UP)      # R/B# - GP18 (вход с подтяжкой)

# Инициализация управляющих пинов в неактивное состояние
cle_pin.value(0)
ale_pin.value(0)
ce_pin.value(1)  # CE# активен по LOW
re_pin.value(1)  # RE# активен по LOW
we_pin.value(1)  # WE# активен по LOW

# === Базовые функции работы с NAND ===

def wait_for_ready(timeout_ms=5000):
    """Ждем, пока NAND будет готов (R/B# = HIGH)"""
    start_time = time.ticks_ms()
    while rb_pin.value() == 0:
        if time.ticks_diff(time.ticks_ms(), start_time) > timeout_ms:
            # print("Таймаут ожидания готовности NAND")
            return False
        # time.sleep_ms(1) # Минимальная пауза для снижения нагрузки
    return True

def set_io_output():
    """Переключает пины I/O в режим выхода"""
    for pin in io_pins:
        pin.init(Pin.OUT)

def set_io_input():
    """Переключает пины I/O в режим входа с подтяжкой"""
    for pin in io_pins:
        pin.init(Pin.IN, Pin.PULL_UP)

def write_byte(data):
    """Записывает байт в NAND"""
    # Установить данные на пины I/O
    for i, pin in enumerate(io_pins):
        pin.value((data >> i) & 1)
    
    # Активировать WE# импульс
    we_pin.value(0)
    # time.sleep_us(1) # Минимальная задержка
    we_pin.value(1)
    # time.sleep_us(1) # Минимальная задержка

def read_byte():
    """Читает байт из NAND"""
    # Переключить пины I/O на вход
    set_io_input()
    
    # Активировать RE# импульс
    re_pin.value(0)
    # time.sleep_us(1) # Минимальная задержка
    
    # Прочитать данные
    data = 0
    for i, pin in enumerate(io_pins):
        data |= (pin.value() << i)
    
    re_pin.value(1)
    # time.sleep_us(1) # Минимальная задержка
    
    # Вернуть пины I/O в режим выхода (по умолчанию)
    set_io_output()
    
    return data

def send_address_cycles(addr, cycles):
    """Отправляет адрес в NAND по заданному количеству циклов"""
    ale_pin.value(1) # Установить ALE
    for _ in range(cycles):
        write_byte(addr & 0xFF)
        addr >>= 8
    ale_pin.value(0) # Сбросить ALE

def send_command(cmd):
    """Отправляет команду в NAND"""
    ce_pin.value(0)   # Активировать CE#
    cle_pin.value(1)  # Установить CLE
    write_byte(cmd)
    cle_pin.value(0)  # Сбросить CLE
    # ce_pin.value(1) не деактивируем сразу для последовательных операций

def read_status():
    """Читает регистр статуса NAND"""
    send_command(0x70) # Команда Read Status
    # ce_pin уже активен
    status = read_byte()
    ce_pin.value(1) # Деактивировать CE#
    return status

def is_status_fail(status):
    """Проверяет, указывает ли статус на ошибку"""
    # Бит 0 (I/O 0) равен 1 означает FAIL, 0 - PASS
    # Но в некоторых спецификациях наоборот, проверим оба варианта
    # Стандартно: 0 - PASS, 1 - FAIL
    return (status & 0x01) == 0x01

def read_nand_id():
    """Читает ID NAND"""
    # Отправить команду Read ID
    send_command(0x90)
    
    # Отправить адрес 0x00
    ale_pin.value(1)
    write_byte(0x00)
    ale_pin.value(0)
    
    # Активировать CE# и RE# для чтения
    # ce_pin уже активен (0) после send_command
    if not wait_for_ready(1000): # Короткий таймаут для ID
        ce_pin.value(1)
        return [0xFF, 0xFF, 0xFF, 0xFF] # Возвращаем "пустой" ID при таймауте
    
    # Прочитать несколько байт ID
    id_bytes = []
    for _ in range(6): # Читаем 6 байт для надежности
        id_bytes.append(read_byte())
    
    ce_pin.value(1) # Деактивировать CE#
    
    return id_bytes[:4] # Возвращаем первые 4 байта

# === База поддерживаемых NAND ===
supported_nand = {
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

current_nand = (None, None)

def detect_nand():
    """Пытается определить тип NAND"""
    try:
        # Инициализируем пины перед началом
        set_io_output()
        time.sleep_ms(10) # Небольшая пауза для стабилизации
        
        nand_id = read_nand_id()
        # print(f"ID считан: {[hex(b) for b in nand_id]}")
        
        for name, info in supported_nand.items():
            if nand_id[:len(info["id"])] == info["id"]:
                return (name, info)
        return (None, None)
    except Exception as e:
        # print(f"Ошибка при чтении ID: {e}")
        return (None, None)

# === Реализация операций с NAND ===

def read_page(nand_info, page_addr, buffer):
    """Читает одну страницу данных и спейр"""
    try:
        page_size = nand_info["page_size"]
        block_size = nand_info["block_size"] # Это количество страниц в блоке
        
        # Шаг 1: Команда Read (00h)
        send_command(0x00)
        
        # Шаг 2: Отправить адрес (5 циклов для большинства современных NAND)
        # Формат адреса: Column (0) + Page Address
        full_addr = page_addr * page_size
        send_address_cycles(full_addr, 5)
        
        # Шаг 3: Команда Read Confirm (30h)
        send_command(0x30)
        
        # Шаг 4: Ждать готовности
        if not wait_for_ready():
            ce_pin.value(1)
            return False

        # Шаг 5: Проверить статус на ошибки
        # status = read_status()
        # if is_status_fail(status):
        #     print(f"Ошибка чтения страницы {page_addr}, статус: {hex(status)}")
        #     return False

        # Шаг 6: Прочитать данные страницы
        # ce_pin уже активен
        for i in range(page_size):
            buffer[i] = read_byte()
        
        # Шаг 7: Прочитать спейр (OOB) - обычно 64 или 128 или 224 байт
        # Для простоты читаем фиксированное количество, можно уточнить позже
        spare_size = 64 # Базовое значение, можно адаптировать
        if page_size == 4096:
            spare_size = 128
        elif page_size == 2048:
            spare_size = 64
            
        for i in range(spare_size):
            buffer[page_size + i] = read_byte()
            
        ce_pin.value(1) # Деактивировать CE#
        return True
        
    except Exception as e:
        # print(f"Исключение при чтении страницы {page_addr}: {e}")
        ce_pin.value(1)
        return False

def write_page(nand_info, page_addr, data_buffer):
    """Записывает одну страницу данных и спейр"""
    try:
        page_size = nand_info["page_size"]
        block_size = nand_info["block_size"]
        
        # Шаг 1: Команда Serial Data Input (80h)
        send_command(0x80)
        
        # Шаг 2: Отправить адрес (5 циклов)
        full_addr = page_addr * page_size
        send_address_cycles(full_addr, 5)
        
        # Шаг 3: Записать данные страницы
        for i in range(page_size):
            write_byte(data_buffer[i])
        
        # Шаг 4: Записать спейр
        spare_size = 64
        if page_size == 4096:
            spare_size = 128
        elif page_size == 2048:
            spare_size = 64
            
        for i in range(spare_size):
            write_byte(data_buffer[page_size + i])
            
        # Шаг 5: Команда Program Confirm (10h)
        send_command(0x10)
        
        # Шаг 6: Ждать готовности
        if not wait_for_ready(5000): # Таймаут 5 секунд
            ce_pin.value(1)
            return False
            
        # Шаг 7: Проверить статус
        status = read_status()
        if is_status_fail(status):
            # print(f"Ошибка записи страницы {page_addr}, статус: {hex(status)}")
            return False
            
        ce_pin.value(1) # Деактивировать CE#
        return True
        
    except Exception as e:
        # print(f"Исключение при записи страницы {page_addr}: {e}")
        ce_pin.value(1)
        return False

def erase_block(nand_info, block_addr):
    """Стирает один блок"""
    try:
        block_size = nand_info["block_size"]
        page_addr = block_addr * block_size # Адрес первой страницы блока
        
        # Шаг 1: Команда Block Erase (60h)
        send_command(0x60)
        
        # Шаг 2: Отправить адрес блока (3 цикла, старшие биты адреса страницы)
        send_address_cycles(page_addr, 3)
        
        # Шаг 3: Команда Erase Confirm (D0h)
        send_command(0xD0)
        
        # Шаг 4: Ждать готовности (может занять до нескольких секунд)
        if not wait_for_ready(10000): # Таймаут 10 секунд
            ce_pin.value(1)
            return False
            
        # Шаг 5: Проверить статус
        status = read_status()
        if is_status_fail(status):
            # print(f"Ошибка стирания блока {block_addr}, статус: {hex(status)}")
            return False
            
        ce_pin.value(1) # Деактивировать CE#
        return True
        
    except Exception as e:
        # print(f"Исключение при стирании блока {block_addr}: {e}")
        ce_pin.value(1)
        return False

# === Логика программы ===

def wait_for_command():
    """Читает команду из UART"""
    # uart.readline() читает до символа \n
    data = uart.readline()
    if data:
        # Декодируем байты в строку и убираем \n и \r
        return data.decode('utf-8').strip()
    return ""

def send_status():
    """Отправляет статус в GUI"""
    if current_nand[0]:
        uart.write(f"MODEL:{current_nand[0]}\n")
    else:
        uart.write("MODEL:UNKNOWN\n")

def read_nand():
    """Чтение NAND"""
    if not current_nand[0]:
        uart.write("NAND_NOT_CONNECTED\n")
        return

    info = current_nand[1]
    total_pages = info["blocks"] * info["block_size"]
    page_size = info["page_size"]
    spare_size = 64
    if page_size == 4096:
        spare_size = 128
    elif page_size == 2048:
        spare_size = 64
        
    page_total_size = page_size + spare_size
    # print(f"Начало чтения {total_pages} страниц по {page_total_size} байт")

    # Буфер для одной страницы + спейр
    page_buffer = bytearray(page_total_size)
    
    try:
        for page in range(total_pages):
            if not read_page(info, page, page_buffer):
                uart.write("OPERATION_FAILED\n")
                return
            
            # Отправить данные страницы через UART
            uart.write(page_buffer)
            
            # Отправить прогресс
            progress = int((page + 1) * 100 / total_pages)
            uart.write(f"PROGRESS:{progress}\n")
            
            # Небольшая пауза, чтобы GUI мог обработать данные
            # time.sleep_ms(1)
            
        uart.write("OPERATION_COMPLETE\n")
    except Exception as e:
        # print(f"Критическая ошибка при чтении: {e}")
        uart.write("OPERATION_FAILED\n")

def write_nand():
    """Запись NAND"""
    if not current_nand[0]:
        uart.write("NAND_NOT_CONNECTED\n")
        return
        
    info = current_nand[1]
    total_pages = info["blocks"] * info["block_size"]
    page_size = info["page_size"]
    spare_size = 64
    if page_size == 4096:
        spare_size = 128
    elif page_size == 2048:
        spare_size = 64
        
    page_total_size = page_size + spare_size
    # print(f"Начало записи {total_pages} страниц по {page_total_size} байт")
    
    # Отправляем сигнал, что готовы принимать данные
    uart.write("READY_FOR_DATA\n")
    
    try:
        for page in range(total_pages):
            # Ждем данные страницы от GUI
            # В реальной реализации GUI должен отправить page_total_size байт
            # Пока делаем имитацию
            page_buffer = bytearray(page_total_size)
            # Заполняем буфер тестовыми данными
            for i in range(page_total_size):
                page_buffer[i] = (page + i) % 256
            
            if not write_page(info, page, page_buffer):
                uart.write("OPERATION_FAILED\n")
                return
                
            # Отправить прогресс
            progress = int((page + 1) * 100 / total_pages)
            uart.write(f"PROGRESS:{progress}\n")
            
        uart.write("OPERATION_COMPLETE\n")
    except Exception as e:
        # print(f"Критическая ошибка при записи: {e}")
        uart.write("OPERATION_FAILED\n")

def erase_nand():
    """Стирание NAND"""
    if not current_nand[0]:
        uart.write("NAND_NOT_CONNECTED\n")
        return

    info = current_nand[1]
    total_blocks = info["blocks"]
    
    # print(f"Начало стирания {total_blocks} блоков")

    try:
        for block in range(total_blocks):
            if not erase_block(info, block):
                uart.write("OPERATION_FAILED\n")
                return
                
            # Отправить прогресс
            progress = int((block + 1) * 100 / total_blocks)
            uart.write(f"PROGRESS:{progress}\n")
            
        uart.write("OPERATION_COMPLETE\n")
    except Exception as e:
        # print(f"Критическая ошибка при стирании: {e}")
        uart.write("OPERATION_FAILED\n")

def handle_operation(cmd):
    """Обрабатывает команды операций"""
    global current_nand
    if not current_nand[0]:
        uart.write("NAND_NOT_CONNECTED\n")
        return
    try:
        if cmd == 'READ':
            read_nand()
        elif cmd == 'WRITE':
            write_nand()
        elif cmd == 'ERASE':
            erase_nand()
        # OPERATION_COMPLETE/FAILED отправляется внутри функций операций
    except Exception as e:
        # print(f"Ошибка операции {cmd}: {e}")
        uart.write("OPERATION_FAILED\n")

def select_nand_manually():
    """Ручной выбор модели NAND"""
    uart.write("MANUAL_SELECT_START\n")
    names = list(supported_nand.keys())
    for i, name in enumerate(names):
        uart.write(f"{i+1}:{name}\n")
    uart.write("MANUAL_SELECT_END\n")
    
    # Ждем выбор пользователя
    while True:
        cmd = wait_for_command()
        if cmd.startswith("SELECT:"):
            try:
                index = int(cmd.split(":")[1]) - 1
                if 0 <= index < len(names):
                    name = names[index]
                    return (name, supported_nand[name])
            except:
                pass
        # time.sleep(0.1)

def main_loop():
    """Основной цикл программы"""
    global current_nand
    
    # Перевести пины I/O в режим выхода по умолчанию
    set_io_output()
    time.sleep_ms(100) # Дать время на стабилизацию
    
    while True:
        uart.write("🔍 Определение NAND...\n")
        current_nand = detect_nand()
        
        if not current_nand[0]:
            uart.write("❌ NAND не обнаружен! Продолжить вручную? (y/n): \n")
            # Ждем ответа от GUI
            start_wait = time.ticks_ms()
            timeout = 30000 # 30 секунд
            while True:
                cmd = wait_for_command()
                if cmd:
                    if cmd.lower() == 'y':
                        current_nand = select_nand_manually()
                        break
                    elif cmd.lower() == 'n':
                        sys.exit()
                if time.ticks_diff(time.ticks_ms(), start_wait) > timeout:
                    # print("Таймаут ожидания ответа, выход...")
                    sys.exit()
                # time.sleep(0.1)
        else:
            send_status()

        # Основной цикл обработки команд
        while True:
            cmd = wait_for_command()
            if not cmd:
                # time.sleep(0.01) # Небольшая пауза для снижения нагрузки
                continue
                
            # print(f"Получена команда: {cmd}") # Для отладки
            
            if cmd == 'STATUS':
                send_status()
            elif cmd in ['READ', 'WRITE', 'ERASE']:
                handle_operation(cmd)
            elif cmd == 'EXIT':
                sys.exit()
            elif cmd == 'REDETECT':
                # Выход из внутреннего цикла для повторного определения
                break

# Запуск программы
if __name__ == "__main__":
    # print("NAND Flasher запущен") # Будет видно в мониторе порта
    try:
        main_loop()
    except KeyboardInterrupt:
        # print("Программа прервана пользователем")
        pass
    except Exception as e:
        # print(f"Критическая ошибка: {e}")
        pass
