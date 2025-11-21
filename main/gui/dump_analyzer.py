"""
Dump Analyzer for Pico NAND Flasher
Provides tools for analyzing NAND flash dumps including hex view, string extraction, and statistics
"""

import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIntValidator
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.config.settings import config_manager
from src.utils.ecc import verify_and_correct


class DumpAnalyzer(QMainWindow):
    """Dump analysis tool for NAND flash dumps"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔍 Pico NAND Flash Dump Analyzer")
        self.setGeometry(100, 100, 1200, 800)

        self.dump_data = None
        self.dump_path = None
        self.second_dump_data = None
        self.second_dump_path = None
        # NAND layout defaults
        self.page_size = 2048
        self.spare_size = 64
        self.show_oob = False
        self.show_badblocks = True
        self.show_ecc = True
        self._last_bad_blocks = []
        self._ecc_error_pages = set()
        self._ecc_error_pages_detail = {}

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Create tabs
        self.tabs = QTabWidget()

        # Hex view tab
        self.hex_tab = QWidget()
        self.setup_hex_tab()

        # Strings tab
        self.strings_tab = QWidget()
        self.setup_strings_tab()

        # Statistics tab
        self.stats_tab = QWidget()
        self.setup_stats_tab()

        # Add tabs
        self.tabs.addTab(self.hex_tab, "Шестнадцатеричный вид")
        self.tabs.addTab(self.strings_tab, "Строки")
        self.tabs.addTab(self.stats_tab, "Статистика")

        main_layout.addWidget(self.tabs)

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")

        open_action = file_menu.addAction("Открыть дамп")
        open_action.triggered.connect(self.open_dump)
        open2_action = file_menu.addAction("Открыть второй дамп (для diff)")
        open2_action.triggered.connect(self.open_second_dump)

        # Status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Готов")

    def setup_hex_tab(self):
        """Setup the hex view tab"""
        layout = QVBoxLayout(self.hex_tab)

        # Controls
        controls_layout = QHBoxLayout()

        self.addr_label = QLabel("Адрес (HEX):")
        self.addr_input = QLineEdit()
        self.addr_input.setValidator(QIntValidator(0, 0xFFFFFFFF))
        self.addr_input.setText("0")

        self.size_label = QLabel("Размер (HEX):")
        self.size_input = QLineEdit()
        self.size_input.setValidator(QIntValidator(0, 0xFFFFFFFF))
        self.size_input.setText("256")

        # NAND geometry
        self.page_label = QLabel("Page size:")
        self.page_input = QLineEdit()
        self.page_input.setValidator(QIntValidator(512, 8192))
        self.page_input.setText(str(self.page_size))
        self.spare_label = QLabel("Spare size:")
        self.spare_input = QLineEdit()
        self.spare_input.setValidator(QIntValidator(16, 1024))
        self.spare_input.setText(str(self.spare_size))
        self.oob_checkbox = QCheckBox("Показывать OOB")
        self.oob_checkbox.setChecked(self.show_oob)
        self.oob_checkbox.stateChanged.connect(self.on_toggle_oob)
        self.badblock_checkbox = QCheckBox("Показывать bad-block")
        self.badblock_checkbox.setChecked(self.show_badblocks)
        self.badblock_checkbox.stateChanged.connect(self.on_toggle_badblocks)
        self.ecc_checkbox = QCheckBox("Показывать ECC")
        self.ecc_checkbox.setChecked(self.show_ecc)
        self.ecc_checkbox.stateChanged.connect(self.on_toggle_ecc)

        self.refresh_hex_btn = QPushButton("Обновить")
        self.refresh_hex_btn.clicked.connect(self.refresh_hex_view)
        self.scan_bad_blocks_btn = QPushButton("Сканировать bad-block")
        self.scan_bad_blocks_btn.clicked.connect(self.scan_bad_blocks)

        controls_layout.addWidget(self.addr_label)
        controls_layout.addWidget(self.addr_input)
        controls_layout.addWidget(self.size_label)
        controls_layout.addWidget(self.size_input)
        controls_layout.addWidget(self.page_label)
        controls_layout.addWidget(self.page_input)
        controls_layout.addWidget(self.spare_label)
        controls_layout.addWidget(self.spare_input)
        controls_layout.addWidget(self.oob_checkbox)
        controls_layout.addWidget(self.badblock_checkbox)
        controls_layout.addWidget(self.ecc_checkbox)
        controls_layout.addWidget(self.refresh_hex_btn)
        controls_layout.addWidget(self.scan_bad_blocks_btn)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Hex view
        self.hex_view = QTextEdit()
        self.hex_view.setReadOnly(True)
        self.hex_view.setFont(QFont("Courier New", 10))

        layout.addWidget(self.hex_view)

    def setup_strings_tab(self):
        """Setup the strings view tab"""
        layout = QVBoxLayout(self.strings_tab)

        # Controls
        controls_layout = QHBoxLayout()

        self.min_string_length = QLabel("Мин. длина строки:")
        self.min_string_input = QLineEdit()
        self.min_string_input.setValidator(QIntValidator(1, 1000))
        self.min_string_input.setText("4")

        self.search_strings_btn = QPushButton("Найти строки")
        self.search_strings_btn.clicked.connect(self.find_strings)

        controls_layout.addWidget(self.min_string_length)
        controls_layout.addWidget(self.min_string_input)
        controls_layout.addWidget(self.search_strings_btn)
        controls_layout.addStretch()

        layout.addLayout(controls_layout)

        # Strings table
        self.strings_table = QTableWidget()
        self.strings_table.setColumnCount(3)
        self.strings_table.setHorizontalHeaderLabels(["Адрес", "Длина", "Строка"])
        self.strings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout.addWidget(self.strings_table)

    def setup_stats_tab(self):
        """Setup the statistics tab"""
        layout = QVBoxLayout(self.stats_tab)

        # Stats display
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setFont(QFont("Courier New", 10))

        layout.addWidget(self.stats_text)

        # Bad blocks table and buttons
        bb_layout = QHBoxLayout()
        self.bad_blocks_table = QTableWidget()
        self.bad_blocks_table.setColumnCount(1)
        self.bad_blocks_table.setHorizontalHeaderLabels(["Плохие блоки"])
        self.bad_blocks_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        bb_buttons = QVBoxLayout()
        self.export_bb_btn = QPushButton("Экспорт bad-block в CSV")
        self.export_bb_btn.clicked.connect(self.export_bad_blocks)
        self.refresh_bb_btn = QPushButton("Обновить bad-block")
        self.refresh_bb_btn.clicked.connect(self.scan_bad_blocks)
        self.export_report_btn = QPushButton("Сохранить отчёт (Markdown)")
        self.export_report_btn.clicked.connect(self.export_markdown_report)
        bb_buttons.addWidget(self.export_bb_btn)
        bb_buttons.addWidget(self.refresh_bb_btn)
        bb_buttons.addWidget(self.export_report_btn)
        bb_buttons.addStretch()
        bb_layout.addWidget(self.bad_blocks_table)
        bb_layout.addLayout(bb_buttons)
        layout.addLayout(bb_layout)

        # Refresh button
        self.refresh_stats_btn = QPushButton("Обновить статистику")
        self.refresh_stats_btn.clicked.connect(self.calculate_statistics)
        layout.addWidget(self.refresh_stats_btn)

        # ECC verify button and legend
        ecc_layout = QHBoxLayout()
        self.verify_ecc_btn = QPushButton("Проверка ECC")
        self.verify_ecc_btn.clicked.connect(self.verify_ecc)
        self.legend_label = QLabel(
            "Легенда: OOB> — зона OOB, ECC! — страница с ошибкой ECC, BB# — блок с bad-block"
        )
        ecc_layout.addWidget(self.verify_ecc_btn)
        ecc_layout.addWidget(self.legend_label)
        layout.addLayout(ecc_layout)

        # Help/Legend dialog button
        help_layout = QHBoxLayout()
        self.help_btn = QPushButton("Справка/Легенда…")
        self.help_btn.clicked.connect(self.show_help)
        help_layout.addWidget(self.help_btn)
        help_layout.addStretch()
        layout.addLayout(help_layout)

    def open_dump(self):
        """Open a dump file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть дамп", "", "Binary files (*.bin);;All files (*)"
        )

        if file_path:
            try:
                with open(file_path, "rb") as f:
                    self.dump_data = f.read()
                self.dump_path = file_path
                self.status_bar.showMessage(
                    f"Загружен дамп: {os.path.basename(file_path)}, размер: {len(self.dump_data)} байт"
                )

                # Refresh all views
                self.refresh_hex_view()
                self.calculate_statistics()
                if self.second_dump_data:
                    self.calculate_diff()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить дамп: {str(e)}")

    def load_dump_from_path(self, file_path: str):
        """Programmatically load a dump file from a given path without dialogs."""
        if not file_path:
            return
        try:
            with open(file_path, "rb") as f:
                self.dump_data = f.read()
            self.dump_path = file_path
            self.status_bar.showMessage(
                f"Загружен дамп: {os.path.basename(file_path)}, размер: {len(self.dump_data)} байт"
            )
            # Refresh all views
            self.refresh_hex_view()
            self.calculate_statistics()
            if self.second_dump_data:
                self.calculate_diff()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить дамп: {str(e)}")

    def open_second_dump(self):
        """Open second dump for diff"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть второй дамп", "", "Binary files (*.bin);;All files (*)"
        )
        if file_path:
            try:
                with open(file_path, "rb") as f:
                    self.second_dump_data = f.read()
                self.second_dump_path = file_path
                self.status_bar.showMessage(
                    f"Второй дамп: {os.path.basename(file_path)}, размер: {len(self.second_dump_data)} байт"
                )
                if self.dump_data:
                    self.calculate_diff()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить второй дамп: {str(e)}")

    def refresh_hex_view(self):
        """Refresh the hex view"""
        if not self.dump_data:
            self.hex_view.setPlainText("Нет данных для отображения. Откройте дамп.")
            return

        try:
            start_addr = int(self.addr_input.text() or "0", 16)
            size = int(self.size_input.text() or "256", 16)
            self.page_size = int(self.page_input.text() or str(self.page_size))
            self.spare_size = int(self.spare_input.text() or str(self.spare_size))

            if start_addr >= len(self.dump_data):
                self.hex_view.setPlainText("Адрес за пределами дампа")
                return

            end_addr = min(start_addr + size, len(self.dump_data))
            data = self.dump_data[start_addr:end_addr]

            hex_text = self.format_hex_dump(data, start_addr)
            self.hex_view.setPlainText(hex_text)
        except ValueError:
            self.hex_view.setPlainText("Неверный формат адреса или размера")

    def on_toggle_oob(self, state):
        self.show_oob = state == Qt.CheckState.Checked
        self.refresh_hex_view()

    def on_toggle_badblocks(self, state):
        self.show_badblocks = state == Qt.CheckState.Checked
        self.refresh_hex_view()

    def on_toggle_ecc(self, state):
        self.show_ecc = state == Qt.CheckState.Checked
        self.refresh_hex_view()

    def format_hex_dump(self, data, start_addr):
        """Format data as hex dump"""
        if not data:
            return "Нет данных для отображения"

        result = []
        bytes_per_line = 16

        for i in range(0, len(data), bytes_per_line):
            # Address
            addr = start_addr + i
            line = f"{addr:08X}: "

            # Hex bytes
            hex_part = ""
            ascii_part = ""

            for j in range(bytes_per_line):
                if i + j < len(data):
                    byte_val = data[i + j]
                    hex_part += f"{byte_val:02X} "
                    if 32 <= byte_val <= 126:  # Printable ASCII
                        ascii_part += chr(byte_val)
                    else:
                        ascii_part += "."
                else:
                    hex_part += "   "

            # Build overlay prefix and page borders
            prefix_flags = []
            # Page border marker
            if self.page_size and self.spare_size:
                page_total = self.page_size + self.spare_size
                page_offset_global = start_addr + i
                if (page_offset_global % page_total) == 0:
                    # Horizontal separator for a new page start
                    page_idx = page_offset_global // page_total
                    result.append(
                        f"========== PAGE {page_idx} (0x{page_idx * page_total:08X}) =========="
                    )
                    prefix_flags.append("|PAGE|")
            # OOB marker
            if self.show_oob and self.page_size and self.spare_size:
                page_total = self.page_size + self.spare_size
                page_offset = (start_addr + i) % page_total
                in_oob = page_offset >= self.page_size and page_offset < page_total
                if in_oob:
                    prefix_flags.append("OOB>")
            # ECC error marker by page
            if self.show_ecc and self.page_size and self.spare_size:
                page_total = self.page_size + self.spare_size
                page_idx = (start_addr + i) // page_total
                if page_idx in self._ecc_error_pages:
                    prefix_flags.append("ECC!")
            # Bad-block overlay by page
            if self.show_badblocks and self._last_bad_blocks and self.page_size and self.spare_size:
                page_total = self.page_size + self.spare_size
                page_idx = (start_addr + i) // page_total
                # Heuristic: 64 pages per block for 2K/4K pages, else 32
                pages_per_block = 64 if self.page_size in (2048, 4096) else 32
                block_idx = page_idx // pages_per_block
                if block_idx in set(self._last_bad_blocks):
                    prefix_flags.append(f"BB{block_idx}")
            prefix = (" ".join(prefix_flags) + " ") if prefix_flags else "    "

            line = prefix + line + hex_part + " |" + ascii_part + "|"
            result.append(line)

        return "\n".join(result)

    def scan_bad_blocks(self):
        """Scan OOB to detect bad blocks (heuristic)."""
        if not self.dump_data:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте дамп")
            return
        try:
            self.page_size = int(self.page_input.text() or str(self.page_size))
            self.spare_size = int(self.spare_input.text() or str(self.spare_size))
        except ValueError:
            pass
        if self.page_size <= 0 or self.spare_size <= 0:
            QMessageBox.warning(self, "Предупреждение", "Некорректные размеры страницы/OOB")
            return
        page_total = self.page_size + self.spare_size
        total_pages = len(self.dump_data) // page_total if page_total > 0 else 0
        bad_blocks = set()
        # Простейшая эвристика: если в первом байте OOB страницы значение не 0xFF, помечать блок как bad
        for p in range(total_pages):
            page_start = p * page_total
            oob_start = page_start + self.page_size
            if oob_start < len(self.dump_data):
                if self.dump_data[oob_start] != 0xFF:
                    block_idx = p // (64 if self.page_size in (2048, 4096) else 32)
                    bad_blocks.add(block_idx)
        # Populate table
        self.bad_blocks_table.setRowCount(len(bad_blocks))
        for r, b in enumerate(sorted(bad_blocks)):
            item = QTableWidgetItem(str(b))
            # Highlight bad-block rows
            item.setBackground(Qt.yellow)
            self.bad_blocks_table.setItem(r, 0, item)
        text = f"Найдено плохих блоков: {len(bad_blocks)}"
        QMessageBox.information(self, "Результат сканирования", text)
        # Save for export
        self._last_bad_blocks = sorted(bad_blocks)
        self.refresh_hex_view()

    def export_bad_blocks(self):
        """Export bad blocks list to CSV file."""
        if not hasattr(self, "_last_bad_blocks") or not self._last_bad_blocks:
            QMessageBox.warning(self, "Предупреждение", "Сначала выполните сканирование bad-block")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить CSV", "bad_blocks.csv", "CSV files (*.csv)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("block\n")
                for b in self._last_bad_blocks:
                    f.write(f"{b}\n")
            QMessageBox.information(self, "Экспорт", f"Экспортировано: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось экспортировать: {e}")

    def export_markdown_report(self):
        """Export a Markdown report with summary, geometry, bad-blocks, and diff statistic."""
        if not self.dump_data:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте дамп")
            return
        # Prepare data
        total_size = len(self.dump_data)
        page_sz = self.page_size
        spare_sz = self.spare_size
        pages = 0
        if page_sz and spare_sz:
            pages = total_size // (page_sz + spare_sz)
        bb_list = getattr(self, "_last_bad_blocks", [])
        diff_info = self.status_bar.currentMessage() if self.status_bar else ""

        lines = []
        lines.append("# Отчёт анализа дампа\n")
        lines.append(f"- Файл: `{os.path.basename(self.dump_path) if self.dump_path else ''}`\n")
        lines.append(f"- Размер: **{total_size}** байт ({total_size/1024/1024:.2f} МБ)\n")
        lines.append(
            f"- Геометрия: страница {page_sz} байт, OOB {spare_sz} байт, страниц ~ {pages}\n"
        )
        if diff_info:
            lines.append(f"- Diff: {diff_info}\n")
        lines.append("\n## Плохие блоки\n")
        if bb_list:
            lines.append("Блоки:\n")
            for b in bb_list:
                lines.append(f"- Block {b}\n")
        else:
            lines.append("Не обнаружены\n")
        # ECC section
        lines.append("\n## ECC\n")
        if self._ecc_error_pages_detail:
            total_err_pages = len(self._ecc_error_pages_detail)
            total_err_sectors = sum(
                len(sectors) for sectors in self._ecc_error_pages_detail.values()
            )
            lines.append(f"Страниц с ошибками ECC: **{total_err_pages}**\n")
            lines.append(f"Секторов с ошибками ECC: **{total_err_sectors}**\n")
            lines.append("\nСписок страниц и индексов секторов с ошибками:\n")
            for page, sectors in sorted(self._ecc_error_pages_detail.items()):
                sector_list = ", ".join(map(str, sectors))
                lines.append(f"- Страница {page}: [{sector_list}]\n")
        else:
            lines.append("Ошибок ECC не обнаружено\n")

        lines.append("\n## Статистика\n")
        lines.append("```\n" + self.stats_text.toPlainText() + "\n```\n")

        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчёт", "dump_report.md", "Markdown files (*.md)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            QMessageBox.information(self, "Экспорт", f"Отчёт сохранён: {path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить отчёт: {e}")

    def verify_ecc(self):
        """Run ECC verification over pages and mark pages with errors."""
        if not self.dump_data:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте дамп")
            return
        try:
            self.page_size = int(self.page_input.text() or str(self.page_size))
            self.spare_size = int(self.spare_input.text() or str(self.spare_size))
        except ValueError:
            pass
        if self.page_size <= 0 or self.spare_size < 0:
            QMessageBox.warning(self, "Предупреждение", "Некорректные размеры страницы/OOB")
            return
        page_total = self.page_size + self.spare_size
        total_pages = len(self.dump_data) // page_total if page_total > 0 else 0
        error_pages = set()
        error_detail = {}
        # ECC parameters from config
        scheme = str(config_manager.get("ecc_scheme", "crc16"))
        sector_size = int(config_manager.get("ecc_sector_size", 512))
        bytes_per_sector = int(config_manager.get("ecc_bytes_per_sector", 2))
        oob_offset = int(config_manager.get("ecc_oob_offset", 0))
        for p in range(total_pages):
            start = p * page_total
            data = self.dump_data[start : start + self.page_size]
            oob = (
                self.dump_data[start + self.page_size : start + page_total]
                if self.spare_size
                else b""
            )
            _, sectors_with_err = verify_and_correct(
                data,
                oob,
                scheme=scheme,
                sector_size=sector_size,
                bytes_per_sector=bytes_per_sector,
                oob_offset=oob_offset,
            )
            if sectors_with_err:
                error_pages.add(p)
                # store sector indices within page
                error_detail[p] = sectors_with_err
        self._ecc_error_pages = error_pages
        self._ecc_error_pages_detail = error_detail
        self.refresh_hex_view()
        QMessageBox.information(self, "ECC", f"Страниц с ошибками ECC: {len(error_pages)}")

    def show_help(self):
        msg = (
            "Легенда и справка:\n\n"
            "- OOB>: строка отображает байты из области OOB (spare).\n"
            "- ECC!: страница имеет ошибки ECC (по выбранной схеме).\n"
            "- BB#: страница принадлежит блоку, помеченному как bad-block.\n\n"
            "Типичные размеры:\n"
            "- Страница 2048 байт, OOB 64 байта (64 страницы на блок).\n"
            "- Страница 4096 байт, OOB 128 байт (64 страницы на блок).\n\n"
            "Эвристика bad-block: первый байт OOB страницы не 0xFF — блок помечается плохим.\n"
            "Схема ECC: выбирается в Settings → ECC Parameters (none|crc16|hamming_512_3byte).\n\n"
            "Шаблоны расположения ECC в OOB (примеры):\n"
            "- YAFFS-like (2K+64): 4 сектора по 512 байт, ECC по 3 байта на сектор в OOB смещениях [40..42], [43..45], [46..48], [49..51].\n"
            "- Samsung common (2K+64): 4×(3 байта ECC) начиная с 0x30 (48) — итого 12 байт ECC.\n"
            "- Legacy CRC16 (2 байта на страницу): начало OOB (смещение 0).\n\n"
            "Примечание: точные смещения зависят от схемы контроллера/прошивки. Установите параметр ecc_oob_offset в Settings.\n"
        )
        QMessageBox.information(self, "Справка/Легенда", msg)

    def calculate_diff(self):
        """Calculate simple diff stats between two dumps (same length)."""
        if not self.dump_data or not self.second_dump_data:
            return
        if len(self.dump_data) != len(self.second_dump_data):
            self.status_bar.showMessage(
                "Diff: размеры файлов различаются — сравнение по длине невозможно"
            )
            return
        diffs = 0
        for a, b in zip(self.dump_data, self.second_dump_data):
            if a != b:
                diffs += 1
        self.status_bar.showMessage(f"Diff: отличающихся байт — {diffs}")

    def find_strings(self):
        """Find strings in the dump"""
        if not self.dump_data:
            QMessageBox.warning(self, "Предупреждение", "Сначала откройте дамп")
            return

        try:
            min_len = int(self.min_string_input.text() or "4")
        except ValueError:
            min_len = 4

        strings = []
        current_string = ""
        current_addr = -1

        for i, byte in enumerate(self.dump_data):
            if 32 <= byte <= 126 or byte in [
                9,
                10,
                13,
            ]:  # Printable chars including tab, newline, carriage return
                if not current_string:
                    current_addr = i
                current_string += chr(byte)
            else:
                if len(current_string) >= min_len:
                    strings.append((current_addr, len(current_string), current_string))
                current_string = ""
                current_addr = -1

        # Handle string at end of file
        if len(current_string) >= min_len:
            strings.append((current_addr, len(current_string), current_string))

        # Populate table
        self.strings_table.setRowCount(len(strings))
        for row, (addr, length, string) in enumerate(strings):
            self.strings_table.setItem(row, 0, QTableWidgetItem(f"0x{addr:08X}"))
            self.strings_table.setItem(row, 1, QTableWidgetItem(str(length)))
            self.strings_table.setItem(row, 2, QTableWidgetItem(string))

    def calculate_statistics(self):
        """Calculate statistics about the dump"""
        if not self.dump_data:
            self.stats_text.setPlainText("Нет данных для анализа. Откройте дамп.")
            return

        total_size = len(self.dump_data)

        # Count byte values
        byte_counts = [0] * 256
        for byte in self.dump_data:
            byte_counts[byte] += 1

        # Find most and least common bytes
        most_common = max(enumerate(byte_counts), key=lambda x: x[1])
        least_common = min(enumerate(byte_counts), key=lambda x: x[1] if x[1] > 0 else float("inf"))

        # Calculate entropy
        entropy = 0
        for count in byte_counts:
            if count > 0:
                p = count / total_size
                entropy -= p * (p.bit_length() - 1)  # Approximate log2

        # Find blank regions (all 0xFF)
        blank_regions = 0
        in_blank = False
        for byte in self.dump_data:
            if byte == 0xFF:
                if not in_blank:
                    blank_regions += 1
                    in_blank = True
            else:
                in_blank = False

        # Create statistics text
        stats_text = f"""Статистика дампа:
        
Размер: {total_size:,} байт ({total_size / 1024 / 1024:.2f} МБ)

Часто используемые байты:
- Наиболее частый: 0x{most_common[0]:02X} (встречается {most_common[1]:,} раз)
- Наименее частый: 0x{least_common[0]:02X} (встречается {least_common[1]:,} раз)

Статистика:
- Уникальных значений байтов: {sum(1 for c in byte_counts if c > 0)}
- Области с пустыми данными (0xFF): {blank_regions}
- Приблизительная энтропия: {entropy:.2f}

Распределение байтов:
"""

        # Show top 10 most common bytes
        stats_text += "\nТоп 10 наиболее частых байтов:\n"
        sorted_bytes = sorted(enumerate(byte_counts), key=lambda x: x[1], reverse=True)
        for i in range(min(10, len(sorted_bytes))):
            byte_val, count = sorted_bytes[i]
            if count > 0:
                stats_text += f"  0x{byte_val:02X}: {count:,} раз ({count/total_size*100:.2f}%)\n"

        self.stats_text.setPlainText(stats_text)


def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Set application font
    font = QFont("Arial", 9)
    app.setFont(font)

    window = DumpAnalyzer()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
