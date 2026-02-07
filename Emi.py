import os
import time
import re
import pandas as pd
import yagmail
import schedule
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display

def timing():
    print(f"\n--- شروع تسک: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    # راه‌اندازی نمایشگر مجازی
    display = Display(visible=0, size=(1366, 768))
    display.start()
    
    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--remote-debugging-port=9222")
        # هویت‌سازی برای جلوگیری از بلاک شدن
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

        # در اکثر سرورهای لینوکس، کروم در این مسیر نصب می‌شود
        driver = webdriver.Chrome(options=chrome_options)
        
        driver.set_page_load_timeout(60)
        driver.get('https://dexscreener.com/')
        
        # صبر برای لود شدن جدول
        wait = WebDriverWait(driver, 30)
        table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ds-dex-table")))
        
        print("✅ صفحه لود شد. در حال استخراج...")
        time.sleep(5) 

        # استخراج متن جدول
        data_list = table.text.splitlines()
        
        # استخراج آدرس‌ها از لینک‌ها
        source = driver.page_source
        links = re.findall(r'href="/([^"]+)"', source)
        contracts = [l.split('/')[-1] for l in links if len(l.split('/')[-1]) > 30]

        # پردازش داده‌ها
        titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
        
        # فیلتر کردن ردیف‌های اضافی (منطق شما)
        bad_words = ['750', '3', '210', '880', '780', 'WP', 'V4', 'V3', 'V2', 'V1', '/', 'CPMM', 'CLMM']
        clean_nd = [x for x in data_list if x not in bad_words and len(x) > 0]

        rows = []
        for i in range(0, len(clean_nd) - 14, 15):
            rows.append(clean_nd[i:i+15])

        if rows:
            df = pd.DataFrame(rows, columns=titles)
            # ست کردن کنتراکت‌ها
            df['CONTRACT ADDRESS'] = (contracts * (len(df)//len(contracts)+1))[:len(df)]
            
            csv_name = 'report.csv'
            df.to_csv(csv_name, index=False, encoding='utf-8-sig')
            
            # ارسال ایمیل
            yag = yagmail.SMTP('dexscreeneramirzamani@gmail.com', 'urcs rehx ttyt hzbv')
            yag.send('amirhosseinzamanifarsi@gmail.com', 'Update Report', 'فایل جدید پیوست شد.', attachments=csv_name)
            print("🚀 ایمیل با موفقیت ارسال شد.")
        else:
            print("⚠️ داده‌ای برای استخراج پیدا نشد.")

    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
    
    finally:
        if driver:
            driver.quit()
        display.stop()
        print("--- پایان عملیات و پاکسازی حافظه ---")

# اجرا
timing() # یک بار اجرا برای تست فوری

schedule.every(10).minutes.do(timing)
while True:
    schedule.run_pending()
    time.sleep(1)
