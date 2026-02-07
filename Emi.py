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
from webdriver_manager.chrome import ChromeDriverManager
from pyvirtualdisplay import Display

def timing():
    print(f"\n--- شروع عملیات در ساعت: {time.strftime('%H:%M:%S')} ---")
    
    # ۱. ایجاد یک نمایشگر مجازی برای فریب دادن سایت و پایداری در لینوکس
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    driver = None
    try:
        # ۲. تنظیمات پیشرفته کروم برای محیط سرور
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # اجرا بدون پنجره
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        # جلوگیری از شناسایی توسط آنتی‌بات
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        # ۳. نصب و اجرای خودکار درایور کروم
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get('https://dexscreener.com/')
        
        # ۴. انتظار هوشمند برای لود شدن جدول
        wait = WebDriverWait(driver, 25)
        table_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.ds-dex-table')))
        
        # اسکرول نرم برای لود شدن همه ردیف‌ها
        driver.execute_script("window.scrollBy(0, 1000);")
        time.sleep(5)

        # ۵. استخراج داده‌ها
        source_site = driver.page_source
        data_text = table_element.text
        data_list = data_text.splitlines()

        # استخراج آدرس‌ها (کنتراکت) از سورس صفحه
        # پیدا کردن الگوهای شبیه آدرس در لینک‌های دکس‌اسکرینر
        v = re.findall(r'href="/([^"]+)"', source_site)
        ls_con = [i.split('/')[-1] for i in v if len(i.split('/')[-1]) > 30]

        titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
        
        # پاکسازی لیست از مقادیر تکراری و اضافی سایت
        dl_list = ['750', '3', '210', '880', '780', '150', 'WP', '720', 'V4', '20', '50', '70', '60', 'CPMM', '180', '620', '80', '100V3', 'V3', '200', 'V1', '30', 'OOPS', '100', '550', '130', 'CLMM', 'DLMM', '40', '600', '300', 'V2', '500', '110', 'DYN', 'DYN2', '/', '1000', '10', '310', '850', '120', '660', '510', '530']
        
        clean_data = [item for item in data_list if item not in dl_list and len(item) > 0]
        
        # سازماندهی در گروه‌های ۱۵ تایی
        rows = []
        for i in range(0, len(clean_data) - 14, 15):
            rows.append(clean_data[i:i+15])

        if not rows:
            print("⚠️ داده‌ای یافت نشد. احتمالا ساختار صفحه تغییر کرده است.")
            return

        df = pd.DataFrame(rows, columns=titles)
        
        # اضافه کردن کنتراکت آدرس‌ها (تطبیق طول لیست)
        if ls_con:
            df['CONTRACT ADDRESS'] = (ls_con * (len(df) // len(ls_con) + 1))[:len(df)]
        else:
            df['CONTRACT ADDRESS'] = "Not Found"

        # ۶. ذخیره فایل
        csv_file = 'dex_report.csv'
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"✅ فایل CSV با {len(df)} ردیف ساخته شد.")

        # ۷. ارسال ایمیل
        sender_email = 'dexscreeneramirzamani@gmail.com'
        app_password = 'urcs rehx ttyt hzbv' # پسورد مخصوص برنامه گوگل
        receiver_email = 'amirhosseinzamanifarsi@gmail.com'
        
        yag = yagmail.SMTP(sender_email, app_password)
        yag.send(
            to=receiver_email,
            subject='DexScreener Daily Report',
            contents=f'گزارش جدید در ساعت {time.strftime("%H:%M")} استخراج شد.',
            attachments=csv_file
        )
        print('✉️ ایمیل با موفقیت ارسال شد.')

    except Exception as e:
        print(f"❌ خطا رخ داد: {str(e)}")
    
    finally:
        # ۸. بستن کامل منابع (بسیار مهم برای جلوگیری از تعلیق سرور)
        if driver:
            driver.quit()
        display.stop()
        print("--- منابع آزاد شدند. در انتظار اجرای بعدی... ---")

# تنظیم اجرای خودکار هر ۱۰ دقیقه (برای جلوگیری از بن شدن IP سرور توسط دکس‌اسکرینر)
schedule.every(10).minutes.do(timing)

print("🚀 اسکریپت با موفقیت شروع شد. برای توقف Ctrl+C را بزنید.")
# اجرای اولین بار بلافاصله پس از اجرا
timing()

while True:
    schedule.run_pending()
    time.sleep(1)
