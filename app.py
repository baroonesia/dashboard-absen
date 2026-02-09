import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import calendar
from fpdf import FPDF
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
import time as time_lib
# LIBRARY NAVIGASI MODERN
from streamlit_option_menu import option_menu 

# --- IMPORT VERSI OTOMATIS ---
try:
    from version_info import VERSION_TAG, LAST_UPDATED
except ImportError:
    VERSION_TAG = "v1.0 (Dev)"
    LAST_UPDATED = "Belum Disinkronisasi"

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Absensi BP3MI", layout="wide", page_icon="🏢")

# --- 2. CSS CUSTOM (ELEGANT THEME) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    :root { 
        --bg-card: #ffffff; 
        --text-main: #0F172A; 
        --text-sub: #64748B; 
        --border: #E2E8F0; 
        --accent: #2563EB; /* Biru Royal */
        --success: #10B981;
    }
    @media (prefers-color-scheme: dark) { 
        :root { 
            --bg-card: #1E293B; 
            --text-main: #F8FAFC; 
            --text-sub: #94A3B8; 
            --border: #334155; 
            --accent: #38BDF8; /* Biru Langit */
        } 
    }
    
    .metric-card {
        background-color: var(--bg-card); 
        color: var(--text-main);
        padding: 24px; 
        border-radius: 12px; 
        border: 1px solid var(--border);
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .header-title { font-size: 2rem; font-weight: 800; color: var(--text-main); line-height: 1.2; }
    .header-subtitle { font-size: 1rem; color: var(--text-sub); font-weight: 400; }

    .clock-container-new {
        display: flex; flex-direction: column; align-items: flex-end; justify-content: center; height: 100%;
    }
    .clock-time-new {
        font-size: 3rem; font-weight: 300; color: var(--text-main); line-height: 1; font-variant-numeric: tabular-nums;
    }
    .clock-date-new {
        font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; color: var(--accent); margin-top: 5px;
    }
    
    .login-container {
        max-width: 400px; margin: 100px auto; padding: 30px; border-radius: 12px;
        background-color: var(--bg-card); border: 1px solid var(--border);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1); text-align: center;
    }
    
    .version-tag {
        font-size: 0.70rem; 
        color: var(--text-sub); 
        margin-top: 15px; 
        margin-bottom: 5px;
        text-align: center;
        opacity: 0.8;
    }

    .feature-box {
        background-color: var(--bg-card);
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid var(--accent);
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .feature-title { font-weight: 800; font-size: 1.1rem; color: var(--text-main); margin-bottom: 5px; }
    .feature-desc { font-size: 0.9rem; color: var(--text-sub); }
    </style>
    """, unsafe_allow_html=True)

# --- KONEKSI DATABASE ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- LOGIN SYSTEM ---
def get_users_db():
    try:
        df = conn.read(worksheet="Users", ttl=0)
        return df
    except Exception:
        return pd.DataFrame()

def check_login():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_role'] = None
        st.session_state['user_name'] = None
    
    if not st.session_state['logged_in']:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("<div style='text-align:center; margin-top:50px;'>", unsafe_allow_html=True)
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg/960px-Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg.png", width=100)
            st.markdown("### Login Sistem Informasi Absensi")
            st.markdown("BP3MI Jawa Tengah")
            
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            
            if st.button("Masuk Sistem", use_container_width=True):
                with st.spinner("Memverifikasi..."):
                    users_df = get_users_db()
                    if not users_df.empty:
                        user_found = users_df[
                            (users_df['Username'] == username_input) & 
                            (users_df['Password'] == password_input)
                        ]
                        if not user_found.empty:
                            st.session_state['logged_in'] = True
                            st.session_state['user_role'] = user_found.iloc[0]['Role']
                            st.session_state['user_name'] = user_found.iloc[0]['Nama_Lengkap']
                            st.success(f"Selamat datang, {st.session_state['user_name']}")
                            time_lib.sleep(1)
                            st.rerun()
                        else:
                            st.error("Username atau Password salah!")
                    else:
                        st.error("Database user kosong.")
            
            # Info Versi di Layar Login
            st.markdown(f"""
            <div style='text-align:center; margin-top:20px; font-size:0.8rem; color:#888;'>
                Ver: {VERSION_TAG}
            </div>
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        return False 
    return True 

if not check_login():
    st.stop()

# --- AKSES DITERIMA ---
USER_ROLE = st.session_state['user_role']
USER_NAME = st.session_state['user_name']

# --- CRUD DATA (Logika Tetap) ---
def get_data():
    try:
        df = conn.read(worksheet="Data_Utama", ttl="0")
        if not df.empty:
            df['Tanggal'] = pd.to_datetime(df['Tanggal']).dt.date
        return df
    except:
        return pd.DataFrame(columns=['Nama', 'Tanggal', 'Jam_Masuk', 'Jam_Pulang', 'Status_Data'])

def save_data(new_df):
    try:
        current_df = get_data()
        if not current_df.empty:
            current_df['Tanggal'] = pd.to_datetime(current_df['Tanggal']).dt.date
        
        updated_df = pd.concat([current_df, new_df], ignore_index=True)
        updated_df = updated_df.drop_duplicates(subset=['Nama', 'Tanggal'])
        updated_df['Tanggal'] = updated_df['Tanggal'].astype(str)
        conn.update(worksheet="Data_Utama", data=updated_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def clear_all_data():
    try:
        empty_df = pd.DataFrame(columns=['Nama', 'Tanggal', 'Jam_Masuk', 'Jam_Pulang', 'Status_Data'])
        conn.update(worksheet="Data_Utama", data=empty_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Gagal menghapus: {e}")
        return False

# --- LOGGING ---
def get_logs():
    try:
        df_logs = conn.read(worksheet="Log_Sistem", ttl=0)
        if df_logs.empty: return pd.DataFrame(columns=['Waktu', 'Aksi', 'Detail'])
        return df_logs
    except:
        return pd.DataFrame(columns=['Waktu', 'Aksi', 'Detail'])

def add_log(aksi, detail):
    now = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
    detail_with_user = f"[{USER_NAME}] {detail}"
    new_entry = pd.DataFrame([{"Waktu": now, "Aksi": aksi, "Detail": detail_with_user}])
    try:
        current_logs = get_logs()
        updated_logs = pd.concat([current_logs, new_entry], ignore_index=True) if not current_logs.empty else new_entry
        conn.update(worksheet="Log_Sistem", data=updated_logs)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"Gagal log: {e}")

# --- PROSES FILE (ANTI-OVERLAP SHIFT LOGIC) ---
def process_file(file):
    try:
        df = pd.read_csv(file, sep='\t', header=None, names=['ID','Timestamp','Mch','Cd','Nama','Status','X1','X2'])
    except:
        file.seek(0)
        df = pd.read_csv(file, header=None, names=['ID','Timestamp','Mch','Cd','Nama','Status','X1','X2'])

    df['Nama'] = df['Nama'].str.strip()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Tanggal_Asli'] = df['Timestamp'].dt.date
    df = df.sort_values(['Nama', 'Timestamp'])

    final_data = []

    for nama, group in df.groupby('Nama'):
        dates = sorted(group['Tanggal_Asli'].unique())
        used_timestamps = set()

        for i, tgl in enumerate(dates):
            logs_hari_ini = group[group['Tanggal_Asli'] == tgl]
            timestamps = sorted(logs_hari_ini['Timestamp'].tolist())
            timestamps = [t for t in timestamps if t not in used_timestamps]
            
            if not timestamps:
                continue

            log_pertama = timestamps[0]
            log_terakhir = timestamps[-1] if len(timestamps) > 1 else None
            
            jam_masuk_fix = "-"
            jam_pulang_fix = "-"
            status_data = "Tidak Absen Pulang"
            
            waktu_log = log_pertama.time()
            batas_malam = time(18, 15)

            # SKENARIO 1: NORMAL
            if log_pertama.hour < 13:
                jam_masuk_fix = log_pertama.strftime('%H:%M:%S')
                if log_terakhir:
                    jam_pulang_fix = log_terakhir.strftime('%H:%M:%S')
                    status_data = "Lengkap (Normal)"
                    used_timestamps.add(log_terakhir) 
                else:
                    status_data = "Tidak Absen Pulang"
            
            # SKENARIO 2: ZONA AMBIGU
            elif log_pertama.hour >= 13 and waktu_log < batas_malam:
                if log_terakhir is None:
                    jam_masuk_fix = "-"
                    jam_pulang_fix = log_pertama.strftime('%H:%M:%S')
                    status_data = "Tidak Absen Pagi"
                    used_timestamps.add(log_pertama)
                else:
                    jam_masuk_fix = log_pertama.strftime('%H:%M:%S')
                    jam_pulang_fix = log_terakhir.strftime('%H:%M:%S')
                    status_data = "Lengkap (Normal)"
                    used_timestamps.add(log_terakhir)

            # SKENARIO 3: SHIFT MALAM
            else: # waktu_log >= 18:15
                jam_masuk_fix = log_pertama.strftime('%H:%M:%S')
                found_out = False
                if log_terakhir:
                    durasi = (log_terakhir - log_pertama).total_seconds() / 3600
                    if durasi > 3: 
                        jam_pulang_fix = log_terakhir.strftime('%H:%M:%S')
                        status_data = "Lengkap (Normal)"
                        used_timestamps.add(log_terakhir)
                        found_out = True
                
                if not found_out:
                    tgl_besok = tgl + timedelta(days=1)
                    if tgl_besok in dates:
                        logs_besok = group[group['Tanggal_Asli'] == tgl_besok]
                        if not logs_besok.empty:
                            timestamps_besok = sorted(logs_besok['Timestamp'].tolist())
                            potential_out = timestamps_besok[0]
                            if potential_out.hour < 13:
                                jam_pulang_fix = potential_out.strftime('%H:%M:%S')
                                status_data = "Lengkap (Malam)"
                                used_timestamps.add(potential_out)

            final_data.append({
                'Nama': nama,
                'Tanggal': tgl,
                'Jam_Masuk': jam_masuk_fix,
                'Jam_Pulang': jam_pulang_fix,
                'Status_Data': status_data
            })

    res = pd.DataFrame(final_data)
    if not res.empty:
        return res[['Nama', 'Tanggal', 'Jam_Masuk', 'Jam_Pulang', 'Status_Data']]
    else:
        return pd.DataFrame(columns=['Nama', 'Tanggal', 'Jam_Masuk', 'Jam_Pulang', 'Status_Data'])

# --- FUNGSI PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 10)
        self.cell(0, 10, 'LAPORAN REKAPITULASI ABSENSI OUTSOURCING', 0, 1, 'C')
        self.cell(0, 10, 'BP3MI JAWA TENGAH', 0, 1, 'C')
        
def generate_pdf(df_source, year, month):
    df_source = df_source.copy()
    df_source['Nama'] = df_source['Nama'].fillna("Tanpa Nama")
    df_source['Jam_Masuk'] = df_source['Jam_Masuk'].fillna("-").astype(str)
    df_source['Jam_Pulang'] = df_source['Jam_Pulang'].fillna("-").astype(str)
    df_source['Status_Data'] = df_source['Status_Data'].fillna("Tidak Lengkap").astype(str)

    pdf = PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    num_days = calendar.monthrange(year, month)[1]
    col_no, col_nama, col_summary = 8, 35, 15
    w_remain = pdf.w - col_no - col_nama - (col_summary*3) - 20
    col_day = w_remain / num_days
    
    nama_bulan = calendar.month_name[month].upper()
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, f"PERIODE : {nama_bulan} {year}", 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font("Arial", 'B', 6)
    pdf.cell(col_no, 12, 'No', 1, 0, 'C')
    pdf.cell(col_nama, 12, 'Nama Pegawai', 1, 0, 'C')
    for d in range(1, num_days+1):
        wk = calendar.weekday(year, month, d)
        pdf.set_fill_color(220,220,220) if wk >= 5 else pdf.set_fill_color(255,255,255)
        pdf.cell(col_day, 12, str(d), 1, 0, 'C', fill=True)
    pdf.cell(col_summary, 12, 'HADIR', 1, 0, 'C')
    pdf.cell(col_summary, 12, 'ALPA', 1, 0, 'C')
    pdf.cell(col_summary, 12, 'TIDAK LKP', 1, 1, 'C')

    pegawai = sorted(df_source['Nama'].unique())
    for idx, nama in enumerate(pegawai, 1):
        h, a, tl = 0, 0, 0
        pdf.set_font("Arial", '', 6)
        pdf.cell(col_no, 10, str(idx), 1, 0, 'C')
        pdf.cell(col_nama, 10, str(nama)[:18], 1, 0, 'L')
        
        for d in range(1, num_days+1):
            curr_date = pd.Timestamp(year, month, d).date()
            row = df_source[(df_source['Nama'] == nama) & (df_source['Tanggal'] == curr_date)]
            fill, txt = False, ""
            
            if not row.empty:
                m = row.iloc[0]['Jam_Masuk']
                p = row.iloc[0]['Jam_Pulang']
                stat = row.iloc[0]['Status_Data']
                m = "-" if m in ["None","nan"] else m
                p = "-" if p in ["None","nan"] else p
                
                if "Lengkap" in stat:
                     if "Malam" in stat: pdf.set_fill_color(173, 216, 230) 
                     else: pdf.set_fill_color(144, 238, 144) 
                     txt = f"{m}\n{p}"; h += 1
                else:
                    pdf.set_fill_color(255, 255, 153); txt = f"{m if m!='-' else p}"; tl += 1
                fill = True
            else:
                if calendar.weekday(year, month, d) < 5: 
                    pdf.set_fill_color(255, 153, 153); txt = "X"; a += 1; fill = True
                else: 
                    pdf.set_fill_color(240,240,240); fill = True
            
            x, y = pdf.get_x(), pdf.get_y()
            pdf.cell(col_day, 10, "", 1, 0, 'C', fill=fill)
            pdf.set_xy(x, y+1); pdf.set_font("Arial",'',3); pdf.multi_cell(col_day, 3, txt, 0, 'C')
            pdf.set_xy(x+col_day, y); pdf.set_font("Arial",'',6)
        
        pdf.cell(col_summary, 10, str(h), 1, 0, 'C')
        pdf.cell(col_summary, 10, str(a), 1, 0, 'C')
        pdf.cell(col_summary, 10, str(tl), 1, 1, 'C')

    # LEGENDA
    pdf.ln(8)
    pdf.set_font("Arial", 'B', 7)
    pdf.cell(0, 5, "KETERANGAN WARNA (LEGENDA):", 0, 1, 'L')
    
    def draw_legend(r, g, b, text):
        pdf.set_fill_color(r, g, b)
        pdf.cell(4, 4, "", 1, 0, 'C', fill=True)
        pdf.cell(2)
        pdf.cell(30, 4, text, 0, 0, 'L')
        pdf.cell(5)

    pdf.set_font("Arial", '', 7)
    draw_legend(144, 238, 144, "Lengkap (Normal)")
    draw_legend(173, 216, 230, "Lengkap (Shift Malam)")
    draw_legend(255, 255, 153, "Data Tidak Lengkap")
    draw_legend(255, 153, 153, "Tidak Hadir (Alpa)")
    draw_legend(240, 240, 240, "Hari Libur / Kosong")
    
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR MENU MODERN & ELEGAN ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg/960px-Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg.png", width=60)
    st.markdown(f"**Halo, {USER_NAME}**")
    st.caption(f"Role: {USER_ROLE}")
    
    # Logout Button
    if st.button("🔒 Logout", use_container_width=True):
        st.session_state['logged_in'] = False
        st.rerun()
    
    st.write("---")
    
    # KONFIGURASI NAVIGASI MODERN
    menu_list = ["Dashboard", "Analisis Pegawai", "Manajemen Data", "Tentang Aplikasi"]
    icon_list = ["house", "bar-chart-line", "folder2-open", "info-circle"]
    
    if USER_ROLE == "Administrator":
        menu_list.append("System Logs")
        icon_list.append("journal-text")

    # OPTION MENU DENGAN WARNA HOVER YANG DIPERBAIKI (VISIBLE DARK/LIGHT)
    menu = option_menu(
        menu_title=None, 
        options=menu_list,
        icons=icon_list,
        menu_icon="cast", 
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#2563EB", "font-size": "18px"}, # Warna Icon Biru Brand
            "nav-link": {
                "font-size": "15px",
                "text-align": "left",
                "margin": "5px",
                # FIX VISIBILITY: Gunakan RGBA transparan agar cocok di dark/light mode
                # Tidak menggunakan warna solid #eee yang tabrakan dengan teks putih di dark mode
                "--hover-color": "rgba(37, 99, 235, 0.1)", 
            },
            "nav-link-selected": {"background-color": "#2563EB", "font-weight": "600"},
        }
    )

    st.write("---")
    if st.button("🔄 Refresh Data Cloud"):
        st.cache_data.clear()
        add_log("REFRESH", "Manual refresh") 
        st.rerun()

    # --- VERSI DI BAWAH ---
    st.markdown(f"<div class='version-tag'>System Version: <b>{VERSION_TAG}</b><br>Updated: {LAST_UPDATED}</div>", unsafe_allow_html=True)
    st.caption("BP3MI Jateng © 2026")

# --- KONTEN UTAMA ---
df_global = get_data()
now_indo = datetime.utcnow() + timedelta(hours=7)
str_hari = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"][now_indo.weekday()]
str_tgl = now_indo.strftime('%d %B %Y')
str_jam = now_indo.strftime('%H:%M')
clock_html = f"<div class='clock-container-new'><div class='clock-time-new'>{str_jam}</div><div class='clock-date-new'>{str_hari}, {str_tgl}</div></div>"

# --- LOGIKA KONTEN BERDASARKAN MENU MODERN ---

if menu == "Tentang Aplikasi":
    col_L, col_R = st.columns([2, 1])
    with col_L:
        st.markdown(f"""
        <div style='padding-top:10px;'>
            <div class='header-title'>Tentang Aplikasi</div>
            <div class='header-subtitle'>Sistem Presensi Outsourcing BP3MI Jawa Tengah</div>
        </div>
        """, unsafe_allow_html=True)
    with col_R:
        st.markdown(clock_html, unsafe_allow_html=True)
    st.markdown("---")

    # KONTEN UTAMA DENGAN PARAMETER YANG DIKEMBALIKAN
    st.markdown("""
    Sistem Informasi Absensi Outsourcing
    Sistem ini dirancang sebagai **Solusi Terintegrasi** untuk mengelola kompleksitas jadwal kerja secara modern di lingkungan BP3MI Jawa Tengah. 
    Dengan arsitektur *Cloud-Hybrid*, sistem menjamin efisiensi rekapitulasi dan akurasi pelaporan yang tinggi.
    """)
    st.write("")

    # PARAMETER FITUR UTAMA (3 Kolom)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        <div class='feature-box'>
            <div class='feature-title'>Anti-Overlap Logic</div>
            <div class='feature-desc'>Algoritma cerdas yang mampu membedakan <b>Shift Beruntun</b>, Lembur Lintas Hari, dan kepulangan pagi secara otomatis.</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class='feature-box'>
            <div class='feature-title'>Cloud Sync & Security</div>
            <div class='feature-desc'>Data tersimpan aman di <b>Google Cloud Database</b>. Memungkinkan akses real-time dan kolaboratif antar admin.</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class='feature-box'>
            <div class='feature-title'>Automated PDF Report</div>
            <div class='feature-desc'>Generator laporan bulanan otomatis dengan pewarnaan kondisional (Legenda) yang memudahkan proses audit.</div>
        </div>
        """, unsafe_allow_html=True)

    st.write("---")
    
    # PARAMETER TERMINOLOGI & DETAIL TEKNIS
    st.subheader("Terminologi & Logika Sistem")
    col_term1, col_term2 = st.columns(2)
    with col_term1:
        st.markdown("""
        **1. Status: Lengkap (Normal)** Pegawai melakukan absen masuk dan pulang pada rentang waktu yang wajar di hari yang sama.
        
        **2. Status: Lengkap (Shift Malam)** Sistem mendeteksi masuk malam (>18:15) dan secara otomatis mencari pasangan absen pulang di keesokan paginya (<13:00).
        """)
    with col_term2:
        st.markdown("""
        **3. Zona Ambigu (13:00 - 18:14)** Jika hanya ada satu log di jam ini, sistem akan mengidentifikasinya sebagai "Tidak Absen Pagi".
        
        **4. Smart Deduplication** Mencegah data ganda jika pegawai melakukan tapping mesin berkali-kali dalam waktu singkat.
        """)
    
    # INFO VERSI (PARAMETER SYSTEM)
    with st.expander("Spesifikasi Teknis & Versi"):
        st.markdown(f"""
        * **Framework:** Python Streamlit
        * **Database:** Google Cloud Database
        * **System Version:** `{VERSION_TAG}`
        * **Last Build Update:** `{LAST_UPDATED}`
        * **Developer:** Prima Ammaray 
        """)

elif menu == "Dashboard":
    col_L, col_R = st.columns([2, 1])
    with col_L: st.markdown("<div class='header-title'>Dashboard Absensi</div><div class='header-subtitle'>Monitoring Kehadiran Outsourcing</div>", unsafe_allow_html=True)
    with col_R: st.markdown(clock_html, unsafe_allow_html=True)
    st.markdown("---")
    if not df_global.empty:
        total_p = df_global['Nama'].nunique()
        lengkap = len(df_global[df_global['Status_Data'].str.contains('Lengkap')])
        tl = len(df_global[df_global['Status_Data'].str.contains('Tidak')])
        m1, m2, m3 = st.columns(3)
        m1.markdown(f"<div class='metric-card'><h4>👥 Pegawai</h4><h1>{total_p}</h1></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='metric-card'><h4>✅ Hadir</h4><h1 style='color:#10B981;'>{lengkap}</h1></div>", unsafe_allow_html=True)
        m3.markdown(f"<div class='metric-card'><h4>⚠️ Tdk Lengkap</h4><h1 style='color:#F59E0B;'>{tl}</h1></div>", unsafe_allow_html=True)
        st.write("### 📋 Log Masuk Terakhir")
        st.dataframe(df_global.sort_values('Tanggal', ascending=False).head(10), use_container_width=True)
    else: st.info("Database kosong.")

elif menu == "Analisis Pegawai":
    col_L, col_R = st.columns([2, 1])
    with col_L: st.markdown("<div class='header-title'>Analisis Performa</div>", unsafe_allow_html=True)
    with col_R: st.markdown(clock_html, unsafe_allow_html=True)
    if not df_global.empty:
        st.write("---")
        # --- FITUR MULTISELECT FILTER ---
        all_pegawai = sorted(df_global['Nama'].unique().tolist())
        c1, c2, c3 = st.columns([1, 1, 2])
        with c1: sel_bulan = st.selectbox("Bulan", range(1, 13), index=datetime.now().month-1, format_func=lambda x: calendar.month_name[x])
        with c2: sel_tahun = st.number_input("Tahun", value=datetime.now().year)
        with c3: sel_nama = st.multiselect("🔍 Cari Pegawai", all_pegawai)
        
        df_global['Tanggal'] = pd.to_datetime(df_global['Tanggal'])
        mask = (df_global['Tanggal'].dt.month == sel_bulan) & (df_global['Tanggal'].dt.year == sel_tahun)
        if sel_nama: mask = mask & (df_global['Nama'].isin(sel_nama))
        df_filtered = df_global[mask]
        
        if not df_filtered.empty:
            if sel_nama: st.success(f"Data: {len(sel_nama)} Pegawai Terpilih")
            else: st.success("Data: Semua Pegawai")
            
            gc1, gc2 = st.columns(2)
            with gc1:
                chart_data = df_filtered.copy()
                chart_data['Kategori'] = chart_data['Status_Data'].apply(lambda x: 'Lengkap' if 'Lengkap' in x else ('Tidak Absen Pagi' if 'Pagi' in x else 'Tidak Absen Pulang'))
                fig = px.bar(chart_data.groupby(['Nama', 'Kategori']).size().reset_index(name='Jumlah'), x='Nama', y='Jumlah', color='Kategori', color_discrete_map={'Lengkap':'#2563EB', 'Tidak Absen Pagi':'#EF553B', 'Tidak Absen Pulang':'#F59E0B'})
                st.plotly_chart(fig, use_container_width=True)
            with gc2:
                pie = df_filtered['Status_Data'].value_counts().reset_index(); pie.columns = ['Status','Jumlah']
                st.plotly_chart(px.pie(pie, values='Jumlah', names='Status', hole=0.6), use_container_width=True)
            df_display = df_filtered.copy(); df_display['Tanggal'] = df_display['Tanggal'].dt.date
            st.dataframe(df_display.sort_values('Tanggal'), use_container_width=True, hide_index=True)
        else: st.warning("Data tidak ditemukan.")
    else: st.warning("Database kosong.")

elif menu == "Manajemen Data":
    col_L, col_R = st.columns([2, 1])
    with col_L: st.markdown("<div class='header-title'>Manajemen Data</div>", unsafe_allow_html=True)
    with col_R: st.markdown(clock_html, unsafe_allow_html=True)
    st.write("---")
    tabs_list = ["Upload Data", "Download Laporan"]
    if USER_ROLE == "Administrator": tabs_list.append("⚠️ Hapus Database")
    mytabs = st.tabs(tabs_list)
    with mytabs[0]: 
        f = st.file_uploader("Upload .txt", type=['txt'])
        if f and st.button("Simpan Data"):
            bar = st.progress(0, text="Membaca Data...")
            res = process_file(f); bar.progress(60, text="Analisis Cerdas...")
            if save_data(res):
                bar.progress(100, text="Berhasil!"); add_log("UPLOAD", f.name); st.success("Selesai!"); st.balloons()
    with mytabs[1]: 
        c1, c2 = st.columns(2)
        b = c1.selectbox("Laporan Bulan", range(1,13), index=datetime.now().month-1); t = c2.number_input("Laporan Tahun", value=datetime.now().year)
        if st.button("Proses PDF"):
            df_global['Tanggal'] = pd.to_datetime(df_global['Tanggal'])
            df_filt = df_global[(df_global['Tanggal'].dt.month == b) & (df_global['Tanggal'].dt.year == t)]
            if not df_filt.empty:
                df_filt['Tanggal'] = df_filt['Tanggal'].dt.date
                pdf = generate_pdf(df_filt, t, b); add_log("DOWNLOAD", f"PDF {b}/{t}")
                st.download_button("Unduh PDF", pdf, f"Laporan Absensi Outsourcing Bulan {b} Tahun {t}.pdf", "application/pdf")
            else: st.error("Data kosong.")
    if USER_ROLE == "Administrator":
        with mytabs[2]:
            st.error("⚠️ PERHATIAN: Hapus data bersifat permanen!")
            if st.checkbox("Konfirmasi Hapus Seluruh Database"):
                if st.button("HAPUS PERMANEN", type="primary"):
                    if clear_all_data(): add_log("DELETE_ALL", "DB Cleared"); st.rerun()

elif menu == "System Logs":
    col_L, col_R = st.columns([2, 1])
    with col_L:
        st.markdown("<div class='header-title'>System Logs</div>", unsafe_allow_html=True)
    with col_R:
        st.markdown(clock_html, unsafe_allow_html=True)
    st.write("---")
    if st.button("🔄 Refresh Log"): st.cache_data.clear(); st.rerun()
    log_df = get_logs()
    if not log_df.empty: st.dataframe(log_df.sort_values(by="Waktu", ascending=False), use_container_width=True, hide_index=True)