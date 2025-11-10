import os, sys, json, threading, subprocess
import minecraft_launcher_lib
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QMessageBox, QSpacerItem, QSizePolicy
from PyQt6.QtGui import QPixmap, QPalette, QBrush
from PyQt6.QtCore import Qt
import updater

class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Launcher GTS")
        self.resize(600, 400)

        # --- Estilo visual ---
        self.setStyleSheet("""
            QLabel, QPushButton, QComboBox {
                font-family: 'Segoe UI';
                color: white;
            }
            QPushButton {
                background-color: rgba(25,25,25,0.85);
                border-radius: 8px;
                padding: 8px;
                border: 1px solid #3a3a3a;
            }
            QPushButton:hover {
                background-color: rgba(40,40,40,0.9);
            }
            QComboBox {
                background-color: rgba(30,30,30,0.85);
                border-radius: 6px;
                padding: 6px;
            }
        """)

        # --- Fondo ---
        bg_path = os.path.join("assets", "bg.jpg")
        if os.path.exists(bg_path):
            palette = QPalette()
            palette.setBrush(QPalette.ColorRole.Window, QBrush(QPixmap(bg_path).scaled(600, 400, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)))
            self.setPalette(palette)

        # --- Layout principal ---
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Logo
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path).scaled(160, 160, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo_label)

        layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Estado
        self.status_label = QLabel("Iniciando launcher...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        layout.addSpacerItem(QSpacerItem(0, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Selector de versión
        self.version_box = QComboBox()
        layout.addWidget(self.version_box)

        # Botones
        self.refresh_button = QPushButton("🔄 Actualizar launcher y archivos")
        self.refresh_button.clicked.connect(lambda: threading.Thread(target=self.run_update, daemon=True).start())
        layout.addWidget(self.refresh_button)

        self.play_button = QPushButton("▶ Iniciar Minecraft")
        self.play_button.clicked.connect(lambda: threading.Thread(target=self.launch_game, daemon=True).start())
        layout.addWidget(self.play_button)

        self.setLayout(layout)

        # --- Configuración ---
        self.config = self.load_config()

        # --- Tareas paralelas ---
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
