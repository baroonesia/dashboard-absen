import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from fpdf import FPDF
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Absensi BP3MI", layout="wide", page_icon="🏢")

# --- 2. CSS CUSTOM (STYLE MINIMALIS) ---
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
    </style>
    """, unsafe_allow_html=True)

# --- 3. KONEKSI GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

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

if 'system_logs' not in st.session_state:
    st.session_state['system_logs'] = []

def add_log(aksi, detail):
    now = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
    st.session_state['system_logs'].insert(0, {"Waktu": now, "Aksi": aksi, "Detail": detail})

# --- 4. LOGIKA PROSES FILE ---
def process_file(file):
    df = pd.read_csv(file, sep='\t', header=None, names=['ID','Timestamp','Mch','Cd','Nama','Status','X1','X2'])
    df['Nama'] = df['Nama'].str.strip()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Tanggal'] = df['Timestamp'].dt.date
    
    in_data = df[df['Status'] == 'I'].groupby(['Nama', 'Tanggal'])['Timestamp'].max().reset_index()
    out_data = df[df['Status'] == 'O'].groupby(['Nama', 'Tanggal'])['Timestamp'].max().reset_index()
    
    res = pd.merge(in_data, out_data, on=['Nama', 'Tanggal'], how='outer', suffixes=('_In', '_Out'))
    res['Jam_Masuk'] = res['Timestamp_In'].dt.strftime('%H:%M:%S').fillna("-")
    res['Jam_Pulang'] = res['Timestamp_Out'].dt.strftime('%H:%M:%S').fillna("-")
    
    res['Status_Data'] = res.apply(lambda row: "Lengkap" if row['Jam_Masuk'] != "-" and row['Jam_Pulang'] != "-" else "Tidak Lengkap", axis=1)
    return res[['Nama', 'Tanggal', 'Jam_Masuk', 'Jam_Pulang', 'Status_Data']]

# --- 5. FUNGSI PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'LAPORAN REKAPITULASI ABSENSI OUTSOURCING', 0, 1, 'C')
        self.cell(0, 10, 'BP3MI JAWA TENGAH', 0, 1, 'C')
        self.cell(0, 10, '', 0, 1, 'C')

def generate_pdf(df_source, year, month):
    # --- PEMBERSIHAN DATA (Mencegah "None") ---
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

    # Header Tabel
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

    # Isi Data Pegawai
    pegawai = sorted(df_source['Nama'].unique())
    for idx, nama in enumerate(pegawai, 1):
        h, a, tl = 0, 0, 0
        pdf.set_font("Arial", '', 6)
        pdf.cell(col_no, 10, str(idx), 1, 0, 'C')
        pdf.cell(col_nama, 10, str(nama)[:18], 1, 0, 'L')
        
        for d in range(1, num_days+1):
            curr_date = pd.Timestamp(year, month, d).date()
            # Filter baris berdasarkan nama dan tanggal
            row = df_source[(df_source['Nama'] == nama) & (df_source['Tanggal'] == curr_date)]
            
            fill, txt = False, ""
            if not row.empty:
                m = row.iloc[0]['Jam_Masuk']
                p = row.iloc[0]['Jam_Pulang']
                stat = row.iloc[0]['Status_Data']
                
                # Pastikan m dan p bukan string 'None' (hasil bacaan Sheets)
                m = "-" if m == "None" or m == "nan" else m
                p = "-" if p == "None" or p == "nan" else p

                if stat == "Lengkap" and m != "-" and p != "-":
                    pdf.set_fill_color(144, 238, 144); txt = f"{m}\n{p}"; h += 1
                else:
                    pdf.set_fill_color(255, 255, 102); txt = f"{m if m!='-' else p}"; tl += 1
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
        
        # Kolom Summary di Kanan
        pdf.cell(col_summary, 10, str(h), 1, 0, 'C')
        pdf.cell(col_summary, 10, str(a), 1, 0, 'C')
        pdf.cell(col_summary, 10, str(tl), 1, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')
# --- 6. SIDEBAR MENU ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg/960px-Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg.png", width=50)
    st.markdown("BP3MI Jawa Tengah")
    menu = st.radio("MENU UTAMA", ["🏠 Dashboard", "📈 Analisis Pegawai", "📂 Manajemen Data", "📜 System Logs"])
    st.divider()
    if st.button("🔄 Refresh Data Cloud"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Connected to Database")
    st.caption("Pranata Komputer - BP3MI Jateng © 2026")

# --- 7. DASHBOARD CONTENT ---
df_global = get_data()

if menu == "🏠 Dashboard":
    now_indo = datetime.utcnow() + timedelta(hours=7)
    hari_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
    str_hari = hari_indo[now_indo.weekday()]
    str_tgl = now_indo.strftime('%d %B %Y')
    str_jam = now_indo.strftime('%H:%M') 
    
    col_L, col_R = st.columns([2, 1])
    
    with col_L:
        st.markdown(f"""
        <div style='padding-top:10px;'>
            <div class='header-title'>Dashboard Absensi BP3MI Jawa Tengah</div>
            <div class='header-subtitle'>Monitoring Kehadiran Outsourcing</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col_R:
        st.markdown(f"""
        <div class='clock-container-new'>
            <div class='clock-time-new'>{str_jam}</div>
            <div class='clock-date-new'>{str_hari}, {str_tgl}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    
    if not df_global.empty:
        total_p = df_global['Nama'].nunique()
        lengkap = len(df_global[df_global['Status_Data'] == 'Lengkap'])
        tl = len(df_global[df_global['Status_Data'] == 'Tidak Lengkap'])
        
        m1, m2, m3 = st.columns(3)
        m1.markdown(f"<div class='metric-card'><h4>👥 Pegawai</h4><h1>{total_p}</h1></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='metric-card'><h4>✅ Hadir</h4><h1 style='color:#10B981;'>{lengkap}</h1></div>", unsafe_allow_html=True)
        m3.markdown(f"<div class='metric-card'><h4>⚠️ Tdk Lengkap</h4><h1 style='color:#F59E0B;'>{tl}</h1></div>", unsafe_allow_html=True)
        
        st.write("### 📋 Log Masuk Terakhir")
        st.dataframe(df_global.sort_values('Tanggal', ascending=False).head(10), use_container_width=True)
    else:
        st.info("Database kosong.")

elif menu == "📈 Analisis Pegawai":
    st.markdown("<div class='header-title'>Analisis Performa Bulanan</div>", unsafe_allow_html=True)
    
    if not df_global.empty:
        # --- FITUR BARU: SELECT BY MONTH ---
        st.write("---")
        col_filter1, col_filter2 = st.columns(2)
        with col_filter1:
            sel_bulan = st.selectbox("Pilih Bulan", range(1, 13), index=datetime.now().month-1, format_func=lambda x: calendar.month_name[x])
        with col_filter2:
            sel_tahun = st.number_input("Pilih Tahun", value=datetime.now().year)

        # Proses Filter Data
        df_global['Tanggal'] = pd.to_datetime(df_global['Tanggal'])
        mask = (df_global['Tanggal'].dt.month == sel_bulan) & (df_global['Tanggal'].dt.year == sel_tahun)
        df_filtered = df_global[mask]

        if not df_filtered.empty:
            # 1. Grafik (Mengikuti Filter Bulan)
            st.success(f"Menampilkan Data: **{calendar.month_name[sel_bulan]} {sel_tahun}**")
            
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Grafik Kepatuhan (Bulan Ini)**")
                chart_data = df_filtered.groupby(['Nama', 'Status_Data']).size().reset_index(name='Jumlah')
                fig = px.bar(chart_data, x='Nama', y='Jumlah', color='Status_Data', 
                             color_discrete_map={'Lengkap':'#2563EB', 'Tidak Lengkap':'#EF553B'})
                st.plotly_chart(fig, use_container_width=True)
            with c2:
                st.write("**Proporsi (Bulan Ini)**")
                pie = df_filtered['Status_Data'].value_counts().reset_index()
                pie.columns = ['Status','Jumlah']
                fig2 = px.pie(pie, values='Jumlah', names='Status', hole=0.6, 
                              color_discrete_map={'Lengkap':'#2563EB', 'Tidak Lengkap':'#EF553B'})
                st.plotly_chart(fig2, use_container_width=True)
            
            # 2. Tabel Daftar Data (Sesuai Request)
            st.markdown(f"### 📋 Daftar Detail Absensi: {calendar.month_name[sel_bulan]} {sel_tahun}")
            # Format tanggal agar enak dilihat di tabel
            df_display = df_filtered.copy()
            df_display['Tanggal'] = df_display['Tanggal'].dt.date
            st.dataframe(df_display.sort_values('Tanggal'), use_container_width=True, hide_index=True)
            
        else:
            st.warning(f"Tidak ada data absensi ditemukan pada **{calendar.month_name[sel_bulan]} {sel_tahun}**.")
    else:
        st.warning("Belum ada data sama sekali di sistem.")

elif menu == "📂 Manajemen Data":
    st.markdown("<div class='header-title'>Manajemen Data</div>", unsafe_allow_html=True)
    st.write("---")
    
    t1, t2 = st.tabs(["Upload Data", "Download Laporan"])
    
    with t1:
        f = st.file_uploader("Upload .txt", type=['txt'])
        if f and st.button("Simpan Data"):
            res = process_file(f)
            if save_data(res):
                add_log("UPLOAD", f.name)
                st.success("Berhasil!")
    
    with t2:
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
                st.download_button("Unduh PDF", pdf_bytes, f"Laporan_Absen_Outsourcing_Bulan_{b}_{t}.pdf", "application/pdf")
            else:
                st.error("Data kosong.")

elif menu == "📜 System Logs":
    st.markdown("<div class='header-title'>System Logs</div>", unsafe_allow_html=True)
    st.write("---")
    if st.session_state['system_logs']:
        st.table(pd.DataFrame(st.session_state['system_logs']))
    else:
        st.info("Log kosong.")