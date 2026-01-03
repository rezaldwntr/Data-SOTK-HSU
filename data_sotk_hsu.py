import pandas as pd
import numpy as np
import streamlit as st
import io

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard SOTK HSU",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Modern & Perbaikan Tampilan
st.markdown("""
<style>
    .block-container {padding-top: 2rem;}
    /* Kartu Metric Transparan */
    div[data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    div[data-testid="stMetricValue"] {
        color: inherit !important;
    }
    /* Tombol Download Full Width */
    div[data-testid="stDownloadButton"] button {
        width: 100%;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# --- 2. FUNGSI BANTUAN (DIPERBAIKI) ---
def tampilkan_dan_download(df_input, file_label, height=None):
    if df_input.empty:
        st.warning("Data kosong.")
        return

    df_show = df_input.copy()

    # Rename kolom agar lebih rapi di tampilan (Opsional)
    rename_map = {
        'NAMA UNOR': 'Nama Unit Kerja',
        'TOTAL KEBUTUHAN': 'Kebutuhan Pegawai',
        'NAMA ATASAN': 'Atasan Langsung',
        'Count': 'Jumlah Unit',
        'Jumlah': 'Jumlah'
    }
    df_show = df_show.rename(columns={k: v for k, v in rename_map.items() if k in df_show.columns})

    # Konfigurasi kolom (Agar angka muncul bulat tanpa koma)
    col_config = {}
    if 'Kebutuhan Pegawai' in df_show.columns:
        col_config['Kebutuhan Pegawai'] = st.column_config.NumberColumn(
            "Kebutuhan Pegawai", help="Total Kebutuhan", format="%.0f"
        )
    if 'Jumlah Unit' in df_show.columns:
        col_config['Jumlah Unit'] = st.column_config.NumberColumn(
            "Jumlah Unit", format="%.0f"
        )

    # Tampilkan Tabel
    st.dataframe(
        df_show,
        use_container_width=True,
        hide_index=True,
        column_config=col_config,
        height=height
    )

    # Tombol Download
    # FIX: Menggunakan label sebagai key agar stabil (bukan random)
    safe_label = str(file_label).replace(" ", "_").replace(".", "")
    safe_key = f"btn_down_{safe_label}"
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_show.to_excel(writer, index=False, sheet_name='Data')
    
    st.download_button(
        label=f"📥 Download Excel ({file_label})",
        data=buffer.getvalue(),
        file_name=f"{safe_label}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=safe_key
    )

# --- 3. LOGIKA UTAMA ---
st.sidebar.header("📂 Panel Kontrol")
file_sotk = st.sidebar.file_uploader("Upload File SOTK (.xlsx)", type=['xlsx', 'xls'])
st.sidebar.caption("Developed by Rezal Dewantara")

st.title("📊 Dashboard Analisis SOTK")
st.subheader("Pemerintah Kabupaten Hulu Sungai Utara")
st.markdown("---")

if file_sotk is not None:
    # 1. LOAD DATA
    try:
        # Default baca Excel (sesuai request Anda)
        df = pd.read_excel(file_sotk)
    except Exception as e:
        st.error(f"Gagal membaca file Excel. Pastikan format benar. Error: {e}")
        st.stop()

    # 2. PROSES DATA (Rekonstruksi Hierarki)
    with st.spinner('Sedang memproses struktur organisasi...'):
        # Normalisasi Nama Kolom (Huruf Besar semua)
        df.columns = [str(c).strip().upper() for c in df.columns]

        # Validasi Kolom Wajib
        if 'ID' not in df.columns or 'NAMA UNOR' not in df.columns:
            st.error("File Excel harus memiliki kolom 'ID' dan 'NAMA UNOR'.")
            st.stop()

        # Konversi Tipe Data (Penting untuk mapping)
        if 'TOTAL KEBUTUHAN' in df.columns:
            df['TOTAL KEBUTUHAN'] = pd.to_numeric(df['TOTAL KEBUTUHAN'], errors='coerce').fillna(0)
        
        # Pastikan ID jadi String (biar '001' tidak jadi 1)
        df['ID'] = df['ID'].astype(str).str.strip()
        df['NAMA UNOR'] = df['NAMA UNOR'].astype(str).str.lstrip('-')
        
        if 'DIATASAN ID' in df.columns:
            df['DIATASAN ID'] = df['DIATASAN ID'].astype(str).str.strip().replace(['nan', 'None', '', 'NaN'], np.nan)

        # Buat Dictionary Mapping
        parent_map = df.set_index('ID')['DIATASAN ID'].to_dict()
        name_map = df.set_index('ID')['NAMA UNOR'].to_dict()

        # Fungsi Cari Jalur (Kakek -> Bapak -> Anak)
        def get_lineage(node_id):
            path = []
            curr = node_id
            for _ in range(10):  # Batas kedalaman 10 level
                if pd.isna(curr) or curr not in name_map:
                    break
                path.append(curr)
                parent = parent_map.get(curr)
                # Berhenti jika tidak punya atasan atau atasan adalah diri sendiri
                if pd.isna(parent) or parent == curr:
                    break
                curr = parent
            return path[::-1] # Balik urutan

        # Terapkan ke seluruh data
        df['hierarchy_path'] = df['ID'].apply(get_lineage)

        # Pecah List menjadi Kolom Level
        hierarchy_df = pd.DataFrame(df['hierarchy_path'].tolist(), index=df.index)
        hierarchy_df = hierarchy_df.iloc[:, :6] # Ambil max 6 level
        hierarchy_df.columns = [f'Level {i+1}' for i in range(hierarchy_df.shape[1])]
        
        df = pd.concat([df, hierarchy_df], axis=1)

        # Ubah ID di kolom Level menjadi Nama
        level_cols = [c for c in df.columns if c.startswith('Level ')]
        for col in level_cols:
            df[col] = df[col].map(name_map).fillna('-')

    # Kolom Tambahan: Nama Atasan
    if 'DIATASAN ID' in df.columns:
        df['NAMA ATASAN'] = df['DIATASAN ID'].map(name_map).fillna('-')
    
    # Bersihkan Kolom Teknis
    drop_cols = ['DIATASAN ID', 'ROOT ID', 'ROW LEVEL', 'URUTAN', 'AKTIF', 'CORDER', 'INDUK UNOR ID', 'hierarchy_path']
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # 3. DASHBOARD METRICS
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Jabatan/Unit", f"{len(df):,}")
    c2.metric("Total Kebutuhan", f"{int(df['TOTAL KEBUTUHAN'].sum()):,}")
    if 'Level 2' in df.columns:
        c3.metric("Jumlah SKPD", f"{df['Level 2'].nunique()}")
    else:
        c3.metric("Status", "Data Hierarki Kosong")

    st.markdown("---")

    # 4. TAB NAVIGASI
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏢 Struktur SKPD", 
        "📂 Data Master", 
        "🔍 Cari ID", 
        "🔎 Cari Nama", 
        "✅ Validasi Listing"
    ])

    # === TAB 1: STRUKTUR SKPD ===
    with tab1:
        if 'Level 2' in df.columns:
            unique_skpd = sorted([x for x in df['Level 2'].unique() if x != '-'])
            
            col_filter, col_view = st.columns([1, 3])
            
            with col_filter:
                pilihdinas = st.selectbox("Pilih Unit Organisasi (Level 2)", unique_skpd)
            
            with col_view:
                if pilihdinas:
                    filtered_df = df[df['Level 2'] == pilihdinas].copy()
                    
                    # Metrics Lokal
                    m1, m2 = st.columns(2)
                    m1.metric(f"Kebutuhan {pilihdinas}", f"{int(filtered_df['TOTAL KEBUTUHAN'].sum())}")
                    if 'Level 3' in filtered_df.columns:
                        m2.metric("Jumlah Bidang/Bagian", f"{filtered_df['Level 3'].nunique()}")

                    # Tabel Rekap
                    agg_cols = [c for c in ['Level 3', 'Level 4', 'Level 5', 'Level 6'] if c in filtered_df.columns]
                    if agg_cols:
                        st.markdown("##### 📋 Rekapitulasi Struktur")
                        view_df = filtered_df.groupby(agg_cols)['TOTAL KEBUTUHAN'].sum().reset_index()
                        tampilkan_dan_download(view_df, f"Rekap_{pilihdinas}")
                        
                        # Drill Down Bidang
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

    # === TAB 2: DATA MASTER ===
    with tab2:
        st.markdown("### 📂 Data Master Keseluruhan")
        filter_nama = st.text_input("Cari nama unit kerja (filter):", key="filter_master")
        
        df_display = df.copy()
        if filter_nama:
            df_display = df_display[df_display['NAMA UNOR'].str.contains(filter_nama, case=False, na=False)]
        
        st.caption(f"Menampilkan {len(df_display)} baris data.")
        tampilkan_dan_download(df_display, "Master_Data_SOTK")

    # === TAB 3: CARI ID ===
    with tab3:
        cari_id = st.text_input("Masukkan ID Unor:")
        if cari_id:
            res = df[df['ID'] == cari_id]
            if not res.empty:
                st.success("ID Ditemukan")
                tampilkan_dan_download(res, f"Search_ID_{cari_id}")
            else:
                st.warning("ID Tidak Ditemukan")

    # === TAB 4: CARI NAMA ===
    with tab4:
        cari_nama_tab = st.text_input("Cari Nama Jabatan / Unit:")
        if cari_nama_tab:
            res = df[df['NAMA UNOR'].str.contains(cari_nama_tab, case=False, na=False)]
            if not res.empty:
                st.info(f"Ditemukan {len(res)} data")
                # Pilih kolom relevan saja
                cols_show = ['NAMA UNOR'] + [c for c in df.columns if c.startswith('Level ')] + ['TOTAL KEBUTUHAN']
                cols_show = [c for c in cols_show if c in res.columns] # Safety check
                tampilkan_dan_download(res[cols_show], f"Search_Nama_{cari_nama_tab}")
            else:
                st.warning("Tidak ditemukan")

    # === TAB 5: VALIDASI ===
    with tab5:
        st.write("Upload File Listing (.xlsx)")
        file_list = st.file_uploader("Upload File Listing", type=['xlsx', 'xls'], key='list_up')
        
        if file_list and 'Level 2' in df.columns:
            try:
                df_list = pd.read_excel(file_list)
                # Normalisasi ID Listing
                if 'ID' in df_list.columns:
                    df_list['ID'] = df_list['ID'].astype(str).str.strip()
                
                cols_to_merge = ['ID', 'Level 2', 'Level 3']
                cols_to_merge = [c for c in cols_to_merge if c in df.columns]
                
                df_merge = pd.merge(df_list, df[cols_to_merge], on='ID', how='left')
                
                grp = df_merge.groupby('Level 2').size().reset_index(name='Jumlah')
                tampilkan_dan_download(grp, "Hasil_Validasi_Listing")
                
            except Exception as e:
                st.error(f"Error proses listing: {e}")

else:
    st.info("👋 Silakan upload file SOTK (.xlsx) di panel sebelah kiri untuk memulai.")
