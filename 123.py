import os
import schedule
import time
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime

def timing():
    try:
        # ░▒▓ اصلاحات حیاتی برای سرور لینوکس ▓▒░
        os.environ['PATH'] = '/usr/local/bin:' + os.environ['PATH']  # اضافه کردن مسیر درایور به PATH
        
        options = Options()
        options.binary_location = '/usr/bin/firefox'  # مسیر فایرفاکس
        options.add_argument("--headless=new")  # حالت بدون نمایش
        
        service = Service(
            executable_path='/usr/local/bin/geckodriver',  # مسیر مطلق درایور
            service_args=['--log', 'debug']  # فعال‌سازی لاگ کامل
        )
        
        # ░▒▓ اجرای کراولر ▓▒░
        driver = webdriver.Firefox(service=service, options=options)
        driver.get("https://dexscreener.com/")
        
        # ... (بقیه کدهای شما بدون تغییر)
        
        driver.quit()
        print(f"{datetime.now()} - عملیات موفق ✅")
        
    except Exception as e:
        print(f"❌ خطای جدی: {str(e)}")
        if 'driver' in locals():
            driver.quit()

# ░▒▓ زمان‌بندی اجرا ▓▒░
schedule.every(10).minutes.do(timing)

while True:
    schedule.run_pending()
    time.sleep(1)
