import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import urllib.parse
import re
import os
import requests
from huggingface_hub import HfApi
from huggingface_hub import login, snapshot_download

def main():
    st.set_page_config(page_title="Persebaya Match Data", layout="wide")
    
    st.title("Persebaya Match Data Scraper")
    st.write("Mengambil data jadwal pertandingan Persebaya Surabaya")
    
    # Tambahkan progress indicator
    with st.spinner("Sedang mengambil data dari website Persebaya..."):
        xdata = take_datamatch()
    
    if xdata:
        st.success("Berhasil mengambil data!")
        
        # Tampilkan preview data
        with st.expander("Preview Data HTML"):
            st.code(xdata[:2000] + "..." if len(xdata) > 2000 else xdata, language='html')
        
        # Simpan di lokal
        file_path = save_to_temp_file(xdata)
        
        if file_path:
            st.write(f"Data disimpan sementara di: `{file_path}`")
            
            # Upload ke Hugging Face
            with st.spinner("Mengupload data ke Hugging Face Hub..."):
                try:
                    # Login dengan token dari secrets
                    token = st.secrets.get("AKSES_MATCH")
                    if token:
                        login(token=token)
                        st.success("Berhasil login ke Hugging Face")
                    else:
                        st.error("Token Hugging Face tidak ditemukan. Pastikan sudah diatur di Streamlit Secrets.")
                        return

                    api = HfApi()
                    api.create_repo(
                        repo_id="sintamar/dataliga1",
                        repo_type="dataset",
                        exist_ok=True
                    )
                    
                    if os.path.exists(file_path):
                        api.upload_file(
                            path_or_fileobj=file_path,
                            path_in_repo="data/match_psby.txt",
                            repo_id="sintamar/dataliga1",
                            repo_type="dataset",
                            commit_message="update otomatis match psby"
                        )
                        st.success("Berhasil upload data ke Hugging Face Hub!")
                    else:
                        st.error(f"File tidak ditemukan: {file_path}")
                        
                except Exception as e:
                    st.error(f"Error saat upload ke Hugging Face: {e}")
                
    else:
        st.error("Gagal mengambil data dari website.")
    
    # Tambahkan informasi tambahan
    st.markdown("---")
    st.markdown("""
    **Fitur:**
    - Scraping data jadwal pertandingan Persebaya Surabaya
    - Penyimpanan otomatis ke Hugging Face Dataset
    - Update data secara berkala
    
    **Sumber Data:** [persebaya.id](https://www.persebaya.id/jadwal-pertandingan/91/persebaya-surabaya)
    """)

def save_to_temp_file(cleaned_content):
    """
    Fungsi untuk menyimpan konten yang sudah dibersihkan ke file temporary
    """
    filename = "match_psby.txt"
    
    try:
        # Membuat direktori /tmp jika belum ada
        temp_dir = "/tmp"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Path file
        file_path = os.path.join(temp_dir, filename)
        
        # Menyimpan konten ke file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        return file_path
    except Exception as e:
        st.error(f"Error saving file: {e}")
        return None

def take_datamatch():
    """
    Fungsi untuk mengambil data jadwal pertandingan dari website Persebaya
    """
    # Konfigurasi Chrome untuk Streamlit Cloud
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--remote-debugging-port=9222')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Untuk menghindari issues di cloud environment
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    wd = None
    try:
        # Inisialisasi WebDriver
        wd = webdriver.Chrome(options=chrome_options)
        wd.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Set timeout
        wd.set_page_load_timeout(30)
        wd.implicitly_wait(10)
        
        # Buka URL target
        url = 'https://www.persebaya.id/jadwal-pertandingan/91/persebaya-surabaya'
        wd.get(url)
        
        # Tunggu sampai page load
        WebDriverWait(wd, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Ambil HTML
        html = wd.execute_script("return document.documentElement.outerHTML;")
        soup = BeautifulSoup(html, "html.parser")
        
        # Daftar elemen yang akan dihapus
        elements_to_remove = [
            {'name': 'div', 'class': 'container persebaya-nav'},
            {'name': 'h4', 'class': 'modal-title', 'text': 'Search'},
            {'name': 'button', 'class': 'close', 'attrs': {'data-dismiss': 'modal'}},
            {'name': 'div', 'class': 'row mt-4 mb-2'},
            {'name': 'div', 'class': 'col-md-12 px-0 px-md-3'},
            {'name': 'div', 'class': 'col-12 col-md-3 order-last order-md-last text-center'},
            {'name': 'form', 'attrs': {'action': 'https://www.persebaya.id/search/result', 'class': 'form-inline navbar-right ml-auto', 'method': 'GET', 'role': 'search'}},
            {'name': 'div', 'id': 'footer-top', 'class': 'row align-items-center text-center pb-5 pb-md-3 pt-md-4'}
        ]
        
        # Hapus setiap elemen yang ditentukan
        for element_config in elements_to_remove:
            if 'class' in element_config and 'text' in element_config:
                elements = soup.find_all(element_config['name'], 
                                       class_=element_config['class'],
                                       string=element_config['text'])
            elif 'class' in element_config:
                elements = soup.find_all(element_config['name'], class_=element_config['class'])
            elif 'attrs' in element_config:
                elements = soup.find_all(element_config['name'], attrs=element_config['attrs'])
            else:
                elements = soup.find_all(element_config['name'])
            
            for element in elements:
                element.decompose()

        # Mendapatkan HTML yang sudah dibersihkan
        cleaned_html = str(soup)
        return cleaned_html
                  
    except WebDriverException as e:
        st.error(f"WebDriver Error: {e}")
        return None
    except Exception as e:
        st.error(f"Unexpected Error: {e}")
        return None
    finally:
        if wd:
            wd.quit()

if __name__ == "__main__":
    main()
