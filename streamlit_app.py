import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from bs4 import BeautifulSoup
import re
import os
from ftplib import FTP
import tempfile

def main():
    st.title("Scraping Data Klasemen Liga 1")
    
    if st.button("Ambil Data Klasemen Terbaru"):
        with st.spinner("Mengambil data dari website..."):
            xdata = take_dataklasemen()
            
        if xdata:
            with st.spinner("Memproses data..."):
                df = pd.read_html(str(xdata))[0]
                
                # Bersihkan header ganda jika ada
                if df.columns[0] == df.iloc[0, 0]:
                    df = df.drop(0)
                
                # Normalisasi nama kolom
                df.columns = [
                    "Posisi", "Klub", "Main", "Menang", "Seri", "Kalah",
                    "GF", "GA", "GD", "Poin", "Form", "Next"
                ][:len(df.columns)]
                
                # Konversi nilai numerik untuk kolom statistik
                for col in ["Posisi", "Main", "Menang", "Seri", "Kalah", "GF", "GA", "GD", "Poin"]:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                
                # Tampilkan preview data
                st.subheader("Preview Data Klasemen")
                st.dataframe(df)
                
                # Simpan ke file CSV sementara
                with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8-sig') as tmp_file:
                    csv_path = tmp_file.name
                    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                
                # Upload ke FTP
                try:
                    with st.spinner("Mengupload ke server FTP..."):
                        upload_via_ftp(csv_path, "klasemen_liga1.csv")
                    st.success("Data berhasil diambil dan diupload ke server FTP!")
                    
                    # Tampilkan link download
                    st.info("Data telah disimpan sebagai 'klasemen_liga1.csv' di server FTP")
                    
                except Exception as e:
                    st.error(f"Gagal mengupload ke FTP: {str(e)}")
                
                # Hapus file temporary
                os.unlink(csv_path)
                
        else:
            st.error("Tidak dapat mengambil data dari website. Silakan coba lagi.")

def take_dataklasemen():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--remote-debugging-port=9222')
    
    # Untuk Streamlit Cloud
    options.binary_location = "/usr/bin/google-chrome"
    
    try:
        wd = webdriver.Chrome(options=options)
        wd.set_window_size(1080, 720)
        wd.get('https://www.ligaindonesiabaru.com/table/index/BRI_SUPER_LEAGUE_2025-26')
        wd.implicitly_wait(10)
        
        # Tunggu sampai tabel muncul
        WebDriverWait(wd, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "table-striped"))
        )
        
        html = wd.execute_script("return document.documentElement.outerHTML;")
        soup = BeautifulSoup(html, "html.parser")

        tableklasemen = soup.find("table", class_="table-striped table-responsive table-hover result-point")
        
        return tableklasemen
          
    except WebDriverException as e:
        st.error(f"Error WebDriver: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None
    finally:
        if 'wd' in locals():
            wd.quit()

def upload_via_ftp(local_file_path, remote_file_name):
    """
    Upload file ke server FTP
    """
    # Ganti dengan kredensial FTP Anda
    FTP_HOST = st.secrets.get("FTP_HOST", os.environ.get('FTP_HOST'))
    FTP_USER = st.secrets.get("FTP_USER", os.environ.get('FTP_USER'))
    FTP_PASS = st.secrets.get("FTP_PASS", os.environ.get('FTP_PASS'))
    FTP_PATH = st.secrets.get("FTP_PATH", os.environ.get('FTP_PATH', ''))
    
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

if __name__ == "__main__":
    main()
