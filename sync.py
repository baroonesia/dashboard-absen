import os
import subprocess
from datetime import datetime

# --- KONFIGURASI ---
FILE_VERSION = "version_info.py"
COMMIT_MESSAGE = input("Masukkan Pesan Update (Commit Message): ") or "Update rutin otomatis"

def get_current_build():
    """Mencoba membaca build number terakhir"""
    try:
        with open(FILE_VERSION, "r") as f:
            content = f.read()
            # Cari baris BUILD_NUMBER
            for line in content.splitlines():
                if "BUILD_NUMBER =" in line:
                    return int(line.split("=")[1].strip())
        return 0
    except FileNotFoundError:
        return 0

def update_version_file():
    """Update file version_info.py dengan nomor baru"""
    current_build = get_current_build()
    new_build = current_build + 1
    now = datetime.now().strftime("%d-%m-%Y %H:%M")
    
    content = f'''# FILE INI DIGENERATE OTOMATIS OLEH SYNC.PY
# JANGAN DIEDIT MANUAL

BUILD_NUMBER = {new_build}
LAST_UPDATED = "{now}"
VERSION_TAG = "v2.{new_build}"
'''
    
    with open(FILE_VERSION, "w") as f:
        f.write(content)
    
    print(f"✅ Versi Aplikasi Dinaikkan ke: v1.{new_build} ({now})")
    return f"v1.{new_build}"

def run_git_commands():
    """Menjalankan perintah Git"""
    try:
        print("⏳ Sedang memproses Git...")
        
        # 1. Add semua file (termasuk version_info.py yang baru)
        subprocess.run(["git", "add", "."], check=True)
        
        # 2. Commit
        full_message = f"{COMMIT_MESSAGE} [Auto-Build v1.{get_current_build()}]"
        subprocess.run(["git", "commit", "-m", full_message], check=True)
        
        # 3. Push
        subprocess.run(["git", "push"], check=True)
        
        print("\n🚀 SUKSES! Perubahan berhasil dikirim ke GitHub.")
        print("👉 Streamlit Cloud akan otomatis mendeteksi perubahan ini dalam beberapa detik.")
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ TERJADI KESALAHAN GIT: {e}")

if __name__ == "__main__":
    update_version_file()
    run_git_commands()