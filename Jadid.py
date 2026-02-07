from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import yagmail
import schedule
import time
import re

def timing():
    print(f"Starting task at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    options = Options()
    options.add_argument("--headless")
    # اضافه کردن تنظیمات برای پایداری بیشتر در سرور
    options.set_preference("dom.webdriver.enabled", False)
    options.set_preference("useAutomationExtension", False)
    
    # مسیر صحیح درایور (مطمئن شوید فایل در این مسیر است)
    service = Service('/usr/local/bin/geckodriver')
    
    driver = None
    try:
        driver = webdriver.Firefox(service=service, options=options)
        # افزایش زمان انتظار برای لود شدن کامل اولیه
        driver.set_page_load_timeout(30)
        driver.get('https://dexscreener.com/')
        
        # استفاده از Explicit Wait به جای sleep ثابت
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ds-dex-table')))
        
        # اسکرول به پایین برای اطمینان از لود شدن دیتا
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3) 

        source_site = driver.page_source
        
        # استخراج لینک‌ها (کنتراکت‌ها)
        t = r'href="(/[^"]*/[a-zA-Z0-9]+)"'
        v = re.findall(t, source_site)
        # فیلتر کردن لینک‌هایی که احتمالاً آدرس توکن هستند
        ls_con = [i.split('/')[-1] for i in v if len(i) > 20]

        # استخراج داده‌های جدول
        data_table = driver.find_element(By.CSS_SELECTOR, '.ds-dex-table')
        data_text = data_table.text
        data_list = data_text.splitlines()
        
        titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
        
        # پاکسازی داده‌ها (منطق فیلتر شما اصلاح شد)
        dl_list = ['750', '3', '210', '880', '780', '150', 'WP', '720', 'V4', '20', '50', '70', '60', 'CPMM', '180', '620', '80', '100V3', 'V3', '200', 'V1', '30', 'OOPS', '100', '550', '130', 'CLMM', 'DLMM', '40', '600', '300', 'V2', '500', '110', 'DYN', 'DYN2', '/', '1000', '10', '310', '850', '120', '660', '510', '530']
        
        # فیلتر کردن ردیف‌های نامربوط بر اساس منطق شما
        nd = [item for item in data_list if item not in dl_list and len(item) > 0]
        
        # پیدا کردن شروع داده‌ها (ردیف ۱ معمولا بعد از هدرهاست)
        # توجه: دکس‌اسکرینر داینامیک است، این بخش ممکن است نیاز به تنظیم دستی داشته باشد
        arzha = []
        for i in range(0, len(nd) - 14, 15):
            row = nd[i:i+15]
            arzha.append(row)

        if not arzha:
            print("No data extracted. Table structure might have changed.")
            return

        pd_df = pd.DataFrame(arzha, columns=titles)
        
        # تطبیق آدرس کنتراکت
        pd_df['CONTRACT ADDRESS'] = (ls_con * (len(pd_df) // len(ls_con) + 1))[:len(pd_df)]

        csvname = 'dexscreener.csv'
        pd_df.to_csv(csvname, index=False, encoding='utf-8')
        print(f"CSV generated: {csvname}")

        # ارسال ایمیل
        yag = yagmail.SMTP('dexscreeneramirzamani@gmail.com', 'urcs rehx ttyt hzbv')
        yag.send('amirhosseinzamanifarsi@gmail.com', 'DexScreener Report Update', 
                 f"Report generated at {time.ctime()}", attachment=csvname)
        print('Email sent successfully.')

    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        if driver:
            driver.quit()
            print("Driver session closed.")

# اجرای زمان‌بندی
schedule.every(5).minutes.do(timing) # پیشنهاد: زمان را به ۵ دقیقه افزایش دهید تا تداخل ایجاد نشود

print("Scheduler started. Waiting for next run...")
while True:
    schedule.run_pending()
    time.sleep(1)
