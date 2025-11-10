import os, sys, json, threading, subprocess
import minecraft_launcher_lib
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QMessageBox
from PyQt6.QtCore import Qt
import updater

class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Launcher GTS")
        self.resize(500, 350)
        self.setStyleSheet("""
            QWidget {
                background-color: #141414;
                color: white;
                font-family: 'Segoe UI';
                font-size: 14px;
            }
            QPushButton {
                background-color: #242424;
                border: 1px solid #3a3a3a;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #2d2d2d;
            }
            QComboBox {
                background-color: #1f1f1f;
                border-radius: 6px;
                padding: 5px;
                color: white;
            }
        """)

        layout = QVBoxLayout()

        self.status_label = QLabel("Iniciando launcher...")
        layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.version_box = QComboBox()
        layout.addWidget(self.version_box)

        self.refresh_button = QPushButton("🔄 Actualizar launcher y archivos")
        self.refresh_button.clicked.connect(lambda: threading.Thread(target=self.run_update, daemon=True).start())
        layout.addWidget(self.refresh_button)

        self.play_button = QPushButton("▶ Iniciar Minecraft")
        self.play_button.clicked.connect(lambda: threading.Thread(target=self.launch_game, daemon=True).start())
        layout.addWidget(self.play_button)

        self.setLayout(layout)

        # Cargar configuración
        self.config = self.load_config()

        # Iniciar procesos paralelos
        threading.Thread(target=self.load_versions, daemon=True).start()
        threading.Thread(target=self.run_update, daemon=True).start()

    def load_config(self):
        config_path = "config.json"
        if not os.path.exists(config_path):
            default = {"minecraft_dir": "data/.minecraft", "java_path": "data/bin/javaw.exe"}
            json.dump(default, open(config_path, "w"), indent=4)
        return json.load(open(config_path))

    def load_versions(self):
        try:
            mc_dir = self.config["minecraft_dir"]
            os.makedirs(mc_dir, exist_ok=True)
            versions = minecraft_launcher_lib.utils.get_available_versions(mc_dir)
            self.version_box.clear()
            for v in versions:
                self.version_box.addItem(v["id"])
            self.status_label.setText("Versiones cargadas correctamente ✅")
        except Exception as e:
            self.status_label.setText(f"Error al cargar versiones: {e}")

    def run_update(self):
        try:
            self.status_label.setText("Buscando actualizaciones...")
            updated_files = updater.check_for_updates()
            if updated_files:
                self.status_label.setText(f"Archivos actualizados: {', '.join(updated_files)} ✅")
            else:
                self.status_label.setText("Launcher y archivos actualizados ✅")
        except Exception as e:
            self.status_label.setText(f"Error al actualizar: {e}")

    def launch_game(self):
        try:
            mc_dir = self.config["minecraft_dir"]
            java_path = self.config["java_path"]
            selected_version = self.version_box.currentText()

            self.status_label.setText("Descargando archivos necesarios...")
            minecraft_launcher_lib.install.install_minecraft_version(selected_version, mc_dir)

            options = {
                "username": "JugadorGTS",
                "uuid": "",
                "token": ""
            }

            command = minecraft_launcher_lib.command.get_minecraft_command(selected_version, mc_dir, options)
            command[0] = java_path  # usar tu propio java
            subprocess.Popen(command, cwd=mc_dir)
            self.status_label.setText("Minecraft iniciado ✅")
        except Exception as e:
            self.status_label.setText(f"Error al iniciar Minecraft: {e}")
            QMessageBox.critical(self, "Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = Launcher()
    launcher.show()
    sys.exit(app.exec())
