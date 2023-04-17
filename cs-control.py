import sys, json, re
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from valve.rcon import *
import a2s

# address = ('172.99.189.25', 35400)
# print(a2s.info(address).map_name)
# print(a2s.players(address))

# exit()

MAPS_REGEX = re.compile(r'PENDING:\s*\(fs\)\s*(\w+).bsp')

class MacroApplication(QMainWindow):
    def __init__(self):
        super().__init__()

        self.macro_menu_items = {}
        self.macro_buttons = {}
        self.rcon = None

        self.init_ui()

        self.load_data()

        self.reconnect()

    def init_ui(self):

        QApplication.setStyle(QStyleFactory.create('fusion'))
        QApplication.setPalette(QApplication.style().standardPalette())

        self.setWindowTitle("Macro RCON")

        self.create_menu_bar()
        self.create_main_widget()

    def create_menu_bar(self):
        menu_bar = QMenuBar()
        connection_menu = QMenu("Connection", menu_bar)
        connection_menu.addAction("Edit", self.edit_connection)
        connection_menu.addAction("Connect", self.reconnect)
        connection_menu.addAction("Disconnect", self.close_connection)
        menu_bar.addMenu(connection_menu)

        self.macros_menu = QMenu("Macros", menu_bar)
        self.macros_menu.addAction("New macro", self.new_macro)
        self.macros_menu.addSeparator()
        menu_bar.addMenu(self.macros_menu)

        self.setMenuBar(menu_bar)

    def create_main_widget(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setMinimumSize(QSize(400, 500))

        # Connection GroupBox
        self.connection_group = QGroupBox()
        connection_layout = QFormLayout()

        self.server_name_label = QLabel()
        connection_layout.addRow("Server:", self.server_name_label)

        self.current_map_label = QLabel()
        connection_layout.addRow("Map:", self.current_map_label)

        self.players_label = QLabel()
        connection_layout.addRow("Players:", self.players_label)

        self.connection_status_label = QLabel()
        connection_layout.addRow("Status:", self.connection_status_label)

        self.connection_group.setLayout(connection_layout)

        main_layout.addWidget(self.connection_group)
        

        # Macros GroupBox
        self.macros_group = QGroupBox("Macros")
        self.macros_layout = QVBoxLayout()
        self.macros_group.setLayout(self.macros_layout)
        main_layout.addWidget(self.macros_group)

        # Log GroupBox
        self.output_group = QGroupBox("Log")
        output_layout = QVBoxLayout()

        self.command_edit = QLineEdit()
        self.command_edit.setPlaceholderText("Run command...")
        self.command_edit.returnPressed.connect(self.log_single_command)
        output_layout.addWidget(self.command_edit)

        self.output_area = QPlainTextEdit()
        self.output_area.setFont(QFont("monospace", 8))
        self.output_area.setReadOnly(True)
        output_layout.addWidget(self.output_area)
        self.output_group.setLayout(output_layout)

        main_layout.addWidget(self.output_group)

        # Maps GroupBox
        self.change_maps_group = QGroupBox("Maps")
        change_maps_layout = QHBoxLayout()
        self.change_maps_edit = QLineEdit()
        self.change_maps_edit.setPlaceholderText("Map name...")

        self.maps_model = QStringListModel()
        self.maps_completer = QCompleter(self.maps_model, self)
        self.maps_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.change_maps_edit.setCompleter(self.maps_completer)

        self.load_map_button = QPushButton("Load")
        self.load_map_button.clicked.connect(self.execute_change_map)

        change_maps_layout.addWidget(self.change_maps_edit)
        change_maps_layout.addWidget(self.load_map_button)
        self.change_maps_group.setLayout(change_maps_layout)
        main_layout.addWidget(self.change_maps_group)

        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

    def close_connection(self):
        self.output_area.appendPlainText(f"> Closing connection...")

        if self.rcon != None:
            self.rcon.close()
            self.rcon = None

        self.update_connection_group()

    def reconnect(self):
        self.output_area.appendPlainText(f"> Trying to connect...")

        try:
            self.rcon = RCON((self.hostname, self.port), self.password)
            self.rcon.connect()
            self.rcon.authenticate()
            self.output_area.appendPlainText(f"> Connection established")
            self.refresh_maps()
        except Exception as e:
            self.output_area.appendPlainText(f"> Connection failed")
            self.output_area.appendPlainText(str(e))
            self.close_connection()
            
        self.update_connection_group()

    def update_connection_group(self):
        if self.rcon != None:

            info = a2s.info((self.hostname, self.port))

            self.server_name_label.setText(info.server_name)
            self.current_map_label.setText(info.map_name)
            self.players_label.setText(f"{info.player_count}/{info.max_players}")
            self.connection_status_label.setText("Online")

            self.connection_group.setEnabled(True)

        else:
            self.server_name_label.setText("------------")
            self.current_map_label.setText("Unknown")
            self.players_label.setText("Unknown")
            self.connection_status_label.setText("Failed")

            self.connection_group.setEnabled(False)


    def refresh_maps(self, event=None):
        if self.maps_model.rowCount() == 0:
            res, err = self.log_commands("Caching all maps", "maps *", silent_output=True)
            self.maps_model.setStringList(re.findall(MAPS_REGEX, res) if not err else [])
        
    def execute_change_map(self):
        command = f"map {self.change_maps_edit.text()}"
        self.log_commands(command, command)
        self.change_maps_edit.clear()    

    def execute(self, commands):
        try:
            if self.rcon == None: raise Exception("Error: Not connected to server")
            res = self.rcon.execute(commands).text
            res = "\n".join(filter(lambda s: not s.startswith("L "), res.split("\n")))
            return res, None
        except Exception as error:
            self.close_connection()
            return f"Error: {error}", error

    def log_single_command(self):
        command = self.command_edit.text()
        self.log_commands(command, command)
        self.command_edit.clear()

    def log_commands(self, descriptor, commands, silent_output=False):
        self.output_area.appendPlainText(f"> {descriptor}")

        res, err = self.execute(commands)

        if not silent_output or err != None:
            self.output_area.appendPlainText(f"{res}\n")

        return res, err

    def load_data(self):
        try:
            with open("data.json", "r") as file:
                data = json.load(file)

                if hasattr(self, 'macros'):
                    for macro in self.macros:
                        self.macros_menu.removeAction(self.macro_menu_items[macro.name].menuAction())
                        self.macro_buttons[macro.name].setParent(None)
                        del self.macro_menu_items[macro.name]
                        del self.macro_buttons[macro.name]

                self.hostname = data["hostname"]
                self.port = data["port"]
                self.password = data["password"]
                self.macros = [Macro(macro["name"], macro["commands"]) for macro in data["macros"]]
                for macro in self.macros:
                    self.add_macro_menu_item(macro)
                    self.add_macro_button(macro)
            return True
        except FileNotFoundError:
            self.hostname = ""
            self.port = 0
            self.password = ""
            self.macros = []
            return False

    def save_data(self):
        data = {
            "hostname": self.hostname,
            "port": self.port,
            "password": self.password,
            "macros": [{"name": macro.name, "commands": macro.commands} for macro in self.macros]
        }
        with open("data.json", "w") as file:
            json.dump(data, file, indent=4)

    def edit_connection(self):
        connection_diaoutput = EditConnectionDialog(self)
        connection_diaoutput.hostname_edit.setText(self.hostname)
        connection_diaoutput.port_edit.setText(str(self.port))
        connection_diaoutput.password_edit.setText(self.password)
        if connection_diaoutput.exec() == QDialog.DialogCode.Accepted:
            self.hostname = connection_diaoutput.hostname_edit.text()
            self.port = int(connection_diaoutput.port_edit.text())
            self.password = connection_diaoutput.password_edit.text()
            self.save_data()
            self.reconnect()

    def new_macro(self):
        macro = Macro("", "")
        macro_diaoutput = MacroEditDialog(macro)
        if macro_diaoutput.exec() == QMessageBox.StandardButton.Ok:
            macro.name = macro_diaoutput.name_edit.text()
            macro.commands = macro_diaoutput.commands_edit.toPlainText()
            self.macros.append(macro)
            self.add_macro_menu_item(macro)
            self.add_macro_button(macro)
            self.save_data()

    def add_macro_menu_item(self, macro):
        macro_menu = QMenu(macro.name, self.macros_menu)
        macro_menu.addAction("Edit", lambda: self.edit_macro(macro))
        macro_menu.addAction("Delete", lambda: self.delete_macro(macro))
        self.macros_menu.addMenu(macro_menu)
        self.macro_menu_items[macro.name] = macro_menu

    def add_macro_button(self, macro):
        button = QPushButton(macro.name)
        button.clicked.connect(lambda: self.run_macro(macro))
        self.macros_layout.addWidget(button)
        self.macro_buttons[macro.name] = button
        return button

    def run_macro(self, macro):
        self.log_commands(f'Running "{macro.name}"', macro.commands)

    def edit_macro(self, macro):
        macro_diaoutput = MacroEditDialog(macro)
        if macro_diaoutput.exec() == QMessageBox.StandardButton.Ok:
            old_name = macro.name
            macro.name = macro_diaoutput.name_edit.text()
            macro.commands = macro_diaoutput.commands_edit.toPlainText()
            self.save_data()

            self.macro_menu_items[old_name].setTitle(macro.name)
            self.macro_buttons[old_name].setText(macro.name)
            self.macro_menu_items[macro.name] = self.macro_menu_items.pop(old_name)
            self.macro_buttons[macro.name] = self.macro_buttons.pop(old_name)

    def delete_macro(self, macro):
        self.macros.remove(macro)
        self.save_data()

        self.macros_menu.removeAction(self.macro_menu_items[macro.name].menuAction())
        self.macro_buttons[macro.name].setParent(None)
        del self.macro_menu_items[macro.name]
        del self.macro_buttons[macro.name]


class EditConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Setup connection")

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

class Macro:
    def __init__(self, name, commands):
        self.name = name
        self.commands = commands

class MacroEditDialog(QMessageBox):
    def __init__(self, macro):
        super().__init__()

        self.setWindowTitle("Edit Macro")
        self.setIcon(QMessageBox.Icon.NoIcon)
        self.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Name:"))
        self.name_edit = QLineEdit(macro.name)
        layout.addWidget(self.name_edit)

        layout.addWidget(QLabel("Commands:"))
        self.commands_edit = QPlainTextEdit(macro.commands)
        self.commands_edit.setMinimumSize(QSize(400, 300))
        layout.addWidget(self.commands_edit)

        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addItem(spacer)

        grid_layout = self.layout()
        grid_layout.addLayout(layout, 0, 0, 1, grid_layout.columnCount())


def main():
    app = QApplication(sys.argv)
    
    main_window = MacroApplication()
    
    if not main_window.load_data():
        connection_diaoutput = EditConnectionDialog()
        if connection_diaoutput.exec() == QDialog.DialogCode.Accepted:
            main_window.hostname = connection_diaoutput.hostname_edit.text()
            main_window.port = int(connection_diaoutput.port_edit.text())
            main_window.password = connection_diaoutput.password_edit.text()
            main_window.save_data()
        else:
            sys.exit(0)

    main_window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()


