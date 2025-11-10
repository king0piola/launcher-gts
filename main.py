import sys, os, json, threading, subprocess
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import minecraft_launcher_lib
import updater

# ================================
# CONFIGURACIÓN
# ================================
MINECRAFT_DIR = os.path.join("data", ".minecraft")
JAVA_PATH = os.path.join("data", "bin", "javaw.exe")

os.makedirs(MINECRAFT_DIR, exist_ok=True)

# ================================
# CLASE PRINCIPAL
# ================================
class Launcher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Launcher GTS")
        self.setFixedSize(750, 450)
        self.setStyleSheet(open("assets/style.qss", "r").read())

        # UI
        central = QWidget()
        layout = QVBoxLayout(central)

        logo = QLabel()
        logo.setPixmap(QPixmap("assets/logo.png").scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.version_box = QComboBox()
        self.version_box.setObjectName("combo")

        self.status_label = QLabel("Cargando versiones de Minecraft...")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.play_button = QPushButton("▶ JUGAR")
        self.play_button.setObjectName("btnPlay")
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.launch_game)

        layout.addWidget(logo)
        layout.addWidget(QLabel("Selecciona versión de Minecraft:"))
        layout.addWidget(self.version_box)
        layout.addWidget(self.play_button)
        layout.addWidget(self.status_label)
        self.setCentralWidget(central)

        # Revisar actualizaciones
        threading.Thread(target=updater.update_from_github, daemon=True).start()

        # Cargar versiones después de construir toda la interfaz
        threading.Thread(target=self.load_versions, daemon=True).start()

    # ================================
    # CARGAR VERSIONES DISPONIBLES
    # ================================
    def load_versions(self):
        try:
            versions = minecraft_launcher_lib.utils.get_available_versions(MINECRAFT_DIR)
            for v in versions:
                if v.get("type") == "release":
                    self.version_box.addItem(v["id"])

            self.status_label.setText("Versiones cargadas.")
            self.play_button.setEnabled(True)

        except Exception as e:
            self.status_label.setText(f"Error al cargar versiones: {e}")

    # ================================
    # DESCARGAR E INICIAR EL JUEGO
    # ================================
    def launch_game(self):
        version = self.version_box.currentText()
        self.play_button.setEnabled(False)
        self.status_label.setText(f"Descargando Minecraft {version}...")

        def run():
            try:
                os.makedirs(MINECRAFT_DIR, exist_ok=True)

                # Instalar versión automáticamente
                minecraft_launcher_lib.install.install_minecraft_version(version, MINECRAFT_DIR)

                # Datos de inicio offline
                options = {
                    "username": "JugadorGTS",
                    "uuid": "00000000-0000-0000-0000-000000000000",
                    "token": "null"
                }

                # Configuración del juego
                launch_options = {
                    "username": options["username"],
                    "uuid": options["uuid"],
                    "token": options["token"],
                    "executablePath": JAVA_PATH,
                    "jvmArguments": ["-Xmx2G"]
                }

                # Obtener comando de inicio
                cmd = minecraft_launcher_lib.command.get_minecraft_command(
                    version, MINECRAFT_DIR, launch_options
                )

                self.status_label.setText("Iniciando Minecraft...")
                subprocess.Popen(cmd, cwd=MINECRAFT_DIR)
                self.close()

            except Exception as e:
                self.status_label.setText(f"Error: {e}")
                self.play_button.setEnabled(True)

        threading.Thread(target=run, daemon=True).start()

# ================================
# MAIN APP
# ================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = Launcher()
    launcher.show()
    sys.exit(app.exec())
