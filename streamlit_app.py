import streamlit as st
import requests
from bs4 import BeautifulSoup
from ftplib import FTP
import os
import pandas as pd
from io import BytesIO
import tempfile
import datetime

def clean_html_content(html_content):
    """
    Membersihkan HTML dengan menghapus elemen-elemen tertentu
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    tableklasemen = soup.find("table", class_="table-striped table-responsive table-hover result-point")

    if tableklasemen:
        df = pd.read_html(str(tableklasemen))[0]
        # 4️⃣ Bersihkan header ganda jika ada
        if df.columns[0] == df.iloc[0, 0]:
            df = df.drop(0)
        
        # 5️⃣ Normalisasi nama kolom
        df.columns = [
            "Posisi", "Klub", "Main", "Menang", "Seri", "Kalah",
            "GF", "GA", "GD", "Poin", "Form", "Next"
        ][:len(df.columns)]
        
        # 6️⃣ Konversi nilai numerik untuk kolom statistik
        for col in ["Posisi", "Main", "Menang", "Seri", "Kalah", "GF", "GA", "GD", "Poin"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        # 8️⃣ Simpan ke file CSV lokal
        # Simpan CSV lokal
    # Daftar elemen yang akan dihapus
    
    
    return df

def upload_via_ftp(local_file_path, remote_file_name):
    """
    Upload file ke server FTP
    """
    # Ganti dengan kredensial FTP Anda
    FTP_HOST = "157.66.54.106"
    FTP_USER = "appbonek"
    FTP_PASS = "jikasupport081174"
    FTP_PATH = "/" 
    
    if not all([FTP_HOST, FTP_USER, FTP_PASS]):
        st.error("Kredensial FTP tidak ditemukan. Silakan setting environment variables atau Streamlit secrets.")
        return False
    
    try:
        # Connect to FTP server
        ftp = FTP(FTP_HOST)
        ftp.login(FTP_USER, FTP_PASS)
        
        # Change to target directory if specified
        if FTP_PATH:
            ftp.cwd(FTP_PATH)
        
        # Upload file
        with open(local_file_path, 'rb') as file:
            ftp.storbinary(f'STOR {remote_file_name}', file)
        
        ftp.quit()
        return True
        
    except Exception as e:
        st.error(f"Error FTP: {str(e)}")
        return False

def main():
    st.set_page_config(
        page_title="Persebaya Klasemen Auto Upload",
        page_icon="⚽",
        layout="centered"
    )
    
    st.title("⚽ Persebaya Klasemen Auto Upload")
    st.info("Aplikasi sedang berjalan...")
       
    # URL target (hardcoded sesuai permintaan)
    TARGET_URL = "https://www.ligaindonesiabaru.com/table/index/BRI_SUPER_LEAGUE_2025-26"
    FILENAME = "klasemen_liga1.csv"
    
    # Progress bar dan status
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Ambil konten dari URL
        status_text.text("📥 Mengambil data dari Liga Indonesia...")
        progress_bar.progress(25)
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(TARGET_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Step 2: Bersihkan konten HTML
        status_text.text("🧹 Membersihkan konten HTML...")
        progress_bar.progress(50)
        
       
        cleaned_content = clean_html_content(response.text)
        st.subheader("Preview Data Klasemen")
        st.dataframe(cleaned_content)
        # Simpan ke file CSV sementara
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as tmp_file:
            csv_path = tmp_file.name
            cleaned_content.to_csv(csv_path, index=False, encoding="utf-8-sig")
        # Step 3: Upload ke hosting via FTP
        status_text.text("📤 Mengupload ke hosting...")
        progress_bar.progress(75)
        
        try:
            with st.spinner("Mengupload ke server FTP..."):
                upload_via_ftp(csv_path, "klasemen_liga1.csv")
                    
        except Exception as e:
                st.error(f"Gagal mengupload ke FTP: {str(e)}")
                
        # Hapus file temporary
        os.unlink(csv_path)
        status_text.text("✅ Proses selesai!", csv_path)
        status_text.text("✅ Proses selesai!")
        progress_bar.progress(100)
            
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Gagal mengambil data : {str(e)}")
        progress_bar.progress(0)      
   
if __name__ == "__main__":
    main()
    st.title("Streamlit Keep-Alive Demo 🚀")

    st.write("Aplikasi ini menampilkan waktu saat ini dan bisa dipakai untuk uji anti-sleep.")
    
    st.write("Waktu sekarang:", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Opsional: tampilan log keepalive
    try:
        with open("keepalive.log") as f:
            log = f.readlines()[-5:]  # 5 log terakhir
        st.write("Log keepalive terakhir:")
        st.write("".join(log))
    except:
        st.write("Belum ada log keepalive.")
