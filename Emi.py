from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import yagmail
import schedule
import time
import re
import datetime
from selenium.webdriver.firefox.options import Options

def timing():
    try:
        # تنظیمات حرفه‌ای برای هدلس مود
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")  # ضروری برای نمایش صحیح عناصر
        
        service = Service('/snap/bin/geckodriver')
        driver = webdriver.Firefox(service=service, options=options)
        
        try:
            # بارگیری صفحه با کنترل خطا
            driver.get('https://dexscreener.com/')
            
            # انتظار هوشمند برای جدول اصلی (تا ۴۰ ثانیه)
            try:
                table_element = WebDriverWait(driver, 40).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".ds-dex-table"))
                )
            except TimeoutException:
                driver.save_screenshot('table_timeout.png')
                print("خطا: جدول پس از ۴۰ ثانیه ظاهر نشد!")
                return
            
            # استخراج داده‌های صفحه
            source_site = driver.page_source
            soup = BeautifulSoup(source_site, 'html.parser')
            
            # استخراج آدرس‌ها با regex
            t = r'" href="([^".]*[a-z0-9])"'
            v = re.findall(t, source_site)
            ls_con = [i for i in v if len(i) >= 20]
            
            # پردازش داده‌های جدول
            data_text = table_element.text
            data_list = data_text.splitlines()
            titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
            
            new_data = data_list[12:]
            dl_list = ['750', '3', '210', '880', '780', '150', 'WP', '720', 'V4', '20', '50', '70', '60', 'CPMM', '180', '620', '80', '100V3', 'V3', '200', 'V1', '30', 'OOPS', '100', '550', '130', 'CLMM', 'DLMM', '40', '600', '300', 'V2', '500', '110', 'DYN', 'DYN2', '/', '1000', '10', '310', '850', '120', '660', '510', '530']
            nd = [item for item in new_data if item not in dl_list]
            
            # ساخت دیتافریم
            arzha = [nd[ia:ia + 15] for ia in range(0, len(nd), 15)]
            pd_df = pd.DataFrame(arzha, columns=titles)
            
            # تطابق آدرس‌ها با ردیف‌ها
            pd_df['CONTRACT ADDRESS'] = ls_con[:len(pd_df)] if len(ls_con) >= len(pd_df) else ls_con + ['N/A']*(len(pd_df)-len(ls_con))
            
            # ذخیره CSV
            csvname = f'dexsc_{datetime.datetime.now().strftime("%H%M")}.csv'
            pd_df.to_csv(csvname, index=False)
            print(f"فایل {csvname} ساخته شد")
            
            # ارسال ایمیل
            yag = yagmail.SMTP('dexscreeneramirzamani@gmail.com', 'urcs rehx ttyt hzbv')
            yag.send(
                to='amirhosseinzamanifarsi@gmail.com',
                subject='آپدیت جدید دکس‌اسکرینر',
                contents='جدیدترین داده‌ها ضمیمه شده',
                attachments=csvname
            )
            print("ایمانیل ارسال شد")
            
        finally:
            driver.quit()
            
    except Exception as e:
        print(f"خطای کلی: {
