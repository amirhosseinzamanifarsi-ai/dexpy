from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
import requests
import schedule
import re
import pandas as pd
import yagmail
import time
from selenium.webdriver.firefox.options import Options

def timing():
    print(f"Starting task at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # تنظیمات بهینه برای سرور
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    # جلوگیری از لاگ‌های اضافی که باعث اختلال در ارتباط درایور می‌شود
    options.set_preference("browser.tabs.remote.autostart", False)
    
    # مسیر geckodriver
    service = Service('/usr/local/bin/geckodriver')
    
    driver = None # تعریف اولیه برای جلوگیری از ارور در finally
    
    try:
        driver = webdriver.Firefox(service=service, options=options)
        driver.get('https://dexscreener.com/')
        
        # صبر کردن برای لود شدن جدول (به جای implicitly_wait ثابت)
        time.sleep(10) 

        source_site = driver.page_source
        
        # بخش استخراج داده‌ها (بدون تغییر در منطق شما)
        z = requests.get('https://dexscreener.com/')
        soup2 = BeautifulSoup(z.text, 'html.parser')
        
        t = r'" href="([^".]*[a-z0-9])"'
        v = re.findall(t, source_site)

        ls_con = [i for i in v if len(i) >= 20]

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
            if len(arz) == 15: # اطمینان از کامل بودن ردیف
                arzha.append(arz)

        pd_df = pd.DataFrame(arzha, columns=titles)

        # تطبیق آدرس کنتراکت
        if len(ls_con) < len(pd_df):
            ls_con_extended = (ls_con * ((len(pd_df) // len(ls_con)) + 1))[:len(pd_df)]
        else:
            ls_con_extended = ls_con[:len(pd_df)]
        
        pd_df['CONTRACT ADDRESS'] = ls_con_extended

        csvname = 'dexscrrener.csv'
        pd_df.to_csv(csvname, index=False, encoding='utf-8')
        print(f"CSV generated: {csvname}")

        # ارسال ایمیل
        ersal_konandeh = 'dexscreeneramirzamani@gmail.com'
        password = 'urcs rehx ttyt hzbv'
        daryaft_konandeh = 'amirhosseinzamanifarsi@gmail.com'
        
        yag = yagmail.SMTP(ersal_konandeh, password)
        yag.send(daryaft_konandeh, 'DexScreener Report', csvname)
        print('Email sent successfully.')

    except Exception as e:
        print(f"Error in timing(): {e}")
    finally:
        if driver:
            driver.quit()
            print("Driver closed.")

# اجرای زمان‌بندی
schedule.every(1).minutes.do(timing)

print("Scheduler started...")
while True:
    schedule.run_pending()
    time.sleep(1)
