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
    
    # ۱. راه‌اندازی نمایشگر مجازی
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        # حذف ورژن هاردکد شده برای جلوگیری از تداخل ورژن‌های بعدی
        print("🚀 در حال باز کردن مرورگر...")
        driver = uc.Chrome(options=options,version_main=144 ,headless=False) 
        
        driver.get('https://dexscreener.com/')
        
        # ۲. صبر استراتژیک برای عبور از Cloudflare
        # دکس‌اسکرینر اول یه تست میگیره، اگه زود بخوایم به جدول دست بزنیم بلاک میشیم
        print("⏳ در حال عبور از لایه‌های امنیتی (۴۰ ثانیه صبر)...")
        time.sleep(40) 

        # ۳. انتظار برای لود شدن جدول
        wait = WebDriverWait(driver, 30)
        try:
            table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ds-dex-table")))
            print("✅ جدول با موفقیت لود شد.")
        except:
            print("❌ جدول لود نشد. احتمالاً کپچا ظاهر شده.")
            driver.save_screenshot("captcha_blocked.png")
            return

        # ۴. استخراج داده‌ها
        source_site = driver.page_source
        data_text = table.text
        data_list = data_text.splitlines()

        # استخراج کنتراکت‌ها
        links = re.findall(r'href="/([^"]+)"', source_site)
        contracts = [l.split('/')[-1] for l in links if len(l.split('/')[-1]) > 30]

        titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
        
        # لیست کلمات مزاحم که ساختار جدول رو بهم می‌ریزن
        dl_list = ['750', '3', '210', '880', '780', 'WP', 'V4', 'V3', 'V2', '/', 'CPMM', 'CLMM', 'V1', '100', '200']
        clean_data = [x for x in data_list if x not in dl_list and len(x) > 0]

        rows = []
        # ۵. دسته‌بندی داده‌ها (با احتیاط برای جلوگیری از بهم ریختگی ستون‌ها)
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

            # ۶. ارسال ایمیل
            try:
                yag = yagmail.SMTP('dexscreeneramirzamani@gmail.com', 'urcs rehx ttyt hzbv')
                yag.send(
                    to='amirhosseinzamanifarsi@gmail.com',
                    subject='DexScreener Update Report',
                    contents=f'گزارش جدید در ساعت {time.strftime("%H:%M")} استخراج شد.',
                    attachments=csv_name
                )
                print("✉️ ایمیل با موفقیت ارسال شد.")
            except Exception as e:
                print(f"❌ خطا در ارسال ایمیل: {e}")
        else:
            print("⚠️ دیتایی یافت نشد. لیست clean_data را بررسی کنید.")

    except Exception as e:
        print(f"❌ خطای بحرانی: {str(e)}")
        if driver:
            driver.save_screenshot("error_debug.png")
    
    finally:
        if driver:
            driver.quit()
        if display:
            display.stop()
        print("--- پایان عملیات و پاکسازی حافظه ---")

# تنظیم زمان‌بندی
schedule.every(10).minutes.do(timing)

# اجرای اول برای تست
timing()

while True:
    schedule.run_pending()
    time.sleep(1)
