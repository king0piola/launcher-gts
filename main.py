import os
import sys
import json
import threading
import subprocess
import platform
import urllib.request
from pathlib import Path

import minecraft_launcher_lib

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QSpacerItem, QSizePolicy, QProgressBar, QFrame,
    QTextEdit, QSplitter
)
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QColor, QLinearGradient, QMovie
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject


# ---------------------------------------------------------
# SIGNALS
# ---------------------------------------------------------
class Signals(QObject):
    status_updated = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    versions_loaded = pyqtSignal(list)


# ---------------------------------------------------------
# MAIN LAUNCHER
# ---------------------------------------------------------
class ModernLauncher(QWidget):
    def __init__(self):
        super().__init__()

        self.signals = Signals()
        self.setup_signals()

        self.launcher_version = "0.0.0"
        self.mods_list = []
        self.mods_base_url = ""

        self.init_ui()
        self.load_config()
        self.load_version_json()

        threading.Thread(target=self.load_versions, daemon=True).start()


    # ----------------------------------------
    # SIGNALS
    # ----------------------------------------
    def setup_signals(self):
        self.signals.status_updated.connect(self.update_status)
        self.signals.progress_updated.connect(self.update_progress)
        self.signals.versions_loaded.connect(self.populate_versions)


    # ----------------------------------------
    # UI
    # ----------------------------------------
    def init_ui(self):
        self.setWindowTitle("GTS Studio Launcher")
        self.setFixedSize(1000, 700)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # LEFT PANEL
        left_panel = QFrame()
        left_panel.setObjectName("leftPanel")

        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(30, 30, 30, 30)

        # LOGO
        logo_path = "assets/logo.png"
        if os.path.exists(logo_path):
            logo = QLabel()
            pix = QPixmap(logo_path).scaled(110, 110, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(pix)
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            left_layout.addWidget(logo)

        # TITLE
        title = QLabel("GTS Studio")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(title)

        left_layout.addSpacerItem(QSpacerItem(1, 20))

        # STATUS
        self.status_label = QLabel("Inicializando...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(6)
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

        left_layout.addSpacerItem(QSpacerItem(1, 20))

        # CONTROLS FRAME
        controls = QFrame()
        layout_c = QVBoxLayout()

        lbl_v = QLabel("Versión de Minecraft:")
        lbl_v.setObjectName("sectionLabel")
        layout_c.addWidget(lbl_v)

        self.version_box = QComboBox()
        self.version_box.setObjectName("versionBox")
        layout_c.addWidget(self.version_box)

        layout_c.addSpacerItem(QSpacerItem(1, 15))

        # PLAY BUTTON
        self.play_button = QPushButton("🎮 Iniciar Minecraft")
        self.play_button.setObjectName("playButton")
        self.play_button.clicked.connect(self.launch_game)
        layout_c.addWidget(self.play_button)

        controls.setLayout(layout_c)
        left_layout.addWidget(controls)

        left_layout.addStretch()

        os_label = QLabel(f"Sistema: {platform.system()} {platform.release()}")
        os_label.setObjectName("sysInfo")
        left_layout.addWidget(os_label)

        left_panel.setLayout(left_layout)

        # RIGHT PANEL (CONSOLE)
        right_panel = QFrame()
        right_panel.setObjectName("rightPanel")

        rlayout = QVBoxLayout()
        label_console = QLabel("Consola")
        label_console.setObjectName("sectionLabel")
        rlayout.addWidget(label_console)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        rlayout.addWidget(self.console_output)

        right_panel.setLayout(rlayout)

        # SPLITTER
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 650])

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        self.setup_background()
        self.apply_stylesheet()


    # ----------------------------------------
    # STYLESHEET
    # ----------------------------------------
    def apply_stylesheet(self):

        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI';
                color: #e6e6e6;
            }

            #leftPanel {
                background: rgba(30, 30, 46, 0.82);
                border-right: 1px solid #444;
            }

            #rightPanel {
                background: rgba(20, 20, 30, 0.60);
            }

            #title {
                font-size: 26px;
                font-weight: bold;
                color: #89c4f4;
            }

            #statusLabel {
                background: rgba(0, 0, 0, 0.35);
                padding: 6px;
                border-radius: 8px;
                border: 1px solid #444;
            }

            #sectionLabel {
                color: #88bdf2;
                font-size: 13px;
                font-weight: bold;
            }

            #versionBox {
                background: rgba(0,0,0,0.25);
                border-radius: 8px;
                padding: 6px;
                border: 1px solid #555;
            }

            #playButton {
                background: linear-gradient(#67b26f, #4ca2cd);
                padding: 10px;
                font-size: 16px;
                color: white;
                border-radius: 10px;
                border: none;
                font-weight: bold;
            }

            #consoleOutput {
                background: rgba(0,0,0,0.35);
                border-radius: 8px;
                padding: 10px;
                font-family: Consolas;
                font-size: 12px;
                border: 1px solid #444;
            }

            #sysInfo {
                font-size: 11px;
                color: #aaa;
            }
        """)


    # ----------------------------------------
    # BACKGROUND GIF
    # ----------------------------------------
    def setup_background(self):
        gif_path = "assets/bg.gif"
        if not os.path.exists(gif_path):
            return

        self.movie = QMovie(gif_path)
        self.movie.frameChanged.connect(self.update_gif_frame)
        self.movie.start()

    def update_gif_frame(self):
        pix = self.movie.currentPixmap()
        if pix.isNull():
            return

        scaled = pix.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
        pal = QPalette()
        pal.setBrush(QPalette.ColorRole.Window, QBrush(scaled))
        self.setPalette(pal)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "movie"):
            self.update_gif_frame()


    # ---------------------------------------------------------
    # CONFIG
    # ---------------------------------------------------------
    def load_config(self):
        if not os.path.exists("config.json"):
            config = {
                "minecraft_dir": "data/.minecraft",
                "java_path": "java",
                "max_ram": "4096",
                "username": "JugadorGTS"
            }
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)

        with open("config.json") as f:
            self.config = json.load(f)



    # ---------------------------------------------------------
    # VERSION.JSON READING
    # ---------------------------------------------------------
    def load_version_json(self):
        url = "https://raw.githubusercontent.com/king0piola/launcher-gts/main/version.json"

        try:
            urllib.request.urlretrieve(url, "version.json")

            with open("version.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            self.launcher_version = data.get("launcher_version", "0.0.0")
            self.mods_list = data.get("mods", [])
            self.mods_base_url = data.get("mods_base_url", "")

            self.update_status(f"Launcher versión {self.launcher_version}")

        except Exception as e:
            self.update_status(f"Error leyendo version.json: {e}")


    # ---------------------------------------------------------
    # DOWNLOAD MODS
    # ---------------------------------------------------------
    def download_mods(self):
        try:
            mc_dir = Path(self.config["minecraft_dir"])
            mods_dir = mc_dir / "mods"
            mods_dir.mkdir(parents=True, exist_ok=True)

            for mod in self.mods_list:
                url = self.mods_base_url + mod
                path = mods_dir / mod

                self.update_status(f"Descargando mod {mod}")
                urllib.request.urlretrieve(url, path)

            self.update_status("Mods descargados correctamente")

        except Exception as e:
            self.update_status(f"Error descargando mods: {e}")


    # ---------------------------------------------------------
    # LOAD MINECRAFT VERSIONS
    # ---------------------------------------------------------
    def load_versions(self):
        try:
            mc_dir = self.config["minecraft_dir"]
            os.makedirs(mc_dir, exist_ok=True)

            versions = minecraft_launcher_lib.utils.get_available_versions(mc_dir)
            filtered = [v for v in versions if v["type"] == "release"]

            self.signals.versions_loaded.emit(filtered)

        except Exception as e:
            self.update_status(f"Error cargando versiones: {e}")


    def populate_versions(self, versions):
        self.version_box.clear()
        for v in versions:
            self.version_box.addItem(v["id"])

        self.update_status(f"Versiones cargadas: {len(versions)}")


    # ---------------------------------------------------------
    # STATUS + PROGRESS
    # ---------------------------------------------------------
    def update_status(self, msg):
        self.status_label.setText(msg)
        self.console_output.append(f"[INFO] {msg}")

    def update_progress(self, v):
        self.progress_bar.setVisible(v > 0 and v < 100)
        self.progress_bar.setValue(v)


    # ---------------------------------------------------------
    # LAUNCH GAME
    # ---------------------------------------------------------
    def launch_game(self):

        self.play_button.setEnabled(False)

        threading.Thread(target=self._launch_thread, daemon=True).start()


    def _launch_thread(self):
        try:
            version = self.version_box.currentText()
            mc_dir = self.config["minecraft_dir"]

            self.update_status(f"Instalando {version}...")
            minecraft_launcher_lib.install.install_minecraft_version(
                version, mc_dir, callback=self._install_callback
            )

            # Mods
            self.update_status("Descargando mods...")
            self.download_mods()

            # Run game
            self.update_status("Iniciando Minecraft...")

            options = {
                "username": self.config["username"],
                "uuid": "",
                "token": "",
                "jvmArguments": [
                    f"-Xmx{self.config['max_ram']}M"
                ]
            }

            cmd = minecraft_launcher_lib.command.get_minecraft_command(version, mc_dir, options)
            cmd[0] = self.config["java_path"]

            subprocess.Popen(cmd, cwd=mc_dir)

            self.update_status("Minecraft iniciado ✔️")

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

        finally:
            self.play_button.setEnabled(True)


    def _install_callback(self, type, cur, tot):
        if tot == 0:
            return
        percent = int((cur / tot) * 100)
        self.signals.progress_updated.emit(percent)



# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    launcher = ModernLauncher()
    launcher.show()

    sys.exit(app.exec())
