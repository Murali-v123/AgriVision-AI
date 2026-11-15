import os
import zipfile
import shutil

PROJECT_DIR = r"c:\Users\HP\Desktop\hackathon\AgriVisionAI"
OUTPUT_PATHS = [
    r"c:\Users\HP\Desktop\hackathon\AgriVisionAI\agri.zip",
    r"c:\Users\HP\Desktop\hackathon\agri.zip",
    r"c:\Users\HP\Desktop\hackathon\agrivision_clean_submission.zip"
]

EXCLUDE_DIRS = {
    "venv", ".venv", "env", "__pycache__", ".pytest_cache", ".git", "media", "staticfiles"
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
    if filename.endswith(".zip"):
        return True
    return False

def make_clean_zip():
    primary_zip = OUTPUT_PATHS[0]
    # Remove existing agri.zip first so it's not scanned or locked
    for path in OUTPUT_PATHS:
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                print(f"Warning removing {path}: {e}")

    print(f"Creating clean zip archive at: {primary_zip}")
    file_count = 0
    with zipfile.ZipFile(primary_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(PROJECT_DIR):
            # Prune excluded directories in-place so os.walk doesn't even descend
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if should_exclude(root, file):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, PROJECT_DIR)
                # Store root files clean or under project prefix
                zf.write(full_path, rel_path)
                file_count += 1
    
    zip_size_mb = os.path.getsize(primary_zip) / (1024 * 1024)
    print(f"Done! Bundled {file_count} files into clean archive.")
    print(f"Clean archive size: {zip_size_mb:.2f} MB")

    # Copy to the other output destinations
    for target in OUTPUT_PATHS[1:]:
        shutil.copy2(primary_zip, target)
        print(f"Copied clean zip to: {target}")

    # Verification audit
    print("\n--- AUDIT OF GENERATED ARCHIVE ---")
    with zipfile.ZipFile(primary_zip, 'r') as test_zf:
        names = test_zf.namelist()
        venv_count = sum(1 for n in names if 'venv' in n)
        pycache_count = sum(1 for n in names if '__pycache__' in n)
        env_files = [n for n in names if n.endswith('.env')]
        db_files = [n for n in names if 'db.sqlite3' in n]
        print(f"Total files in archive: {len(names)}")
        print(f"venv files: {venv_count} (Must be 0)")
        print(f"__pycache__ files: {pycache_count} (Must be 0)")
        print(f".env files: {env_files} (Must be empty)")
        print(f"db.sqlite3 files: {db_files} (Must be empty)")
        assert venv_count == 0, "Error: venv files found in archive!"
        assert pycache_count == 0, "Error: __pycache__ files found in archive!"
        assert len(env_files) == 0, "Error: .env found in archive!"
        assert len(db_files) == 0, "Error: db.sqlite3 found in archive!"
        print("ALL PACKAGING AUDIT CHECKS PASSED: 100% CLEAN ARCHIVE!")

if __name__ == "__main__":
    make_clean_zip()
