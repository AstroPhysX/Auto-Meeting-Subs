import sys, os
sys.path.insert(0, os.path.dirname(__file__))  # ensure sibling modules can be imported

from file_utils import setup_app_environment, audio_or_video, get_creation_date
APPDATA_DIR = setup_app_environment()
from config_manager import save_config, load_config
import subprocess
import json

from datetime import datetime
import platform

# GUI specific Imports
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QCheckBox, QProgressBar,
    QFileDialog, QDateEdit, QMenuBar, QDialog,
    QLabel,QLineEdit, QComboBox, QSpinBox, QRadioButton, QAbstractItemView,
    QMenu, QMessageBox
)
from PySide6.QtCore import Qt, QDate, QUrl
from PySide6.QtGui import QIcon, QDesktopServices


# -----------------------------
# Settings Window
# -----------------------------

class SettingsDialog(QDialog):
    
    def __init__(self):
        super().__init__()
        print("Opening Settings")
        self.setWindowTitle("AMS Settings")
        self.setWindowIcon(QIcon("linux.png"))
        self.setMinimumWidth(420)
        self.setMinimumHeight(800)

        layout = QVBoxLayout()
        # ---------------------------
        # Default Output Directory
        # ---------------------------

        layout.addWidget(QLabel("<b>Default Output Directory</b>"))

        folder_layout = QHBoxLayout()

        self.output_path = QLineEdit()
        self.output_button = QPushButton("Select Folder")

        folder_layout.addWidget(self.output_path)
        folder_layout.addWidget(self.output_button)

        layout.addLayout(folder_layout)

        self.output_button.clicked.connect(self.select_folder)

        #---------------------------
        # Naming Convention
        #---------------------------
        name_con_label = QLabel(f"""
        <b>File Naming Convention</b><br>
        - This will be the base name for the ouputed files, DO NOT INCLUDE FILE EXTENSIONS.<br>
        - %Y = 4 digit year; %y = 2 digit year; %m = 2 digit month; %d = 2 digit day<br>
        - For options please visit <a href="https://www.pythonmorsels.com/strptime/">strftime</a>
        """)
        name_con_label.setOpenExternalLinks(True)  # Opens the link in the default browser
        name_con_label.setTextInteractionFlags(Qt.TextBrowserInteraction)  # Enables link detection
        name_con_label.setWordWrap(True)
        layout.addWidget(name_con_label)

        self.naming_convention = QLineEdit()
        layout.addWidget(self.naming_convention)
        self.naming_convention.setText(f'Meeting %Y.%m.%d')

        #--------------------------------
        # Output video and Audio format
        #--------------------------------
        layout.addWidget(QLabel("<b>Video and Audio file ouput format</b>"))
        
        video_layout = QHBoxLayout()
        video_layout.addWidget(QLabel("Video Format:"))
        self.v_extension = QComboBox()
        self.v_extension.addItems(['mp4','mkv'])
        video_layout.addWidget(self.v_extension)
        layout.addLayout(video_layout)
        
        audio_layout = QHBoxLayout()
        audio_layout.addWidget(QLabel("Audio Format:"))
        self.a_extension = QComboBox()
        self.a_extension.addItems(['mp3','flac','wav'])
        audio_layout.addWidget(self.a_extension)
        layout.addLayout(audio_layout)

        #---------------------------
        # Language
        #--------------------------
        layout.addWidget(QLabel("<b>Meeting language</b>"))

        self.lang_english = QRadioButton("English")
        self.lang_other = QRadioButton("Other")
        self.lang_other.setChecked(True)

        layout.addWidget(self.lang_english)
        layout.addWidget(self.lang_other)

        # ---------------------------
        # Compression Settings
        # ---------------------------
        compression_label = QLabel("""
            <b>Compression Mode</b><br>
            - CQ maintains that level of quality, therefore if there is alot of in the video then it will maintain a consistent fluid quality throughout the video (can end up in larger files if there is lots of motion)<br>
            - CBR maintains a bitrate, therefore if there is alot of in the video then it will degrade the image quality to keep the MB/s of video constant."""
        )
        compression_label.setWordWrap(True)
        layout.addWidget(compression_label)

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
        
        #----------------------------
        # Sub format
        #----------------------------
        sub_format_label = QLabel("""
            <b>Subtitle Format</b><br>
            - If you are unfamiliar with these formats, I highly recommend to choose 'srt' as it is one of the most compatible formats."""
        )
        sub_format_label.setWordWrap(True)
        layout.addWidget(sub_format_label)

        self.sub_format = QComboBox()
        self.sub_format.addItems(['srt','txt','vtt','tsv','aud','json'])

        layout.addWidget(self.sub_format)

        # ---------------------------
        # HuggingFace Token
        # ---------------------------

        layout.addWidget(QLabel("<b>HuggingFace API Token (Required)</b>"))

        self.hf_token = QLineEdit()
        self.hf_token.setEchoMode(QLineEdit.Password)
        self.hf_token.setPlaceholderText("hf_xxxxxxxxxxxxx")

        layout.addWidget(self.hf_token)

        # ---------------------------
        # Linux sudo password
        # ---------------------------

        if platform.system() == "Linux":
            password_label = QLabel("""
            <b>Sudo Password (Linux only)</b><br>
            - Note: This is only used to activate and deactivate Ollama to save VRAM when summarizing.""")
            password_label.setWordWrap(True)
            layout.addWidget(password_label)

            self.sudo_password = QLineEdit()
            self.sudo_password.setEchoMode(QLineEdit.Password)

            layout.addWidget(self.sudo_password)

        # ---------------------------
        # Save Button
        # ---------------------------

        self.save_button = QPushButton("Save")

        layout.addWidget(self.save_button)

        self.setLayout(layout)
        self.save_button.clicked.connect(self.save_settings)

        self.load_settings()

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
        print("Selecting output folder")
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Default Output Folder"
        )

        if folder:
            self.output_path.setText(folder)
    
    def save_settings(self):
        config_dir = os.path.join(APPDATA_DIR,'GUIconfig.ini')
        data = {
            "output_dir": self.output_path.text(),
            "naming_convention": self.naming_convention.text(),
            "video_ext": self.v_extension.currentText(),
            "audio_ext": self.a_extension.currentText(),
            "language": 'y' if self.lang_english.isChecked() else 'n',
            "subtitle_format": self.sub_format.currentText(),
            "token": self.hf_token.text(),
            "compression_mode": "CQ" if "CQ" in self.compression_mode.currentText() else "CBR",
            "compression_value": self.compression_value.value(),
        }
        if len(data['token']) == 0 :
            token_val = "No Hf token"
        else:
            token_val = "Token inputed"
        
        language = 'english' if data['language'] == 'y' else 'other language'

        if hasattr(self, "sudo_password"):
            data["sudo_password"] = self.sudo_password.text()
            if len(data['sudo_password']) > 0:
                print("sudo given")
            else:
                print("---->sudo not given")

        save_config(config_dir, data)

        print(f"Settings saved:\n-{data['output_dir']}\n-{data['naming_convention']}\n-{data['video_ext']},\n-{data['audio_ext']}\n-{language}\n-{data['subtitle_format']}\n-{token_val}\n-{data['compression_mode']}:{data['compression_value']}")

        self.accept()

    def load_settings(self):
        config_dir = os.path.join(APPDATA_DIR,'GUIconfig.ini')
        config = load_config(config_dir)
        if not config:
            print("No GUIconfig.ini file found")
            return

        self.output_path.setText(config["output_dir"])

        self.naming_convention.setText(config["naming_convention"])

        self.v_extension.setCurrentText(config["video_ext"])
        self.a_extension.setCurrentText(config["audio_ext"])

        if config["language"] == 'y':
            self.lang_english.setChecked(True)
        else:
            self.lang_other.setChecked(True)

        self.sub_format.setCurrentText(config["subtitle_format"])
        self.hf_token.setText(config["token"])

        if config["compression_mode"] == "CQ":
            self.compression_mode.setCurrentIndex(0)
        else:
            self.compression_mode.setCurrentIndex(1)

        self.update_compression_mode(self.compression_mode.currentText())
        self.compression_value.setValue(config["compression_value"])

        if hasattr(self, "sudo_password"):
            self.sudo_password.setText(config["sudo_password"])
        print("GUIconfig.ini loaded")

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
    def show_invalid_file_error(parent=None, filepath=None):
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("Invalid File")
        msg.setText("Unsupported file type")
        msg.setInformativeText("The selected file is not a valid audio or video file.")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

    def add_file_row(self, filepath):
        file_directory = Path(input_file).parent
        # File check
        if audio_or_video(filepath) == 'unknown':
            self.show_invalid_file_error(filepath=filepath)
            return

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