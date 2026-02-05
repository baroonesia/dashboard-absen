import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from fpdf import FPDF
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Absensi BP3MI", layout="wide", page_icon="🏢")

# --- 2. CSS CUSTOM (Dual Mode & Styling Profesional) ---
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
    .clock-box { 
        background: #1e293b; color: #38bdf8; padding: 10px 20px; 
        border-radius: 8px; font-family: 'Courier New', Courier, monospace;
        font-weight: bold; font-size: 1.2rem; border-left: 5px solid #38bdf8;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. KONEKSI DATABASE (GOOGLE SHEETS) ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    """Mengambil data dari Sheet 'Data_Utama'"""
    try:
        df = conn.read(worksheet="Data_Utama", ttl="0")
        # Pastikan kolom tanggal dibaca sebagai datetime
        if not df.empty:
            df['Tanggal'] = pd.to_datetime(df['Tanggal']).dt.date
        return df
    except Exception:
        # Kembalikan dataframe kosong jika sheet belum ada isinya
        return pd.DataFrame(columns=['Nama', 'Tanggal', 'Jam_Masuk', 'Jam_Pulang', 'Status_Data'])

def save_data(new_df):
    """Menyimpan data (Append) ke Google Sheet"""
    try:
        current_df = get_data()
        # Konversi tanggal di dataframe lama agar tipe datanya sama
        if not current_df.empty:
            current_df['Tanggal'] = pd.to_datetime(current_df['Tanggal']).dt.date
            
        updated_df = pd.concat([current_df, new_df], ignore_index=True)
        # Hapus duplikat berdasarkan Nama dan Tanggal
        updated_df = updated_df.drop_duplicates(subset=['Nama', 'Tanggal'])
        
        # Ubah kembali ke string sebelum simpan ke Sheet agar aman
        updated_df['Tanggal'] = updated_df['Tanggal'].astype(str)
        conn.update(worksheet="Data_Utama", data=updated_df)
        st.cache_data.clear()
        return True
    except Exception as e:
        st.error(f"Error Saving: {e}")
        return False

# Fungsi Log Sederhana (Session State untuk Online)
if 'system_logs' not in st.session_state:
    st.session_state['system_logs'] = []

def add_log(aksi, detail):
    now = (datetime.utcnow() + timedelta(hours=7)).strftime("%Y-%m-%d %H:%M:%S")
    st.session_state['system_logs'].insert(0, {"Waktu": now, "Aksi": aksi, "Detail": detail})

# --- 4. LOGIKA PEMROSESAN FILE ---
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
    
    def cek_status(row):
        return "Lengkap" if row['Jam_Masuk'] != "-" and row['Jam_Pulang'] != "-" else "Tidak Lengkap"
    
    res['Status_Data'] = res.apply(cek_status, axis=1)
    return res[['Nama', 'Tanggal', 'Jam_Masuk', 'Jam_Pulang', 'Status_Data']]

# --- 5. FUNGSI PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'LAPORAN REKAPITULASI ABSENSI ONLINE', 0, 1, 'C')

def generate_pdf(df_source, year, month):
    pdf = PDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    num_days = calendar.monthrange(year, month)[1]
    col_no, col_nama, col_summary = 8, 35, 15
    w_remain = pdf.w - col_no - col_nama - (col_summary*3) - 20
    col_day = w_remain / num_days
    
    nama_bulan = calendar.month_name[month].upper()
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(0, 5, f"PERIODE: {nama_bulan} {year}", 0, 1, 'L')
    pdf.ln(2)

    pdf.set_font("Arial", 'B', 6)
    pdf.cell(col_no, 12, 'No', 1, 0, 'C')
    pdf.cell(col_nama, 12, 'Nama Pegawai', 1, 0, 'C')
    for d in range(1, num_days+1):
        wk = calendar.weekday(year, month, d)
        pdf.set_fill_color(200,200,200) if wk >= 5 else pdf.set_fill_color(255,255,255)
        pdf.cell(col_day, 12, str(d), 1, 0, 'C', fill=True)
    pdf.cell(col_summary, 12, 'HADIR', 1, 0, 'C')
    pdf.cell(col_summary, 12, 'ALPA', 1, 0, 'C')
    pdf.cell(col_summary, 12, 'TDK LKP', 1, 1, 'C')

    pegawai = sorted(df_source['Nama'].unique())
    for idx, nama in enumerate(pegawai, 1):
        h, a, tl = 0, 0, 0
        pdf.set_font("Arial", '', 6)
        pdf.cell(col_no, 10, str(idx), 1, 0, 'C')
        pdf.cell(col_nama, 10, nama[:18], 1, 0, 'L')
        
        for d in range(1, num_days+1):
            curr = pd.Timestamp(year, month, d).date()
            row = df_source[(df_source['Nama'] == nama) & (df_source['Tanggal'] == curr)]
            fill, txt = False, ""
            
            if not row.empty:
                m, p = row.iloc[0]['Jam_Masuk'], row.iloc[0]['Jam_Pulang']
                if row.iloc[0]['Status_Data'] == "Lengkap":
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
            pdf.set_xy(x, y+1); pdf.set_font("Arial",'',4); pdf.multi_cell(col_day, 3, txt, 0, 'C')
            pdf.set_xy(x+col_day, y); pdf.set_font("Arial",'',6)
        
        pdf.cell(col_summary, 10, str(h), 1, 0, 'C')
        pdf.cell(col_summary, 10, str(a), 1, 0, 'C')
        pdf.cell(col_summary, 10, str(tl), 1, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# --- 6. NAVIGASI SIDEBAR (KEMBALI KE SIDEBAR) ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg/960px-Logo_Kementerian_Pelindungan_Pekerja_Migran_Indonesia_-_BP2MI_v2_%282024%29.svg.png", width=60)
    st.markdown("###BP3MI Jawa Tengah")
    
    # Menu Navigasi Sesuai Permintaan
    menu = st.radio("MAIN MENU", 
        ["🏠 Dashboard", "📈 Analisis Pegawai", "📂 Manajemen Data", "📜 System Logs"]
    )
    
    st.divider()
    if st.button("🔄 Refresh Data Cloud"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Connected to Google Sheets")
    st.caption("Pranata Komputer - BP3MI Jateng © 2026")

# --- 7. LOAD DATA GLOBAL ---
df_global = get_data()

# --- 8. KONTEN UTAMA ---

if menu == "🏠 Dashboard":
    # Header Waktu
    now_indo = datetime.utcnow() + timedelta(hours=7)
    hari_list = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]
    nama_hari = hari_list[now_indo.weekday()]
    
    c1, c2 = st.columns([3,1])
    with c1: st.markdown("<div class='main-title'>Dashboard Absensi</div>", unsafe_allow_html=True)
    with c2: 
        st.markdown(f"""<div class='clock-box'>📍 WIB (GMT+7)<br>{nama_hari}, {now_indo.strftime('%d %b %Y')}<br>{now_indo.strftime('%H:%M:%S')}</div>""", unsafe_allow_html=True)
    
    st.write("---")
    
    if not df_global.empty:
        # Hitung Metrik
        total_p = df_global['Nama'].nunique()
        lengkap = len(df_global[df_global['Status_Data'] == 'Lengkap'])
        tl = len(df_global[df_global['Status_Data'] == 'Tidak Lengkap'])
        
        m1, m2, m3 = st.columns(3)
        m1.markdown(f"<div class='metric-card'><h4>👥 Total Pegawai</h4><h2>{total_p}</h2><p>Terdaftar di Database</p></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='metric-card'><h4>✅ Kehadiran Lengkap</h4><h2 style='color:#10B981;'>{lengkap}</h2><p>Data Bersih</p></div>", unsafe_allow_html=True)
        m3.markdown(f"<div class='metric-card'><h4>⚠️ Data Tidak Lengkap</h4><h2 style='color:#F59E0B;'>{tl}</h2><p>Perlu Dicek</p></div>", unsafe_allow_html=True)
        
        st.subheader("📋 10 Data Presensi Terakhir Masuk")
        st.dataframe(df_global.sort_values('Tanggal', ascending=False).head(10), use_container_width=True)
    else:
        st.info("Database Google Sheet masih kosong. Silakan upload data di menu 'Manajemen Data'.")

elif menu == "📈 Analisis Pegawai":
    st.markdown("<div class='main-title'>Analisis Performa</div>", unsafe_allow_html=True)
    
    if not df_global.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("#### 📊 Grafik Kepatuhan per Pegawai")
            # Grouping Data
            chart_data = df_global.groupby(['Nama', 'Status_Data']).size().reset_index(name='Jumlah')
            fig = px.bar(chart_data, x='Nama', y='Jumlah', color='Status_Data',
                         color_discrete_map={'Lengkap':'#10B981', 'Tidak Lengkap':'#EF553B'},
                         template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            
        with col2:
            st.write("#### 🍰 Proporsi Keseluruhan")
            pie_data = df_global['Status_Data'].value_counts().reset_index()
            pie_data.columns = ['Status', 'Jumlah']
            fig2 = px.pie(pie_data, values='Jumlah', names='Status', hole=0.4,
                          color_discrete_map={'Lengkap':'#10B981', 'Tidak Lengkap':'#EF553B'})
            st.plotly_chart(fig2, use_container_width=True)
            
        st.write("#### 🏆 Peringkat Kedisiplinan")
        rank = df_global[df_global['Status_Data']=='Lengkap'].groupby('Nama').size().reset_index(name='Jml_Hadir_Lengkap')
        st.dataframe(rank.sort_values('Jml_Hadir_Lengkap', ascending=False), use_container_width=True)
    else:
        st.warning("Belum ada data untuk dianalisis.")

elif menu == "📂 Manajemen Data":
    st.markdown("<div class='main-title'>Manajemen Data</div>", unsafe_allow_html=True)
    
    tab_up, tab_down = st.tabs(["📤 Upload Data Baru", "📄 Download Laporan PDF"])
    
    with tab_up:
        st.info("Upload file .txt dari mesin absen. Data akan otomatis digabungkan ke Google Sheets.")
        file = st.file_uploader("Pilih File Absen (.txt)", type=['txt'])
        if file:
            if st.button("Proses & Simpan ke Cloud"):
                with st.spinner("Sedang memproses..."):
                    new_data = process_file(file)
                    sukses = save_data(new_data)
                    if sukses:
                        add_log("UPLOAD", f"Berhasil upload file: {file.name}")
                        st.success("Data berhasil disimpan!")
                        st.balloons()
    
    with tab_down:
        st.write("### Generate Laporan Bulanan")
        if not df_global.empty:
            c_bln, c_thn = st.columns(2)
            bulan = c_bln.selectbox("Pilih Bulan", range(1,13), index=datetime.now().month-1)
            tahun = c_thn.number_input("Pilih Tahun", value=datetime.now().year)
            
            if st.button("Download PDF"):
                # Filter Data
                df_global['Tanggal'] = pd.to_datetime(df_global['Tanggal']) # Pastikan datetime
                mask = (df_global['Tanggal'].dt.month == bulan) & (df_global['Tanggal'].dt.year == tahun)
                df_filtered = df_global[mask]
                
                if not df_filtered.empty:
                    # Kembalikan ke format date object untuk PDF generator
                    df_filtered['Tanggal'] = df_filtered['Tanggal'].dt.date
                    pdf_bytes = generate_pdf(df_filtered, tahun, bulan)
                    add_log("DOWNLOAD", f"Download PDF Laporan Bulan {bulan}/{tahun}")
                    st.download_button("📥 Klik Disini untuk Download PDF", data=pdf_bytes, file_name=f"Laporan_{bulan}_{tahun}.pdf", mime="application/pdf")
                else:
                    st.error("Tidak ada data pada periode bulan/tahun tersebut.")

elif menu == "📜 System Logs":
    st.markdown("<div class='main-title'>System Activity Logs</div>", unsafe_allow_html=True)
    st.info("Log ini mencatat aktivitas sesi ini (Upload/Download).")
    
    if st.session_state['system_logs']:
        log_df = pd.DataFrame(st.session_state['system_logs'])
        st.table(log_df)
    else:
        st.write("Belum ada aktivitas tercatat.")