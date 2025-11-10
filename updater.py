import os
import json
import requests
from pathlib import Path

def update_from_github():
    """Descarga actualizaciones desde GitHub automáticamente."""
    try:
        with open("config.json", "r") as f:
            config = json.load(f)

        repo = config["github_repo"].rstrip("/")
        version_url = f"{repo}/raw/main/config.json"
        remote_version = requests.get(version_url, timeout=5).json()["launcher_version"]

        if remote_version != config["launcher_version"]:
            print(f"[Updater] Nueva versión detectada ({remote_version}), actualizando...")
            for file in config["update_files"]:
                url = f"{repo}/raw/main/{file}"
                r = requests.get(url, timeout=10)
                if r.status_code == 200:
                    os.makedirs(os.path.dirname(file), exist_ok=True)
                    with open(file, "wb") as f_out:
                        f_out.write(r.content)
                        print(f"✅ Archivo actualizado: {file}")

            config["launcher_version"] = remote_version
            with open("config.json", "w") as f:
                json.dump(config, f, indent=4)
            print("✅ Actualización completada, reinicia el launcher.")
        else:
            print("[Updater] No hay actualizaciones disponibles.")
    except Exception as e:
        print(f"[Updater] Error: {e}")
