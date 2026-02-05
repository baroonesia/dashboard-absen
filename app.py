import streamlit as st
import pandas as pd
from datetime import datetime
import calendar
from fpdf import FPDF
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Sistem Absensi BP3MI", layout="wide", page_icon="🏢")

# --- 2. KONEKSI GOOGLE SHEETS ---
# Membuat koneksi ke Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data_from_sheet():
    """Mengambil data dari Google Sheet"""
    try:
        # Mengambil data dan memastikan format tanggal benar
        df = conn.read(worksheet="Data_Utama", ttl="0") # ttl=0 agar tidak dicache lama
        return df
    except:
        return pd.DataFrame(columns=['Nama', 'Tanggal', 'Jam_Masuk', 'Jam_Pulang', 'Status_Data'])

def save_data_to_sheet(new_df):
    """Menambahkan data baru ke Google Sheet"""
    try:
        current_df = get_data_from_sheet()
        updated_df = pd.concat([current_df, new_df], ignore_index=True)
        # Hapus duplikat agar data tidak dobel jika diupload ulang
        updated_df = updated_df.drop_duplicates(subset=['Nama', 'Tanggal'])
        conn.update(worksheet="Data_Utama", data=updated_df)
        st.cache_data.clear() # Hapus cache agar tampilan refresh
        return True
    except Exception as e:
        st.error(f"Gagal menyimpan ke Google Sheet: {e}")
        return False

# --- 3. LOGIKA PEMROSESAN RAW DATA ---
def process_raw_file(file):
    # Membaca file TXT mesin absen
    df = pd.read_csv(file, sep='\t', header=None, names=['ID','Timestamp','Mch','Cd','Nama','Status','X1','X2'])
    df['Nama'] = df['Nama'].str.strip()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    df['Tanggal'] = df['Timestamp'].dt.date
    
    # Logika Ambil Terakhir
    in_data = df[df['Status'] == 'I'].groupby(['Nama', 'Tanggal'])['Timestamp'].max().reset_index()
    out_data = df[df['Status'] == 'O'].groupby(['Nama', 'Tanggal'])['Timestamp'].max().reset_index()
    
    res = pd.merge(in_data, out_data, on=['Nama', 'Tanggal'], how='outer', suffixes=('_In', '_Out'))
    
    # Format untuk Database
    res['Jam_Masuk'] = res['Timestamp_In'].dt.strftime('%H:%M:%S').fillna("-")
    res['Jam_Pulang'] = res['Timestamp_Out'].dt.strftime('%H:%M:%S').fillna("-")
    
    # Status kelengkapan untuk analisis
    def cek_status(row):
        if row['Jam_Masuk'] != "-" and row['Jam_Pulang'] != "-": return "Lengkap"
        return "Tidak Lengkap"
    
    res['Status_Data'] = res.apply(cek_status, axis=1)
    
    # Bersihkan kolom untuk disimpan
    final_df = res[['Nama', 'Tanggal', 'Jam_Masuk', 'Jam_Pulang', 'Status_Data']]
    # Pastikan tanggal jadi string agar aman di Google Sheet
    final_df['Tanggal'] = final_df['Tanggal'].astype(str)
    
    return final_df

# --- 4. FUNGSI PDF (Tetap dipertahankan) ---
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

    # Header
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

    # Isi
    pegawai = sorted(df_source['Nama'].unique())
    for idx, nama in enumerate(pegawai, 1):
        h, a, tl = 0, 0, 0
        pdf.set_font("Arial", '', 6)
        pdf.cell(col_no, 10, str(idx), 1, 0, 'C')
        pdf.cell(col_nama, 10, nama[:18], 1, 0, 'L')
        
        for d in range(1, num_days+1):
            curr = f"{year}-{month:02d}-{d:02d}"
            # Filter data dari DataFrame Google Sheet
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

# --- 5. UI UTAMA ---
st.markdown("<h2 style='text-align: center;'>Sistem Absensi Online Terintegrasi</h2>", unsafe_allow_html=True)

# Menu Tabs
tab1, tab2, tab3 = st.tabs(["🏠 Dashboard & Analisis", "📤 Upload Data Baru", "📄 Laporan PDF"])

# Load Data Global dari Google Sheets
df_global = get_data_from_sheet()

with tab1:
    if not df_global.empty:
        # KPI Cards
        col1, col2, col3 = st.columns(3)
        total_p = df_global['Nama'].nunique()
        lengkap = len(df_global[df_global['Status_Data'] == 'Lengkap'])
        tl = len(df_global[df_global['Status_Data'] == 'Tidak Lengkap'])
        
        col1.metric("Total Pegawai", total_p)
        col2.metric("Total Kehadiran Lengkap", lengkap)
        col3.metric("Data Tidak Lengkap", tl)
        
        st.markdown("---")
        
        # Grafik
        c1, c2 = st.columns(2)
        with c1:
            st.write("##### 📊 Performa Pegawai")
            # Grouping untuk grafik
            grafik_df = df_global.groupby(['Nama', 'Status_Data']).size().reset_index(name='Jumlah')
            fig = px.bar(grafik_df, x='Nama', y='Jumlah', color='Status_Data', 
                         color_discrete_map={'Lengkap':'#00CC96', 'Tidak Lengkap':'#EF553B'})
            st.plotly_chart(fig, use_container_width=True)
            
        with c2:
            st.write("##### 📝 Data Terakhir Masuk")
            st.dataframe(df_global.sort_values('Tanggal', ascending=False).head(10), use_container_width=True)
    else:
        st.info("Database Google Sheet masih kosong.")

with tab2:
    st.write("### Upload Data Mesin Absen (.txt)")
    st.info("Data yang diupload akan otomatis ditambahkan ke Google Sheet Database.")
    
    file = st.file_uploader("Pilih File", type=['txt'])
    if file:
        if st.button("Proses & Simpan ke Cloud"):
            with st.spinner("Memproses data..."):
                processed_df = process_raw_file(file)
                sukses = save_data_to_sheet(processed_df)
                if sukses:
                    st.success("✅ Data berhasil disimpan ke Google Sheets!")
                    st.rerun()

with tab3:
    st.write("### Download Laporan Bulanan")
    if not df_global.empty:
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            bulan = st.selectbox("Pilih Bulan", range(1, 13), index=datetime.now().month-1)
        with col_t2:
            tahun = st.number_input("Pilih Tahun", min_value=2024, max_value=2030, value=datetime.now().year)
            
        if st.button("Generate PDF"):
            # Filter data sesuai bulan tahun
            df_global['Tanggal'] = pd.to_datetime(df_global['Tanggal'])
            df_filter = df_global[
                (df_global['Tanggal'].dt.month == bulan) & 
                (df_global['Tanggal'].dt.year == tahun)
            ]
            
            # Kembalikan tanggal ke string untuk PDF
            df_filter['Tanggal'] = df_filter['Tanggal'].dt.strftime('%Y-%m-%d')
            
            if not df_filter.empty:
                pdf_data = generate_pdf(df_filter, tahun, bulan)
                st.download_button("📥 Download PDF", data=pdf_data, file_name=f"Laporan_{bulan}_{tahun}.pdf", mime="application/pdf")
            else:
                st.warning("Tidak ada data pada periode tersebut.")