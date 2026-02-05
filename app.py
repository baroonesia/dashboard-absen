import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Konfigurasi Halaman
st.set_page_config(page_title="Sistem Absensi BP3MI", layout="wide")

# Folder Riwayat
SAVE_DIR = "riwayat"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# --- NAVIGASI SIDEBAR ---
st.sidebar.title("🧭 Navigasi")
menu = st.sidebar.selectbox("Pilih Menu", ["Upload Data Baru", "Lihat Data Riwayat"])

# --- FUNGSI PEMROSESAN DATA (Logika Tapping Terakhir) ---
def process_data(df, date_range):
    df['Nama'] = df['Nama'].str.strip()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Tanggal_Date'] = df['Timestamp'].dt.date
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        df = df[(df['Tanggal_Date'] >= start_date) & (df['Tanggal_Date'] <= end_date)]
    
    # Ambil tapping 'I' terakhir dan 'O' terakhir
    df_masuk = df[df['Status'] == 'I'].groupby(['Nama', 'Tanggal_Date'])['Timestamp'].max().reset_index()
    df_masuk = df_masuk.rename(columns={'Timestamp': 'Jam_Masuk', 'Tanggal_Date': 'Tanggal'})
    
    df_pulang = df[df['Status'] == 'O'].groupby(['Nama', 'Tanggal_Date'])['Timestamp'].max().reset_index()
    df_pulang = df_pulang.rename(columns={'Timestamp': 'Jam_Pulang', 'Tanggal_Date': 'Tanggal'})
    
    resume = pd.merge(df_masuk, df_pulang, on=['Nama', 'Tanggal'], how='outer')
    resume = resume.sort_values(by=['Tanggal', 'Nama'], ascending=[False, True])
    
    resume['Jam_Masuk'] = resume['Jam_Masuk'].dt.strftime('%H:%M:%S').fillna("-")
    resume['Jam_Pulang'] = resume['Jam_Pulang'].dt.strftime('%H:%M:%S').fillna("-")
    return resume

# --- MENU 1: UPLOAD DATA BARU ---
if menu == "Upload Data Baru":
    st.header("📤 Upload & Rekap Data")
    uploaded_file = st.file_uploader("Pilih file (1.txt)", type=['txt', 'csv'])
    
    if uploaded_file:
        # Simpan file ke riwayat
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(SAVE_DIR, f"{timestamp}_{uploaded_file.name}")
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"File berhasil diupload dan diarsipkan!")
        
        # Tampilkan Rekap Instan
        df_raw = pd.read_csv(uploaded_file, sep='\t', header=None, 
                             names=['ID', 'Timestamp', 'Machine', 'Code', 'Nama', 'Status', 'X1', 'X2'])
        
        st.subheader("Preview Rekap (Semua Tanggal)")
        # Kita berikan filter default hari ini untuk preview
        res = process_data(df_raw, (df_raw['Timestamp'].dt.date.min(), df_raw['Timestamp'].dt.date.max()))
        st.dataframe(res, use_container_width=True, hide_index=True)

# --- MENU 2: LIHAT DATA RIWAYAT & HAPUS ---
elif menu == "Lihat Data Riwayat":
    st.header("📂 Manajemen Riwayat File")
    
    files = sorted(os.listdir(SAVE_DIR), reverse=True)
    
    if not files:
        st.info("Belum ada riwayat data.")
    else:
        # Filter Tanggal di Menu Riwayat
        st.subheader("Filter & Analisis")
        date_filter = st.date_input("Pilih Rentang Tanggal", value=(datetime(2026, 2, 4), datetime(2026, 2, 5)))
        
        st.markdown("---")
        
        # Menampilkan daftar file dengan tombol Hapus
        for file in files:
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"📄 {file}")
            
            # Tombol Analisis
            if col2.button("Analisis", key=f"an_{file}"):
                path = os.path.join(SAVE_DIR, file)
                df_old = pd.read_csv(path, sep='\t', header=None, 
                                     names=['ID', 'Timestamp', 'Machine', 'Code', 'Nama', 'Status', 'X1', 'X2'])
                res_old = process_data(df_old, date_filter)
                st.subheader(f"Hasil Rekap: {file}")
                st.dataframe(res_old, use_container_width=True, hide_index=True)
            
            # Tombol Hapus
            if col3.button("Hapus", key=f"del_{file}", type="secondary"):
                os.remove(os.path.join(SAVE_DIR, file))
                st.rerun() # Refresh halaman setelah hapus