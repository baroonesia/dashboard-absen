import streamlit as st
import pandas as pd
import os
from datetime import datetime
import calendar
from fpdf import FPDF

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Absensi BP3MI", layout="wide", page_icon="🏢")

# --- 2. CSS DUAL MODE & UI ---
st.markdown("""
    <style>
    :root { --bg-card: #ffffff; --text-main: #1E293B; --border: #E2E8F0; }
    @media (prefers-color-scheme: dark) { :root { --bg-card: #1E293B; --text-main: #F8FAFC; --border: #334155; } }
    .metric-card {
        background-color: var(--bg-card); color: var(--text-main);
        padding: 20px; border-radius: 12px; border: 1px solid var(--border);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px;
    }
    .main-title { color: var(--text-main); font-weight: 700; font-size: 2.2rem; }
    .info-box { background: linear-gradient(90deg, #2563EB 0%, #1D4ED8 100%); color: white; padding: 20px; border-radius: 12px; margin-bottom: 25px; }
    </style>
    """, unsafe_allow_html=True)

SAVE_DIR = "riwayat"
LOG_FILE = "system_logs.csv"
if not os.path.exists(SAVE_DIR): os.makedirs(SAVE_DIR)

# --- 3. FUNGSI LOGGING & PDF ---
def add_log(action, detail):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_log = pd.DataFrame([[now, action, detail]], columns=['Waktu', 'Aksi', 'Detail'])
    new_log.to_csv(LOG_FILE, mode='a', header=not os.path.exists(LOG_FILE), index=False)

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'LAPORAN REKAPITULASI ABSENSI BULANAN', 0, 1, 'C')

def generate_pdf(resume_all, year, month):
    pdf = PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    num_days = calendar.monthrange(year, month)[1]
    col_no, col_nama, col_summary = 8, 35, 15
    w_total_summary = col_summary * 3
    w_remaining = pdf.w - col_no - col_nama - w_total_summary - 20
    col_day = w_remaining / num_days
    
    nama_bulan = calendar.month_name[month].upper()
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, f"PERIODE LAPORAN: 01 {nama_bulan} {year} S.D {num_days} {nama_bulan} {year}", 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font("Arial", 'B', 6)
    pdf.cell(col_no, 12, 'No', 1, 0, 'C')
    pdf.cell(col_nama, 12, 'Nama Pegawai', 1, 0, 'C')
    for d in range(1, num_days + 1):
        weekday = calendar.weekday(year, month, d)
        pdf.set_fill_color(200, 200, 200) if weekday >= 5 else pdf.set_fill_color(255, 255, 255)
        pdf.cell(col_day, 12, str(d), 1, 0, 'C', fill=True)
    
    pdf.cell(col_summary, 12, 'JML HADIR', 1, 0, 'C')
    pdf.cell(col_summary, 12, 'JML ALPA', 1, 0, 'C')
    pdf.cell(col_summary, 12, 'TDK LKP', 1, 1, 'C')

    pegawai_list = sorted(resume_all['Nama'].unique())
    for idx, nama in enumerate(pegawai_list, 1):
        jml_hadir, jml_alpa, jml_tl = 0, 0, 0
        pdf.set_font("Arial", '', 6)
        pdf.cell(col_no, 10, str(idx), 1, 0, 'C')
        pdf.cell(col_nama, 10, nama[:18], 1, 0, 'L')
        
        for d in range(1, num_days + 1):
            curr_date = datetime(year, month, d).date()
            data_hari = resume_all[resume_all['Tanggal'] == curr_date]
            data_hari = data_hari[data_hari['Nama'] == nama]
            
            fill, status_text = False, ""
            if not data_hari.empty:
                m, p = data_hari.iloc[0]['Jam_Masuk'], data_hari.iloc[0]['Jam_Pulang']
                if m != "-" and p != "-":
                    pdf.set_fill_color(144, 238, 144); status_text = f"{m}\n{p}"; jml_hadir += 1
                else:
                    pdf.set_fill_color(255, 255, 102); status_text = f"{m if m != '-' else p}"; jml_tl += 1
                fill = True
            else:
                if calendar.weekday(year, month, d) < 5:
                    pdf.set_fill_color(255, 153, 153); status_text = "X"; jml_alpa += 1; fill = True
                else:
                    pdf.set_fill_color(240, 240, 240); fill = True

            cur_x, cur_y = pdf.get_x(), pdf.get_y()
            pdf.cell(col_day, 10, "", 1, 0, 'C', fill=fill)
            pdf.set_xy(cur_x, cur_y + 1)
            pdf.set_font("Arial", '', 4); pdf.multi_cell(col_day, 3, status_text, 0, 'C'); pdf.set_xy(cur_x + col_day, cur_y)
            
        pdf.set_font("Arial", 'B', 6)
        pdf.cell(col_summary, 10, str(jml_hadir), 1, 0, 'C')
        pdf.cell(col_summary, 10, str(jml_alpa), 1, 0, 'C')
        pdf.cell(col_summary, 10, str(jml_tl), 1, 1, 'C')
        
    return pdf.output(dest='S').encode('latin-1')

# --- 4. LOGIKA DATA ---
def get_all_stored_data():
    files = [os.path.join(SAVE_DIR, f) for f in os.listdir(SAVE_DIR) if f.endswith('.txt')]
    if not files: return pd.DataFrame()
    all_df = []
    for f in files:
        temp_df = pd.read_csv(f, sep='\t', header=None, names=['ID','Timestamp','Mch','Cd','Nama','Status','X1','X2'])
        all_df.append(temp_df)
    return pd.concat(all_df).drop_duplicates() if all_df else pd.DataFrame()

def process_logic(df, date_range=None):
    if df.empty: return df
    df['Nama'] = df['Nama'].str.strip()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Tanggal'] = df['Timestamp'].dt.date
    if date_range and len(date_range) == 2:
        df = df[(df['Tanggal'] >= date_range[0]) & (df['Tanggal'] <= date_range[1])]
    
    in_data = df[df['Status'] == 'I'].groupby(['Nama', 'Tanggal'])['Timestamp'].max().reset_index()
    out_data = df[df['Status'] == 'O'].groupby(['Nama', 'Tanggal'])['Timestamp'].max().reset_index()
    res = pd.merge(in_data, out_data, on=['Nama', 'Tanggal'], how='outer', suffixes=('_In', '_Out'))
    res['Jam_Masuk'] = res['Timestamp_In'].dt.strftime('%H:%M:%S').fillna("-")
    res['Jam_Pulang'] = res['Timestamp_Out'].dt.strftime('%H:%M:%S').fillna("-")
    return res

# --- 5. MAIN APP ---
with st.sidebar:
    st.markdown("### 🏢 BP3MI Navigasi")
    menu = st.radio("MENU", ["🏠 Dashboard", "📈 Analisis Pegawai", "📂 Manajemen Data", "📜 System Logs"])
    st.divider()
    if st.button("🔄 Refresh Data"): st.rerun()

data_global = get_all_stored_data()
res_global = process_logic(data_global.copy()) if not data_global.empty else pd.DataFrame()

if menu == "🏠 Dashboard":
    st.markdown("<div class='main-title'>Sistem Absensi BP3MI 😊</div>", unsafe_allow_html=True)
    if not res_global.empty:
        total_p = res_global['Nama'].nunique()
        total_hadir = len(res_global[(res_global['Jam_Masuk'] != "-") & (res_global['Jam_Pulang'] != "-")])
        total_tl = len(res_global[(res_global['Jam_Masuk'] == "-") | (res_global['Jam_Pulang'] == "-")])
        
        m1, m2, m3 = st.columns(3)
        m1.markdown(f"<div class='metric-card'><h4>👥 Total Pegawai</h4><h2>{total_p}</h2></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='metric-card'><h4>✅ Hadir Lengkap</h4><h2 style='color:#10B981;'>{total_hadir}</h2></div>", unsafe_allow_html=True)
        m3.markdown(f"<div class='metric-card'><h4>⚠️ Tidak Lengkap</h4><h2 style='color:#F59E0B;'>{total_tl}</h2></div>", unsafe_allow_html=True)
        st.write("### 10 Data Presensi Terkini")
        st.dataframe(res_global[['Nama', 'Tanggal', 'Jam_Masuk', 'Jam_Pulang']].head(10), use_container_width=True)

elif menu == "📈 Analisis Pegawai":
    st.markdown("<div class='main-title'>Analisis Performa</div>", unsafe_allow_html=True)
    if not res_global.empty:
        stats = res_global.groupby('Nama').size().reset_index(name='Total_Hari')
        st.dataframe(stats, use_container_width=True)

elif menu == "📂 Manajemen Data":
    st.markdown("<div class='main-title'>Manajemen Arsip & Export</div>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["📤 Unggah Data", "📜 Daftar Arsip"])
    with tab1:
        file = st.file_uploader("Pilih file log .txt", type=['txt'])
        if file:
            t_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"{t_str}_{file.name}"
            with open(os.path.join(SAVE_DIR, fname), "wb") as f: f.write(file.getbuffer())
            add_log("UPLOAD", f"File {fname} diunggah")
            st.success("Berhasil!")
    with tab2:
        d_filter = st.date_input("Filter Rentang Tanggal untuk PDF", [datetime(2026,2,4), datetime(2026,2,5)])
        for f in sorted(os.listdir(SAVE_DIR), reverse=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            col1.write(f"📄 {f}")
            if col2.button("📥 PDF", key=f"pdf_{f}"):
                p = os.path.join(SAVE_DIR, f)
                df_f = pd.read_csv(p, sep='\t', header=None, names=['ID','Timestamp','Mch','Cd','Nama','Status','X1','X2'])
                res_f = process_logic(df_f, d_filter)
                pdf_b = generate_pdf(res_f, d_filter[0].year, d_filter[0].month)
                st.download_button("Download PDF", pdf_b, f"Laporan_{f}.pdf")
            if col3.button("🗑️", key=f"del_{f}"):
                os.remove(os.path.join(SAVE_DIR, f))
                add_log("DELETE", f"File {f} dihapus")
                st.rerun()

elif menu == "📜 System Logs":
    st.markdown("<div class='main-title'>Aktivitas Sistem</div>", unsafe_allow_html=True)
    if os.path.exists(LOG_FILE):
        st.table(pd.read_csv(LOG_FILE).sort_index(ascending=False))