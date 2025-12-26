# 📊 Data SOTK HSU (Hulu Sungai Utara)

Project ini berisi *tools* dan skrip Python untuk pengolahan, analisis, dan pemetaan data **SOTK (Susunan Organisasi dan Tata Kerja)** di lingkungan Pemerintah Kabupaten Hulu Sungai Utara.

Project ini bertujuan untuk mempermudah manajemen data jabatan, unit kerja, dan struktur organisasi agar lebih terstruktur dan mudah dianalisis.

## 🎯 Fungsi Utama

* **Data Processing:** Membersihkan dan menstandarisasi data mentah SOTK.
* **Analisis Jabatan:** (Opsional: sesuaikan dengan isi script) Membantu pemetaan Analisis Jabatan (Anjab) dan Analisis Beban Kerja (ABK).
* **Reporting:** Menghasilkan output data yang siap digunakan untuk laporan atau integrasi aplikasi lain.

## 🛠️ Teknologi

* **Language:** Python 3.x
* **Data Manipulation:** Pandas (Asumsi, sesuaikan jika pakai library lain)
* **Environment:** VS Code (DevContainer Support)

## 🚀 Cara Menjalankan

1.  **Clone Repository**
    ~~~bash
    git clone https://github.com/rezaldwntr/data-sotk-hsu.git
    cd data-sotk-hsu
    ~~~

2.  **Setup Environment**
    Disarankan menggunakan Virtual Environment agar library tidak bentrok.
    ~~~bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    ~~~

3.  **Install Dependencies**
    ~~~bash
    pip install -r requirements.txt
    ~~~

4.  **Jalankan Skrip**
    ~~~bash
    python data_sotk_hsu.py
    ~~~

## 📂 Struktur Project

~~~text
data-sotk-hsu/
├── .devcontainer/    # Konfigurasi environment VS Code
├── data/             # Folder untuk menyimpan file raw/output (Ignored by Git)
├── data_sotk_hsu.py  # Skrip utama
├── requirements.txt  # Daftar library yang dibutuhkan
└── README.md         # Dokumentasi project
~~~

---
© 2025 Rezal Dewantara.
