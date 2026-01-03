import pandas as pd
import numpy as np
import streamlit as st

# --- 1. KONFIGURASI HALAMAN (MODERN UI) ---
st.set_page_config(
    page_title="Dashboard SOTK HSU",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan lebih rapi
st.markdown("""
<style>
    .block-container {padding-top: 2rem;}
    div[data-testid="stMetric"] {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR (INPUT DATA) ---
with st.sidebar:
    st.header("📂 Panel Kontrol")
    st.write("Silakan upload file data utama SOTK untuk memulai analisis.")
    
    file_sotk = st.file_uploader("Upload File SOTK (.xlsx)", type=['xlsx', 'xls'])
    
    st.divider()
    st.caption("📊 **SOTK HSU Analytics**")
    st.caption("Developed by Rezal Dewantara")

# --- 3. MAIN APP LOGIC ---
st.title("📊 Dashboard Analisis SOTK")
st.subheader("Pemerintah Kabupaten Hulu Sungai Utara")
st.markdown("---")

if file_sotk is not None:
    # Load Data
    try:
        df = pd.read_excel(file_sotk)
    except Exception as e:
        st.error(f"Gagal membaca file: {e}")
        st.stop()

    # --- DATA PROCESSING (Logika Perbaikan Sebelumnya) ---
    if 'TOTAL KEBUTUHAN' in df.columns:
        df['TOTAL KEBUTUHAN'] = pd.to_numeric(df['TOTAL KEBUTUHAN'], errors='coerce').fillna(0)

    id_to_nama_unor = df.set_index('ID')['NAMA UNOR'].to_dict()
    df['NAMA ATASAN'] = df['DIATASAN ID'].map(id_to_nama_unor)

    df['NAMA UNOR'] = df['NAMA UNOR'].str.lstrip('-')
    df['NAMA ATASAN'] = df['NAMA ATASAN'].astype(str).str.lstrip('-')

    # Reorder Columns
    cols = df.columns.tolist()
    try:
        diatasan_id_index = cols.index('DIATASAN ID')
        nama_atasan_index = cols.index('NAMA ATASAN')
        if 'NAMA ATASAN' in cols:
            cols.pop(nama_atasan_index)
        cols.insert(diatasan_id_index + 1, 'NAMA ATASAN')
        df = df[cols]
    except ValueError as e:
        st.error(f"⚠️ Struktur kolom tidak sesuai: {e}")

    # Logic Split CORDER
    def split_corder_by_width(corder):
        if not isinstance(corder, str):
            return [None] * 6 
        codes = []
        start = 0
        while start < len(corder):
            end = min(start + 37, len(corder))
            codes.append(corder[start:end])
            start += 37
        if len(codes) > 1 and len(codes[-1]) < 36:
            last_code = codes.pop()
            codes[-1] += last_code
        while len(codes) < 6:
            codes.append(None)
        return codes[:6]

    df[['code_1', 'code_2', 'code_3', 'code_4', 'code_5', 'code_6']] = df['CORDER'].apply(split_corder_by_width).tolist()

    # Clean Codes
    code_cols = ['code_1', 'code_2', 'code_3', 'code_4', 'code_5', 'code_6']
    for col in code_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str[4:].str.rstrip('-').map(id_to_nama_unor).astype(str).str.lstrip('-')
        else:
            st.warning(f"Kolom bantu {col} tidak ditemukan saat pemrosesan.")

    # Final Cleanup
    drop_cols = ['DIATASAN ID', 'ROOT ID','ROW LEVEL','URUTAN','AKTIF','CORDER','INDUK UNOR ID']
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    rename_dict = {f'code_{i}': f'Level {i}' for i in range(1, 7)}
    df = df.rename(columns=rename_dict)
    df = df.replace([np.nan, 'nan'], '-')

    # --- 4. DASHBOARD HEADER (GLOBAL STATS) ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Data Unor", f"{len(df):,}")
    with col2:
        total_keb_kab = df['TOTAL KEBUTUHAN'].sum()
        st.metric("Total Kebutuhan Pegawai (Kab)", f"{int(total_keb_kab):,}")
    with col3:
        jumlah_skpd = df['Level 2'].nunique()
        st.metric("Jumlah SKPD", f"{jumlah_skpd}")

    st.markdown("---")

    # --- 5. TABS NAVIGATION ---
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏢 Dashboard SKPD", 
        "🔍 Cari ID", 
        "🔎 Cari Nama", 
        "✅ Validasi Listing"
    ])

    # === TAB 1: SOTK PER SKPD ===
    with tab1:
        level2_group = df.groupby('Level 2').size().reset_index(name='Count')
        
        # Layout: Filter di kiri (kecil), Hasil di kanan (besar)
        col_filter, col_view = st.columns([1, 3])
        
        with col_filter:
            st.markdown("### ⚙️ Filter")
            pilihdinas = st.selectbox(
                "Pilih Unit Organisasi (Level 2)",
                level2_group['Level 2'],
                index=None,
                placeholder="Pilih Dinas/Badan...",
            )

        with col_view:
            if pilihdinas:
                filtered_df = df[df['Level 2'] == pilihdinas]
                
                if not filtered_df.empty:
                    # Metrics Lokal SKPD
                    tot_keb_dinas = filtered_df['TOTAL KEBUTUHAN'].sum()
                    tot_bidang = filtered_df['Level 3'].nunique()
                    
                    m1, m2 = st.columns(2)
                    m1.metric(f"Kebutuhan {pilihdinas}", f"{int(tot_keb_dinas)}")
                    m2.metric("Jumlah Bidang/Bagian", f"{tot_bidang}")
                    
                    st.markdown("##### 📋 Detail Struktur")
                    dinas_df = filtered_df.copy()
                    
                    # Agregasi Level
                    agg_cols = ['Level 3', 'Level 4', 'Level 5', 'Level 6']
                    view_df = dinas_df.groupby(agg_cols)['TOTAL KEBUTUHAN'].sum().reset_index()
                    st.dataframe(view_df, use_container_width=True, hide_index=True)

                    st.divider()
                    
                    # Drill Down ke Bidang
                    st.markdown("##### 📂 Drill Down: Per Bidang")
                    grupbid = dinas_df.groupby('Level 3').size().reset_index(name='Count')
                    
                    pilihbidangsotk = st.selectbox(
                        "Filter Bidang (Level 3)",
                        grupbid['Level 3'],
                        index=None,
                        placeholder="Pilih Bidang..."
                    )
                    
                    if pilihbidangsotk:
                        bidang_df = view_df[view_df['Level 3'] == pilihbidangsotk]
                        tot_keb_bid = bidang_df['TOTAL KEBUTUHAN'].sum()
                        
                        st.info(f"Total Kebutuhan **{pilihbidangsotk}**: **{tot_keb_bid}**")
                        st.dataframe(bidang_df, use_container_width=True)
                else:
                    st.warning("Data tidak ditemukan untuk pilihan ini.")
            else:
                st.info("👈 Silakan pilih Dinas di panel sebelah kiri.")

    # === TAB 2: CARI ID ===
    with tab2:
        col_search, col_res = st.columns([1, 2])
        with col_search:
            cari_id = st.text_input("Masukkan ID Unor", placeholder="Contoh: 12345")
        
        with col_res:
            if cari_id:
                result_row = df[df['ID'] == cari_id]
                if not result_row.empty:
                    st.success(f"ID {cari_id} Ditemukan!")
                    level_cols_data = result_row[[f'Level {i}' for i in range(1, 7) if f'Level {i}' in result_row.columns]]
                    level_values = level_cols_data.iloc[0].astype(str).replace('nan', '').tolist()
                    filtered_levels = [level for level in level_values if level]
                    
                    if filtered_levels:
                        st.markdown("**Jalur Hierarki (Breadcrumbs):**")
                        st.code(" > ".join(filtered_levels), language="text")
                    
                    with st.expander("Lihat Data Lengkap Baris Ini"):
                        st.dataframe(result_row, use_container_width=True)
                else:
                    st.error("❌ ID Tidak Ditemukan dalam database.")

    # === TAB 3: CARI NAMA ===
    with tab3:
        cari_nama = st.text_input("Cari Nama Jabatan / Unit Kerja", placeholder="Ketik kata kunci (misal: Keuangan)...")
        
        if cari_nama:
            df['NAMA UNOR'] = df['NAMA UNOR'].astype(str)
            filtered_rows = df[df['NAMA UNOR'].str.contains(cari_nama, case=False, na=False)].copy()
            
            if not filtered_rows.empty:
                st.markdown(f"Ditemukan **{len(filtered_rows)}** data mengandung kata: *'{cari_nama}'*")
                
                total_kebutuhan_sum = filtered_rows['TOTAL KEBUTUHAN'].sum()
                st.metric(f"Total Kebutuhan (Hasil Pencarian)", f"{int(total_kebutuhan_sum)}")
                
                show_cols = ['NAMA UNOR', 'Level 2', 'Level 3', 'TOTAL KEBUTUHAN']
                st.dataframe(filtered_rows[show_cols], use_container_width=True)
            else:
                st.warning(f"Tidak ada data yang cocok dengan '{cari_nama}'.")

    # === TAB 4: LISTING VALIDASI ===
    with tab4:
        st.markdown("### 🔄 Validasi Data Listing")
        st.write("Bandingkan data SOTK utama dengan File Listing (Excel).")
        
        file_list = st.file_uploader("Upload File Listing", type=['xlsx', 'xls'], key="uploader_listing")
        
        if file_list is not None:
            try:
                df1 = pd.read_excel(file_list)
                
                # Merge Logic
                level_cols = ['ID','Level 2', 'Level 3', 'Level 4']
                available_level_cols = [col for col in level_cols if col in df.columns]
                df_levels = df[available_level_cols]
                
                df1 = pd.merge(df1, df_levels, on='ID', how='left')
                
                grouped_df1 = df1.groupby('Level 2')
                level2_counts = grouped_df1.size().reset_index(name='Count')
                
                c1, c2 = st.columns([1, 1])
                with c1:
                    st.caption("Rekapitulasi per SKPD (Listing):")
                    st.dataframe(level2_counts, use_container_width=True, height=300)
                
                with c2:
                    st.markdown("#### Detail SKPD")
                    pilihlistdinas = st.selectbox(
                        "Filter List Dinas",
                        level2_counts['Level 2'],
                        placeholder="Pilih Dinas..."
                    )
                    
                    if pilihlistdinas:
                        filterdinaslisting = df1[df1['Level 2'] == pilihlistdinas].copy()
                        
                        gruplv3 = filterdinaslisting.groupby('Level 3').size().reset_index(name='Count')
                        
                        pilihbidang = st.selectbox(
                            "Filter Bidang (Listing)",
                            gruplv3['Level 3'],
                            index=None,
                            placeholder="Semua Bidang"
                        )
                        
                        if pilihbidang:
                            final_view = filterdinaslisting[filterdinaslisting['Level 3'] == pilihbidang]
                        else:
                            final_view = filterdinaslisting
                            
                        st.dataframe(final_view, use_container_width=True)
            except Exception as e:
                st.error(f"Terjadi kesalahan saat memproses file listing: {e}")

else:
    # Tampilan awal jika belum upload file
    st.info("👋 **Selamat Datang!** Silakan upload file data SOTK di panel sebelah kiri untuk memulai.")
    st.markdown("""
    **Panduan Singkat:**
    1. Siapkan file Excel SOTK Anda.
    2. Upload melalui panel sidebar di sebelah kiri.
    3. Gunakan tab **Dashboard SKPD** untuk melihat struktur organisasi.
    4. Gunakan tab **Cari** untuk menelusuri jabatan spesifik.
    """)
