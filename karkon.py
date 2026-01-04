from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
import requests
import schedule
import re
import pandas
import yagmail
import datetime
import time
import random
def timing():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64; rv:136.0) Gecko/20100101 Firefox/136.0")
    
    path_geckodriver = '/usr/bin/geckodriver'
    service_path = Service(path_geckodriver)
    bot_ertebati = webdriver.Firefox(service=service_path, options=options)
    
    # افزایش تأخیر اولیه
    bot_ertebati.get('https://dexscreener.com/')
    time.sleep(random.uniform(3, 7))
    time.sleep(2)
    bot_ertebati.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    # افزایش زمان انتظار
    wait = WebDriverWait(bot_ertebati, 30)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ds-dex-table')))
    time.sleep(5)  # استراحت بیشتر
    
    data1 = bot_ertebati.find_element(By.CSS_SELECTOR, '.ds-dex-table')
    data_text = data1.text
    data_list = data_text.splitlines()
    
    titles = ['RANK','TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
    new_data = data_list[12:]
    
    dl_list = ['750','3','210','880','780','150','WP','720','V4','20','50','70','60','CPMM','180','620','80','100V3','V3','200','V1','30','OOPS','100','550','130','CLMM','DLMM','40','600','300','V2','500','110','DYN','DYN2','/','1000','10','310','850','120','660','510','530']
    
    nd = [item for item in new_data if item not in dl_list]
    
    arzha = []
    for i in range(0, len(nd), 15):
        arz = nd[i:i+15]
        arzha.append(arz)
    
    pd = pandas.DataFrame(arzha, columns=titles)
    
    # --- token_add بدون درایور جدید ---
    source_site = bot_ertebati.page_source
    t = r'" href="([^".]*[a-z0-9])"'
    v = re.findall(t, source_site)
    ls_con = [i for i in v if len(i) >= 20]
    
    if len(pd) == len(ls_con):
        pd['CONTRACT ADDRESS'] = ls_con
    else:
        pd['CONTRACT ADDRESS'] = ls_con + ls_con[:1]
    
    csvname = 'dexscrrener.csv'
    pd.to_csv(csvname, index=False, encoding='utf-8')
    bot_ertebati.quit()
    
    # ارسال ایمیل
    yag = yagmail.SMTP('dexscreeneramirzamani@gmail.com', 'urcs rehx ttyt hzbv')
    yag.send('amirhosseinzamanifarsi@gmail.com', 'test', csvname)
    print('file ba movafaghiat ersal shod.')

schedule.every(1).minute.do(timing)

while True:
    schedule.run_pending()
    time.sleep(1)
