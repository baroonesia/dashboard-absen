import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Dashboard Absensi BP3MI", layout="wide")

st.title("📊 Dashboard Monitoring Absensi (Docker Mode)")

def load_data():
    file_path = '1.txt'
    if os.path.exists(file_path):
        try:
            # Membaca data dengan separator tab sesuai struktur file 1.txt
            df = pd.read_csv(file_path, sep='\t', header=None, 
                             names=['ID', 'Timestamp', 'Machine', 'Code', 'Nama', 'Status', 'X1', 'X2'])
            
            # Konversi kolom waktu
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            df['Tanggal'] = df['Timestamp'].dt.date
            
            # Pengolahan M4: Ambil jam datang paling awal dan jam pulang paling akhir
            summary = df.groupby(['Nama', 'Tanggal']).agg(
                Jam_Datang=('Timestamp', 'min'),
                Jam_Pulang=('Timestamp', 'max')
            ).reset_index()
            
            # Format tampilan jam
            summary['Jam_Datang'] = summary['Jam_Datang'].dt.strftime('%H:%M:%S')
            summary['Jam_Pulang'] = summary['Jam_Pulang'].dt.strftime('%H:%M:%S')
            
            return summary
        except Exception as e:
            st.error(f"Terjadi kesalahan pembacaan data: {e}")
            return None
    else:
        st.warning("Menunggu file 1.txt terdeteksi di folder /app...")
        return None

# Eksekusi fungsi
data_absen = load_data()

if data_absen is not None:
    st.success("Data berhasil dimuat dari Docker Volume")
    
    # Filter Nama Pegawai
    list_nama = ["Semua"] + list(data_absen['Nama'].unique())
    pilihan = st.selectbox("Pilih Nama Pegawai:", list_nama)
    
    if pilihan != "Semua":
        data_absen = data_absen[data_absen['Nama'] == pilihan]
    
    st.dataframe(data_absen, use_container_width=True)