import os
import sys
import json
import zipfile
import shutil
import threading
import subprocess
import platform
import urllib.request
import hashlib
from pathlib import Path
import minecraft_launcher_lib

# PyQt6 imports
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QComboBox, QMessageBox, QSpacerItem, QSizePolicy, 
    QProgressBar, QFrame, QTextEdit, QSplitter, QDialog, QDialogButtonBox
)
from PyQt6.QtGui import QPixmap, QPalette, QBrush, QColor, QLinearGradient, QMovie, QCursor
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QUrl
from PyQt6.QtGui import QDesktopServices

# ---------------------------------------------------------
# UPDATE CHECKER
# ---------------------------------------------------------
class UpdateChecker:
    def __init__(self, repo_url, local_dir):
        self.repo_url = repo_url.rstrip('/')
        self.local_dir = Path(local_dir)
        self.raw_base = self.repo_url.replace('github.com', 'raw.githubusercontent.com') + '/main'
        
    def get_file_hash(self, filepath):
        """Calcula el hash MD5 de un archivo"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return None
    
    def check_updates(self):
        """Verifica si hay archivos actualizados en el repositorio"""
        try:
            # Descargar la lista de archivos del repositorio
            files_url = f"{self.repo_url}/contents"
            with urllib.request.urlopen(files_url) as response:
                repo_files = json.loads(response.read().decode())
            
            updated_files = []
            
            for file_info in repo_files:
                if file_info['type'] == 'file':
                    filename = file_info['name']
                    remote_hash = file_info['sha']  # GitHub usa SHA para tracking
                    local_file = self.local_dir / filename
                    
                    # Verificar si el archivo local existe y coincide
                    if local_file.exists():
                        # Para simplificar, comparamos tamaños primero
                        local_size = local_file.stat().st_size
                        remote_size = file_info['size']
                        
                        if local_size != remote_size:
                            updated_files.append(filename)
                        else:
                            # Si el tamaño es igual, comparamos contenido
                            local_hash = self.get_file_hash(local_file)
                            if local_hash and local_hash != remote_hash:
                                updated_files.append(filename)
                    else:
                        # Archivo nuevo que no existe localmente
                        updated_files.append(filename)
            
            return updated_files
            
        except Exception as e:
            print(f"Error checking updates: {e}")
            return []
    
    def download_updated_files(self, files, progress_callback=None):
        """Descarga los archivos actualizados"""
        try:
            total_files = len(files)
            for index, filename in enumerate(files):
                # Descargar archivo
                file_url = f"{self.raw_base}/{filename}"
                local_path = self.local_dir / filename
                
                # Crear directorio si no existe
                local_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Descargar archivo
                urllib.request.urlretrieve(file_url, local_path)
                
                if progress_callback:
                    progress = int((index + 1) / total_files * 100)
                    progress_callback(progress, f"Descargando {filename}")
            
            return True
        except Exception as e:
            print(f"Error downloading files: {e}")
            return False

# ---------------------------------------------------------
# UPDATE DIALOGS
# ---------------------------------------------------------
class UpdateAvailableDialog(QDialog):
    def __init__(self, file_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Actualizaciones Disponibles")
        self.setFixedSize(400, 200)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Message
        message = QLabel(f"Se encontraron {file_count} archivo(s) actualizado(s) en el repositorio.\n\n¿Quieres descargar las actualizaciones ahora?")
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)
        
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.later_button = QPushButton("Más tarde")
        self.later_button.clicked.connect(self.reject)
        button_layout.addWidget(self.later_button)
        
        self.download_button = QPushButton("Descargar ahora")
        self.download_button.clicked.connect(self.accept)
        button_layout.addWidget(self.download_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)

class UpdateCompleteDialog(QDialog):
    def __init__(self, file_count, parent=None):
        super().__init__(parent)
        self.setWindowTitle("¡Actualización Completa!")
        self.setFixedSize(400, 150)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        # Message
        message = QLabel(f"✅ ¡Se han descargado {file_count} archivo(s) actualizado(s)!\n\nEl launcher está actualizado.")
        message.setWordWrap(True)
        message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(message)
        
        layout.addSpacerItem(QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # OK button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        
        self.setLayout(layout)

# ---------------------------------------------------------
# SOCIAL MEDIA BUTTON
# ---------------------------------------------------------
class SocialMediaButton(QLabel):
    def __init__(self, icon_path, url, tooltip, parent=None):
        super().__init__(parent)
        self.url = url
        
        # Cargar y escalar el icono
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            scaled_pixmap = pixmap.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled_pixmap)
        else:
            # Icono de fallback si no existe el archivo
            self.setText("🌐")
            self.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setStyleSheet("font-size: 20px;")
        
        self.setFixedSize(36, 36)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setToolTip(tooltip)
        self.setStyleSheet(self.styleSheet() + """
            QLabel {
                background: rgba(0, 0, 0, 0.3);
                border-radius: 18px;
                padding: 2px;
            }
            QLabel:hover {
                background: rgba(0, 0, 0, 0.5);
                border: 1px solid #89c4f4;
            }
        """)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            QDesktopServices.openUrl(QUrl(self.url))
        super().mousePressEvent(event)

# ---------------------------------------------------------
# SIGNALS
# ---------------------------------------------------------
class Signals(QObject):
    status_updated = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    versions_loaded = pyqtSignal(list)
    update_check_complete = pyqtSignal(list)  # Lista de archivos actualizados
    update_download_complete = pyqtSignal(int)  # Número de archivos descargados

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
        
        # Configurar el verificador de actualizaciones
        self.repo_url = "https://github.com/king0piola/launcher-gts"
        self.update_checker = UpdateChecker(self.repo_url, ".")
        
        self.init_ui()
        self.load_config()
        self.load_version_json()
        
        # Verificar actualizaciones al iniciar
        self.check_for_updates_on_start()

    def check_for_updates_on_start(self):
        """Verifica actualizaciones al iniciar el launcher"""
        self.update_status("Buscando actualizaciones...")
        threading.Thread(target=self._check_updates_thread, daemon=True).start()

    def _check_updates_thread(self):
        """Hilo para verificar actualizaciones"""
        try:
            updated_files = self.update_checker.check_updates()
            self.signals.update_check_complete.emit(updated_files)
        except Exception as e:
            self.update_status(f"Error buscando actualizaciones: {e}")

    def handle_update_check_result(self, updated_files):
        """Maneja el resultado de la verificación de actualizaciones"""
        if updated_files:
            self.update_status(f"Se encontraron {len(updated_files)} archivo(s) actualizado(s)")
            # Mostrar diálogo preguntando si descargar actualizaciones
            self.ask_download_updates(updated_files)
        else:
            self.update_status("El launcher está actualizado ✔")
            # Continuar con la carga normal
            threading.Thread(target=self.load_versions, daemon=True).start()

    def ask_download_updates(self, updated_files):
        """Pregunta al usuario si quiere descargar las actualizaciones"""
        dialog = UpdateAvailableDialog(len(updated_files), self)
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            self.update_status("Descargando actualizaciones...")
            threading.Thread(target=self._download_updates_thread, 
                           args=(updated_files,), daemon=True).start()
        else:
            self.update_status("Actualizaciones pospuestas")
            # Continuar sin actualizar
            threading.Thread(target=self.load_versions, daemon=True).start()

    def _download_updates_thread(self, updated_files):
        """Hilo para descargar actualizaciones"""
        try:
            success = self.update_checker.download_updated_files(
                updated_files, 
                self._update_progress_callback
            )
            
            if success:
                self.signals.update_download_complete.emit(len(updated_files))
            else:
                self.update_status("Error descargando actualizaciones")
                
        except Exception as e:
            self.update_status(f"Error en descarga: {e}")

    def _update_progress_callback(self, progress, filename):
        """Callback para actualizar progreso de descarga"""
        self.signals.progress_updated.emit(progress)
        self.signals.status_updated.emit(filename)

    def handle_update_download_complete(self, file_count):
        """Maneja la finalización de la descarga de actualizaciones"""
        self.update_status("¡Actualización completada!")
        self.signals.progress_updated.emit(0)  # Ocultar barra de progreso
        
        # Mostrar diálogo de completado
        dialog = UpdateCompleteDialog(file_count, self)
        dialog.exec()
        
        # Recargar configuración por si hay cambios
        self.load_version_json()
        
        # Continuar con la carga normal
        threading.Thread(target=self.load_versions, daemon=True).start()

    # ----------------------------------------
    # ROUTE FIX – ALWAYS SAFE
    # ----------------------------------------
    def get_mc_dir(self):
        default_path = Path.home() / ".gts_minecraft"
        mc_dir = Path(self.config.get("minecraft_dir", str(default_path)))
        mc_dir.mkdir(parents=True, exist_ok=True)
        if "minecraft_dir" not in self.config:
            self.config["minecraft_dir"] = str(mc_dir)
            self.save_config()
        return mc_dir

    def save_config(self):
        with open("config.json", "w") as f:
            json.dump(self.config, f, indent=4)

    # ----------------------------------------
    # SIGNALS
    # ----------------------------------------
    def setup_signals(self):
        self.signals.status_updated.connect(self.update_status)
        self.signals.progress_updated.connect(self.update_progress)
        self.signals.versions_loaded.connect(self.populate_versions)
        self.signals.update_check_complete.connect(self.handle_update_check_result)
        self.signals.update_download_complete.connect(self.handle_update_download_complete)

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
            pix = QPixmap(logo_path).scaled(
                110, 110, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
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
        self.status_label = QLabel("Buscando actualizaciones...")
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

        # REDES SOCIALES EN ESQUINA INFERIOR IZQUIERDA
        social_layout = QHBoxLayout()
        social_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        
        # Crear directorio de assets si no existe
        os.makedirs("assets", exist_ok=True)
        
        # YouTube
        youtube_icon = "assets/youtube_icon.png"
        youtube_url = "https://www.youtube.com/@GTS-4V"
        self.youtube_btn = SocialMediaButton(youtube_icon, youtube_url, "YouTube: @GTS-4V")
        social_layout.addWidget(self.youtube_btn)
        
        # Instagram
        instagram_icon = "assets/instagram_icon.png"
        instagram_url = "https://www.instagram.com/gtsminecraft"
        self.instagram_btn = SocialMediaButton(instagram_icon, instagram_url, "Instagram: gtsminecraft")
        social_layout.addWidget(self.instagram_btn)
        
        # Si no existen los iconos, descargarlos automáticamente
        threading.Thread(target=self.download_social_icons, daemon=True).start()
        
        left_layout.addLayout(social_layout)

        # INFO DEL SISTEMA
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

    def download_social_icons(self):
        """Descarga los iconos de redes sociales si no existen"""
        icons = {
            "youtube_icon.png": "https://raw.githubusercontent.com/king0piola/launcher-gts/main/assets/youtube_icon.png",
            "instagram_icon.png": "https://raw.githubusercontent.com/king0piola/launcher-gts/main/assets/instagram_icon.png"
        }
        
        for icon_name, icon_url in icons.items():
            icon_path = f"assets/{icon_name}"
            if not os.path.exists(icon_path):
                try:
                    urllib.request.urlretrieve(icon_url, icon_path)
                    print(f"Descargado: {icon_name}")
                except Exception as e:
                    print(f"Error descargando {icon_name}: {e}")

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
        #playButton:hover {
            background: linear-gradient(#5ca465, #4492b8);
        }
        #playButton:disabled {
            background: linear-gradient(#555, #333);
            color: #888;
        }
        #sysInfo {
            font-size: 11px;
            color: #aaa;
        }
        QDialog {
            background: rgba(30, 30, 46, 0.95);
            border: 1px solid #444;
            border-radius: 10px;
        }
        QPushButton {
            background: rgba(0,0,0,0.25);
            padding: 8px 15px;
            border-radius: 6px;
            border: 1px solid #555;
            color: #e6e6e6;
        }
        QPushButton:hover {
            background: rgba(0,0,0,0.4);
        }
        QProgressBar {
            border: none;
            background: rgba(0,0,0,0.3);
            border-radius: 3px;
        }
        QProgressBar::chunk {
            background: linear-gradient(#67b26f, #4ca2cd);
            border-radius: 3px;
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
            cfg = {
                "minecraft_dir": str(Path.home() / ".gts_minecraft"),
                "java_path": "java",
                "max_ram": "4096",
                "username": "JugadorGTS"
            }
            with open("config.json", "w") as f:
                json.dump(cfg, f, indent=4)
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
            mc_dir = self.get_mc_dir()
            mods_dir = mc_dir / "mods"
            mods_dir.mkdir(parents=True, exist_ok=True)
            
            total_mods = len(self.mods_list)
            downloaded_mods = 0
            
            for mod in self.mods_list:
                url = self.mods_base_url + mod
                path = mods_dir / mod
                self.update_status(f"Descargando mod {mod} ({downloaded_mods+1}/{total_mods})")
                urllib.request.urlretrieve(url, path)
                downloaded_mods += 1
                
                # Actualizar progreso
                progress = int((downloaded_mods / total_mods) * 100)
                self.signals.progress_updated.emit(progress)
            
            self.update_status("Todos los mods descargados correctamente")
            
        except Exception as e:
            self.update_status(f"Error descargando mods: {e}")

    # ---------------------------------------------------------
    # LOAD MINECRAFT VERSIONS
    # ---------------------------------------------------------
    def load_versions(self):
        try:
            mc_dir = self.get_mc_dir()
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
            mc_dir = self.get_mc_dir()
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
