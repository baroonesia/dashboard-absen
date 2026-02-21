import subprocess

def git_push():
    # 1. Masukkan pesan commit (Tekan Enter langsung untuk pesan default)
    msg = input("Masukkan pesan commit (default: 'Update App'): ") or "Update App"

    try:
        print("🚀 Sedang memproses...")
        # Jalankan urutan perintah git
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", msg], check=True)
        subprocess.run(['git', 'push', '-u', 'origin', 'main'])
        
        print("\n✅ BERHASIL: Perubahan sudah naik ke GitHub!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ GAGAL: Terjadi kesalahan saat menjalankan Git. {e}")

if __name__ == "__main__":
    git_push()