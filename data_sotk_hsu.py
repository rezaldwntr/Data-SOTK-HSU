import pandas as pd
import numpy as np
import streamlit as st
import io
import re
import uuid
import plotly.express as px

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard SOTK HSU",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.linkedin.com/in/rezaldwntr/',
        'Report a bug': "https://github.com/rezaldwntr/data-sotk-hsu/issues",
        'About': """
        ### Dashboard Analisis SOTK HSU v3.2
        Aplikasi ini dikembangkan untuk membantu analisis struktur organisasi
        Pemerintah Kabupaten Hulu Sungai Utara.
        
        **Fitur Baru:**
        - Klasifikasi Jabatan Spesifik (Eselon II, III, IV, Fungsional, Pelaksana)
        - Layout Grafik Vertikal
        
        Developed by **Rezal Dewantara**
        """
    }
)

# CSS Modern
st.markdown("""
<style>
    .block-container {padding-top: 2rem;}
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    div[data-testid="stMetricValue"] {
        color: inherit !important;
    }
    div[data-testid="stDownloadButton"] button {
        width: 100%;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
    .warning-box {
        padding: 1rem;
        background-color: rgba(255, 255, 0, 0.1);
        border: 1px solid #ffcc00;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. FUNGSI BANTUAN ---
def sanitize_filename(name):
    """Membersihkan string agar aman dijadikan nama file."""
    return re.sub(r'[\\/*?:"<>|]', "_", str(name)).strip()

def tampilkan_dan_download(df_input, file_label, height=None):
    if df_input.empty:
        st.warning("Data kosong.")
        return

    df_show = df_input.copy()

    rename_map = {
        'NAMA UNOR': 'Nama Unit Kerja',
        'TOTAL KEBUTUHAN': 'Kebutuhan Pegawai',
        'NAMA ATASAN': 'Atasan Langsung',
        'Count': 'Jumlah Unit',
        'Jumlah': 'Jumlah'
    }
    df_show = df_show.rename(columns={k: v for k, v in rename_map.items() if k in df_show.columns})

    col_config = {}
    if 'Kebutuhan Pegawai' in df_show.columns:
        col_config['Kebutuhan Pegawai'] = st.column_config.NumberColumn("Kebutuhan Pegawai", format="%.0f")
    if 'Jumlah Unit' in df_show.columns:
        col_config['Jumlah Unit'] = st.column_config.NumberColumn("Jumlah Unit", format="%.0f")

    # Dynamic Height
    dataframe_args = {
        "use_container_width": True,
        "hide_index": True,
        "column_config": col_config
    }
    if height: 
        dataframe_args["height"] = height
    
    st.dataframe(df_show, **dataframe_args)

    try:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_show.to_excel(writer, index=False, sheet_name='Data')
        
        safe_label = sanitize_filename(file_label)
        unique_key = f"btn_{safe_label}_{uuid.uuid4()}"
        
        st.download_button(
            label=f"📥 Download Excel ({file_label})",
            data=buffer.getvalue(),
            file_name=f"{safe_label}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=unique_key
        )
    except Exception as e:
        st.error(f"Gagal membuat tombol download: {e}")

# --- 3. CACHING & DATA PROCESSING ---
@st.cache_data(show_spinner=False)
def process_sotk_data(df):
    # Standarisasi Header
    df.columns = [str(c).strip().upper() for c in df.columns]

    # Validasi Kolom
    if 'ID' not in df.columns or 'NAMA UNOR' not in df.columns:
        return None, "Kolom 'ID' dan 'NAMA UNOR' wajib ada."

    # Tipe Data
    df['ID'] = df['ID'].astype(str).str.strip()
    df['NAMA UNOR'] = df['NAMA UNOR'].astype(str).str.lstrip('-')
    
    if 'TOTAL KEBUTUHAN' in df.columns:
        df['TOTAL KEBUTUHAN'] = pd.to_numeric(df['TOTAL KEBUTUHAN'], errors='coerce').fillna(0)
    
    if 'DIATASAN ID' in df.columns:
        df['DIATASAN ID'] = df['DIATASAN ID'].astype(str).str.strip().replace(['nan', 'None', '', 'NaN'], np.nan)

    # Dictionary Mapping
    parent_map = df.set_index('ID')['DIATASAN ID'].to_dict()
    name_map = df.set_index('ID')['NAMA UNOR'].to_dict()

    # --- DETEKSI ORPHAN (DATA YATIM) ---
    orphans = df[df['DIATASAN ID'].notna() & ~df['DIATASAN ID'].isin(df['ID'])].copy()

    # Recursive Lineage Logic
    def get_lineage(node_id):
        path = []
        curr = node_id
        for _ in range(10):
            if pd.isna(curr) or curr not in name_map: break
            path.append(curr)
            parent = parent_map.get(curr)
            if pd.isna(parent) or parent == curr: break
            curr = parent
        return path[::-1]

    df['hierarchy_path'] = df['ID'].apply(get_lineage)

    hierarchy_df = pd.DataFrame(df['hierarchy_path'].tolist(), index=df.index)
    hierarchy_df = hierarchy_df.iloc[:, :6] 
    hierarchy_df.columns = [f'Level {i+1}' for i in range(hierarchy_df.shape[1])]
    
    df = pd.concat([df, hierarchy_df], axis=1)

    # Mapping Level Names
    level_cols = [c for c in df.columns if c.startswith('Level ')]
    for col in level_cols:
        df[col] = df[col].map(name_map).fillna('-')

    if 'DIATASAN ID' in df.columns:
        df['NAMA ATASAN'] = df['DIATASAN ID'].map(name_map).fillna('-')
    
    drop_cols = ['DIATASAN ID', 'ROOT ID', 'ROW LEVEL', 'URUTAN', 'AKTIF', 'CORDER', 'INDUK UNOR ID', 'hierarchy_path']
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    return df, orphans

# --- 4. LOGIKA UTAMA ---
st.sidebar.header("📂 Panel Kontrol")
file_sotk = st.sidebar.file_uploader("Upload File SOTK", type=['xlsx', 'xls', 'csv'])
st.sidebar.caption("Developed by Rezal Dewantara")

st.title("📊 Dashboard Analisis SOTK")
st.subheader("Pemerintah Kabupaten Hulu Sungai Utara")
st.markdown("---")

if file_sotk is not None:
    try:
        if file_sotk.name.endswith('.csv'):
            raw_df = pd.read_csv(file_sotk)
        else:
            raw_df = pd.read_excel(file_sotk)
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        st.stop()

    with st.spinner('Sedang memproses struktur organisasi...'):
        df, orphans = process_sotk_data(raw_df)
        
        if df is None:
            st.error(orphans)
            st.stop()

    if not orphans.empty:
        with st.sidebar:
            st.markdown("### ⚠️ Data Quality Alert")
            st.warning(f"Ditemukan **{len(orphans)}** unit kerja 'Yatim'.")
            with st.expander("Lihat Data Yatim"):
                st.dataframe(orphans[['ID', 'NAMA UNOR', 'DIATASAN ID']])

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Jabatan/Unit", f"{len(df):,}")
    c2.metric("Total Kebutuhan", f"{int(df['TOTAL KEBUTUHAN'].sum()):,}")
    if 'Level 2' in df.columns:
        c3.metric("Jumlah SKPD", f"{df['Level 2'].nunique()}")
    else:
        c3.metric("Status", "Data Hierarki Kosong")

    st.markdown("---")

    # --- TABS ---
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Visualisasi", 
        "🏢 Struktur SKPD", 
        "📂 Data Master", 
        "🔍 Cari ID", 
        "🔎 Cari Nama", 
        "✅ Validasi"
    ])

    # === TAB 1: VISUALISASI GRAFIK ===
    with tab1:
        st.markdown("### 📈 Visualisasi Data SOTK")
        
        # 1. Top 10 SKPD (Posisi Atas)
        st.markdown("#### 1. Top 10 SKPD dengan Kebutuhan Terbanyak")
        if 'Level 2' in df.columns:
            skpd_stats = df[df['Level 2'] != '-'].groupby('Level 2')['TOTAL KEBUTUHAN'].sum().reset_index()
            skpd_stats = skpd_stats.sort_values(by='TOTAL KEBUTUHAN', ascending=False).head(10)
            
            fig_bar = px.bar(
                skpd_stats,
                x='TOTAL KEBUTUHAN',
                y='Level 2',
                orientation='h',
                text_auto=True,
                color='TOTAL KEBUTUHAN',
                color_continuous_scale='Viridis',
                height=400
            )
            fig_bar.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()

        # 2. Distribusi Jabatan (Posisi Bawah, Vertikal)
        st.markdown("#### 2. Distribusi Jabatan")
        
        # Logic Klasifikasi Jabatan (Sesuai Permintaan)
        if 'ESELON' in df.columns and 'JENIS JABATAN' in df.columns:
            def klasifikasi_jabatan(row):
                eselon = str(row['ESELON']).strip().upper()
                jenis = str(row['JENIS JABATAN']).strip().upper()
                
                # Cek Struktural Berdasarkan Eselon
                if 'II' in eselon: # Mencakup II.a, II.b
                    return 'JABATAN PIMPINAN TINGGI PRATAMA (Eselon II)'
                elif 'III' in eselon: # Mencakup III.a, III.b
                    return 'JABATAN ADMINISTRATOR (Eselon III)'
                elif 'IV' in eselon: # Mencakup IV.a, IV.b
                    return 'JABATAN PENGAWAS (Eselon IV)'
                
                # Cek Fungsional dan Pelaksana Berdasarkan Jenis Jabatan
                if 'FUNGSIONAL' in jenis:
                    return 'JABATAN FUNGSIONAL'
                elif 'PELAKSANA' in jenis:
                    return 'JABATAN PELAKSANA'
                
                return None # Kategori 'Lainnya' akan dibuang (None)

            df_viz = df.copy()
            df_viz['KELOMPOK_JABATAN'] = df_viz.apply(klasifikasi_jabatan, axis=1)
            
            # Filter hanya kategori yang valid (Hapus 'None' / Lainnya)
            df_viz = df_viz.dropna(subset=['KELOMPOK_JABATAN'])
            
            # Hitung Jumlah
            jabatan_stats = df_viz.groupby('KELOMPOK_JABATAN').size().reset_index(name='Jumlah')
            
            # Urutan Kategori yang diinginkan
            urutan_custom = [
                'JABATAN PIMPINAN TINGGI PRATAMA (Eselon II)',
                'JABATAN ADMINISTRATOR (Eselon III)',
                'JABATAN PENGAWAS (Eselon IV)',
                'JABATAN FUNGSIONAL',
                'JABATAN PELAKSANA'
            ]
            
            # Terapkan urutan
            jabatan_stats['KELOMPOK_JABATAN'] = pd.Categorical(
                jabatan_stats['KELOMPOK_JABATAN'], 
                categories=urutan_custom, 
                ordered=True
            )
            jabatan_stats = jabatan_stats.sort_values('KELOMPOK_JABATAN')

            # Plot Chart
            if not jabatan_stats.empty:
                fig_jab = px.bar(
                    jabatan_stats,
                    x='Jumlah',
                    y='KELOMPOK_JABATAN',
                    orientation='h',
                    text_auto=True,
                    title="Jumlah Pegawai per Kelompok Jabatan",
                    color='KELOMPOK_JABATAN',
                    height=500
                )
                fig_jab.update_layout(
                    showlegend=False,
                    yaxis=dict(autorange="reversed") # Agar urutan dari atas (Eselon II) ke bawah
                )
                st.plotly_chart(fig_jab, use_container_width=True)
                
                with st.expander("Lihat Detail Data Distribusi Jabatan"):
                    tampilkan_dan_download(jabatan_stats, "Distribusi_Jabatan")
            else:
                st.warning("Tidak ada data jabatan yang sesuai dengan kriteria filter.")
        else:
            st.warning("Kolom 'ESELON' atau 'JENIS JABATAN' tidak ditemukan dalam file untuk membuat grafik distribusi.")

        st.divider()
        if 'Level 2' in df.columns and 'Level 3' in df.columns:
             st.markdown("#### 3. Peta Hierarki Organisasi (Sunburst)")
             df_chart = df[df['Level 2'] != '-'].copy()
             try:
                fig_sun = px.sunburst(
                    df_chart, 
                    path=['Level 2', 'Level 3', 'Level 4'], 
                    values='TOTAL KEBUTUHAN',
                    color='Level 2', 
                    height=700
                )
                st.plotly_chart(fig_sun, use_container_width=True)
             except Exception as e:
                st.warning("Data belum cukup dalam untuk Sunburst Chart.")

    # === TAB 2: SKPD ===
    with tab2:
        if 'Level 2' in df.columns:
            unique_skpd = sorted([x for x in df['Level 2'].unique() if x != '-'])
            
            col_filter, col_view = st.columns([1, 3])
            with col_filter:
                pilihdinas = st.selectbox("Pilih Unit Organisasi (Level 2)", unique_skpd)
            
            with col_view:
                if pilihdinas:
                    filtered_df = df[df['Level 2'] == pilihdinas].copy()
                    
                    m1, m2 = st.columns(2)
                    m1.metric(f"Kebutuhan {pilihdinas}", f"{int(filtered_df['TOTAL KEBUTUHAN'].sum())}")
                    if 'Level 3' in filtered_df.columns:
                        m2.metric("Jumlah Bidang/Bagian", f"{filtered_df['Level 3'].nunique()}")

                    agg_cols = [c for c in ['Level 3', 'Level 4', 'Level 5', 'Level 6'] if c in filtered_df.columns]
                    if agg_cols:
                        st.markdown("##### 📋 Rekapitulasi Struktur")
                        view_df = filtered_df.groupby(agg_cols)['TOTAL KEBUTUHAN'].sum().reset_index()
                        
                        tampilkan_dan_download(view_df, f"Rekap_{pilihdinas}")
                        
                        if 'Level 3' in filtered_df.columns:
                            st.divider()
                            st.markdown("##### 📂 Detail per Bidang")
                            unique_bidang = sorted([x for x in filtered_df['Level 3'].unique() if x != '-'])
                            
                            pilihbidang = st.selectbox("Filter Bidang (Level 3)", unique_bidang, index=None)
                            
                            if pilihbidang:
                                bidang_view = view_df[view_df['Level 3'] == pilihbidang]
                                tot_bid = bidang_view['TOTAL KEBUTUHAN'].sum()
                                st.metric(f"Total Kebutuhan: {pilihbidang}", int(tot_bid))
                                tampilkan_dan_download(bidang_view, f"Detail_{pilihbidang}")

    # === TAB 3: DATA MASTER ===
    with tab3:
        st.markdown("### 📂 Data Master Keseluruhan")
        filter_nama = st.text_input("Cari nama unit kerja:", key="filter_master")
        
        df_display = df.copy()
        if filter_nama:
            df_display = df_display[df_display['NAMA UNOR'].str.contains(filter_nama, case=False, na=False)]
        
        st.caption(f"Menampilkan {len(df_display)} baris data.")
        tampilkan_dan_download(df_display, "Master_Data_SOTK")

    # === TAB 4: CARI ID ===
    with tab4:
        cari_id = st.text_input("Masukkan ID Unor:")
        if cari_id:
            res = df[df['ID'] == cari_id]
            if not res.empty:
                st.success("ID Ditemukan")
                tampilkan_dan_download(res, f"Search_ID_{cari_id}")
            else:
                st.warning("ID Tidak Ditemukan")

    # === TAB 5: CARI NAMA ===
    with tab5:
        cari_nama_tab = st.text_input("Cari Nama Jabatan / Unit:")
        if cari_nama_tab:
            res = df[df['NAMA UNOR'].str.contains(cari_nama_tab, case=False, na=False)]
            if not res.empty:
                st.info(f"Ditemukan {len(res)} data")
                total_keb_cari = res['TOTAL KEBUTUHAN'].sum()
                st.metric("Total Kebutuhan (Hasil Pencarian)", int(total_keb_cari))
                
                cols_show = ['NAMA UNOR'] + [c for c in df.columns if c.startswith('Level ')] + ['TOTAL KEBUTUHAN']
                cols_show = [c for c in cols_show if c in res.columns]
                tampilkan_dan_download(res[cols_show], f"Search_Nama_{cari_nama_tab}")
            else:
                st.warning("Tidak ditemukan")

    # === TAB 6: VALIDASI ===
    with tab6:
        st.markdown("### 🔄 Validasi Data Listing")
        st.write("Upload File Listing untuk melihat rekapitulasi dan detail data per SKPD.")
        
        file_list = st.file_uploader("Upload File Listing", type=['xlsx', 'xls', 'csv'], key='list_up')
        
        if file_list and 'Level 2' in df.columns:
            try:
                try:
                    df_list = pd.read_excel(file_list)
                except:
                    file_list.seek(0)
                    df_list = pd.read_csv(file_list)

                df_list.columns = [str(c).strip().upper() for c in df_list.columns]
                if 'ID' in df_list.columns:
                    df_list['ID'] = df_list['ID'].astype(str).str.strip()
                
                cols_to_merge = ['ID', 'Level 2', 'Level 3']
                cols_to_merge = [c for c in cols_to_merge if c in df.columns]
                
                df_merge = pd.merge(df_list, df[cols_to_merge], on='ID', how='left')
                
                # 1. Tampilkan Rekap
                grp = df_merge.groupby('Level 2').size().reset_index(name='Jumlah')
                st.markdown("#### 📊 Rekapitulasi Jumlah Pegawai per SKPD (Listing)")
                
                if not grp.empty:
                    grp_sorted = grp.sort_values(by='Jumlah', ascending=True)
                    fig_val = px.bar(
                        grp_sorted,
                        x='Jumlah',
                        y='Level 2',
                        orientation='h',
                        title="Distribusi Data Listing per SKPD",
                        text_auto=True,
                        height=600 if len(grp) > 10 else 400
                    )
                    st.plotly_chart(fig_val, use_container_width=True)

                tampilkan_dan_download(grp, "Rekap_Validasi_Listing")
                
                st.divider()

                # 2. FITUR DETAIL
                st.markdown("#### 📂 Detail Data Listing per SKPD")
                
                list_dinas = sorted([x for x in df_merge['Level 2'].unique() if pd.notna(x) and str(x) != '-' and str(x) != 'nan'])
                pilih_dinas_val = st.selectbox("Pilih Unit Organisasi (Listing):", list_dinas, index=None)
                
                if pilih_dinas_val:
                    detail_val = df_merge[df_merge['Level 2'] == pilih_dinas_val].copy()
                    st.info(f"Menampilkan detail data untuk **{pilih_dinas_val}**")
                    tampilkan_dan_download(detail_val, f"Listing_{pilih_dinas_val}")
                    
                    if 'Level 3' in detail_val.columns:
                        list_bidang = sorted([x for x in detail_val['Level 3'].unique() if pd.notna(x) and str(x) != '-' and str(x) != 'nan'])
                        if list_bidang:
                            st.markdown("##### Filter Bidang (Opsional)")
                            pilih_bidang_val = st.selectbox("Pilih Bidang (Listing):", list_bidang, index=None)
                            if pilih_bidang_val:
                                detail_bidang_val = detail_val[detail_val['Level 3'] == pilih_bidang_val]
                                tampilkan_dan_download(detail_bidang_val, f"Listing_{pilih_bidang_val}")

            except Exception as e:
                st.error(f"Terjadi kesalahan pada file listing: {e}")

else:
    st.info("👋 Silakan upload file SOTK (.xlsx / .csv) di panel sebelah kiri untuk memulai.")
