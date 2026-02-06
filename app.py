import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import calendar
from fpdf import FPDF
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
import time as time_lib 

# --- IMPORT VERSI OTOMATIS ---
try:
    from version_info import VERSION_TAG, LAST_UPDATED
except ImportError:
    VERSION_TAG = "v1.0 (Dev)"
    LAST_UPDATED = "Belum Disinkronisasi"

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Absensi BP3MI", layout="wide", page_icon="🏢")

# --- 2. CSS CUSTOM ---
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
        --accent: #2563EB;
    }
    @media (prefers-color-scheme: dark) { 
        :root { 
            --bg-card: #1E293B; 
            --text-main: #F8FAFC; 
            --text-sub: #94A3B8; 
            --border: #334155; 
            --accent: #38BDF8;
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
        font-size: 0.75rem; color: var(--text-sub); margin-top: 20px; text-align: center;
        border-top: 1px solid var(--border); padding-top: 10px;
    }
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
            st.markdown("### Login Sistem Absensi")
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
            st.markdown(f"""
            """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        return False 
    return True 

if not check_login():
    st.stop()

# --- AKSES DITERIMA ---
USER_ROLE = st.session_state['user_role']
USER_NAME = st.session_state['user_name']

# --- CRUD DATA ---
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
        
        # ALGORITMA BARU: TRACKING LOG YANG SUDAH TERPAKAI
        used_timestamps = set()

        for i, tgl in enumerate(dates):
            logs_hari_ini = group[group['Tanggal_Asli'] == tgl]
            timestamps = sorted(logs_hari_ini['Timestamp'].tolist())
            
            # FILTER: Buang log yang sudah terpakai
            timestamps = [t for t in timestamps if t not in used_timestamps]
            
            if not timestamps:
                continue

            # Inisialisasi
            log_pertama = timestamps[0]
            log_terakhir = timestamps[-1] if len(timestamps) > 1 else None
            
            jam_masuk_fix = "-"
            jam_pulang_fix = "-"
            status_data = "Tidak Absen Pulang"
            
            # Helper Waktu
            waktu_log = log_pertama.time()
            batas_malam = time(18, 15)

            # --- SKENARIO 1: MASUK PAGI/SIANG NORMAL (< 13:00) ---
            if log_pertama.hour < 13:
                jam_masuk_fix = log_pertama.strftime('%H:%M:%S')
                if log_terakhir:
                    jam_pulang_fix = log_terakhir.strftime('%H:%M:%S')
                    status_data = "Lengkap (Normal)"
                    used_timestamps.add(log_terakhir) # Tandai pulang hari ini terpakai
                else:
                    status_data = "Tidak Absen Pulang"
            
            # --- SKENARIO 2: ZONA AMBIGU (13:00 - 18:14) ---
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

            # --- SKENARIO 3: SHIFT MALAM (>= 18:15) ---
            else: # waktu_log >= 18:15
                jam_masuk_fix = log_pertama.strftime('%H:%M:%S')
                
                # Cek 1: Pulang di hari yang sama (Lembur pendek)
                found_out = False
                if log_terakhir:
                    durasi = (log_terakhir - log_pertama).total_seconds() / 3600
                    if durasi > 3: # Hanya valid jika kerja > 3 jam
                        jam_pulang_fix = log_terakhir.strftime('%H:%M:%S')
                        status_data = "Lengkap (Normal)"
                        used_timestamps.add(log_terakhir)
                        found_out = True
                
                # Cek 2: Pulang Besok Pagi (Shift Malam Sejati)
                if not found_out:
                    tgl_besok = tgl + timedelta(days=1)
                    if tgl_besok in dates:
                        logs_besok = group[group['Tanggal_Asli'] == tgl_besok]
                        if not logs_besok.empty:
                            timestamps_besok = sorted(logs_besok['Timestamp'].tolist())
                            potential_out = timestamps_besok[0]
                            
                            # Syarat: Pulang sebelum jam 13:00 siang besoknya
                            if potential_out.hour < 13:
                                jam_pulang_fix = potential_out.strftime('%H:%M:%S')
                                status_data = "Lengkap (Malam)"
                                
                                # KUNCI: Tandai log besok ini sebagai "Terpakai"
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

# --- FUNGSI PDF (VISUALISASI LENGKAP) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'LAPORAN REKAPITULASI ABSENSI OUTSOURCING', 0, 1, 'C')
        self.cell(0, 10, 'BP3MI JAWA TENGAH', 0, 1, 'C')
        self.cell(0, 10, '', 0, 1, 'C')

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

    # HEADER TABEL
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

    # BODY TABEL
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
                
                # --- LOGIKA WARNA ---
                if "Lengkap" in stat:
                     if "Malam" in stat: 
                         pdf.set_fill_color(173, 216, 230) # Biru Muda (Malam)
                     else: 
                         pdf.set_fill_color(144, 238, 144) # Hijau Muda (Normal)
                     txt = f"{m}\n{p}"; h += 1
                else:
                    pdf.set_fill_color(255, 255, 153); txt = f"{m if m!='-' else p}"; tl += 1 # Kuning
                
                fill = True
            else:
                # TIDAK ADA DATA
                if calendar.weekday(year, month, d) < 5: # Senin-Jumat
                    pdf.set_fill_color(255, 153, 153); txt = "X"; a += 1; fill = True # Merah
                else: # Sabtu-Minggu
                    pdf.set_fill_color(240,240,240); fill = True # Abu
            
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

# --- SIDEBAR MENU ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg/960px-Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg.png", width=50)
    st.markdown(f"**Halo, {USER_NAME}**")
    st.caption(f"Role: {USER_ROLE}")
    
    # --- TAMPILAN VERSI APLIKASI DI SIDEBAR ---
    st.markdown(f"""
    <div class='version-tag'>
        System Version: <b>{VERSION_TAG}</b><br>
        Updated: {LAST_UPDATED}
    </div>
    """, unsafe_allow_html=True)

    if st.button("🔒 Logout"):
        st.session_state['logged_in'] = False
        st.session_state['user_role'] = None
        st.rerun()
    st.divider()
    
    menu_options = ["🏠 Dashboard", "📈 Analisis Pegawai", "📂 Manajemen Data"]
    if USER_ROLE == "Administrator":
        menu_options.append("📜 System Logs")
        
    menu = st.radio("MENU UTAMA", menu_options)
    st.divider()
    if st.button("🔄 Refresh Data Cloud"):
        st.cache_data.clear()
        add_log("REFRESH", "Manual refresh") 
        st.rerun()
    <div class='version-tag'>
                System Version: <b>{VERSION_TAG}</b><br>
                Updated: {LAST_UPDATED}
            </div>
    st.caption("BP3MI Jateng © 2026")

# --- KONTEN UTAMA ---
df_global = get_data()

now_indo = datetime.utcnow() + timedelta(hours=7)
hari_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
str_hari = hari_indo[now_indo.weekday()]
str_tgl = now_indo.strftime('%d %B %Y')
str_jam = now_indo.strftime('%H:%M')

clock_html = f"""
<div class='clock-container-new'>
    <div class='clock-time-new'>{str_jam}</div>
    <div class='clock-date-new'>{str_hari}, {str_tgl}</div>
</div>
"""

# --- TAMPILAN MENU ---
if menu == "🏠 Dashboard":
    col_L, col_R = st.columns([2, 1])
    with col_L:
        st.markdown(f"""
        <div style='padding-top:10px;'>
            <div class='header-title'>Dashboard Absensi</div>
            <div class='header-subtitle'>Monitoring Kehadiran Outsourcing</div>
        </div>
        """, unsafe_allow_html=True)
    with col_R:
        st.markdown(clock_html, unsafe_allow_html=True)
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
    else:
        st.info("Database kosong.")

elif menu == "📈 Analisis Pegawai":
    col_L, col_R = st.columns([2, 1])
    with col_L:
        st.markdown("<div class='header-title'>Analisis Performa</div>", unsafe_allow_html=True)
    with col_R:
        st.markdown(clock_html, unsafe_allow_html=True)
    
    if not df_global.empty:
        st.write("---")
        c1, c2 = st.columns(2)
        with c1:
            sel_bulan = st.selectbox("Pilih Bulan", range(1, 13), index=datetime.now().month-1, format_func=lambda x: calendar.month_name[x])
        with c2:
            sel_tahun = st.number_input("Pilih Tahun", value=datetime.now().year)

        df_global['Tanggal'] = pd.to_datetime(df_global['Tanggal'])
        mask = (df_global['Tanggal'].dt.month == sel_bulan) & (df_global['Tanggal'].dt.year == sel_tahun)
        df_filtered = df_global[mask]

        if not df_filtered.empty:
            st.success(f"Data: **{calendar.month_name[sel_bulan]} {sel_tahun}**")
            gc1, gc2 = st.columns(2)
            with gc1:
                st.write("**Grafik Kepatuhan**")
                chart_data = df_filtered.copy()
                chart_data['Kategori'] = chart_data['Status_Data'].apply(
                    lambda x: 'Lengkap' if 'Lengkap' in x else ('Tidak Absen Pagi' if 'Pagi' in x else 'Tidak Absen Pulang')
                )
                chart_data_grp = chart_data.groupby(['Nama', 'Kategori']).size().reset_index(name='Jumlah')
                fig = px.bar(chart_data_grp, x='Nama', y='Jumlah', color='Kategori', 
                             color_discrete_map={'Lengkap':'#2563EB', 'Tidak Absen Pagi':'#EF553B', 'Tidak Absen Pulang':'#F59E0B'})
                st.plotly_chart(fig, use_container_width=True)
            with gc2:
                st.write("**Proporsi**")
                pie = df_filtered['Status_Data'].value_counts().reset_index()
                pie.columns = ['Status','Jumlah']
                fig2 = px.pie(pie, values='Jumlah', names='Status', hole=0.6)
                st.plotly_chart(fig2, use_container_width=True)
            
            st.markdown(f"### 📋 Daftar Detail")
            df_display = df_filtered.copy()
            df_display['Tanggal'] = df_display['Tanggal'].dt.date
            st.dataframe(df_display.sort_values('Tanggal'), use_container_width=True, hide_index=True)
        else:
            st.warning("Data tidak ditemukan.")
    else:
        st.warning("Database kosong.")

elif menu == "📂 Manajemen Data":
    col_L, col_R = st.columns([2, 1])
    with col_L:
        st.markdown("<div class='header-title'>Manajemen Data</div>", unsafe_allow_html=True)
    with col_R:
        st.markdown(clock_html, unsafe_allow_html=True)
    st.write("---")
    
    tabs_list = ["Upload Data", "Download Laporan"]
    if USER_ROLE == "Administrator":
        tabs_list.append("⚠️ Hapus Database")
        
    mytabs = st.tabs(tabs_list)
    
    with mytabs[0]: 
        f = st.file_uploader("Upload .txt", type=['txt'])
        if f and st.button("Simpan Data"):
            progress_text = "Memulai proses..."
            my_bar = st.progress(0, text=progress_text)
            
            time_lib.sleep(0.5)
            my_bar.progress(30, text="📂 Membaca & Membersihkan Data...")
            res = process_file(f)
            
            time_lib.sleep(0.5)
            my_bar.progress(60, text="🧠 Analisis Cerdas (Anti-Overlap Shift)...")
            
            my_bar.progress(90, text="☁️ Sinkronisasi ke Database...")
            saved = save_data(res)
            
            if saved:
                my_bar.progress(100, text="✅ Selesai!")
                time_lib.sleep(0.5)
                my_bar.empty()
                add_log("UPLOAD", f.name)
                st.success(f"Berhasil memproses {len(res)} data presensi!")
                st.balloons()
    
    with mytabs[1]: 
        c1, c2 = st.columns(2)
        b = c1.selectbox("Bulan", range(1,13), index=datetime.now().month-1)
        t = c2.number_input("Tahun", value=datetime.now().year)
        if st.button("Proses Laporan"):
            df_global['Tanggal'] = pd.to_datetime(df_global['Tanggal'])
            mask = (df_global['Tanggal'].dt.month == b) & (df_global['Tanggal'].dt.year == t)
            df_filt = df_global[mask]
            if not df_filt.empty:
                df_filt['Tanggal'] = df_filt['Tanggal'].dt.date
                pdf_bytes = generate_pdf(df_filt, t, b)
                add_log("DOWNLOAD", f"Unduh PDF Periode {b}/{t}")
                st.download_button("Unduh PDF", pdf_bytes, f"Laporan Absensi Bulan {b} Tahun {t}.pdf", "application/pdf")
            else:
                st.error("Data kosong.")

    if USER_ROLE == "Administrator":
        with mytabs[2]:
            st.error("⚠️ PERHATIAN: Hapus data bersifat permanen!")
            confirm_del = st.checkbox("Saya mengerti dan ingin menghapus seluruh data.")
            if confirm_del:
                if st.button("HAPUS SEMUA DATA PERMANEN", type="primary"):
                    if clear_all_data():
                        add_log("DELETE_ALL", "Administrator menghapus seluruh database absensi")
                        st.success("Database berhasil dikosongkan.")
                        time_lib.sleep(2)
                        st.rerun()

elif menu == "📜 System Logs":
    col_L, col_R = st.columns([2, 1])
    with col_L:
        st.markdown("<div class='header-title'>System Logs</div>", unsafe_allow_html=True)
    with col_R:
        st.markdown(clock_html, unsafe_allow_html=True)
    st.write("---")
    
    if st.button("🔄 Refresh Log"):
        st.cache_data.clear()
        st.rerun()
    
    with st.spinner("Memuat data log..."):
        log_df = get_logs()
    
    if not log_df.empty:
        log_df['Waktu'] = log_df['Waktu'].astype(str)
        st.dataframe(log_df.sort_values(by="Waktu", ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("Log kosong.")