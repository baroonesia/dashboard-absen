import os
import subprocess
import time
import webbrowser

def run_command(command):
    try:
        return subprocess.check_output(command, shell=True).decode('utf-8')
    except Exception as e:
        return str(e)

def start_services():
    print("🚀 Menginisialisasi Dashboard Absensi...")
    
    # 1. Pastikan Docker Desktop berjalan
    print("🐳 Mengecek Docker Engine...")
    check_docker = run_command("docker info")
    if "error" in check_docker.lower():
        print("❌ Docker belum aktif. Silakan buka Docker Desktop terlebih dahulu!")
        # Di Mac, kita bisa mencoba membukanya secara otomatis
        subprocess.run(["open", "-a", "Docker"])
        print("⏳ Menunggu Docker Engine siap (30 detik)...")
        time.sleep(30)

    # 2. Nyalakan Container
    container_name = "dashboard-absen"
    print(f"🔄 Menjalankan Container: {container_name}...")
    
    # Cek apakah container sudah ada (meskipun mati)
    containers = run_command("docker ps -a")
    
    if container_name in containers:
        subprocess.run(["docker", "start", container_name])
    else:
        # Jika container belum ada, kita jalankan run baru (pastikan path benar)
        current_dir = os.getcwd()
        run_cmd = f'docker run -d -p 8501:8501 -v "{current_dir}:/app" --restart always --name {container_name} {container_name}'
        subprocess.run(run_cmd, shell=True)

    # 3. Beri waktu sebentar agar Streamlit siap
    print("⏳ Menyiapkan tampilan dashboard...")
    time.sleep(3)

    # 4. Buka Browser Otomatis
    url = "http://localhost:8501"
    print(f"🌐 Membuka Dashboard di: {url}")
    webbrowser.open(url)
    print("\n✅ Semua layanan berhasil dijalankan! Selamat bekerja.")

if __name__ == "__main__":
    start_services()