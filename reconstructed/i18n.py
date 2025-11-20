import json
import os
from typing import Dict, Any

class I18n:
    """
    Internationalization class for NAND Flasher
    Supports Russian and English languages
    """
    
    def __init__(self, default_lang: str = 'en'):
        self.current_lang = default_lang
        self.translations = {}
        self.load_translations()
    
    def load_translations(self):
        """Load translation files for all supported languages"""
        # Default English translations
        self.translations['en'] = {
            'title': 'NAND Flasher',
            'read_button': 'Read Flash',
            'write_button': 'Write Flash',
            'erase_button': 'Erase Flash',
            'select_file': 'Select File',
            'connect_button': 'Connect',
            'disconnect_button': 'Disconnect',
            'status_connected': 'Connected',
            'status_disconnected': 'Disconnected',
            'progress_reading': 'Reading...',
            'progress_writing': 'Writing...',
            'progress_erasing': 'Erasing...',
            'success_read': 'Read operation completed successfully',
            'success_write': 'Write operation completed successfully',
            'success_erase': 'Erase operation completed successfully',
            'error_connection': 'Connection error',
            'error_operation': 'Operation error',
            'file_size': 'File Size:',
            'flash_size': 'Flash Size:',
            'operation_complete': 'Operation Complete',
            'operation_failed': 'Operation Failed',
            'confirm_erase': 'Are you sure you want to erase the flash? This will permanently delete all data.',
            'yes': 'Yes',
            'no': 'No',
            'settings': 'Settings',
            'language': 'Language',
            'english': 'English',
            'russian': 'Russian',
            'about': 'About',
            'version': 'Version',
            'author': 'Author',
            'github': 'GitHub Repository',
            'save': 'Save',
            'cancel': 'Cancel',
            'file_saved': 'File saved successfully',
            'file_loaded': 'File loaded successfully',
            'error_file_access': 'File access error',
            'error_flash_access': 'Flash access error',
            'warning_large_file': 'Warning: File size is larger than flash capacity',
            'bytes': 'bytes',
            'kb': 'KB',
            'mb': 'MB',
            'gb': 'GB',
            'read_speed': 'Read Speed:',
            'write_speed': 'Write Speed:',
            'bytes_per_sec': 'bytes/sec',
            'estimated_time': 'Estimated Time:',
            'seconds': 'seconds',
            'minutes': 'minutes',
            'hours': 'hours',
            'no_ports_available': 'No ports available!',
            'com_auto_detect': '🔌 Auto-detecting COM port...',
            'com_found': '✅ Connected to ',
            'com_not_found': '❌ Pico not found!',
            'manual_com': '🖥 Select COM port manually:',
            'invalid_selection': '❌ Invalid selection!',
            'progress': '⏳ Processing',
            'selected_dump': 'Selected dump: ',
            'no_dump': '❌ Dump not selected!',
            'selected_operation': 'Selected operation: ',
            'no_operation': '❌ Operation not selected!',
            'op_controls': 'Operation control: [p] - pause, [r] - resume, [c] - cancel.',
            'nand_status': 'NAND Status: ',
            'nand_model': '📝 Model: ',
            'operation_cancelled': '🚫 Operation cancelled!',
            'dump_saved': '💾 Dump saved to: ',
            'dump_load_error': '❌ Error loading dump!',
            'dump_send_progress': '📤 Sending dump: ',
            'dump_send_complete': '✅ Dump sent.',
            'select_model_prompt': 'Enter model number: ',
            'operation_not_possible': '⚠️ Operation not possible: NAND not connected!',
            'nand_detection_failed': '❌ NAND not detected! Continue manually? (y/n): ',
            'warning': '⚠️ Warning! This operation may erase data! Continue? (Y/N): ',
            'title_cli': '🚀 Pico NAND Flasher 🚀',
            'footer': '😊 made with love by bobberdolle1 😊',
            'menu_operations': '📁 NAND Operations',
            'menu_instruction': '📘 Instruction',
            'menu_change_language': '🌍 Change Language',
            'menu_exit': '🚪 Exit',
            'operations_select_dump': '📂 Select Dump',
            'operations_select_operation': '🔧 Select Operation',
            'operations_confirm_operation': '✅ Confirm Operation',
            'operations_back': '🔙 Back',
            'nand_operations_read': '📥 Read NAND',
            'nand_operations_write': '📤 Write NAND',
            'nand_operations_erase': '🧹 Erase NAND',
            'pause': 'Pause',
            'resume': 'Resume',
            'cancel_operation': 'Cancel',
            'manual_selection': '🔍 Manual selection...',
            'timeout_waiting_response': 'Timeout waiting for response from Pico on STATUS',
            'error_checking_nand': 'Error checking NAND',
            'connection_error': '❌ Connection error',
            'error': '❌ Error',
            'unknown_operation': '❌ Unknown operation!',
            'command_sent': 'Command',
            'to_pico': 'to Pico',
            'write_not_implemented': '⚠️ Write is not fully implemented in the current Pico main.py version.',
            'operation_timeout': 'Operation timeout',
            'seconds': 'seconds',
            'operation_completed_successfully': '✅ Operation completed!',
            'error_saving_dump': 'Error saving dump',
            'operation_failed': '❌ Operation failed!',
            'nand_not_connected_pico': '❌ NAND not connected (reported by Pico)!',
            'operation_cancelled_by_user': '🚫 Operation cancelled by user!',
            'critical_error_in_operation_thread': '❌ Critical error in operation thread',
            'operation_interrupted_partial_saved': '⚠️ Operation interrupted. Partial dump saved to',
            'manual_model_selection': 'Manual model selection',
            'available_models': 'Available models',
            'waiting_for_models_from_pico': 'Waiting for models list from Pico...',
            'press_enter_to_continue': 'Press Enter to continue',
            'goodbye': 'Goodbye!',
            'menu': 'Menu',
            'instruction_manual': (
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
            )
        }
        
        # Russian translations
        self.translations['ru'] = {
            'title': 'NAND Flasher',
            'read_button': 'Прочитать Flash',
            'write_button': 'Записать Flash',
            'erase_button': 'Стереть Flash',
            'select_file': 'Выбрать файл',
            'connect_button': 'Подключить',
            'disconnect_button': 'Отключить',
            'status_connected': 'Подключено',
            'status_disconnected': 'Отключено',
            'progress_reading': 'Чтение...',
            'progress_writing': 'Запись...',
            'progress_erasing': 'Стирание...',
            'success_read': 'Операция чтения завершена успешно',
            'success_write': 'Операция записи завершена успешно',
            'success_erase': 'Операция стирания завершена успешно',
            'error_connection': 'Ошибка подключения',
            'error_operation': 'Ошибка операции',
            'file_size': 'Размер файла:',
            'flash_size': 'Размер Flash:',
            'operation_complete': 'Операция завершена',
            'operation_failed': 'Операция не удалась',
            'confirm_erase': 'Вы уверены, что хотите стереть flash? Это навсегда удалит все данные.',
            'yes': 'Да',
            'no': 'Нет',
            'settings': 'Настройки',
            'language': 'Язык',
            'english': 'Английский',
            'russian': 'Русский',
            'about': 'О программе',
            'version': 'Версия',
            'author': 'Автор',
            'github': 'Репозиторий GitHub',
            'save': 'Сохранить',
            'cancel': 'Отмена',
            'file_saved': 'Файл успешно сохранен',
            'file_loaded': 'Файл успешно загружен',
            'error_file_access': 'Ошибка доступа к файлу',
            'error_flash_access': 'Ошибка доступа к flash',
            'warning_large_file': 'Предупреждение: Размер файла больше, чем объем flash',
            'bytes': 'байт',
            'kb': 'КБ',
            'mb': 'МБ',
            'gb': 'ГБ',
            'read_speed': 'Скорость чтения:',
            'write_speed': 'Скорость записи:',
            'bytes_per_sec': 'байт/сек',
            'estimated_time': 'Расчетное время:',
            'seconds': 'секунд',
            'minutes': 'минут',
            'hours': 'часов',
            'no_ports_available': 'Нет доступных портов!',
            'com_auto_detect': '🔌 Автоопределение COM-порта...',
            'com_found': '✅ Подключено к ',
            'com_not_found': '❌ Pico не найден!',
            'manual_com': '🖥 Выберите COM-порт вручную:',
            'invalid_selection': '❌ Неверный выбор!',
            'progress': '⏳ Выполняется',
            'selected_dump': 'Выбранный дамп: ',
            'no_dump': '❌ Дамп не выбран!',
            'selected_operation': 'Выбранная операция: ',
            'no_operation': '❌ Операция не выбрана!',
            'op_controls': 'Управление операцией: [p] - пауза, [r] - продолжить, [c] - отмена.',
            'nand_status': 'Состояние NAND: ',
            'nand_model': '📝 Модель: ',
            'operation_cancelled': '🚫 Операция отменена!',
            'dump_saved': '💾 Дамп сохранен в: ',
            'dump_load_error': '❌ Ошибка загрузки дампа!',
            'dump_send_progress': '📤 Отправка дампа: ',
            'dump_send_complete': '✅ Дамп отправлен.',
            'select_model_prompt': 'Введите номер модели: ',
            'operation_not_possible': '⚠️ Невозможно выполнить операцию: NAND не подключен!',
            'nand_detection_failed': '❌ NAND не обнаружен! Продолжить вручную? (y/n): ',
            'warning': '⚠️ Внимание! Эта операция может стереть данные! Продолжить? (Y/N): ',
            'title_cli': '🚀 Pico NAND Flasher 🚀',
            'footer': '😊 сделал с любовью - bobberdolle1 😊',
            'menu_operations': '📁 Операции с NAND',
            'menu_instruction': '📘 Инструкция',
            'menu_change_language': '🌍 Сменить язык',
            'menu_exit': '🚪 Выход',
            'operations_select_dump': '📂 Выбрать дамп',
            'operations_select_operation': '🔧 Выбрать операцию',
            'operations_confirm_operation': '✅ Подтвердить операцию',
            'operations_back': '🔙 Назад',
            'nand_operations_read': '📥 Прочитать NAND',
            'nand_operations_write': '📤 Записать NAND',
            'nand_operations_erase': '🧹 Очистить NAND',
            'pause': 'Пауза',
            'resume': 'Продолжить',
            'cancel_operation': 'Отмена',
            'manual_selection': '🔍 Ручной выбор модели...',
            'timeout_waiting_response': 'Таймаут ожидания ответа от Pico на STATUS',
            'error_checking_nand': 'Ошибка проверки NAND',
            'connection_error': '❌ Ошибка связи',
            'error': '❌ Ошибка',
            'unknown_operation': '❌ Неизвестная операция!',
            'command_sent': 'Команда',
            'to_pico': 'на Pico',
            'write_not_implemented': '⚠️ Запись в текущей версии Pico main.py не реализована до конца.',
            'operation_timeout': 'Таймаут операции',
            'seconds': 'секунд',
            'operation_completed_successfully': '✅ Операция завершена!',
            'error_saving_dump': 'Ошибка сохранения дампа',
            'operation_failed': '❌ Операция не удалась!',
            'nand_not_connected_pico': '❌ NAND не подключен (сообщено Pico)!',
            'operation_cancelled_by_user': '🚫 Операция отменена пользователем!',
            'critical_error_in_operation_thread': '❌ Критическая ошибка в потоке операции',
            'operation_interrupted_partial_saved': '⚠️ Операция прервана. Частичный дамп сохранен в',
            'manual_model_selection': 'Ручной выбор модели',
            'available_models': 'Доступные модели',
            'waiting_for_models_from_pico': 'Ожидание списка моделей от Pico...',
            'press_enter_to_continue': 'Нажмите Enter для продолжения',
            'goodbye': 'До свидания!',
            'menu': 'Меню',
            'instruction_manual': (
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
            )
        }
    
    def set_language(self, lang: str):
        """Set the current language"""
        if lang in self.translations:
            self.current_lang = lang
    
    def t(self, key: str) -> str:
        """Get translated text for the current language"""
        if self.current_lang in self.translations:
            if key in self.translations[self.current_lang]:
                return self.translations[self.current_lang][key]
        
        # Fallback to English if translation not found
        if key in self.translations['en']:
            return self.translations['en'][key]
        
        # Return the key itself if no translation found
        return key
    
    def get_available_languages(self) -> list:
        """Get list of available languages"""
        return list(self.translations.keys())
    
    def get_language_name(self, lang_code: str) -> str:
        """Get display name for language code"""
        names = {
            'en': self.translations['en']['english'],
            'ru': self.translations['ru']['russian']
        }
        return names.get(lang_code, lang_code)

# Global instance for easy access
i18n = I18n()