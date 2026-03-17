import sys
import subprocess
import json
from file_utils import get_creation_date
from datetime import datetime
import platform
import os
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QCheckBox, QProgressBar,
    QFileDialog, QDateEdit, QMenuBar, QDialog,
    QLabel,QLineEdit, QComboBox, QSpinBox, QRadioButton, QAbstractItemView,
    QMenu
)

from PySide6.QtCore import Qt, QDate, QUrl
from PySide6.QtGui import QIcon, QDesktopServices


# -----------------------------
# Settings Window
# -----------------------------

class SettingsDialog(QDialog):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AMS Settings")
        self.setWindowIcon(QIcon("linux.png"))
        self.setMinimumWidth(420)

        layout = QVBoxLayout()
        # ---------------------------
        # Default Output Directory
        # ---------------------------

        layout.addWidget(QLabel("Default Output Directory"))

        folder_layout = QHBoxLayout()

        self.output_path = QLineEdit()
        self.output_button = QPushButton("Select Folder")

        folder_layout.addWidget(self.output_path)
        folder_layout.addWidget(self.output_button)

        layout.addLayout(folder_layout)

        self.output_button.clicked.connect(self.select_folder)
        #---------------------------
        # Language
        #--------------------------
        layout.addWidget(QLabel("Meeting language"))

        self.lang_english = QRadioButton("English")
        self.lang_other = QRadioButton("Other")

        layout.addWidget(self.lang_english)
        layout.addWidget(self.lang_other)

        # ---------------------------
        # Compression Settings
        # ---------------------------

        layout.addWidget(QLabel("Compression Mode\n -CQ maintains that level of quality, therefore if there is alot of in the video then it will maintain a consistent fluid quality throughout the video (can end up in larger files if there is lots of motion)\n -CBR maintains a bitrate, therefore if there is alot of in the video then it will degrade the image quality to keep the MB/s of video constant."))

        compression_layout = QHBoxLayout()

        self.compression_mode = QComboBox()
        self.compression_mode.addItems([
            "CQ (Constant Quality)",
            "CBR (Constant Bitrate)"
        ])

        compression_layout.addWidget(self.compression_mode)
        self.compression_value = QSpinBox()

        compression_layout.addWidget(self.compression_value)

        layout.addLayout(compression_layout)

        # update settings when mode changes
        self.compression_mode.currentTextChanged.connect(self.update_compression_mode)

        # initialize default values
        self.update_compression_mode(self.compression_mode.currentText())
        

        # ---------------------------
        # HuggingFace Token
        # ---------------------------

        layout.addWidget(QLabel("HuggingFace API Token"))

        self.hf_token = QLineEdit()
        self.hf_token.setEchoMode(QLineEdit.Password)
        self.hf_token.setPlaceholderText("hf_xxxxxxxxxxxxx")

        layout.addWidget(self.hf_token)

        # ---------------------------
        # Linux sudo password
        # ---------------------------

        if platform.system() == "Linux":

            layout.addWidget(QLabel("Sudo Password (Linux only)\n - Note: This is only used to activate and deactivate Ollama to save VRAM when summarizing."))

            self.sudo_password = QLineEdit()
            self.sudo_password.setEchoMode(QLineEdit.Password)

            layout.addWidget(self.sudo_password)

        

        # ---------------------------
        # Save Button
        # ---------------------------

        self.save_button = QPushButton("Save")

        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def update_compression_mode(self, mode):
            if "CQ" in mode:
                # typical NVENC CQ range
                self.compression_value.setRange(0, 51)
                self.compression_value.setValue(18)
                self.compression_value.setSuffix(" CQ")

            elif "CBR" in mode:

                # bitrate in kbps
                self.compression_value.setRange(100, 20000)
                self.compression_value.setValue(1500)
                self.compression_value.setSuffix(" kbps")
    # ---------------------------
    # Folder picker
    # ---------------------------

    def select_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Default Output Folder"
        )

        if folder:
            self.output_path.setText(folder)

# -----------------------------
# Table Widget
# -----------------------------

class MediaTable(QTableWidget):

    def __init__(self):

        super().__init__(0, 5)

        self.setHorizontalHeaderLabels([
            "Input File",
            "Options",
            "Date",
            "Output File",
            "Progress"
        ])
        # 
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DropOnly)
        
        # Used for row deletion
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        
        # Used for right clicking file
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    # -----------------------------
    # Drag & Drop (Cross-platform)
    # -----------------------------

    def dragEnterEvent(self, event):
        if event.mimeData().urls():
            event.acceptProposedAction()
        else:
            event.ignore()


    def dragMoveEvent(self, event):
        if event.mimeData().urls():
            event.acceptProposedAction()
        else:
            event.ignore()


    def dropEvent(self, event):
        if not event.mimeData().urls():
            event.ignore()
            return

        # Optional: restrict to Input File column
        pos = event.position().toPoint()
        index = self.indexAt(pos)

        if index.isValid() and index.column() != 0:
            event.ignore()
            return

        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path:
                self.add_file_row(file_path)

        event.acceptProposedAction()

    # -----------------------------
    # Checkbox column
    # -----------------------------

    def create_options_widget(self):

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)
        transcribe = QCheckBox("Transcribe")
        compress = QCheckBox("Compress")
        summarize = QCheckBox("Summarize")

        layout.addWidget(transcribe)
        layout.addWidget(compress)
        layout.addWidget(summarize)

        layout.setContentsMargins(0,0,0,0)

        return widget

    # -----------------------------
    # Add row
    # -----------------------------

    def add_file_row(self, filepath):
        # Creating row
        row = self.rowCount()
        self.insertRow(row)

        self.setItem(row, 0, QTableWidgetItem(filepath))
        
        # Creating options to transcribe, compress or summarize
        options = self.create_options_widget()
        self.setCellWidget(row, 1, options)
        self.resizeColumnToContents(1)

        # File date
        date_widget = QDateEdit()
        date_widget.setCalendarPopup(True)
        
        timestamp = get_creation_date(filepath)
        dt_from_timestamp = datetime.fromtimestamp(timestamp)
        qdate = QDate(dt_from_timestamp.year, dt_from_timestamp.month, dt_from_timestamp.day)
        date_widget.setDate(qdate)

        self.setCellWidget(row, 2, date_widget)
        # Output file dir
        output = filepath + ".processed"
        self.setItem(row, 3, QTableWidgetItem(output))

        # Progress Bar
        progress = QProgressBar()
        progress.setValue(0)

        self.setCellWidget(row, 4, progress)
    
    # Remove Row with Delete
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected_rows()
        else:
            super().keyPressEvent(event)
        
    def delete_selected_rows(self):
        selected_rows = set()

        for index in self.selectedIndexes():
            selected_rows.add(index.row())

        # Remove from bottom → top (avoids index shifting issues)
        for row in sorted(selected_rows, reverse=True):
            self.removeRow(row)

    # Context Menu
    def show_context_menu(self, position):
        index = self.indexAt(position)

        if not index.isValid():
            return

        row = index.row()

        file_item = self.item(row, 0)
        if not file_item:
            return

        file_path = file_item.text()

        menu = QMenu(self)

        delete_action = menu.addAction("🗑 Delete")
        open_action = menu.addAction("📂 Open File")
        reveal_action = menu.addAction("📁 Reveal in Folder")

        action = menu.exec(self.viewport().mapToGlobal(position))

        if action == delete_action:
            self.removeRow(row)

        elif action == open_action:
            self.open_file(file_path)

        elif action == reveal_action:
            self.reveal_in_folder(file_path)
    
    def open_file(self, file_path):
        QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
    
    def reveal_in_folder(self, file_path):
        if not os.path.exists(file_path):
            return

        if sys.platform.startswith("win"):
            subprocess.run(["explorer", "/select,", file_path])

        elif sys.platform == "darwin":
            subprocess.run(["open", "-R", file_path])

        else:  # Linux
            folder = os.path.dirname(file_path)
            subprocess.run(["xdg-open", folder])


# -----------------------------
# Main Window
# -----------------------------

class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("Auto-Meeting-Subs")
        self.setWindowIcon(QIcon("linux.png"))
        container = QWidget()
        layout = QVBoxLayout(container)

        # Menu bar
        menu = self.menuBar()
        settings_menu = menu.addAction("Settings")
        settings_menu.triggered.connect(self.open_settings)

        # Table
        self.table = MediaTable()

        # Buttons
        button_layout = QHBoxLayout()

        self.add_button = QPushButton("Add File")
        self.add_button.clicked.connect(self.add_file_dialog)

        self.start_button = QPushButton("Start Processing")

        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.start_button)

        layout.addWidget(self.table)
        layout.addLayout(button_layout)

        self.setCentralWidget(container)

    # -----------------------------
    # File Browser
    # -----------------------------

    def add_file_dialog(self):

        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Media Files"
        )

        for file in files:
            self.table.add_file_row(file)


    # -----------------------------
    # Settings popup
    # -----------------------------

    def open_settings(self):

        dialog = SettingsDialog()
        dialog.exec()


# -----------------------------
# Run Application
# -----------------------------

app = QApplication([])

# taskbar icon
app.setWindowIcon(QIcon("icon.png"))

window = MainWindow()
window.resize(1100, 500)
window.show()

sys.exit(app.exec())