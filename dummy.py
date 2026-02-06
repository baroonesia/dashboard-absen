import os

# --- SKENARIO DATA ---
# Format: (Nama, Tanggal_Jam)
# Kita anggap Hari H = 2024-02-06 (Selasa)
# Kita anggap Besok = 2024-02-07 (Rabu)

data_log = [
    # 1. Prima (Normal)
    # Absen Masuk & Pulang di hari yang sama
    ("Prima", "2024-02-06 07:43:00"),
    ("Prima", "2024-02-06 17:30:00"),

    # 2. Ivan (Lupa Absen Masuk)
    # Hanya absen sore (dianggap pulang jika < 17:00, dianggap masuk malam jika > 17:00)
    # Request Bapak: 17:32
    ("Ivan",  "2024-02-06 17:32:00"),

    # 3. Kino (Shift Malam / Cross Day)
    # Masuk malam ini, pulang besok pagi
    ("Kino",  "2024-02-06 18:34:00"), # Masuk
    ("Kino",  "2024-02-07 07:32:00"), # Pulang (Besoknya)

    # 4. Andri (Lupa Absen Pulang)
    # Hanya absen pagi
    ("Andri", "2024-02-06 07:55:00"),
]

# --- MEMBUAT FILE TXT ---
nama_file = "tes_absen.txt"

try:
    with open(nama_file, "w") as f:
        for i, (nama, waktu) in enumerate(data_log, 1):
            # Format Standar Mesin Absensi (Sesuai app.py):
            # ID [tab] Waktu [tab] Mch [tab] Cd [tab] Nama [tab] Status [tab] X1 [tab] X2
            # Kita isi data dummy untuk kolom yang tidak diproses (ID, Mch, dll)
            
            line = f"{i}\t{waktu}\t1\t1\t{nama}\t1\t0\t0\n"
            f.write(line)
            
    print(f"✅ Berhasil! File '{nama_file}' telah dibuat.")
    print("👉 Silakan upload file ini ke menu 'Manajemen Data' di aplikasi Streamlit.")

except Exception as e:
    print(f"❌ Gagal membuat file: {e}")