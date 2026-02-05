import streamlit as st
import pandas as pd
import os
from datetime import datetime
import calendar
from fpdf import FPDF

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Sistem Absensi BP3MI",
    layout="wide",
    page_icon="🏢"
)

# --- 2. CSS DUAL MODE (TERANG/GELAP) ---
st.markdown("""
    <style>
    /* Variabel Warna Adaptif */
    :root {
        --bg-card: #ffffff;
        --text-main: #1E293B;
        --text-sub: #64748B;
        --border-color: #E2E8F0;
    }

    @media (prefers-color-scheme: dark) {
        :root {
            --bg-card: #1E293B;
            --text-main: #F8FAFC;
            --text-sub: #94A3B8;
            --border-color: #334155;
        }
    }

    .metric-card {
        background-color: var(--bg-card);
        color: var(--text-main);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border: 1px solid var(--border-color);
        margin-bottom: 20px;
    }

    .main-title { color: var(--text-main); font-weight: 700; font-size: 2.2rem; }
    .sub-title { color: var(--text-sub); margin-bottom: 2rem; }
    
    .info-box {
        background: linear-gradient(90deg, #2563EB 0%, #1D4ED8 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

SAVE_DIR = "riwayat"
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# --- 3. FUNGSI LOGIKA DINAMIS ---
def get_all_stored_data():
    """Menggabungkan semua data dari folder riwayat untuk perhitungan dashboard"""
    files = [os.path.join(SAVE_DIR, f) for f in os.listdir(SAVE_DIR) if f.endswith('.txt')]
    if not files:
        return pd.DataFrame()
    
    all_df = []
    for f in files:
        try:
            temp_df = pd.read_csv(f, sep='\t', header=None, names=['ID','Timestamp','Mch','Cd','Nama','Status','X1','X2'])
            all_df.append(temp_df)
        except:
            continue
    return pd.concat(all_df).drop_duplicates() if all_df else pd.DataFrame()

def process_logic(df):
    if df.empty: return df
    df['Nama'] = df['Nama'].str.strip()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Tanggal'] = df['Timestamp'].dt.date
    
    in_data = df[df['Status'] == 'I'].groupby(['Nama', 'Tanggal'])['Timestamp'].max().reset_index()
    out_data = df[df['Status'] == 'O'].groupby(['Nama', 'Tanggal'])['Timestamp'].max().reset_index()
    
    res = pd.merge(in_data, out_data, on=['Nama', 'Tanggal'], how='outer', suffixes=('_In', '_Out'))
    res['Jam_Masuk'] = res['Timestamp_In'].dt.strftime('%H:%M:%S').fillna("-")
    res['Jam_Pulang'] = res['Timestamp_Out'].dt.strftime('%H:%M:%S').fillna("-")
    return res

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("### 🏢 BP3MI Navigasi")
    menu = st.radio("MENU", ["🏠 Dashboard", "📂 Manajemen Data"])
    st.divider()
    if st.button("🔄 Refresh Data"):
        st.rerun()

# --- 5. MAIN CONTENT ---
data_global = get_all_stored_data()
res_global = process_logic(data_global.copy()) if not data_global.empty else pd.DataFrame()

if menu == "🏠 Dashboard":
    st.markdown("<div class='main-title'>Sistem Absensi BP3MI 😊</div>", unsafe_allow_html=True)
    
    # Hitung Metrik Secara Dinamis
    total_pegawai = res_global['Nama'].nunique() if not res_global.empty else 0
    total_hadir = len(res_global[(res_global['Jam_Masuk'] != "-") & (res_global['Jam_Pulang'] != "-")])
    total_tl = len(res_global[(res_global['Jam_Masuk'] == "-") | (res_global['Jam_Pulang'] == "-")])

    st.markdown(f"""
        <div class='info-box'>
            <h3>Statistik Keseluruhan</h3>
            <p>Berdasarkan {len(os.listdir(SAVE_DIR))} file arsip yang tersimpan.</p>
        </div>
    """, unsafe_allow_html=True)

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div class='metric-card'><h4>👥 Total Pegawai</h4><h2>{total_pegawai}</h2><p>Aktif di Sistem</p></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='metric-card'><h4>✅ Hadir Lengkap</h4><h2 style='color:#10B981;'>{total_hadir}</h2><p>Tapping In & Out</p></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div class='metric-card'><h4>⚠️ Tidak Lengkap</h4><h2 style='color:#F59E0B;'>{total_tl}</h2><p>Finger 1x</p></div>", unsafe_allow_html=True)

    if not res_global.empty:
        st.write("### Data Presensi Terkini")
        st.dataframe(res_global[['Nama', 'Tanggal', 'Jam_Masuk', 'Jam_Pulang']].head(10), use_container_width=True)

else:
    st.markdown("<div class='main-title'>Manajemen Data & Riwayat</div>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📤 Unggah Data", "📜 Daftar Arsip"])
    
    with tab1:
        file = st.file_uploader("Pilih file log .txt", type=['txt'])
        if file:
            t_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(os.path.join(SAVE_DIR, f"{t_str}_{file.name}"), "wb") as f:
                f.write(file.getbuffer())
            st.success("File Berhasil Diunggah! Klik 'Refresh Data' di sidebar untuk update dashboard.")

    with tab2:
        files = sorted(os.listdir(SAVE_DIR), reverse=True)
        for f in files:
            col1, col2 = st.columns([4, 1])
            col1.write(f"📄 {f}")
            if col2.button("🗑️ Hapus", key=f"del_{f}"):
                os.remove(os.path.join(SAVE_DIR, f))
                st.rerun() # Ini akan memicu hitung ulang otomatis