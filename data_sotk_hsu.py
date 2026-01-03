import pandas as pd
import numpy as np
import streamlit as st

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Dashboard SOTK HSU",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS untuk Tampilan Modern & Dark Mode Friendly
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
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR ---
with st.sidebar:
    st.header("📂 Panel Kontrol")
    file_sotk = st.file_uploader("Upload File SOTK (.xlsx)", type=['xlsx', 'xls'])
    st.divider()
    st.caption("Developed by Rezal Dewantara")

# --- 3. LOGIKA UTAMA ---
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

    # --- ALGORITMA BARU: REKONSTRUKSI HIERARKI (PARENT-CHILD TRACING) ---
    with st.spinner('Sedang merekonstruksi struktur organisasi...'):
        
        # 1. Pre-processing standar
        if 'TOTAL KEBUTUHAN' in df.columns:
            df['TOTAL KEBUTUHAN'] = pd.to_numeric(df['TOTAL KEBUTUHAN'], errors='coerce').fillna(0)

        # Bersihkan string nama
        df['NAMA UNOR'] = df['NAMA UNOR'].astype(str).str.lstrip('-')
        
        # 2. Buat Dictionary untuk Lookup Cepat (Sangat Cepat & Efisien)
        #    Map: ID -> DIATASAN ID (Untuk mencari bapaknya siapa)
        parent_map = df.set_index('ID')['DIATASAN ID'].to_dict()
        #    Map: ID -> NAMA UNOR (Untuk memberi nama nanti)
        name_map = df.set_index('ID')['NAMA UNOR'].to_dict()

        # 3. Fungsi Penelusuran Jalur (Path Finding)
        #    Fungsi ini melacak dari Unit terbawah naik ke atas sampai mentok (Root)
        def get_lineage(node_id):
            path = []
            curr = node_id
            
            # Loop naik ke atas (maksimal kedalaman 10 untuk mencegah infinite loop)
            for _ in range(10):
                if pd.isna(curr) or curr not in name_map:
                    break
                
                path.append(curr) # Simpan ID saat ini
                
                # Cari ID Bapaknya
                parent = parent_map.get(curr)
                
                # Jika Bapaknya kosong atau sama dengan diri sendiri (root), berhenti
                if pd.isna(parent) or parent == curr:
                    break
                curr = parent
            
            # Karena urutannya [Anak, Bapak, Kakek], kita balik jadi [Kakek, Bapak, Anak]
            return path[::-1]

        # 4. Terapkan ke semua baris
        #    Hasilnya adalah list ID hierarki [Level 1 ID, Level 2 ID, dst]
        df['hierarchy_path'] = df['ID'].apply(get_lineage)

        # 5. Pecah List menjadi Kolom Level 1 - Level 6
        hierarchy_df = pd.DataFrame(df['hierarchy_path'].tolist(), index=df.index)
        #    Ambil maksimal 6 kolom
        hierarchy_df = hierarchy_df.iloc[:, :6]
        #    Beri nama kolom
        hierarchy_df.columns = [f'Level {i+1}' for i in range(hierarchy_df.shape[1])]
        
        #    Gabungkan kembali ke DF utama
        df = pd.concat([df, hierarchy_df], axis=1)

        # 6. Ubah ID menjadi Nama Unor (Mapping)
        level_cols = [c for c in df.columns if c.startswith('Level ')]
        for col in level_cols:
            # Map ID ke Nama, jika NaN isi dengan strip
            df[col] = df[col].map(name_map).fillna('-')

    # --- PEMBERSIHAN DATA LANJUTAN ---
    # Tambah kolom Nama Atasan Langsung untuk info tambahan
    df['NAMA ATASAN'] = df['DIATASAN ID'].map(name_map).fillna('-')
    
    # Hapus kolom teknis yang tidak perlu ditampilkan
    drop_cols = ['DIATASAN ID', 'ROOT ID', 'ROW LEVEL', 'URUTAN', 'AKTIF', 'CORDER', 'INDUK UNOR ID', 'hierarchy_path']
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # --- 4. DASHBOARD UI (Sama seperti sebelumnya) ---
    
    # Global Stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Jabatan/Unit", f"{len(df):,}")
    c2.metric("Total Kebutuhan (Kab)", f"{int(df['TOTAL KEBUTUHAN'].sum()):,}")
    if 'Level 2' in df.columns:
        c3.metric("Jumlah SKPD", f"{df['Level 2'].nunique()}")
    else:
        c3.metric("Status", "Data Hierarki Kosong")

    st.markdown("---")

    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🏢 Struktur SKPD", "🔍 Cari ID", "🔎 Cari Nama", "✅ Validasi"])

    # === TAB 1: SKPD ===
    with tab1:
        if 'Level 2' in df.columns:
            # Dropdown Level 2 (Dinas)
            unique_skpd = df['Level 2'].unique()
            # Hapus yang kosong/-
            unique_skpd = [x for x in unique_skpd if x != '-']
            unique_skpd.sort()
            
            col_filter, col_view = st.columns([1, 3])
            
            with col_filter:
                pilihdinas = st.selectbox("Pilih Unit Organisasi (Level 2)", unique_skpd)
            
            with col_view:
                if pilihdinas:
                    # Filter Data
                    filtered_df = df[df['Level 2'] == pilihdinas].copy()
                    
                    # Info Metrics
                    m1, m2 = st.columns(2)
                    m1.metric(f"Kebutuhan {pilihdinas}", f"{int(filtered_df['TOTAL KEBUTUHAN'].sum())}")
                    if 'Level 3' in filtered_df.columns:
                        m2.metric("Jumlah Bidang", f"{filtered_df['Level 3'].nunique()}")

                    # Tabel Agregasi
                    agg_cols = [c for c in ['Level 3', 'Level 4', 'Level 5', 'Level 6'] if c in filtered_df.columns]
                    if agg_cols:
                        view_df = filtered_df.groupby(agg_cols)['TOTAL KEBUTUHAN'].sum().reset_index()
                        st.dataframe(view_df, use_container_width=True, hide_index=True)
                        
                        # Drill Down Bidang (Level 3)
                        if 'Level 3' in filtered_df.columns:
                            st.divider()
                            st.markdown("##### 📂 Detail per Bidang")
                            unique_bidang = filtered_df['Level 3'].unique()
                            unique_bidang = [x for x in unique_bidang if x != '-']
                            
                            pilihbidang = st.selectbox("Filter Bidang (Level 3)", unique_bidang, index=None)
                            if pilihbidang:
                                bidang_view = view_df[view_df['Level 3'] == pilihbidang]
                                st.dataframe(bidang_view, use_container_width=True)

    # === TAB 2: Cari ID ===
    with tab2:
        cari_id = st.text_input("Masukkan ID Unor")
        if cari_id:
            res = df[df['ID'] == cari_id]
            if not res.empty:
                st.success("ID Ditemukan")
                st.dataframe(res, use_container_width=True)
            else:
                st.warning("ID Tidak Ditemukan")

    # === TAB 3: Cari Nama ===
    with tab3:
        cari_nama = st.text_input("Cari Nama Jabatan")
        if cari_nama:
            res = df[df['NAMA UNOR'].str.contains(cari_nama, case=False, na=False)]
            if not res.empty:
                st.info(f"Ditemukan {len(res)} data")
                cols_show = ['NAMA UNOR'] + [c for c in df.columns if c.startswith('Level ')] + ['TOTAL KEBUTUHAN']
                st.dataframe(res[cols_show], use_container_width=True)
            else:
                st.warning("Tidak ditemukan")

    # === TAB 4: Validasi ===
    with tab4:
        st.write("Upload File Listing untuk membandingkan.")
        file_list = st.file_uploader("Upload File Listing (.xlsx)", key='list_up')
        
        if file_list and 'Level 2' in df.columns:
            try:
                df_list = pd.read_excel(file_list)
                # Ambil kolom level hasil olahan tadi
                cols_to_merge = ['ID', 'Level 2', 'Level 3']
                # Hanya ambil yg ada di df
                cols_to_merge = [c for c in cols_to_merge if c in df.columns]
                
                df_merge = pd.merge(df_list, df[cols_to_merge], on='ID', how='left')
                
                grp = df_merge.groupby('Level 2').size().reset_index(name='Jumlah')
                st.dataframe(grp, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error proses listing: {e}")

else:
    st.info("👋 Silakan upload file SOTK di panel sebelah kiri.")
