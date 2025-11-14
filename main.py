import os
import sys
import json
import threading
import subprocess
import platform
from pathlib import Path

import minecraft_launcher_lib

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QMessageBox,
    QSpacerItem, QSizePolicy, QProgressBar, QFrame,
    QTextEdit, QSplitter
)

from PyQt6.QtGui import (
    QPixmap, QPalette, QBrush, QColor,
    QLinearGradient, QMovie
)

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject

# -------------------------------
#        SISTEMA DE SEÑALES
# -------------------------------

class Signals(QObject):
    status = pyqtSignal(str)
    progress = pyqtSignal(int)
    versions = pyqtSignal(list)
    update_finished = pyqtSignal(list)


# -------------------------------
#        MAIN LAUNCHER
# -------------------------------

class ModernLauncher(QWidget):
    def __init__(self):
        super().__init__()

        self.signals = Signals()
        self.connect_signals()

        self.init_ui()
        self.load_config()

        # Tareas iniciales
        threading.Thread(target=self.load_versions, daemon=True).start()
        threading.Thread(target=self.check_initial_updates, daemon=True).start()

    # -------------------------------
    #      CONECTAR SEÑALES
    # -------------------------------
    def connect_signals(self):
        self.signals.status.connect(self.update_status)
        self.signals.progress.connect(self.update_progress)
        self.signals.versions.connect(self.populate_versions)
        self.signals.update_finished.connect(self.on_update_finished)

    # -------------------------------
    #      INTERFAZ GRÁFICA
    # -------------------------------
    def init_ui(self):
        self.setWindowTitle("GTS Studio Launcher")
        self.setFixedSize(1000, 700)
        self.setStyleSheet(self.styles())

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # PANEL IZQUIERDO
        left_panel = self.left_panel()

        # PANEL DERECHO
        right_panel = self.right_panel()

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([380, 620])
        splitter.setHandleWidth(2)

        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

        self.setup_background()

    # -------------------------------
    #   PANEL IZQUIERDO (CONTROLES)
    # -------------------------------
    def left_panel(self):
        frame = QFrame()
        frame.setObjectName("leftPanel")

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)

        # LOGO
        logo_path = "assets/logo.png"
        if os.path.exists(logo_path):
            logo_label = QLabel()
            pixmap = QPixmap(logo_path).scaled(110, 110, Qt.AspectRatioMode.KeepAspectRatio)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo_label)

        title = QLabel("GTS Studio")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addSpacerItem(QSpacerItem(0, 20))

        # STATUS
        self.status_label = QLabel("Inicializando launcher…")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(6)
        layout.addWidget(self.progress_bar)

        layout.addSpacerItem(QSpacerItem(0, 30))

        # CONTROLES
        controls = QFrame()
        controls.setObjectName("controlsFrame")
        c_layout = QVBoxLayout()

        version_label = QLabel("Versión de Minecraft:")
        version_label.setObjectName("sectionLabel")

        c_layout.addWidget(version_label)

        self.version_box = QComboBox()
        self.version_box.setObjectName("versionBox")
        c_layout.addWidget(self.version_box)

        c_layout.addSpacerItem(QSpacerItem(0, 20))

        # BOTÓN JUGAR
        self.play_button = QPushButton("🎮 Iniciar Minecraft")
        self.play_button.setObjectName("playButton")
        self.play_button.clicked.connect(self.launch_game)
        c_layout.addWidget(self.play_button)

        # BOTÓN ACTUALIZAR
        self.update_button = QPushButton("🔄 Actualizar Launcher")
        self.update_button.setObjectName("secondaryButton")
        self.update_button.clicked.connect(self.run_update)
        c_layout.addWidget(self.update_button)

        controls.setLayout(c_layout)
        layout.addWidget(controls)
        layout.addStretch()

        # Info del sistema
        sys_info = QLabel(f"Sistema: {platform.system()} {platform.release()}")
        sys_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sys_info.setObjectName("sysInfo")
        layout.addWidget(sys_info)

        frame.setLayout(layout)
        return frame

    # -------------------------------
    #      PANEL DERECHO (CONSOLA)
    # -------------------------------
    def right_panel(self):
        frame = QFrame()
        frame.setObjectName("rightPanel")

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        label = QLabel("Consola")
        label.setObjectName("sectionLabel")
        layout.addWidget(label)

        self.console_output = QTextEdit()
        self.console_output.setObjectName("consoleOutput")
        self.console_output.setReadOnly(True)
        layout.addWidget(self.console_output)

        frame.setLayout(layout)
        return frame

    # -------------------------------
    #       FONDO ANIMADO GIF
    # -------------------------------
    def setup_background(self):
        gif_path = "assets/bg.gif"

        if os.path.exists(gif_path):
            self.movie = QMovie(gif_path)
            self.movie.frameChanged.connect(self.update_gif_frame)
            self.movie.start()
        else:
            gradient = QLinearGradient(0, 0, 0, self.height())
            gradient.setColorAt(0, QColor(30, 30, 50))
            gradient.setColorAt(1, QColor(20, 20, 30))

            palette = self.palette()
            palette.setBrush(QPalette.ColorRole.Window, QBrush(gradient))
            self.setPalette(palette)

    def update_gif_frame(self):
        pixmap = self.movie.currentPixmap()
        if pixmap.isNull():
            return

        scaled = pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        palette = QPalette()
        palette.setBrush(QPalette.ColorRole.Window, QBrush(scaled))
        self.setPalette(palette)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "movie"):
            self.update_gif_frame()

    # -------------------------------
    #       CONFIGURACIÓN
    # -------------------------------
    def load_config(self):
        path = "config.json"
        system = platform.system().lower()

        default_java = {
            "windows": "data/bin/javaw.exe",
            "darwin": "data/bin/java",
            "linux": "data/bin/java"
        }.get(system, "java")

        if not os.path.exists(path):
            base = {
                "minecraft_dir": "data/.minecraft",
                "java_path": default_java,
                "max_ram": "4096",
                "username": "JugadorGTS"
            }
            with open(path, "w") as f:
                json.dump(base, f, indent=4)

        self.config = json.load(open(path, "r"))

    # -------------------------------
    #      ACTUALIZACIÓN DE UI
    # -------------------------------
    def update_status(self, text):
        self.status_label.setText(text)
        self.console_output.append(f"[INFO] {text}")

    def update_progress(self, p):
        self.progress_bar.setValue(p)
        self.progress_bar.setVisible(p > 0 and p < 100)

    # -------------------------------
    #      VERSIONES DE MINECRAFT
    # -------------------------------
    def populate_versions(self, versions):
        self.version_box.clear()
        for v in versions:
            self.version_box.addItem(v["id"])

        self.update_status(f"Versiones cargadas: {len(versions)}")

    def load_versions(self):
        try:
            mc = self.config["minecraft_dir"]
            os.makedirs(mc, exist_ok=True)

            self.signals.status.emit("Buscando versiones disponibles…")

            all_versions = minecraft_launcher_lib.utils.get_available_versions(mc)
            releases = [v for v in all_versions if v["type"] == "release"]

            self.signals.versions.emit(releases)
        except Exception as e:
            self.signals.status.emit(f"Error cargando versiones: {e}")

    # -------------------------------
    #       ACTUALIZADOR
    # -------------------------------
    def check_initial_updates(self):
        self.signals.status.emit("Verificando actualizaciones...")
        try:
            import updater
            updated = updater.check_for_updates()
            self.signals.update_finished.emit(updated)
        except Exception as e:
            self.signals.status.emit(f"Error en actualización: {e}")

    def run_update(self):
        threading.Thread(target=self.check_initial_updates, daemon=True).start()

    def on_update_finished(self, updated):
        if updated:
            self.update_status(f"Actualizados {len(updated)} archivos ✔")
        else:
            self.update_status("Todo está actualizado ✔")

    # -------------------------------
    #       LANZAR MINECRAFT
    # -------------------------------
    def launch_game(self):
        if self.version_box.count() == 0:
            QMessageBox.warning(self, "Error", "No hay versiones disponibles")
            return

        self.play_button.setEnabled(False)
        threading.Thread(target=self._launch_thread, daemon=True).start()

    def _launch_thread(self):
        try:
            mc = self.config["minecraft_dir"]
            java = self.config["java_path"]
            version = self.version_box.currentText()

            self.signals.status.emit(f"Instalando {version}…")
            minecraft_launcher_lib.install.install_minecraft_version(
                version, mc, callback=self._install_callback
            )

            self.signals.status.emit("Iniciando Minecraft…")

            options = {
                "username": self.config.get("username", "JugadorGTS"),
                "uuid": "",
                "token": "",
                "jvmArguments": [
                    f"-Xmx{self.config.get('max_ram', '4096')}M",
                    "-XX:+UseG1GC"
                ]
            }

            cmd = minecraft_launcher_lib.command.get_minecraft_command(
                version, mc, options
            )
            cmd[0] = java

            subprocess.Popen(cmd, cwd=mc)

            self.signals.progress.emit(100)
            self.signals.status.emit("Minecraft iniciado ✔")

            QTimer.singleShot(2000, lambda: self.signals.progress.emit(0))

        except Exception as e:
            self.signals.status.emit(f"Error: {e}")
        finally:
            self.play_button.setEnabled(True)

    def _install_callback(self, t, cur, tot):
        if tot == 0:
            return
        if t == "downloading":
            self.signals.progress.emit(int((cur / tot) * 50))
        elif t == "extracting":
            self.signals.progress.emit(50 + int((cur / tot) * 40))

    # -------------------------------
    #        ESTILOS CSS
    # -------------------------------
    def styles(self):
        return """
        QWidget {
            font-family: 'Segoe UI';
            color: #e0e0e0;
        }

        #leftPanel {
            background: rgba(30,30,46,0.82);
            border-right: 1px solid #444;
        }

        #rightPanel {
            background: rgba(20,20,30,0.65);
        }

        #title {
            font-size: 28px;
            font-weight: bold;
            color: #89c4f4;
            margin-top: 10px;
        }

        #statusLabel {
            padding: 8px;
            background: rgba(0,0,0,0.3);
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
            background: rgba(0,0,0,0.25);
            padding: 15px;
            border-radius: 14px;
            border: 1px solid #444;
        }

        #versionBox {
            background: rgba(0,0,0,0.3);
            padding: 8px;
            border-radius: 8px;
            border: 1px solid #555;
        }

        #playButton {
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                stop:0 #67b26f, stop:1 #4ca2cd);
            border: none;
            padding: 12px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: bold;
        }

        #secondaryButton {
            background: rgba(60,60,80,0.7);
            border: 1px solid #555;
            padding: 10px;
            border-radius: 8px;
        }

        #consoleOutput {
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            font-family: Consolas;
            font-size: 12px;
            border: 1px solid #444;
            padding: 10px;
        }

        #sysInfo {
            font-size: 11px;
            color: #aaa;
        }
        """


# -------------------------------
#              MAIN
# -------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)

    launcher = ModernLauncher()
    launcher.show()

    sys.exit(app.exec())
