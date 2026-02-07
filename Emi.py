import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyvirtualdisplay import Display
import pandas as pd
import yagmail
import schedule
import time
import re
import os

def timing():
    print(f"\n--- شروع تسک: {time.strftime('%H:%M:%S')} ---")
    
    # راه اندازی نمایشگر مجازی برای محیط سرور
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    driver = None
    try:
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # استفاده از undetected-chromedriver برای دور زدن کلودفلر
        driver = uc.Chrome(options=options, headless=True) 
        
        print("🌐 در حال باز کردن سایت...")
        driver.get('https://dexscreener.com/')
        
        # انتظار بیشتر برای لود شدن کامل (سایت سنگین است)
        wait = WebDriverWait(driver, 40)
        
        # تلاش برای پیدا کردن جدول
        try:
            table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".ds-dex-table")))
            print("✅ جدول با موفقیت پیدا شد.")
        except:
            # اگر پیدا نشد، اسکرین شات بگیر تا بفهمیم مشکل چیه (کپچا یا بلاک)
            driver.save_screenshot("error_screen.png")
            print("❌ جدول پیدا نشد. اسکرین‌شات ذخیره شد (error_screen.png)")
            return

        time.sleep(5)
        
        # استخراج داده‌ها
        data_list = table.text.splitlines()
        source = driver.page_source
        
        # استخراج آدرس کنتراکت‌ها
        links = re.findall(r'href="/([^"]+)"', source)
        contracts = [l.split('/')[-1] for l in links if len(l.split('/')[-1]) > 30]

        # سازماندهی داده‌ها
        titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
        
        # فیلتر کردن کلمات مزاحم
        dl_list = ['750', '3', '210', '880', '780', 'WP', 'V4', 'V3', 'V2', '/', 'CPMM']
        clean_data = [x for x in data_list if x not in dl_list and len(x) > 0]

        rows = []
        for i in range(0, len(clean_data) - 14, 15):
            rows.append(clean_data[i:i+15])

        if rows:
            df = pd.DataFrame(rows, columns=titles)
            df['CONTRACT ADDRESS'] = (contracts * (len(df)//len(contracts)+1))[:len(df)]
            
            csv_file = 'dex_report.csv'
            df.to_csv(csv_file, index=False, encoding='utf-8-sig')
            
            # ارسال ایمیل
            yag = yagmail.SMTP('dexscreeneramirzamani@gmail.com', 'urcs rehx ttyt hzbv')
            yag.send('amirhosseinzamanifarsi@gmail.com', 'DexScreener Report', 'گزارش جدید پیوست شد.', attachments=csv_file)
            print("🚀 ایمیل با موفقیت ارسال شد.")
        else:
            print("⚠️ داده‌ها ناقص بودند.")

    except Exception as e:
        print(f"❌ خطای بحرانی: {str(e)}")
        if driver:
            driver.save_screenshot("critical_error.png")
    
    finally:
        if driver:
            driver.quit()
        display.stop()
        print("--- پایان و پاکسازی ---")

# تنظیم زمان‌بندی ۱۰ دقیقه‌ای
schedule.every(10).minutes.do(timing)

# اجرای اولین بار برای تست
timing()

while True:
    schedule.run_pending()
    time.sleep(1)
