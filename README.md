# Dashboard Analisis SOTK - Kabupaten Hulu Sungai Utara 📊

Aplikasi berbasis web untuk menganalisis, memvalidasi, dan memvisualisasikan data Susunan Organisasi dan Tata Kerja (SOTK) Pemerintah Kabupaten Hulu Sungai Utara. Dibangun menggunakan Python dan Streamlit.

## 🚀 Fitur Utama (Versi 3.0)

* **Rekonstruksi Hierarki Otomatis:** Mengubah data *flat* (Excel/CSV) menjadi struktur hierarki Level 1 - Level 6 berdasarkan relasi *Parent-Child* (ID Atasan).
* **Visualisasi Interaktif (Baru):**
    * **Sunburst Chart:** Melihat peta organisasi secara menyeluruh dari Dinas hingga Seksi dalam bentuk diagram matahari.
    * **Bar Charts:** Analisis Top 10 SKPD dengan kebutuhan pegawai terbesar dan distribusi unit per level.
* **Validasi Data (Health Check):**
    * Mendeteksi **"Data Yatim"** (Unit kerja yang memiliki ID Atasan, namun atasannya tidak ditemukan di database).
    * Validasi *Cross-check* dengan file Listing Pegawai.
* **Pencarian Canggih:** Mencari Unit Kerja berdasarkan ID atau Nama dengan kalkulasi total kebutuhan *real-time*.
* **Export Laporan:** Download hasil analisis (Rekap SKPD, Detail Bidang, Hasil Pencarian) ke format Excel (`.xlsx`) yang rapi.
* **Fleksibilitas Input:** Mendukung format file `.xlsx` dan `.csv` secara otomatis.
* **Performa Tinggi:** Menggunakan sistem *caching* agar pemrosesan data instan tanpa loading berulang.

## 🛠️ Teknologi

* **Python 3.10+**
* **Streamlit:** Framework Dashboard Modern.
* **Pandas:** Pemrosesan & Manipulasi Data.
* **Plotly:** Grafik Interaktif.
* **OpenPyxl:** Manipulasi dan Export Excel.

## 📦 Cara Instalasi

1.  **Clone repositori ini:**
    ```bash
    git clone https://github.com/rezaldwntr/data-sotk-hsu.git
    cd data-sotk-hsu
    ```

2.  **Buat Virtual Environment (Disarankan):**
    * **Windows:**
        ```bash
        python -m venv venv
        venv\Scripts\activate
        ```
    * **Mac/Linux:**
        ```bash
        python3 -m venv venv
        source venv/bin/activate
        ```

3.  **Install Dependensi:**
    ```bash
    pip install -r requirements.txt
    ```

## ▶️ Cara Menjalankan Aplikasi

Jalankan perintah berikut di terminal:

```bash
streamlit run data_sotk_hsu.py
```

Aplikasi akan terbuka otomatis di browser Anda (biasanya di `http://localhost:8501`).

## 📝 Catatan Rilis (Changelog)

**Versi 3.0.0 - Major Update: Visualization & Robustness**
* **[ADD]** Tab Visualisasi (Sunburst & Bar Chart) menggunakan Plotly.
* **[FIX]** Algoritma pembacaan hierarki diubah total menjadi *Recursive Lineage* (lebih akurat & mendukung format ID dinamis).
* **[ADD]** Fitur *Caching* (`@st.cache_data`) untuk performa loading data yang jauh lebih cepat.
* **[ADD]** Deteksi Data Error (Orphan Data/Data Yatim) di Sidebar.
* **[FIX]** Perbaikan tombol Download Excel yang sebelumnya error (`StreamlitInvalidHeightError` & `DuplicateWidgetID`).
* **[FIX]** Mendukung upload file `.csv` sebagai fallback otomatis jika `.xlsx` gagal dibaca.

---
Developed by **Rezal Dewantara**
