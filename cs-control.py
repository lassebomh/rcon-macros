import sys
import json
import valve.rcon

from PyQt6.QtWidgets import QApplication, QWidget, QFormLayout, QDialogButtonBox, QDialog, QTextEdit, QGroupBox, QInputDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QPlainTextEdit, QMessageBox, QSpacerItem, QSizePolicy, QStyleFactory, QStyle
from PyQt6.QtCore import QFile, QIODevice, QSize, Qt

class MacroApplication(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Macro Application")
        self.setMinimumWidth(600)

        self.layout = QHBoxLayout()

        self.macro_group = QGroupBox("Macros")
        self.macro_group.setMinimumWidth(240)
        self.macro_layout = QVBoxLayout()
        self.macro_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.macro_list = QVBoxLayout()
        self.load_settings()

        self.add_macro_button = QPushButton("Create New Macro")
        self.add_macro_button.clicked.connect(self.create_macro)

        self.macro_layout.addLayout(self.macro_list)
        self.macro_layout.addWidget(self.add_macro_button)
        self.macro_group.setLayout(self.macro_layout)

        self.layout.addWidget(self.macro_group)

        self.run_command_group = QGroupBox("Run command")
        self.run_command_layout = QVBoxLayout()

        self.command_edit = QLineEdit()
        self.command_edit.returnPressed.connect(self.run_single_line_command)

        self.run_command_layout.addWidget(self.command_edit)

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)

        self.run_command_layout.addWidget(self.output_box)

        self.run_command_group.setLayout(self.run_command_layout)

        self.layout.addWidget(self.run_command_group)

        self.setLayout(self.layout)

    def run_single_line_command(self):
        command = self.command_edit.text().strip()
        self.command_edit.clear()
        try:
            output = eval(command)
            self.output_box.append(f"> {command}\n{output}\n")
        except Exception as e:
            self.output_box.append(f"> {command}\nError: {str(e)}\n")

    def create_macro(self):
        macro = Macro(self)
        self.macro_list.addWidget(macro)
        self.save_settings()

    def load_settings(self):
        try:
            with open("settings.json", "r") as file:
                settings = json.load(file)
                self.hostname = settings["hostname"]
                self.port = settings["port"]
                self.password = settings["password"]

                for macro in settings["macros"]:
                    self.macro_list.addWidget(Macro(self, macro["name"], macro["code"]))

        except FileNotFoundError:
            settings_dialog = SettingsDialog(self)
            result = settings_dialog.exec()

            if result == QDialog.DialogCode.Accepted:
                self.hostname = settings_dialog.hostname_edit.text()
                self.port = int(settings_dialog.port_edit.text())
                self.password = settings_dialog.password_edit.text()
                self.save_settings()
            else:
                sys.exit()

    def save_settings(self):
        settings = {
            "hostname": self.hostname,
            "port": self.port,
            "password": self.password,
            "macros": []
        }

        for i in range(self.macro_list.count()):
            macro = self.macro_list.itemAt(i).widget()
            settings["macros"].append({"name": macro.name, "code": macro.code})

        with open("settings.json", "w") as file:
            json.dump(settings, file)

    def prompt_settings(self):
        settings_dialog = SettingsDialog(self)
        result = settings_dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            return settings_dialog.hostname_edit.text(), int(settings_dialog.port_edit.text()), settings_dialog.password_edit.text()
        else:
            sys.exit()

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Enter Hostname, Port, and Password")

        self.form_layout = QFormLayout()

        self.hostname_edit = QLineEdit()
        self.form_layout.addRow("Hostname:", self.hostname_edit)

        self.port_edit = QLineEdit()
        self.form_layout.addRow("Port:", self.port_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addRow("Password:", self.password_edit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.validate_inputs)
        self.button_box.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.layout.addLayout(self.form_layout)
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)

    def validate_inputs(self):
        if self.hostname_edit.text() and self.port_edit.text().isdigit() and self.password_edit.text():
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Please enter valid hostname, port, and password.")


class Macro(QWidget):
    def __init__(self, parent, name="New Macro", code=""):
        super().__init__(parent)

        self.parent_app = parent
        self.name = name
        self.code = code

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.run_button = QPushButton(self.name)
        self.run_button.clicked.connect(self.run_macro)

        self.edit_button = QPushButton("Edit")
        self.edit_button.setFixedWidth(40)
        self.edit_button.clicked.connect(self.edit_macro)

        self.delete_button = QPushButton()
        self.delete_button.clicked.connect(self.delete_macro)
        self.delete_button.setFixedWidth(25)

        pixmapi = QStyle.StandardPixmap.SP_DialogDiscardButton
        icon = self.style().standardIcon(pixmapi)
        self.delete_button.setIcon(icon)

        layout.addWidget(self.run_button)
        layout.addWidget(self.edit_button)
        layout.addWidget(self.delete_button)

        self.setLayout(layout)

    def run_macro(self):
        try:
            output = eval(self.code)
            self.parent_app.output_box.append(f'> Execute "{self.name}"\n{output}\n')
        except Exception as e:
            self.parent_app.output_box.append(f'> Execute "{self.name}"\nError: {str(e)}\n')

    def edit_macro(self):
        edit_dialog = EditDialog(self)
        result = edit_dialog.exec()

        if result == QMessageBox.StandardButton.Ok:
            self.name = edit_dialog.name_edit.text()
            self.code = edit_dialog.code_edit.toPlainText()

            self.run_button.setText(self.name)
            self.parent_app.save_settings()

    def delete_macro(self):
        reply = QMessageBox.question(self, 'Delete Macro', 'Are you sure you want to delete this macro?',
                                      QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            parent_layout = self.parent_app.macro_layout

            parent_layout.removeWidget(self)
            self.deleteLater()

            self.parent_app.save_settings()

class EditDialog(QMessageBox):
    def __init__(self, macro):
        super().__init__()

        self.setWindowTitle("Edit Macro")
        self.setIcon(QMessageBox.Icon.NoIcon)
        self.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit(macro.name)
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Code:"))
        self.code_edit = QPlainTextEdit(macro.code)
        self.code_edit.setMinimumSize(QSize(400, 300))
        layout.addWidget(self.code_edit)

        layout.addWidget(QLabel("Warning: The code will be executed as is. Be cautious while editing the code."))

        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addItem(spacer)

        grid_layout = self.layout()
        grid_layout.addLayout(layout, 0, 0, 1, grid_layout.columnCount())

app = QApplication(sys.argv)

QApplication.setStyle(QStyleFactory.create('fusion'))
QApplication.setPalette(QApplication.style().standardPalette())

window = MacroApplication()
window.show()

sys.exit(app.exec())