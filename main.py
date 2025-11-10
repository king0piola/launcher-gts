import sys, json, subprocess
from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QComboBox, QMessageBox
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt
import threading
import updater

# Verificar actualizaciones
threading.Thread(target=updater.update_from_github, daemon=True).start()

class Launcher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Launcher GTS")
        self.setFixedSize(700, 400)
        self.setStyleSheet(open("assets/style.qss", "r").read())
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        logo = QLabel()
        pixmap = QPixmap("assets/logo.png")
        logo.setPixmap(pixmap.scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.version_box = QComboBox()
        self.version_box.addItems(["1.20.1", "1.19.2", "1.18.2"])
        self.version_box.setObjectName("combo")

        play_button = QPushButton("Jugar")
        play_button.clicked.connect(self.launch_game)
        play_button.setObjectName("btnPlay")

        layout.addWidget(logo)
        layout.addWidget(QLabel("Versión de Minecraft:"))
        layout.addWidget(self.version_box)
        layout.addWidget(play_button)
        self.setLayout(layout)

    def launch_game(self):
        version = self.version_box.currentText()
        QMessageBox.information(self, "Iniciando", f"Preparando Minecraft {version}...")

        java_path = "data/bin/javaw.exe"
        if not os.path.exists(java_path):
            QMessageBox.critical(self, "Error", "No se encontró javaw.exe en data/bin/")
            return

        # Ejemplo: lanzar Minecraft con versión seleccionada
        subprocess.Popen([java_path, "-jar", f"data/versions/{version}.jar"])
        self.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    launcher = Launcher()
    launcher.show()
    sys.exit(app.exec())
