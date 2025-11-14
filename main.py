import os
import sys
import json
import threading
import subprocess
import platform
from pathlib import Path

import minecraft_launcher_lib
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QPushButton, QComboBox, QMessageBox,
                            QSpacerItem, QSizePolicy, QProgressBar, QFrame,
                            QTextEdit, QSplitter)
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QFont, QColor, QLinearGradient, QMovie
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
import updater


class Signals(QObject):
    status_updated = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    versions_loaded = pyqtSignal(list)
    update_finished = pyqtSignal(list)


class ModernLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.signals = Signals()
        self.setup_signals()
        self.init_ui()
        self.load_config()

        # Tareas iniciales
        threading.Thread(target=self.load_versions, daemon=True).start()
        threading.Thread(target=self.check_initial_updates, daemon=True).start()

    def setup_signals(self):
        self.signals.status_updated.connect(self.update_status)
        self.signals.progress_updated.connect(self.update_progress)
        self.signals.versions_loaded.connect(self.populate_versions)
        self.signals.update_finished.connect(self.on_update_finished)

    def init_ui(self):
        self.setWindowTitle("GTS Studio Launcher")
        self.setFixedSize(1000, 700)
        self.setStyleSheet(self.get_stylesheet())

        # MAIN LAYOUT
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # LEFT PANEL
        left_panel = QFrame()
        left_panel.setObjectName("leftPanel")
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(30, 30, 30, 30)

        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
            left_layout.addWidget(logo_label)

        title = QLabel("GTS Studio")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(title)

        left_layout.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # STATUS
        self.status_label = QLabel("Inicializando launcher...")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(6)
        left_layout.addWidget(self.progress_bar)

        left_layout.addSpacerItem(QSpacerItem(0, 30, QSizePolicy.Minimum, QSizePolicy.Fixed))

        # CONTROLES
        controls_frame = QFrame()
        controls_frame.setObjectName("controlsFrame")
        controls_layout = QVBoxLayout()

        version_label = QLabel("Versión de Minecraft:")
        version_label.setObjectName("sectionLabel")
        controls_layout.addWidget(version_label)

        self.version_box = QComboBox()
        self.version_box.setObjectName("versionBox")
        controls_layout.addWidget(self.version_box)

        controls_layout.addSpacerItem(QSpacerItem(0, 15, QSizePolicy.Minimum, QSizePolicy.Fixed))

        self.play_button = QPushButton("🎮 Iniciar Minecraft")
        self.play_button.setObjectName("playButton")
        self.play_button.clicked.connect(self.launch_game)
        controls_layout.addWidget(self.play_button)

        self.update_button = QPushButton("🔄 Actualizar Launcher")
        self.update_button.setObjectName("secondaryButton")
        self.update_button.clicked.connect(self.run_update)
        controls_layout.addWidget(self.update_button)

        controls_frame.setLayout(controls_layout)
        left_layout.addWidget(controls_frame)

        left_layout.addStretch()

        sys_info = QLabel(f"Sistema: {platform.system()} {platform.release()}")
        sys_info.setObjectName("sysInfo")
        left_layout.addWidget(sys_info)

        left_panel.setLayout(left_layout)

        # RIGHT PANEL (CONSOLE)
        right_panel = QFrame()
        right_panel.setObjectName("rightPanel")
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(20, 20, 20, 20)

        console_label = QLabel("Consola")
        console_label.setObjectName("sectionLabel")
        right_layout.addWidget(console_label)

        self.console_output = QTextEdit()
        self.console_output.setObjectName("consoleOutput")
        self.console_output.setReadOnly(True)
        right_layout.addWidget(self.console_output)

        right_panel.setLayout(right_layout)

        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])
        splitter.setHandleWidth(2)

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        # Fondo GIF
        self.setup_background()

    def get_stylesheet(self):
        return """
            QWidget {
                font-family: 'Segoe UI', 'Arial';
                color: #e0e0e0;
            }

            #leftPanel {
                background: rgba(30, 30, 46, 0.80);
                border-right: 1px solid #444;
            }

            #rightPanel {
                background: rgba(20, 20, 30, 0.65);
            }

            #title {
                font-size: 28px;
                font-weight: bold;
                color: #89c4f4;
                margin: 10px 0px;
            }

            #statusLabel {
                font-size: 14px;
                padding: 8px 12px;
                background: rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                border: 1px solid #444;
            }

            #sectionLabel {
                font-size: 14px;
                font-weight: bold;
                color: #89c4f4;
                margin-bottom: 5px;
            }

            #controlsFrame {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 12px;
                padding: 15px;
                border: 1px solid #444;
            }

            QProgressBar {
                border: none;
                border-radius: 3px;
                background: rgba(0, 0, 0, 0.3);
            }

            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #89c4f4, stop:1 #6789f4);
                border-radius: 3px;
            }

            #versionBox {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid #555;
                border-radius: 8px;
                padding: 8px 12px;
            }

            #playButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #67b26f, stop:1 #4ca2cd);
                border: none;
                border-radius: 10px;
                padding: 12px;
                font-size: 16px;
                font-weight: bold;
                color: white;
            }

            #secondaryButton {
                background: rgba(60, 60, 80, 0.7);
                border: 1px solid #555;
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
            }

            #consoleOutput {
                background: rgba(0, 0, 0, 0.3);
                border: 1px solid #444;
                border-radius: 8px;
                font-family: Consolas;
                font-size: 12px;
                color: #a0a0a0;
                padding: 10px;
            }

            #sysInfo {
                font-size: 11px;
                color: #888;
                text-align: center;
            }
        """

    # ---------------------------------------------------------
    #                    FONDO ANIMADO GIF
    # ---------------------------------------------------------
    def setup_background(self):
        gif_path = os.path.join("assets", "bg.gif")

        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            self.movie.frameChanged.connect(self.update_gif_frame)
            self.movie.start()
        else:
            self.setAutoFillBackground(True)
            palette = self.palette()
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, QColor(30, 30, 50))
            gradient.setColorAt(1, QColor(20, 20, 30))
            palette.setBrush(QPalette.Window, QBrush(gradient))
            self.setPalette(palette)

    def update_gif_frame(self):
        frame = self.movie.currentPixmap()
        if not frame.isNull():
            scaled = frame.scaled(
                self.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            palette = QPalette()
            palette.setBrush(QPalette.Window, QBrush(scaled))
            self.setPalette(palette)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "movie"):
            self.update_gif_frame()

    # ---------------------------------------------------------

    def load_config(self):
        config_path = "config.json"
        system = platform.system().lower()

        if system == "windows":
            default_java = "data/bin/javaw.exe"
        elif system == "darwin":
            default_java = "data/bin/java"
        else:
            default_java = "data/bin/java"

        if not os.path.exists(config_path):
            default_config = {
                "minecraft_dir": "data/.minecraft",
                "java_path": default_java,
                "max_ram": "4096",
                "username": "JugadorGTS"
            }
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=4)

        with open(config_path, "r") as f:
            self.config = json.load(f)

        if not os.path.exists(self.config["java_path"]):
            self.config["java_path"] = "java"

    def update_status(self, message):
        self.status_label.setText(message)
        self.console_output.append(f"[INFO] {message}")

    def update_progress(self, value):
        self.progress_bar.setValue(value)
        self.progress_bar.setVisible(value > 0 and value < 100)

    def populate_versions(self, versions):
        self.version_box.clear()
        for version in versions:
            self.version_box.addItem(version["id"])
        self.update_status(f"Versiones cargadas: {len(versions)}")

    def load_versions(self):
        try:
            mc_dir = self.config["minecraft_dir"]
            os.makedirs(mc_dir, exist_ok=True)

            self.signals.status_updated.emit("Buscando versiones disponibles...")
            versions = minecraft_launcher_lib.utils.get_available_versions(mc_dir)

            release_versions = [v for v in versions if v["type"] == "release"]
            self.signals.versions_loaded.emit(release_versions)

        except Exception as e:
            self.signals.status_updated.emit(f"Error cargando versiones: {str(e)}")

    def check_initial_updates(self):
        self.signals.status_updated.emit("Verificando actualizaciones...")
        try:
            updated_files = updater.check_for_updates()
            if updated_files:
                self.signals.update_finished.emit(updated_files)
            else:
                self.signals.status_updated.emit("Launcher listo ✅")
        except Exception as e:
            self.signals.status_updated.emit(f"Error en actualización: {str(e)}")

    def run_update(self):
        threading.Thread(target=self.check_initial_updates, daemon=True).start()

    def on_update_finished(self, updated_files):
        if updated_files:
            self.update_status(f"Actualizados {len(updated_files)} archivos ✅")
        else:
            self.update_status("Todo está actualizado ✅")

    def launch_game(self):
        if self.version_box.count() == 0:
            QMessageBox.warning(self, "Error", "No hay versiones disponibles")
            return

        self.play_button.setEnabled(False)
        threading.Thread(target=self._launch_game_thread, daemon=True).start()

    def _launch_game_thread(self):
        try:
            mc_dir = self.config["minecraft_dir"]
            java_path = self.config["java_path"]
            selected_version = self.version_box.currentText()

            self.signals.status_updated.emit(f"Instalando versión {selected_version}...")
            self.signals.progress_updated.emit(30)

            minecraft_launcher_lib.install.install_minecraft_version(
                selected_version,
                mc_dir,
                callback=self._install_callback
            )

            self.signals.progress_updated.emit(80)
            self.signals.status_updated.emit("Iniciando Minecraft...")

            options = {
                "username": self.config.get("username", "JugadorGTS"),
                "uuid": "",
                "token": "",
                "jvmArguments": [
                    f"-Xmx{self.config.get('max_ram', '4096')}M",
                    "-XX:+UnlockExperimentalVMOptions",
                    "-XX:+UseG1GC",
                    "-XX:G1NewSizePercent=20",
                    "-XX:G1ReservePercent=20",
                    "-XX:MaxGCPauseMillis=50",
                    "-XX:G1HeapRegionSize=32M"
                ]
            }

            command = minecraft_launcher_lib.command.get_minecraft_command(
                selected_version, mc_dir, options
            )
            command[0] = java_path

            self.signals.progress_updated.emit(100)
            subprocess.Popen(command, cwd=mc_dir)

            self.signals.status_updated.emit("Minecraft iniciado ✅")
            QTimer.singleShot(2000, lambda: self.signals.progress_updated.emit(0))

        except Exception as e:
            self.signals.status_updated.emit(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"No se pudo iniciar Minecraft:\n{str(e)}")
        finally:
            self.play_button.setEnabled(True)

    def _install_callback(self, progress_type, current, total):
        if progress_type == "downloading":
            percent = int((current / total) * 50)
            self.signals.progress_updated.emit(percent)
        elif progress_type == "extracting":
            percent = 50 + int((current / total) * 30)
            self.signals.progress_updated.emit(percent)


if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setEffectEnabled(Qt.UIEffect.UI_AnimateCombo, False)

    launcher = ModernLauncher()
    launcher.show()

    sys.exit(app.exec())

