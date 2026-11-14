import os
import zipfile

PROJECT_DIR = r"c:\Users\HP\Desktop\hackathon\AgriVisionAI"
OUTPUT_ZIP = r"c:\Users\HP\Desktop\hackathon\agrivision_clean_submission.zip"

EXCLUDE_DIRS = {
    "venv", ".venv", "env", "__pycache__", ".pytest_cache", ".git", "media"
}

EXCLUDE_FILES = {
    "db.sqlite3", ".env", "agri.zip"
}

def should_exclude(dirpath, filename):
    parts = dirpath.split(os.sep)
    for p in parts:
        if p in EXCLUDE_DIRS:
            return True
    if filename in EXCLUDE_FILES:
        return True
    if filename.endswith(".pyc") or filename.endswith(".pyo"):
        return True
    return False

def make_clean_zip():
    print(f"Creating clean zip archive at: {OUTPUT_ZIP}")
    file_count = 0
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(PROJECT_DIR):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if should_exclude(root, file):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, PROJECT_DIR)
                zf.write(full_path, os.path.join("AgriVisionAI", rel_path))
                file_count += 1
    
    zip_size_mb = os.path.getsize(OUTPUT_ZIP) / (1024 * 1024)
    print(f"Done! Bundled {file_count} files into clean archive.")
    print(f"Clean archive size: {zip_size_mb:.2f} MB (no venv, no db.sqlite3, no caches, no .env)")

if __name__ == "__main__":
    make_clean_zip()
