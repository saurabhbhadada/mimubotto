import requests
import urllib
import urllib.request
import time
from bs4 import BeautifulSoup
import pandas as pd
import re

SINGLE_QUOTES_PATTERN = '''(?<=')\s*[^']+?\s*(?=')'''

bokete_static_pages= ['boke/hot', 'boke/popular', 'boke/collabo', 'boke/select', 'boke/pickup', 'boke/legend']
bokete_dynamic_pages = ['boke/recent']
base_url = 'https://bokete.jp'

data = pd.Dataframe(columns=['img_name', 'caption', 'score'])
data_count = 0

def scrape(response):
    soup = BeautifulSoup(response.text, 'html.parser')
    boke_divs = soup.findAll('div', {'class': 'boke'})
    for div in boke_divs:
        image_page = div.find('a')['href']
        image_url = div.find('image')['src']
        image_name = image_url.split('/')[-1]
        time.sleep(1)
        urllib.request.urlretrieve('http:'+image_url, 'images/'+image_name)
        time.sleep(1)
        image_page_response = requests.get(base_url+image_page, timeout=5)
        soup_img_page = BeautifulSoup(image_page_response.text, 'html.parser')
        img_page_boke_divs = soup.findAll('div', {'class': 'boke'})
        img_page_boke_divs.pop(0)
        for img_page_div in img_page_boke_divs:
            url_encoded_text = re.search(SINGLE_QUOTES_PATTERN, img_page_div.find('a', 'boke-text').find('div')['ng-init']).group()
            decoded_text = urllib.parse.unquote(url_encoded_text)
            stars = int(img_page_div.find('div', 'boke-stars').text.strip().replace(',',''))
            data = data.append({'img_name':image_name, 'caption':decoded_text, 'stars' stars}, ignore_index=True)
            data_row_count+ = 1
            if data_row_count%100 = 0:
                data.to_pickle('data/data'+str(data_row_count) + '.pkl')

def scrape_static():
    for bokete_page in bokete_static_pages:
        for page_number in range(1,9):
            time.sleep(3)
            response = requests.get(base_url+'/'+bokete_page+'?page='+str(page_number), timeout=10)
            scrape(response)

def scrape_dynamic(start_page_url):
    for bokete_page in bokete_dynamic_pages:
        while True
