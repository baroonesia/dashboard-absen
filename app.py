import streamlit as st
import pandas as pd
import os
from datetime import datetime
import shutil

# Konfigurasi Halaman
st.set_page_config(page_title="Sistem Monitoring Absensi BP3MI", layout="wide")

st.title("📊 Dashboard Absensi & Arsip Riwayat")

# Tentukan folder riwayat
SAVE_DIR = "riwayat"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# --- SIDEBAR: UPLOAD ---
st.sidebar.header("Upload Data Baru")
uploaded_file = st.sidebar.file_uploader("Pilih file mesin absen", type=['txt', 'csv'])

def save_uploaded_file(uploaded_file):
    # Buat nama file unik: riwayat/20260205_1530_1.txt
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = os.path.join(SAVE_DIR, f"{timestamp}_{uploaded_file.name}")
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

if uploaded_file is not None:
    # Simpan file ke folder riwayat
    saved_path = save_uploaded_file(uploaded_file)
    st.sidebar.success(f"File tersimpan di: {saved_path}")

    # Proses data untuk ditampilkan
    try:
        # Gunakan separator tab sesuai data 1.txt Anda
        df = pd.read_csv(uploaded_file, sep='\t', header=None, 
                         names=['ID', 'Timestamp', 'Machine', 'Code', 'Nama', 'Status', 'X1', 'X2'])
        
        # Logika Resume (Min/Max Jam)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df['Tanggal'] = df['Timestamp'].dt.date
        
        resume = df.groupby(['Nama', 'Tanggal']).agg(
            Jam_Masuk=('Timestamp', 'min'),
            Jam_Pulang=('Timestamp', 'max')
        ).reset_index()
        
        st.subheader("Hasil Olah Data Terbaru")
        st.dataframe(resume, use_container_width=True)
        
    except Exception as e:
        st.error(f"Gagal memproses data: {e}")

# --- BAGIAN RIWAYAT ---
st.markdown("---")
st.subheader("📂 Daftar Riwayat File Terunggah")
files = os.listdir(SAVE_DIR)
if files:
    selected_old_file = st.selectbox("Lihat kembali data lama:", sorted(files, reverse=True))
    if st.button("Tampilkan Data Riwayat"):
        path_lama = os.path.join(SAVE_DIR, selected_old_file)
        df_lama = pd.read_csv(path_lama, sep='\t', header=None)
        st.write(f"Menampilkan isi: {selected_old_file}")
        st.dataframe(df_lama)
else:
    st.info("Belum ada riwayat file tersimpan.")