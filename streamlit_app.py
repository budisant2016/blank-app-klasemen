import streamlit as st
from io import BytesIO
import pandas as pd
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from io import BytesIO
from bs4 import BeautifulSoup
import urllib.parse
import re
import os
import requests
from huggingface_hub import HfApi
from huggingface_hub import login, snapshot_download

def main():
    
 
    
    xdata = take_datamatch()
    
    if xdata:
        #st.code(xdata, language='html')  
        
        # Simpan di lokal
        #output_path = "/tmp/match_psby.txt"
        save_to_temp_file(xdata)
        
        # Login dengan token dari environment variable
        token = os.environ.get('akses_match')
        if token:
            login(token=token)
        else:
            print("Token tidak ditemukan")

        api = HfApi()
        api.create_repo(
            repo_id="sintamar/dataliga1",
            repo_type="dataset",
            exist_ok=True  # tidak error kalau sudah ada
        )
        txt_path = "/tmp/match_psby.txt"
        assert os.path.exists(txt_path), f"File tidak ditemukan: {txt_path}"
        api.upload_file(
            path_or_fileobj=txt_path,
            path_in_repo="data/match_psby.txt",
            repo_id="sintamar/dataliga1",   # ganti sesuai nama repo kamu
            repo_type="dataset",
            commit_message="update otomatis match psby"
        )
                
    else:
        st.warning("tidak ditemukan.")  
    
def save_to_temp_file(cleaned_content):
    
    #Fungsi untuk menyimpan konten yang sudah dibersihkan ke file temporary
    filename="match_psby.txt"
    
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


def visualize(url):  
    try:
    # Fetch and display the website content
        with st.spinner("loading website data ..."):
            # innerHTML = get_innerHTML(url)
            html_content, xtarget_dropdown, xurl = take_webdata(url)
            #st.subheader("Website title:")
            if xtarget_dropdown:
                st.code(xtarget_dropdown, language='html')  
                if xurl:
                    st.code(xurl, language='html')                  
                else:
                    st.warning("tidak ditemukan.")  
            else:
                st.warning("tidak ditemukan.")  
    
    except Exception as e:
        st.error(f"Error: {e}")

def take_datamatch():
    #https://www.flashscore.com/standings/pxpznaL7/QqIn9e16/#/QqIn9e16/standings/overall/
    #<div class="JCZQSb"><div class="kXPUVc wp-ms">
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    try:
        wd = webdriver.Chrome(options=options)
        wd.set_window_size(1080, 720)  # Adjust the window size here
        wd.get('https://www.persebaya.id/jadwal-pertandingan/91/persebaya-surabaya')
        wd.implicitly_wait(5)
        
        html = wd.execute_script("return document.documentElement.outerHTML;")
        soup = BeautifulSoup(html, "html.parser")
        #<div class="table table-hover table-responsive col-md-12">

        # Mengambil hanya bagian body
        #body_content = soup.find('body')
        
        #soup = body_content
            
        # Daftar elemen yang akan dihapus <div class="col-12 col-md-3 order-last order-md-last text-center">
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
                  
    except WebDriverException as e:
        return html
    finally:
        if wd:
            wd.quit()

    return cleaned_html


def take_webdata(url):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    try:
        wd = webdriver.Chrome(options=options)
        wd.set_window_size(1080, 720)  # Adjust the window size here
        wd.get(url)
        wd.implicitly_wait(15)
        # Get the page title
        page_title = wd.title
        #screenshot = wd.get_screenshot_as_png()
        #WebDriverWait(wd, 20).until(EC.presence_of_element_located((By.ID, "tournament-table")))
        html = wd.execute_script("return document.documentElement.outerHTML;")
        soup = BeautifulSoup(html, "html.parser")

        target_dropdown = soup.find('div', class_='dropdown-menu', attrs={'aria-labelledby': 'navbar-match'})

        if target_dropdown:
            klasemenlink = target_dropdown.find('a', class_='dropdown-item',string='KLASEMEN')
            if klasemenlink:
                urlx = klasemenlink.get('href')
        else:
            print("Dropdown menu tidak ditemukan")     
      
    except WebDriverException as e:
        return page_title
    finally:
        if wd:
            wd.quit()

    return html ,target_dropdown, urlx

if __name__ == "__main__":
    main()
