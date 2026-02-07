import os
import time
import re
import pandas as pd
import yagmail
import schedule
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display

def timing():
    print(f"\n--- شروع تسک: {time.strftime('%H:%M:%S')} ---")
    
    # راه‌اندازی نمایشگر مجازی برای سرور لینوکس
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # راه‌اندازی مرورگر با قابلیت عبور از کلودفلر
        # تنظیم ورژن به صورت دستی اگر خودکار عمل نکرد
        driver = uc.Chrome(options=options,version_main=144 ,headless=False) # در UC حالت headless باید False باشد تا XVFB کار کند
        
        print("🌐 در حال باز کردن DexScreener...")
        driver.get('https://dexscreener.com/')
        
        # انتظار برای لود شدن جدول (حداکثر ۴۰ ثانیه)
        wait = WebDriverWait(driver, 40)
        table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ds-dex-table")))
        
        print("✅ جدول با موفقیت لود شد.")
        time.sleep(5) # زمان اضافی برای تکمیل لودینگ

        # استخراج داده‌ها
        source_site = driver.page_source
        data_text = table.text
        data_list = data_text.splitlines()

        # استخراج آدرس کنتراکت‌ها با Regex
        links = re.findall(r'href="/([^"]+)"', source_site)
        contracts = [l.split('/')[-1] for l in links if len(l.split('/')[-1]) > 30]

        titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
        
        # فیلتر کردن کلمات نامربوط
        dl_list = ['750', '3', '210', '880', '780', 'WP', 'V4', 'V3', 'V2', '/', 'CPMM', 'CLMM']
        clean_data = [x for x in data_list if x not in dl_list and len(x) > 0]

        rows = []
        for i in range(0, len(clean_data) - 14, 15):
            rows.append(clean_data[i:i+15])

        if rows:
            df = pd.DataFrame(rows, columns=titles)
            # تطبیق کنتراکت‌ها
            if contracts:
                df['CONTRACT ADDRESS'] = (contracts * (len(df)//len(contracts)+1))[:len(df)]
            
            csv_name = 'dex_report.csv'
            df.to_csv(csv_name, index=False, encoding='utf-8-sig')
            print(f"✅ فایل با {len(df)} ردیف ساخته شد.")

            # ارسال ایمیل
            try:
                yag = yagmail.SMTP('dexscreeneramirzamani@gmail.com', 'urcs rehx ttyt hzbv')
                yag.send(
                    to='amirhosseinzamanifarsi@gmail.com',
                    subject='DexScreener Update',
                    contents=f'گزارش جدید در ساعت {time.strftime("%H:%M")} استخراج شد.',
                    attachments=csv_name
                )
                print("✉️ ایمیل با موفقیت ارسال شد.")
            except Exception as e:
                print(f"❌ خطا در ارسال ایمیل: {e}")
        else:
            print("⚠️ دیتای معتبری یافت نشد. اسکرین‌شات چک شود.")
            driver.save_screenshot("no_data.png")

    except Exception as e:
        print(f"❌ خطای بحرانی: {str(e)}")
        if driver:
            driver.save_screenshot("error_debug.png")
    
    finally:
        if driver:
            driver.quit()
        display.stop()
        print("--- پایان و آزادسازی منابع ---")

# اجرای برنامه هر ۱۰ دقیقه
schedule.every(10).minutes.do(timing)

# تست اول بلافاصله بعد از اجرا
timing()

while True:
    schedule.run_pending()
    time.sleep(1)
