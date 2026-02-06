import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, time
import calendar
from fpdf import FPDF
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
import time as time_lib
from streamlit_option_menu import option_menu 

# --- IMPORT VERSI OTOMATIS ---
try:
    from version_info import VERSION_TAG, LAST_UPDATED
except ImportError:
    VERSION_TAG = "v1.0 (Dev)"
    LAST_UPDATED = "Belum Disinkronisasi"

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Absensi BP3MI", layout="wide", page_icon="🏢")

# --- 2. CSS CUSTOM (HORIZONTAL THEME) ---
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
        --success: #10B981;
    }
    
    /* Header Custom */
    .top-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 1px solid var(--border);
        margin-bottom: 20px;
    }
    
    .profile-badge {
        background-color: #F1F5F9;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        color: var(--text-main);
        border: 1px solid var(--border);
    }

    /* Metric Card styling */
    .metric-card {
        background-color: var(--bg-card); 
        color: var(--text-main);
        padding: 24px; 
        border-radius: 12px; 
        border: 1px solid var(--border);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        text-align: center;
    }

    /* Feature Box untuk Halaman Tentang */
    .feature-box {
        background-color: #F8FAFC;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid var(--border);
        margin-bottom: 15px;
        transition: transform 0.2s;
    }
    .feature-box:hover {
        transform: translateY(-5px);
        border-color: var(--accent);
    }
    .feature-title { font-weight: 800; font-size: 1.1rem; color: var(--accent); margin-bottom: 5px; }
    .feature-desc { font-size: 0.9rem; color: var(--text-sub); }

    /* Footer Version */
    .footer-version {
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid var(--border);
        text-align: center;
        font-size: 0.8rem;
        color: var(--text-sub);
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
    except Exception: return pd.DataFrame()

def check_login():
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
        st.session_state['user_role'] = None
        st.session_state['user_name'] = None
    
    if not st.session_state['logged_in']:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("<br><br>", unsafe_allow_html=True)
            st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
            st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg/960px-Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg.png", width=120)
            st.markdown("<h3>Login Sistem Absensi</h3>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            
            if st.button("Masuk Sistem", use_container_width=True):
                with st.spinner("Memverifikasi..."):
                    users_df = get_users_db()
                    if not users_df.empty:
                        user_found = users_df[(users_df['Username'] == username_input) & (users_df['Password'] == password_input)]
                        if not user_found.empty:
                            st.session_state['logged_in'] = True
                            st.session_state['user_role'] = user_found.iloc[0]['Role']
                            st.session_state['user_name'] = user_found.iloc[0]['Nama_Lengkap']
                            st.rerun()
                        else: st.error("Username/Password salah!")
                    else: st.error("Database user kosong.")
        return False 
    return True 

if not check_login(): st.stop()

USER_ROLE = st.session_state['user_role']
USER_NAME = st.session_state['user_name']

# --- DATA & LOGIC FUNCTIONS ---
def get_data():
    try:
        df = conn.read(worksheet="Data_Utama", ttl="0")
        if not df.empty: df['Tanggal'] = pd.to_datetime(df['Tanggal']).dt.date
        return df
    except: return pd.DataFrame(columns=['Nama', 'Tanggal', 'Jam_Masuk', 'Jam_Pulang', 'Status_Data'])

def save_data(new_df):
    try:
        current_df = get_data()
        if not current_df.empty: current_df['Tanggal'] = pd.to_datetime(current_df['Tanggal']).dt.date
        updated_df = pd.concat([current_df, new_df], ignore_index=True).drop_duplicates(subset=['Nama', 'Tanggal'])
        updated_df['Tanggal'] = updated_df['Tanggal'].astype(str)
        conn.update(worksheet="Data_Utama", data=updated_df)
        st.cache_data.clear(); return True
    except: return False

def clear_all_data():
    try:
        empty_df = pd.DataFrame(columns=['Nama', 'Tanggal', 'Jam_Masuk', 'Jam_Pulang', 'Status_Data'])
        conn.update(worksheet="Data_Utama", data=empty_df)
        st.cache_data.clear(); return True
    except: return False

def get_logs():
    try:
        df = conn.read(worksheet="Log_Sistem", ttl=0)
        return df if not df.empty else pd.DataFrame(columns=['Waktu', 'Aksi', 'Detail'])
    except: return pd.DataFrame(columns=['Waktu', 'Aksi', 'Detail'])

def add_log(aksi, detail):
    now = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
    detail_user = f"[{USER_NAME}] {detail}"
    new = pd.DataFrame([{"Waktu": now, "Aksi": aksi, "Detail": detail_user}])
    try:
        cur = get_logs()
        upd = pd.concat([cur, new], ignore_index=True)
        conn.update(worksheet="Log_Sistem", data=upd)
        st.cache_data.clear()
    except: pass

def process_file(file):
    try: df = pd.read_csv(file, sep='\t', header=None, names=['ID','Timestamp','Mch','Cd','Nama','Status','X1','X2'])
    except: file.seek(0); df = pd.read_csv(file, header=None, names=['ID','Timestamp','Mch','Cd','Nama','Status','X1','X2'])
    df['Nama'] = df['Nama'].str.strip(); df['Timestamp'] = pd.to_datetime(df['Timestamp']); df['Tanggal_Asli'] = df['Timestamp'].dt.date
    df = df.sort_values(['Nama', 'Timestamp'])
    final_data = []
    for nama, group in df.groupby('Nama'):
        dates = sorted(group['Tanggal_Asli'].unique())
        used_timestamps = set()
        for tgl in dates:
            logs = group[group['Tanggal_Asli'] == tgl]; ts = sorted([t for t in logs['Timestamp'].tolist() if t not in used_timestamps])
            if not ts: continue
            first = ts[0]; last = ts[-1] if len(ts) > 1 else None
            m_fix = "-"; p_fix = "-"; stat = "Tidak Absen Pulang"
            if first.hour < 13:
                m_fix = first.strftime('%H:%M:%S')
                if last: p_fix = last.strftime('%H:%M:%S'); stat = "Lengkap (Normal)"; used_timestamps.add(last)
            elif first.hour >= 13 and first.time() < time(18, 15):
                if not last: p_fix = first.strftime('%H:%M:%S'); stat = "Tidak Absen Pagi"; used_timestamps.add(first)
                else: m_fix = first.strftime('%H:%M:%S'); p_fix = last.strftime('%H:%M:%S'); stat = "Lengkap (Normal)"; used_timestamps.add(last)
            else:
                m_fix = first.strftime('%H:%M:%S'); found_out = False
                if last:
                    if (last - first).total_seconds() / 3600 > 3: p_fix = last.strftime('%H:%M:%S'); stat = "Lengkap (Normal)"; used_timestamps.add(last); found_out = True
                if not found_out:
                    tgl_bsk = tgl + timedelta(days=1); logs_bsk = group[group['Tanggal_Asli'] == tgl_bsk]
                    if not logs_bsk.empty:
                        pot_out = sorted(logs_bsk['Timestamp'].tolist())[0]
                        if pot_out.hour < 13: p_fix = pot_out.strftime('%H:%M:%S'); stat = "Lengkap (Malam)"; used_timestamps.add(pot_out)
            final_data.append({'Nama': nama, 'Tanggal': tgl, 'Jam_Masuk': m_fix, 'Jam_Pulang': p_fix, 'Status_Data': stat})
    return pd.DataFrame(final_data)

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12); self.cell(0, 10, 'LAPORAN REKAPITULASI ABSENSI OUTSOURCING', 0, 1, 'C'); self.cell(0, 10, 'BP3MI JAWA TENGAH', 0, 1, 'C'); self.ln(5)

def generate_pdf(df_source, year, month):
    pdf = PDF(orientation='L', unit='mm', format='A4'); pdf.add_page()
    num_days = calendar.monthrange(year, month)[1]
    col_no, col_nama, col_summary = 8, 35, 15; w_remain = pdf.w - col_no - col_nama - (col_summary*3) - 20; col_day = w_remain / num_days
    pdf.set_font("Arial", 'B', 9); pdf.cell(0, 5, f"PERIODE : {calendar.month_name[month].upper()} {year}", 0, 1, 'L'); pdf.ln(2)
    pdf.set_font("Arial", 'B', 6); pdf.cell(col_no, 12, 'No', 1, 0, 'C'); pdf.cell(col_nama, 12, 'Nama Pegawai', 1, 0, 'C')
    for d in range(1, num_days+1):
        wk = calendar.weekday(year, month, d)
        pdf.set_fill_color(220,220,220) if wk >= 5 else pdf.set_fill_color(255,255,255)
        pdf.cell(col_day, 12, str(d), 1, 0, 'C', fill=True)
    pdf.cell(col_summary, 12, 'HADIR', 1, 0, 'C'); pdf.cell(col_summary, 12, 'ALPA', 1, 0, 'C'); pdf.cell(col_summary, 12, 'TIDAK LKP', 1, 1, 'C')
    pegawai = sorted(df_source['Nama'].unique())
    for idx, nama in enumerate(pegawai, 1):
        h, a, tl = 0, 0, 0
        pdf.set_font("Arial", '', 6); pdf.cell(col_no, 10, str(idx), 1, 0, 'C'); pdf.cell(col_nama, 10, str(nama)[:18], 1, 0, 'L')
        for d in range(1, num_days+1):
            curr_date = pd.Timestamp(year, month, d).date()
            row = df_source[(df_source['Nama'] == nama) & (df_source['Tanggal'] == curr_date)]
            if not row.empty:
                stat = row.iloc[0]['Status_Data']; m = row.iloc[0]['Jam_Masuk']; p = row.iloc[0]['Jam_Pulang']
                if "Lengkap" in stat:
                    pdf.set_fill_color(173,216,230) if "Malam" in stat else pdf.set_fill_color(144,238,144)
                    txt = f"{m}\n{p}"; h += 1
                else: pdf.set_fill_color(255,255,153); txt = f"{m if m!='-' else p}"; tl += 1
                fill = True
            else:
                if calendar.weekday(year, month, d) < 5: pdf.set_fill_color(255,153,153); txt = "X"; a += 1; fill = True
                else: pdf.set_fill_color(240,240,240); txt = ""; fill = True
            x, y = pdf.get_x(), pdf.get_y(); pdf.cell(col_day, 10, "", 1, 0, 'C', fill=fill)
            pdf.set_xy(x, y+1); pdf.set_font("Arial",'',3); pdf.multi_cell(col_day, 3, txt, 0, 'C'); pdf.set_xy(x+col_day, y); pdf.set_font("Arial",'',6)
        pdf.cell(col_summary, 10, str(h), 1, 0, 'C'); pdf.cell(col_summary, 10, str(a), 1, 0, 'C'); pdf.cell(col_summary, 10, str(tl), 1, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

# --- HEADER LAYOUT (HORIZONTAL) ---
# Bagian ini menggantikan Sidebar
c_logo, c_title, c_profile = st.columns([1, 4, 2])
with c_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg/960px-Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg.png", width=70)
with c_title:
    st.markdown("**Sistem Informasi Absensi**<br><span style='color:grey; font-size:0.9rem'>BP3MI Jawa Tengah</span>", unsafe_allow_html=True)
with c_profile:
    st.markdown(f"""
    <div style='text-align:right;'>
        <span class='profile-badge'>👤 {USER_NAME}</span>
        <div style='font-size:0.75rem; color:grey; margin-top:5px;'>{USER_ROLE}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("---")

# --- NAVIGATION MENU (HORIZONTAL) ---
menu_list = ["Dashboard", "Analisis Pegawai", "Manajemen Data", "Tentang Aplikasi"]
icon_list = ["house", "bar-chart-line", "folder2-open", "info-circle"]
if USER_ROLE == "Administrator":
    menu_list.append("System Logs")
    icon_list.append("journal-text")

selected = option_menu(
    menu_title=None,
    options=menu_list,
    icons=icon_list,
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",  # KUNCI UTAMA: Orientasi Horizontal
    styles={
        "container": {"padding": "0!important", "background-color": "transparent"},
        "icon": {"color": "#2563EB", "font-size": "16px"}, 
        "nav-link": {"font-size": "14px", "text-align": "center", "margin":"0px", "--hover-color": "rgba(37, 99, 235, 0.1)"},
        "nav-link-selected": {"background-color": "#2563EB", "font-weight": "600"},
    }
)

# --- LOAD DATA UTAMA ---
df_global = get_data()

# --- CONTENT LOGIC ---
if selected == "Tentang Aplikasi":
    st.markdown("### ℹ️ Tentang Aplikasi")
    st.markdown("Enterprise-Grade Attendance Management System v2.0")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""<div class='feature-box'><div class='feature-title'>🧠 Anti-Overlap Logic</div><div class='feature-desc'>Algoritma cerdas membedakan Shift Normal, Shift Malam, dan Lembur.</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class='feature-box'><div class='feature-title'>☁️ Cloud Sync</div><div class='feature-desc'>Sinkronisasi real-time dengan Google Sheets Database.</div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""<div class='feature-box'><div class='feature-title'>📑 Auto PDF Audit</div><div class='feature-desc'>Laporan PDF siap cetak dengan pewarnaan otomatis sesuai status kehadiran.</div></div>""", unsafe_allow_html=True)

elif selected == "Dashboard":
    col1, col2 = st.columns([3, 1])
    with col1: st.subheader("📊 Overview Hari Ini")
    with col2: 
        now = datetime.utcnow() + timedelta(hours=7)
        st.markdown(f"<div style='text-align:right; font-size:1.5rem; font-weight:300;'>{now.strftime('%H:%M')}</div>", unsafe_allow_html=True)
    
    if not df_global.empty:
        total = df_global['Nama'].nunique()
        hadir = len(df_global[df_global['Status_Data'].str.contains('Lengkap')])
        incomp = len(df_global[df_global['Status_Data'].str.contains('Tidak')])
        
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'><h3>👥 Total Pegawai</h3><h1>{total}</h1></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><h3>✅ Data Lengkap</h3><h1 style='color:#10B981'>{hadir}</h1></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><h3>⚠️ Tidak Lengkap</h3><h1 style='color:#F59E0B'>{incomp}</h1></div>", unsafe_allow_html=True)
        
        st.write("### 📋 Aktivitas Terakhir")
        st.dataframe(df_global.sort_values('Tanggal', ascending=False).head(8), use_container_width=True)
    else:
        st.info("Belum ada data absensi.")

elif selected == "Analisis Pegawai":
    st.subheader("📈 Analisis Kinerja")
    if not df_global.empty:
        all_pegawai = sorted(df_global['Nama'].unique().tolist())
        c1, c2, c3 = st.columns([1, 1, 3])
        with c1: bln = st.selectbox("Bulan", range(1, 13), index=datetime.now().month-1, format_func=lambda x: calendar.month_name[x])
        with c2: thn = st.number_input("Tahun", value=datetime.now().year)
        with c3: names = st.multiselect("Filter Nama Pegawai", all_pegawai)
        
        df_global['Tanggal'] = pd.to_datetime(df_global['Tanggal'])
        mask = (df_global['Tanggal'].dt.month == bln) & (df_global['Tanggal'].dt.year == thn)
        if names: mask = mask & df_global['Nama'].isin(names)
        df_show = df_global[mask]
        
        if not df_show.empty:
            tab1, tab2 = st.tabs(["📊 Grafik Visual", "📄 Data Detail"])
            with tab1:
                gc1, gc2 = st.columns(2)
                with gc1:
                    dchart = df_show.copy()
                    dchart['Kat'] = dchart['Status_Data'].apply(lambda x: 'Lengkap' if 'Lengkap' in x else 'Tidak Lengkap')
                    fig = px.bar(dchart.groupby(['Nama','Kat']).size().reset_index(name='Jml'), x='Nama', y='Jml', color='Kat')
                    st.plotly_chart(fig, use_container_width=True)
                with gc2:
                    pie = df_show['Status_Data'].value_counts().reset_index()
                    st.plotly_chart(px.pie(pie, values='count', names='Status_Data', hole=0.5), use_container_width=True)
            with tab2:
                df_disp = df_show.copy(); df_disp['Tanggal'] = df_disp['Tanggal'].dt.date
                st.dataframe(df_disp.sort_values('Tanggal'), use_container_width=True)
        else: st.warning("Data tidak ditemukan.")
    else: st.warning("Database kosong.")

elif selected == "Manajemen Data":
    st.subheader("📂 Pusat Data")
    tab1, tab2, tab3 = st.tabs(["📤 Upload Data", "📥 Download Laporan", "⚙️ Admin Tools"])
    
    with tab1:
        f = st.file_uploader("Upload File Absensi (.txt)", type=['txt'])
        if f and st.button("Proses & Simpan"):
            bar = st.progress(0, "Membaca file...")
            res = process_file(f); bar.progress(50, "Menganalisis shift...")
            if save_data(res):
                bar.progress(100, "Selesai!"); add_log("UPLOAD", f.name); st.success(f"Berhasil menyimpan {len(res)} data."); st.balloons()
    
    with tab2:
        c1, c2 = st.columns(2)
        b = c1.selectbox("Bulan Laporan", range(1,13), index=datetime.now().month-1)
        t = c2.number_input("Tahun Laporan", value=datetime.now().year)
        if st.button("Generate PDF Laporan"):
            df_global['Tanggal'] = pd.to_datetime(df_global['Tanggal'])
            df_f = df_global[(df_global['Tanggal'].dt.month == b) & (df_global['Tanggal'].dt.year == t)]
            if not df_f.empty:
                df_f['Tanggal'] = df_f['Tanggal'].dt.date
                pdf = generate_pdf(df_f, t, b); add_log("DOWNLOAD", f"PDF {b}/{t}")
                st.download_button("⬇️ Download PDF", pdf, f"Laporan_{b}_{t}.pdf", "application/pdf", type="primary")
            else: st.error("Data bulan tersebut kosong.")

    with tab3:
        if st.button("🔄 Paksa Refresh Cloud"):
            st.cache_data.clear(); add_log("REFRESH", "Manual"); st.rerun()
        
        if USER_ROLE == "Administrator":
            st.divider()
            st.error("Zona Bahaya")
            if st.checkbox("Saya ingin menghapus SELURUH DATABASE"):
                if st.button("HAPUS PERMANEN"):
                    clear_all_data(); add_log("DELETE_ALL", "Cleared"); st.rerun()

elif selected == "System Logs":
    st.subheader("📜 Log Aktivitas Sistem")
    if st.button("Refresh Log"): st.cache_data.clear(); st.rerun()
    logs = get_logs()
    if not logs.empty: st.dataframe(logs.sort_values('Waktu', ascending=False), use_container_width=True)

# --- FOOTER ---
st.markdown(f"<div class='footer-version'>System Version: <b>{VERSION_TAG}</b> • Last Update: {LAST_UPDATED}<br>© 2026 BP3MI Jawa Tengah</div>", unsafe_allow_html=True)
if st.button("Keluar / Logout", key="logout_footer"):
    st.session_state['logged_in'] = False; st.rerun()