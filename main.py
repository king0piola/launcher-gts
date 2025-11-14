import os
import sys
import json
import urllib.request
import platform
from pathlib import Path
import threading

import minecraft_launcher_lib

from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QMovie
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QSpacerItem, QSizePolicy, QProgressBar, QFrame,
    QTextEdit, QSplitter
)


# ---------------------------------------------------------
#  SEÑALES MULTIHILO
# ---------------------------------------------------------
from PyQt6.QtCore import QObject, pyqtSignal

class WorkerSignals(QObject):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finish = pyqtSignal()


# ---------------------------------------------------------
#  LANZADOR PRINCIPAL
# ---------------------------------------------------------
class ModernLauncher(QWidget):

    def __init__(self):
        super().__init__()

        self.signals = WorkerSignals()
        self.signals.progress.connect(self.on_progress)
        self.signals.status.connect(self.update_status)
        self.signals.finish.connect(self.on_finish)

        self.launcher_version = ""
        self.mods_list = []
        self.mods_base_url = ""

        # leer version.json antes de la UI
        self.load_version_info()

        self.init_ui()
        self.load_config()


    # ---------------------------------------------------------
    #  LEER version.json DESDE LOCAL O GITHUB
    # ---------------------------------------------------------
    def load_version_info(self):
        url = "https://raw.githubusercontent.com/king0piola/launcher-gts/main/version.json"
        file_path = "version.json"

        try:
            # Si no existe, lo descarga
            if not os.path.exists(file_path):
                urllib.request.urlretrieve(url, file_path)

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.launcher_version = data.get("launcher_version", "0.0.0")
            self.mods_list = data.get("mods", [])
            self.mods_base_url = data.get("mods_base_url", "")

        except Exception as e:
            self.launcher_version = "0.0.0"
            self.mods_list = []
            self.mods_base_url = ""
            print("Error leyendo version.json:", e)


    # ---------------------------------------------------------
    #  DESCARGA AUTOMÁTICA DE MODS
    # ---------------------------------------------------------
    def download_mods(self):
        """
        Descarga todos los mods en la carpeta .minecraft/mods/
        """
        try:
            game_dir = Path(minecraft_launcher_lib.utils.get_minecraft_directory())
            mods_folder = game_dir / "mods"
            mods_folder.mkdir(parents=True, exist_ok=True)

            if not self.mods_base_url or not self.mods_list:
                self.update_status("No hay mods para descargar.")
                return

            for mod in self.mods_list:
                url = self.mods_base_url + mod
                output = mods_folder / mod

                self.update_status(f"Descargando mod: {mod}")

                try:
                    urllib.request.urlretrieve(url, output)
                except Exception as e:
                    self.update_status(f"Error descargando {mod}: {e}")

            self.update_status("Mods instalados correctamente.")

        except Exception as e:
            self.update_status(f"Error general descargando mods: {e}")


    # ---------------------------------------------------------
    #  UI PRINCIPAL
    # ---------------------------------------------------------
    def init_ui(self):
        self.setWindowTitle("GTS Launcher")
        self.setGeometry(200, 100, 1100, 650)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # -------- LADO IZQUIERDO PANEL --------
        left_panel = QFrame()
        left_panel.setObjectName("leftPanel")
        left_layout = QVBoxLayout(left_panel)

        # versión del launcher
        version_label = QLabel(f"Launcher v{self.launcher_version}")
        version_label.setObjectName("versionLabel")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(version_label)

        # selector de versión de Minecraft
        self.version_combo = QComboBox()
        left_layout.addWidget(self.version_combo)

        # botón de jugar
        self.play_btn = QPushButton("Jugar")
        self.play_btn.clicked.connect(self.play)
        left_layout.addWidget(self.play_btn)

        left_layout.addStretch()

        # -------- LADO DERECHO: FONDO GIF + CONSOLA --------
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)

        self.gif_label = QLabel()
        self.gif_label.setFixedHeight(350)
        self.gif_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        movie = QMovie("bg.gif")
        movie.setScaledSize(QSize(900, 350))
        self.gif_label.setMovie(movie)
        movie.start()

        right_layout.addWidget(self.gif_label)

        # consola
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        right_layout.addWidget(self.console)

        # progress
        self.progress = QProgressBar()
        right_layout.addWidget(self.progress)

        # SPLITTER
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 850])

        main_layout.addWidget(splitter)

        # estilos
        self.setStyleSheet(self.styles())


    # ---------------------------------------------------------
    #  ESTILOS CSS
    # ---------------------------------------------------------
    def styles(self):
        return """
        #leftPanel {
            background: #1b1b1b;
        }
        #versionLabel {
            color: #ccc;
            font-size: 12px;
            margin-top: 10px;
        }
        QPushButton {
            background: #3a3a3a;
            color: white;
            padding: 10px;
            border-radius: 6px;
        }
        QPushButton:hover {
            background: #505050;
        }
        QComboBox {
            background: #3a3a3a;
            color: white;
            padding: 5px;
        }
        QTextEdit {
            background: #111;
            color: #0f0;
            font-family: Consolas;
            font-size: 12px;
        }
        """


    # ---------------------------------------------------------
    #  LOGS EN CONSOLA
    # ---------------------------------------------------------
    def update_status(self, text):
        self.console.append(text)


    # ---------------------------------------------------------
    #  PROGRESO
    # ---------------------------------------------------------
    def on_progress(self, val):
        self.progress.setValue(val)

    def on_finish(self):
        self.update_status("Listo.")


    # ---------------------------------------------------------
    #  CARGA CONFIG
    # ---------------------------------------------------------
    def load_config(self):
        try:
            self.update_status("Cargando versiones...")
            versions = minecraft_launcher_lib.utils.get_version_list()
            for v in versions:
                self.version_combo.addItem(v["id"])
        except:
            self.update_status("No se pudieron cargar versiones.")


    # ---------------------------------------------------------
    #  BOTÓN JUGAR
    # ---------------------------------------------------------
    def play(self):
        threading.Thread(target=self.run_game, daemon=True).start()

    def run_game(self):
        version = self.version_combo.currentText()

        self.update_status("Descargando mods...")
        self.download_mods()

        self.update_status("Iniciando Minecraft...")

        game_directory = minecraft_launcher_lib.utils.get_minecraft_directory()

        options = {
            "username": "Player",
            "uuid": "",
            "token": ""
        }

        minecraft_launcher_lib.command.run_command(version, game_directory, options)

        self.update_status("Minecraft cerrado.")



# ---------------------------------------------------------
#  MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    launcher = ModernLauncher()
    launcher.show()

    sys.exit(app.exec())
