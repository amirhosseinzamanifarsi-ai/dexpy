from DrissionPage import ChromiumPage, ChromiumOptions
from pyvirtualdisplay import Display
import pandas as pd
import yagmail
import schedule
import time
import os
import subprocess

# --- تنظیمات ---
PROXY_ADDR = "127.0.0.1:8118"
EMAIL_USER = 'dexscreeneramirzamani@gmail.com'
EMAIL_PASS = 'urcs rehx ttyt hzbv'
RECIPIENT = 'amirhosseinzamanifarsi@gmail.com'

def clean_env():
    """پاکسازی پروسه‌های باز مانده برای جلوگیری از پر شدن رم"""
    try:
        subprocess.run(["pkill", "-9", "chrome"], stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-9", "Xvfb"], stderr=subprocess.DEVNULL)
    except:
        pass

def timing():
    print(f"\n--- شروع عملیات: {time.strftime('%H:%M:%S')} ---")
    clean_env()
    
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    page = None
    try:
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_proxy(PROXY_ADDR)
        co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36')
        
        page = ChromiumPage(co)
        print("🌐 در حال باز کردن دکس‌اسکرینر...")
        page.get('https://dexscreener.com/', retry=3)

        success = False
        for i in range(15):
            time.sleep(8)
            
            # ۱. چک کردن لود شدن دیتای واقعی
            if page.ele('.ds-dex-table', timeout=2) or page.ele('tag:main', timeout=2):
                if "RANK" in page.html: # مطمئن شویم متن جدول لود شده
                    print("✅ جدول با محتوا لود شد!")
                    success = True
                    break
            
            # ۲. هندل کردن کپچا (حتی اگر در Iframe باشد)
            print(f"🔄 در حال بررسی موانع (تلاش {i+1})...")
            # جستجو در کل صفحه و فریم‌ها برای تیک کپچا
            btn = page.ele('@type=checkbox', timeout=1) or \
                  page.ele('text:Verify you are human', timeout=1) or \
                  page.ele('.ctp-checkbox-label', timeout=1)
            
            if btn:
                print("👆 دکمه کپچا پیدا شد! کلیک...")
                btn.click()
                time.sleep(10)
            
            # اگر در عنوان صفحه کلمه "Verify" بود و دکمه پیدا نشد، شاید صفحه قفل شده
            if "verify" in page.title.lower() and i > 5:
                print("🔄 رفرش اجباری صفحه...")
                page.refresh()

        if success:
            print("📊 شروع استخراج داده‌ها...")
            time.sleep(5)
            # گرفتن تمام متن بدنه اصلی به عنوان جایگزین اگر جدول مستقیم خوانده نشد
            main_content = page.ele('tag:main').text
            data_list = main_content.splitlines()

            # فیلتر کردن هوشمند
            titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
            rows = []
            # منطق استخراج سطرها بر اساس کلمات کلیدی
            clean_data = [x for x in data_list if len(x) > 0 and x not in titles]
            
            for j in range(0, len(clean_data) - 14, 15):
                rows.append(clean_data[j:j+15])

            if rows:
                df = pd.DataFrame(rows[:100], columns=titles) # فقط ۱۰۰ تا اول
                filename = f"dex_report_{time.strftime('%H%M')}.csv"
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                
                # ارسال ایمیل
                yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASS)
                yag.send(to=RECIPIENT, subject=f"Dex Report {time.strftime('%H:%M')}", attachments=filename)
                print(f"📧 ایمیل با موفقیت ارسال شد. ({len(rows)} ردیف)")
                os.remove(filename)
            else:
                print("⚠️ محتوا لود شد اما سطرها قابل تفکیک نبودند.")
        else:
            print("❌ متاسفانه وارد سایت شدیم ولی دیتا لود نشد.")
            page.get_screenshot('last_error_view.png')

    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
    finally:
        if page: page.quit()
        display.stop()
        print("--- اتمام چرخه ---")

# اجرا
timing()
schedule.every(10).minutes.do(timing)
while True:
    schedule.run_pending()
    time.sleep(1)
