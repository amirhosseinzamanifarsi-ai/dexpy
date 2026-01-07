from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
import schedule
import re
import pandas
import yagmail
import time
import os
import logging

# تنظیم لاگ برای ثبت رویدادها
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# مسیر فایل قفل برای جلوگیری از تداخل
LOCK_FILE = "/tmp/dexscraper.lock"
CSV_NAME = "dexscrener.csv"

def remove_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

def create_lock():
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))

def is_running():
    return os.path.exists(LOCK_FILE)

def send_email(file_path):
    try:
        ersal_konandeh = 'dexscreeneramirzamani@gmail.com'
        # نکته امنیتی: پسورد را در متغیر محیطی یا فایل خارجی بگذارید
        password = 'urcs rehx ttyt hzbv' 
        daryaft_konandeh = 'amirhosseinzamanifarsi@gmail.com'
        
        yag = yagmail.SMTP(ersal_konandeh, password)
        yag.send(daryaft_konandeh, 'گزارش DexScreener', file_path)
        logging.info("ایمیل با موفقیت ارسال شد.")
    except Exception as e:
        logging.error(f"خطا در ارسال ایمیل: {e}")

def timing():
    if is_running():
        logging.warning("اسکریپت در حال اجرا است، این دوره رد شد.")
        return
    
    create_lock()
    bot_ertebati = None
    
    try:
        # تنظیمات هدفمند برای سرور (Headless و جلوگیری از مصرف زیاد RAM)
        from selenium.webdriver.firefox.options import Options
        options = Options()
        options.add_argument("--headless")  # اجرا بدون پنجره گرافیکی
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        path_geckodriver = '/usr/local/bin/geckodriver' # معمولا این مسیر استاندارد است
        service_path = Service(path_geckodriver)
        
        bot_ertebati = webdriver.Firefox(service=service_path, options=options)
        bot_ertebati.set_page_load_timeout(30) # تایم‌اوت ۳۰ ثانیه
        
        logging.info("در حال باز کردن سایت...")
        bot_ertebati.get('https://dexscreener.com/')
        
        # صبر برای لود شدن جدول
        time.sleep(5) 
        
        # دریافت کل صفحه برای پارسینگ دقیق‌تر
        source_site = bot_ertebati.page_source
        soup = BeautifulSoup(source_site, 'html.parser')
        
        # استخراج داده‌های متنی
        table_div = soup.find('div', class_='ds-dex-table')
        if not table_div:
            logging.error("جدول پیدا نشد، ممکن است سایت تغییر کرده باشد.")
            return

        data_text = table_div.get_text(separator='\n')
        data_list = data_text.splitlines()
        
        # عناوین
        titles = ['RANK','TOKEN', 'EXCHANGE' ,' FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
        
        # فیلتر کردن لیست خالی و داده‌های اضافی
        # معمولا ۱۲ خط اول هدر هستند
        new_data = [line for line in data_list if line.strip() != '']
        if len(new_data) > 12:
             new_data = new_data[12:]
        
        # لیست فیلتر (کد اصلی شما حفظ شد)
        dl_list = ['90','750','3','210','880','780','150','WP','720','V4','20','50','70','60' ,'CPMM', '180', '620', '80','100V3', 'V3', '200', 'V1' , '30' ,'OOPS', '100', '550','130' ,'CLMM','DLMM', '40', '600', '300', 'V2', '500',  '110', 'DYN' , 'DYN2', '/', '1000' , '10','310', '850', '120', '660', '510', '530']
        
        nd = [item for item in new_data if item not in dl_list]
        
        # ساختاردهی به داده‌ها
        arzha = []
        for ia in range(0, len(nd), 15):
            if ia + 15 <= len(nd):
                arz = nd[ia : ia + 15]
                if len(arz) == 15:
                    arzha.append(arz)
        
        pd = pandas.DataFrame(arzha, columns=titles)
        
        # استخراج لینک‌ها (آدرس قرارداد)
        ls_con = []
        # استخراج لینک‌ها از تگ‌های a
        links = soup.find_all('a', class_='ds-dex-table-row ds-dex-table-row-top')
        for link in links:
            href = link.get('href')
            if href and len(href) > 20:
                ls_con.append(href)
        
        # هماهنگ‌سازی تعداد لینک‌ها با داده‌ها
        if len(pd) > 0:
            if len(pd) == len(ls_con):
                pd['CONTRACT ADDRESS'] = ls_con
            else:
                # اگر تعداد متفاوت بود، تا جای ممکن پر کنید
                pd['CONTRACT ADDRESS'] = ls_con[:len(pd)]
        
        # ذخیره در CSV
        pd.to_csv(CSV_NAME, index=False, encoding='utf-8')
        logging.info(f"فایل {CSV_NAME} ذخیره شد.")
        
        # ارسال ایمیل
        send_email(CSV_NAME)

    except Exception as e:
        logging.error(f"خطا در اجرای تایمینگ: {e}")
    
    finally:
        if bot_ertebati:
            try:
                bot_ertebati.quit()
                logging.info("مرورگر بسته شد.")
            except:
                pass
        remove_lock()

# زمان‌بندی اجرا (هر ۱ دقیقه)
schedule.every(1).minutes.do(timing)

if __name__ == "__main__":
    logging.info("اسکریپت شروع به کار کرد...")
    while True:
        schedule.run_pending()
        time.sleep(1)
