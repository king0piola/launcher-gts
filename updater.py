import os
import hashlib
import requests
import zipfile
import io
import shutil

GITHUB_REPO = "https://github.com/king0piola/launcher-gts"
GITHUB_ZIP = GITHUB_REPO + "/archive/refs/heads/main.zip"
LOCAL_DIR = os.path.dirname(os.path.abspath(__file__))
TEMP_DIR = os.path.join(LOCAL_DIR, "update_temp")

def file_hash(path):
    if not os.path.exists(path):
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()

def check_for_updates():
    try:
        # Descarga el repo comprimido
        if os.path.exists(TEMP_DIR):
            shutil.rmtree(TEMP_DIR)
        os.makedirs(TEMP_DIR)

        print("Descargando el repositorio...")
        r = requests.get(GITHUB_ZIP, timeout=30)
        with zipfile.ZipFile(io.BytesIO(r.content)) as zip_ref:
            zip_ref.extractall(TEMP_DIR)

        extracted_root = os.path.join(TEMP_DIR, os.listdir(TEMP_DIR)[0])
        updated = False

        # Recorre todos los archivos del repo
        for root, _, files in os.walk(extracted_root):
            for file in files:
                rel_path = os.path.relpath(os.path.join(root, file), extracted_root)
                local_path = os.path.join(LOCAL_DIR, rel_path)

                # Ignora carpetas temporales
                if "update_temp" in local_path:
                    continue

                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                new_file = os.path.join(root, file)

                # Compara hash del archivo local vs remoto
                if file_hash(local_path) != file_hash(new_file):
                    shutil.copy2(new_file, local_path)
                    updated = True
                    print(f"Archivo actualizado: {rel_path}")

        shutil.rmtree(TEMP_DIR)
        return updated

    except Exception as e:
        print(f"Error al verificar actualizaciones: {e}")
        return False
