from DrissionPage import ChromiumPage, ChromiumOptions
from pyvirtualdisplay import Display
import pandas as pd
import yagmail
import schedule
import time
import os

# ==============================================================================
# 🔐 تنظیم مجدد پروکسی با فرمت دقیق
# ==============================================================================
# اگر پروکسی شما SOCKS5 است، به جای http بنویسید socks5
PROXY_ADDRESS = "31.59.20.176:6754"
PROXY_USER = "yahfeawc"
PROXY_PASS = "37tdqv7zdv4b"
# ==============================================================================

def timing():
    print(f"\n--- تلاش مجدد با متد جدید پروکسی: {time.strftime('%H:%M:%S')} ---")
    
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    page = None
    try:
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        
        # متد جدید برای ست کردن پروکسی (جلوگیری از ارور NO_SUPPORTED_PROXIES)
        # ما پروکسی را به صورت مستقیم و بدون پیشوند http در اینجا تست می‌کنیم
        co.set_proxy(f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_ADDRESS}")
        
        co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
        
        page = ChromiumPage(co)
        
        print(f"🌐 در حال تست اتصال به دکس‌اسکرینر با آی‌پی {PROXY_ADDRESS}...")
        
        # افزایش زمان انتظار برای لود شدن با پروکسی
        page.get('https://dexscreener.com/', retry=3, interval=5)
        
        # چک کردن وضعیت صفحه
        if "This site can't be reached" in page.html or page.title == "":
            print("❌ ارور شبکه: پروکسی متصل نشد یا پروتکل آن اشتباه است.")
            # یک تست: اگر پروتکل HTTP نبود، SOCKS5 را امتحان می‌کنیم
            print("🔄 در حال تلاش مجدد با پروتکل SOCKS5...")
            page.quit()
            co.set_proxy(f"socks5://{PROXY_USER}:{PROXY_PASS}@{PROXY_ADDRESS}")
            page = ChromiumPage(co)
            page.get('https://dexscreener.com/')

        # بررسی موفقیت
        if page.ele('.ds-dex-table', timeout=30):
            print("✅ ایول! بالاخره وارد شدیم. در حال استخراج...")
            # ... (بقیه کدهای استخراج و ایمیل که قبلاً داشتی) ...
            table = page.ele('.ds-dex-table')
            # [ادامه کدهای استخراج مشابه قبل]
            print(f"تایتل صفحه: {page.title}")
        else:
            print("❌ هنوز وارد جدول نشدیم.")
            page.get_screenshot('proxy_final_test.png')

    except Exception as e:
        print(f"❌ ارور: {e}")
    finally:
        if page: page.quit()
        display.stop()

timing()
