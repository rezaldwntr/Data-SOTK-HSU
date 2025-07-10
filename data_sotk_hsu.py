import pandas as pd
import numpy as np
import streamlit as st

file_sotk = st.file_uploader("Pilih File SOTK")
if file_sotk is not None:
    file_path = file_sotk
    df = pd.read_excel(file_path)

    id_to_nama_unor = df.set_index('ID')['NAMA UNOR'].to_dict()
    df['NAMA ATASAN'] = df['DIATASAN ID'].map(id_to_nama_unor)

    df['NAMA UNOR'] = df['NAMA UNOR'].str.lstrip('-')
    df['NAMA ATASAN'] = df['NAMA ATASAN'].astype(str).str.lstrip('-')


    cols = df.columns.tolist()

    try:
        diatasan_id_index = cols.index('DIATASAN ID')
        nama_atasan_index = cols.index('NAMA ATASAN')

        if 'NAMA ATASAN' in cols:
            cols.pop(nama_atasan_index)

        cols.insert(diatasan_id_index + 1, 'NAMA ATASAN')

        df = df[cols]

    except ValueError as e:
        print(f"Kolom Tidak Ditemukan: {e}")


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

    for col in ['code_1', 'code_2', 'code_3', 'code_4', 'code_5', 'code_6']:
        if col in df.columns:
            df[col] = df[col].astype(str).str[4:]
        else:
            print(f"Kolom {col} Tidak Ditemukan.")

    for col in ['code_1', 'code_2', 'code_3', 'code_4', 'code_5', 'code_6']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.rstrip('-')
        else:
            print(f"Kolom {col} Tidak Ditemukan.")

    for col in ['code_1', 'code_2', 'code_3', 'code_4', 'code_5', 'code_6']:
        if col in df.columns:
            df[col] = df[col].map(id_to_nama_unor)
            df[col] = df[col].astype(str).str.lstrip('-')
        else:
            print(f"Kolom {col} Tidak Ditemukan.")


    df = df.drop(columns=['DIATASAN ID', 'ROOT ID','ROW LEVEL','URUTAN','AKTIF','CORDER','INDUK UNOR ID'])

    rename_dict = {f'code_{i}': f'Level {i}' for i in range(1, 7)}
    df = df.rename(columns=rename_dict)
    df = df.replace([np.nan, 'nan'], '-')

    # st.dataframe(df)

    level2_group = df.groupby('Level 2').size().reset_index(name='Count')
    
    tab1, tab2, tab3, tab4 = st.tabs(["SOTK Per SKPD", "Cari Dengan ID", "Cari Dengan Nama", "Listing Validasi"])
    with tab1:
        pilihdinas = st.selectbox(
            "Pilih Dinas",
            level2_group['Level 2'],
            index=None,
            placeholder="Pilih Dinas",
            accept_new_options=True)
        if pilihdinas is not None:
            filtered_df = df[df['Level 2'] == pilihdinas]
            if filtered_df is not None:
                df['TOTAL KEBUTUHAN'] = pd.to_numeric(filtered_df['TOTAL KEBUTUHAN'], errors='coerce')

                # total_kebutuhan_by_level2 = df.groupby('Level 2')['TOTAL KEBUTUHAN'].sum().reset_index()

                total_kebutuhan_dinas = df['TOTAL KEBUTUHAN'].sum()
                st.caption(f"Total Kebutuhan untuk {pilihdinas} : {total_kebutuhan_dinas}")

                dinas_df = df[df['Level 2'] == pilihdinas].copy()

                total_kebutuhan_dinas_by_all_levels = dinas_df.groupby(['Level 3', 'Level 4', 'Level 5', 'Level 6'])['TOTAL KEBUTUHAN'].sum().reset_index()
                st.dataframe(total_kebutuhan_dinas_by_all_levels)
                grupbid = dinas_df.groupby('Level 3').size().reset_index(name='Count')
                pilihbidangsotk = st.selectbox(
                    "Pilih Bidang",
                    grupbid['Level 3'],
                    index=None,
                    placeholder="Pilih Bidang",
                    accept_new_options=True
                )
                if pilihbidangsotk is not None:
                    bidang_df = total_kebutuhan_dinas_by_all_levels[total_kebutuhan_dinas_by_all_levels['Level 3'] == pilihbidangsotk].copy()
                    total_kebutuhan_bidang = bidang_df['TOTAL KEBUTUHAN'].sum()
                    st.caption(f"Total Kebutuhan Untuk {pilihbidangsotk} : {total_kebutuhan_bidang}")
                    st.dataframe(bidang_df)

    with tab2:
        def search_by_id_and_display_levels(df, search_id):
            result_row = df[df['ID'] == search_id]

            if not result_row.empty:
                level_cols_data = result_row[[f'Level {i}' for i in range(1, 7) if f'Level {i}' in result_row.columns]]

                level_values = level_cols_data.iloc[0].astype(str).replace('nan', '').tolist()
                filtered_levels = [level for level in level_values if level] # Remove empty strings

                if filtered_levels:
                    st.caption(f"Letak ID : {'|'.join(filtered_levels)}")
                    # print(f"Levels for ID {search_id}: {'|'.join(filtered_levels)}")
                else:
                    st.caption("Lokasi Tidak Ditemukan")
            else:
                st.caption("Lokasi Tidak Ditemukan")
        cari_id = st.text_input(
            "Cari dengan ID"
        )
        if cari_id:
            search_by_id_and_display_levels(df, cari_id)
    
    with tab3:
        def search_by_nama_unor_and_display(df, search_term):
            df['NAMA UNOR'] = df['NAMA UNOR'].astype(str)
            filtered_rows = df[df['NAMA UNOR'].str.contains(search_term, case=False, na=False)].copy() # Add .copy() to avoid SettingWithCopyWarning
            if not filtered_rows.empty:
                st.caption(f"Found {len(filtered_rows)} rows matching '{search_term}' in NAMA UNOR:")
                selected_columns = ['NAMA UNOR','Level 2', 'Level 3', 'Level 4', 'TOTAL KEBUTUHAN']
                st.dataframe(filtered_rows[selected_columns])
                total_kebutuhan_sum = filtered_rows['TOTAL KEBUTUHAN'].sum()
                st.caption(f"\nTotal Kebutuhan for '{search_term}': {total_kebutuhan_sum}")

            else:
                st.caption(f"No data found for NAMA UNOR containing '{search_term}'.")

        cari_nama = st.text_input(
            "Cari Nama Unor"
        )
        if cari_nama:
            search_by_nama_unor_and_display(df, cari_nama)       

    with tab4:
        file_list = st.file_uploader("Pilih File Listing")
        if file_list is not None:
            df1 = pd.read_excel(file_list)
            level_cols = ['ID','Level 2', 'Level 3', 'Level 4']
            df_levels = df[level_cols]
            df1 = pd.merge(df1, df_levels, on='ID', how='left')
            grouped_df1 = df1.groupby('Level 2')
            level2_counts = grouped_df1.size().reset_index(name='Count')
            st.caption("SKPD yang belum melakukan Kunci Validasi")
            st.dataframe(level2_counts)
            pilihlistdinas = st.selectbox(
                "Pilih List Dinas",
                level2_counts['Level 2'],
                index=None,
                placeholder="Pilih List Dinas",
                accept_new_options=True)
            if pilihlistdinas is not None:
                filterdinaslisting = df1[df1['Level 2'] == pilihlistdinas].copy()
                st.dataframe(filterdinaslisting)
                gruplv3 = filterdinaslisting.groupby('Level 3')
                lv3grup = gruplv3.size().reset_index(name='Count')
                pilihbidang = st.selectbox(
                    "Pilih List Bidang",
                    lv3grup['Level 3'],
                    index=None,
                    placeholder="Pilih List Bidang",
                    accept_new_options=True)
                if pilihbidang is not None:
                    filterbidangdinas = filterdinaslisting[filterdinaslisting['Level 3'] == pilihbidang].copy()
                    st.dataframe(filterbidangdinas)

else:
    st.header("Upload Dululah Filenya", divider=True)
