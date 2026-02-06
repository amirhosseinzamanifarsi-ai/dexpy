from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import schedule
import re
import pandas as pd
import yagmail
import time
from selenium.webdriver.firefox.options import Options
import os  # ░▒▓ حیاتی برای محیط سرور ▓▒░

def timing():
    # ░▒▓ تنظیمات تضمینی برای سرور لینوکس ▓▒░
    os.environ['PATH'] = '/usr/local/bin:' + os.environ['PATH']  # حل مشکل PATH
    
    options = Options()
    options.binary_location = '/usr/bin/firefox'  # مسیر دقیق فایرفاکس
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")  # ضروری برای داکر/سرور
    options.add_argument("--disable-dev-shm-usage")  # حل مشکل حافظه
    options.add_argument("--window-size=1920,1080")
    
    service = Service(executable_path='/usr/local/bin/geckodriver')  # مسیر مطلق
    
    driver = webdriver.Firefox(service=service, options=options)

    try:
        driver.get('https://dexscreener.com/')
        
        # ░▒▓ انتظار هوشمندانه با انتخابگر اصلاح شده ▓▒░
        table_element = WebDriverWait(driver, 25).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div[class*='ds-dex-table']"))
        )

        # ░▒▓ بخش استخراج داده (بدون تغییر) ▓▒░
        source_site = driver.page_source
        soup = BeautifulSoup(source_site, 'html.parser')
        z = requests.get('https://dexscreener.com/')
        soup2 = BeautifulSoup(z.text, 'html.parser')
        y = soup2.find_all('a', class_='ds-dex-table-row ds-dex-table-row-top')
        
        t = r'" href="([^".]*[a-z0-9])"'
        v = re.findall(t, source_site)

        ls_con = []
        for i in v:
            if len(i) >= 20:
                ls_con.append(i)

        data1 = driver.find_element(By.CSS_SELECTOR, '.ds-dex-table')
        data_text = data1.text
        data_list = data_text.splitlines()
        titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']

        new_data = data_list[12:]

        dl_list = ['750', '3', '210', '880', '780', '150', 'WP', '720', 'V4', '20', '50', '70', '60', 'CPMM', '180', '620', '80', '100V3', 'V3', '200', 'V1', '30', 'OOPS', '100', '550', '130', 'CLMM', 'DLMM', '40', '600', '300', 'V2', '500', '110', 'DYN', 'DYN2', '/', '1000', '10', '310', '850', '120', '660', '510', '530']

        nd = [item for item in new_data if item not in dl_list]

        arzha = []
        for ia in range(0, len(nd), 15):
            arz = nd[ia:ia + 15]
            arzha.append(arz)

        pd_df = pd.DataFrame(arzha, columns=titles)

        # ░▒▓ منطق تطابق آدرس‌ها ▓▒░
        if len(pd_df) == len(ls_con):
            pd_df['CONTRACT ADDRESS'] = ls_con
        else:
            ls_con_extended = ls_con[:len(pd_df)] if len(ls_con) > len(pd_df) else ls_con + ['N/A']*(len(pd_df)-len(ls_con))
            pd_df['CONTRACT ADDRESS'] = ls_con_extended

        csvname = 'dexscrrener.csv'
        pd_df.to_csv(csvname, index=False, encoding='utf-8')
        print(f"CSV generated: {csvname}")

        # ░▒▓ ارسال ایمیل ▓▒░
        ersal_konandeh = 'dexscreeneramirzamani@gmail.com'
        password = 'urcs rehx ttyt hzbv'
        file_ersali = csvname
        con = 'گزارش لحظه‌ای DexScreener'
        daryaft_konandeh = 'amirhosseinzamanifarsi@gmail.com'
        
        yag = yagmail.SMTP(ersal_konandeh, password)
        yag.send(daryaft_konandeh, con, file_ersali)
        print('فایل با موفقیت ارسال شد.')
        
    except Exception as e:
        print(f"🚨 خطا: {str(e)}")
        driver.save_screenshot('/root/dexpy/error.png')  # ذخیره تصویر خطا در مسیر مشخص
    finally:
        driver.quit()

# ░▒▓ زمان‌بندی اجرا ▓▒░
schedule.every(1).minute.do(timing)

while True:
    schedule.run_pending()
    time.sleep(1)
