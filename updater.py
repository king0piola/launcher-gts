import os, json, requests, shutil

GITHUB_REPO = "https://raw.githubusercontent.com/king0piola/launcher-gts/main/"

FILES_TO_CHECK = [
    "eventos.json",
    "mods/version.json",
    "main.py"
]

def download_file(url, dest):
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        r = requests.get(url)
        if r.status_code == 200:
            with open(dest, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        print("Error al descargar:", e)
    return False

def check_for_updates():
    updated_files = []
    for file in FILES_TO_CHECK:
        remote_url = GITHUB_REPO + file
        local_path = os.path.join(os.getcwd(), file)

        temp_path = local_path + ".tmp"
        if download_file(remote_url, temp_path):
            # Comparar con el existente
            if not os.path.exists(local_path) or open(local_path, "rb").read() != open(temp_path, "rb").read():
                shutil.move(temp_path, local_path)
                updated_files.append(file)
            else:
                os.remove(temp_path)
    return updated_files
