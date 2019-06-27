# add error handling when respons is not 200.

import requests
import urllib
import urllib.request
import time
from bs4 import BeautifulSoup
import pandas as pd
import re
import logging

# logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
sh.setFormatter(formatter)
logger.addHandler(sh)


SINGLE_QUOTES_PATTERN = '''(?<=')\s*[^']+?\s*(?=')'''

bokete_static_pages= ['boke/hot', 'boke/popular', 'boke/collabo', 'boke/select', 'boke/pickup', 'boke/legend']
bokete_dynamic_pages = ['boke/recent']
base_url = 'https://bokete.jp'

data = pd.DataFrame(columns=['img_name', 'caption', 'score'])
data_row_count = 0

def parse_params(param_string):
    logger.info(param_string)
    param_string = param_string[param_string.find('(')+1: param_string.find(')')]
    sch= re.search("{max_id:(.*),category:(.*),op:(.*),rate:(.*)}", param_string)
    return [sch.group(i) for i in range(1,5)]


def scrape(response):
    global data
    global data_row_count
    global SINGLE_QUOTES_PATTERN
    soup = BeautifulSoup(response.text, 'html.parser')
    boke_divs = soup.findAll('div', {'class': 'boke'})
    for div in boke_divs:
        image_page = div.find('a')['href']
        image_url = div.find('img')['src']
        image_name = image_url.split('/')[-1]
        time.sleep(1)
        logger.info('downloading image:{}'.format(image_url))
        urllib.request.urlretrieve('http:'+image_url, 'images/'+image_name)
        time.sleep(1)
        url_ = base_url+image_page
        logger.info('get request : {}'.format(url_))
        try:
            image_page_response = requests.get(url_, timeout=10)
        except:
            logger.info('timed out{} skipping'.format(url_))
            continue
        if response.status_code != 200:
            continue
        soup_img_page = BeautifulSoup(image_page_response.text, 'html.parser')
        img_page_boke_divs = soup_img_page.findAll('div', {'class': 'boke'})
        img_page_boke_divs.pop(0)
        for img_page_div in img_page_boke_divs:
            url_encoded_text = re.search(SINGLE_QUOTES_PATTERN, img_page_div.find('a', 'boke-text').find('div')['ng-init']).group()
            decoded_text = urllib.parse.unquote(url_encoded_text)
            stars = int(img_page_div.find('div', 'boke-stars').text.strip().replace(',',''))
            logger.info('data row: img_name: {} caption: {} score: {}'.format(image_name, decoded_text, stars))
            data = data.append({'img_name':image_name, 'caption':decoded_text, 'stars':stars}, ignore_index=True)
            data_row_count+= 1
            if data_row_count%100 == 0:
                data.to_pickle('data/data'+str(data_row_count) + '.pkl')

def scrape_static():
    for bokete_page in bokete_static_pages:
        logger.info('scrapping page:{}'.format(bokete_page))
        for page_number in range(1,9):
            time.sleep(3)
            while True:
                url_ = base_url+'/'+bokete_page+'?page='+str(page_number)
                logger.info('get request : {}'.format(url_))
                response = requests.get(url_, timeout=10)
                if response.status_code == 200:
                    scrape(response)
                    break

def scrape_dynamic():
    for bokete_page in bokete_dynamic_pages:
        time.sleep(3)
        while True:
            url_ = base_url+'/'+bokete_page
            logger.info('get request: {}'.format(url_))
            response = requests.get(url_, timeout=10)
            if response.status_code == 200:
                scrape(response)
                break
        soup = BeautifulSoup(response.text, 'html.parser')
        param_string = soup.find('button',{'class':'btn btn-primary btn-long'})['ng-click']
        max_id, category, op, rate = parse_params(param_string)
        while True:
            time.sleep(3)
            while True:
                url_ = base_url+'/'+bokete_page+'/panel?category='+ category +'&max_id=' + max_id +'&op='+op+'&rate='+rate
                logger.info('get request: {}'.format(url_))
                response = requests.get(url_, timeout=5)
                if response.status_code == 200:
                    scrape(response)
            soup = BeautifulSoup(response.text, 'html.parser')
            param_string = soup.find('button',{'class':'btn btn-primary btn-long'})['ng-click']
            max_id, category, op, rate = parse_params(param_string)
            if data_row_count > 100000:
                break


if __name__ == "__main__":
    logger.info('initiating scrapping from static pages')
    scrape_static()
    logger.info('initiating scrapping from dynamic pages')
    scrape_dynamic()
