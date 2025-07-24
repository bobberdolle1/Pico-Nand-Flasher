## **Pico NAND Flasher**

**NAND Flasher для Raspberry Pi Pico на MicroPython**

Этот проект позволяет использовать Raspberry Pi Pico в качестве программатора (флешера) для чтения, записи и стирания NAND Flash памяти. Он состоит из двух частей: скрипта `main.py`, который выполняется на самом Pico и управляет взаимодействием с NAND, и скрипта `GUI.py`, который запускается на компьютере и предоставляет пользовательский интерфейс.

---

## **Содержание**

- [О проекте](#о-проекте)
- [Аппаратное обеспечение](#аппаратное-обеспечение)
- [Установка](#установка)
- [Использование](#использование)
- [Поддерживаемые чипы](#поддерживаемые-чипы)
- [Возможные проблемы](#возможные-проблемы)
- [Лицензия](#лицензия)

---

## **О проекте**

Этот инструмент предназначен для работы с различными NAND Flash чипами через интерфейс GPIO Raspberry Pi Pico. Он поддерживает основные операции: чтение (создание дампа), запись (прошивка из дампа) и стирание (очистка) памяти NAND.

---

## **Аппаратное обеспечение**

- **Raspberry Pi Pico** с установленной прошивкой MicroPython.
- **NAND Flash чип** (поддерживаются различные модели, см. список).
- **Резисторы 10 кОм** (8 штук) для подтяжки линий данных I/O0-I/O7.
- **Провода/монтажная плата** для подключения.

### **Схема подключения**

| NAND Pin | Pico GPIO | Назначение          |
| :------- | :-------- | :------------------ |
| VCC      | 3V3       | Питание (3.3V)      |
| GND      | GND       | Общий провод        |
| I/O0     | GP5       | Линия данных 0      |
| I/O1     | GP6       | Линия данных 1      |
| I/O2     | GP7       | Линия данных 2      |
| I/O3     | GP8       | Линия данных 3      |
| I/O4     | GP9       | Линия данных 4      |
| I/O5     | GP10      | Линия данных 5      |
| I/O6     | GP11      | Линия данных 6      |
| I/O7     | GP12      | Линия данных 7      |
| CLE      | GP13      | Latch Enable        |
| ALE      | GP14      | Address Latch Enable|
| CE#      | GP15      | Chip Enable         |
| RE#      | GP16      | Read Enable         |
| WE#      | GP17      | Write Enable        |
| R/B#     | GP18      | Ready/Busy          |
| WP#      | 3V3       | Write Protect       |

**Важно:** Установите резисторы 10 кОм между каждой линией I/O (I/O0-I/I7) и пином 3V3 на Pico для обеспечения правильного уровня логической "1" при отсутствии сигнала.

---

## **Установка**

### **1. Прошивка Pico**

1. Скачайте последнюю версию [MicroPython для RP2040](https://micropython.org/download/rp2-pico/).
2. Зажмите кнопку **BOOTSEL** на Pico и подключите его к компьютеру по USB.
3. Скопируйте скачанный `.uf2` файл в появившийся USB-накопитель `RPI-RP2`.

### **2. Загрузка скрипта на Pico**

1. Откройте `main.py` в редакторе (например, Thonny).
2. Подключитесь к Pico через Thonny.
3. Сохраните `main.py` **на самом Pico** (File -> Save As -> MicroPython Device).

### **3. Установка зависимостей на компьютер**

Убедитесь, что на вашем компьютере установлен Python 3, затем выполните:

```bash
pip install pyserial tkinter
```

(`tkinter` обычно входит в стандартную библиотеку Python, но может потребоваться установка отдельно в Linux: `sudo apt install python3-tk`)

### **4. Подготовка GUI**

1. Сохраните файл `GUI.py` в любую папку на вашем компьютере.

---

## **Использование**

1. Подключите NAND Flash к Pico согласно схеме.
2. Подключите Pico к компьютеру по USB.
3. Запустите графический интерфейс:
   ```bash
   python GUI.py
   ```
4. Программа автоматически попытается найти и подключиться к Pico. Если это не удается, будет предложено выбрать COM-порт вручную.
5. Программа попытается автоматически определить тип подключенного NAND чипа.
6. Если определение не удалось, можно выбрать модель вручную из списка.
7. Выберите нужную операцию:
   - **Чтение NAND**: Создаст дамп содержимого NAND в указанный файл.
   - **Запись NAND**: Запишет содержимое выбранного дамп-файла в NAND (все данные будут стерты!).
   - **Очистка NAND**: Полностью сотрет NAND (все байты установятся в 0xFF).

---

## **Поддерживаемые чипы**

Программа поддерживает множество популярных NAND Flash чипов:

- **Samsung:** K9F1G08U0A, K9F2G08U0A, K9F4G08U0A, K9GAG08U0M, K9T1G08U0M и др.
- **Micron:** MT29F4G08ABA, MT29F8G08ABACA и др.
- **Hynix:** HY27US08281A, HY27UF082G2B, H27UBG8T2A, H27U4G8F2D и др.
- **Toshiba:** TC58NVG2S3E, TC58NVG3S0F и др.
- **Intel, SanDisk** и другие.

Полный список см. в словаре `supported_nand_db` в файле `main.py`.

---

## **Возможные проблемы**

- **"Ошибка подключения"**: Проверьте USB-кабель, попробуйте другой порт. Убедитесь, что на Pico установлена прошивка MicroPython.
- **"NAND не обнаружен"**: Проверьте правильность подключения по схеме. Убедитесь, что установлены все 8 резисторов 10 кОм. Проверьте напряжение питания (3.3V).
- **Некорректные данные**: Убедитесь, что выбрана правильная модель NAND. Попробуйте временно понизить `BAUDRATE` в скриптах.
- **Зависания**: Убедитесь, что пин `WP#` NAND подключен к `3V3` на Pico (защита записи отключена).

---

## **Лицензия**

Этот проект распространяется "как есть", без каких-либо гарантий. Используйте на свой страх и риск. Перед выполнением любых операций с NAND рекомендуется сделать резервную копию данных.

---

---

## **Pico NAND Flasher**

**NAND Flasher for Raspberry Pi Pico using MicroPython**

This project allows you to use a Raspberry Pi Pico as a programmer (flasher) to read, write, and erase NAND Flash memory. It consists of two parts: the `main.py` script that runs on the Pico itself and controls the interaction with the NAND, and the `GUI.py` script that runs on a computer and provides the user interface.

---

## **Table of Contents**

- [About](#about)
- [Hardware](#hardware)
- [Installation](#installation)
- [Usage](#usage)
- [Supported Chips](#supported-chips)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## **About**

This tool is designed to work with various NAND Flash chips via the GPIO interface of the Raspberry Pi Pico. It supports the basic operations of reading (creating a dump), writing (flashing from a dump), and erasing (clearing) NAND memory.

---

## **Hardware**

- **Raspberry Pi Pico** with MicroPython firmware installed.
- **NAND Flash chip** (various models are supported, see the list).
- **10 kOhm resistors** (8 pcs) for pull-up on data lines I/O0-I/O7.
- **Wires/breadboard** for connections.

### **Wiring Diagram**

| NAND Pin | Pico GPIO | Function            |
| :------- | :-------- | :------------------ |
| VCC      | 3V3       | Power (3.3V)        |
| GND      | GND       | Ground              |
| I/O0     | GP5       | Data Line 0         |
| I/O1     | GP6       | Data Line 1         |
| I/O2     | GP7       | Data Line 2         |
| I/O3     | GP8       | Data Line 3         |
| I/O4     | GP9       | Data Line 4         |
| I/O5     | GP10      | Data Line 5         |
| I/O6     | GP11      | Data Line 6         |
| I/O7     | GP12      | Data Line 7         |
| CLE      | GP13      | Command Latch Enable|
| ALE      | GP14      | Address Latch Enable|
| CE#      | GP15      | Chip Enable         |
| RE#      | GP16      | Read Enable         |
| WE#      | GP17      | Write Enable        |
| R/B#     | GP18      | Ready/Busy          |
| WP#      | 3V3       | Write Protect       |

**Important:** Install 10 kOhm pull-up resistors between each I/O line (I/O0-I/O7) and the Pico's 3V3 pin to ensure a proper logic "1" level when the signal is not driven.

---

## **Installation**

### **1. Flashing the Pico**

1. Download the latest [MicroPython for RP2040](https://micropython.org/download/rp2-pico/).
2. Hold down the **BOOTSEL** button on the Pico and plug it into your computer via USB.
3. Copy the downloaded `.uf2` file to the appearing USB drive `RPI-RP2`.

### **2. Uploading the Script to Pico**

1. Open `main.py` in an editor (e.g., Thonny).
2. Connect to the Pico via Thonny.
3. Save `main.py` **to the Pico itself** (File -> Save As -> MicroPython Device).

### **3. Installing Dependencies on Computer**

Make sure Python 3 is installed on your computer, then run:

```bash
pip install pyserial tkinter
```

(`tkinter` is usually included in the standard Python library but might need separate installation on Linux: `sudo apt install python3-tk`)

### **4. Preparing the GUI**

1. Save the `GUI.py` file to any folder on your computer.

---

## **Usage**

1. Connect the NAND Flash to the Pico according to the wiring diagram.
2. Connect the Pico to your computer via USB.
3. Run the graphical interface:
   ```bash
   python GUI.py
   ```
4. The program will automatically try to find and connect to the Pico. If it fails, you will be prompted to select the COM port manually.
5. The program will attempt to automatically detect the type of the connected NAND chip.
6. If detection fails, you can manually select the model from the list.
7. Select the desired operation:
   - **Read NAND**: Creates a dump of the NAND contents to a specified file.
   - **Write NAND**: Writes the contents of the selected dump file to the NAND (all data will be erased!).
   - **Erase NAND**: Completely erases the NAND (all bytes will be set to 0xFF).

---

## **Supported Chips**

The program supports many popular NAND Flash chips:

- **Samsung:** K9F1G08U0A, K9F2G08U0A, K9F4G08U0A, K9GAG08U0M, K9T1G08U0M, etc.
- **Micron:** MT29F4G08ABA, MT29F8G08ABACA, etc.
- **Hynix:** HY27US08281A, HY27UF082G2B, H27UBG8T2A, H27U4G8F2D, etc.
- **Toshiba:** TC58NVG2S3E, TC58NVG3S0F, etc.
- **Intel, SanDisk** and others.

See the `supported_nand_db` dictionary in `main.py` for the full list.

---

## **Troubleshooting**

- **"Connection Error"**: Check the USB cable, try a different port. Make sure MicroPython firmware is installed on the Pico.
- **"NAND not detected"**: Double-check the wiring diagram. Ensure all 8 10 kOhm resistors are installed. Check the power supply voltage (3.3V).
- **Incorrect data**: Make sure the correct NAND model is selected. Try temporarily lowering the `BAUDRATE` in the scripts.
- **Hangs**: Ensure the NAND's `WP#` pin is connected to `3V3` on the Pico (write protection is disabled).

---

## **License**

This project is provided "as is," without any warranties. Use at your own risk. It is recommended to back up data before performing any operations on the NAND.
