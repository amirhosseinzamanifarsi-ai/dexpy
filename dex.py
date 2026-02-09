from DrissionPage import ChromiumPage, ChromiumOptions
from pyvirtualdisplay import Display
import pandas as pd
import yagmail
import schedule
import time
import os

# ==============================================================================
# 🔐 تنظیمات پروکسی جدید (جایگزین شد)
# ==============================================================================
PROXY_IP = "107.172.163.27"
PROXY_PORT = "6543"
PROXY_USER = "yahfeawc"
PROXY_PASS = "37tdqv7zdv4b"
# ==============================================================================

def timing():
    print(f"\n--- تلاش با پروکسی جدید: {time.strftime('%H:%M:%S')} ---")
    
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    page = None
    try:
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        
        # استفاده از فرمت پروکسی برای درایور
        proxy_full = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_IP}:{PROXY_PORT}"
        co.set_proxy(proxy_full)
        
        # جعل هویت برای عبور از کلودفلر
        co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        page = ChromiumPage(co)
        
        print(f"🌐 اتصال به دکس‌اسکرینر از طریق آی‌پی آمریکا ({PROXY_IP})...")
        page.get('https://dexscreener.com/', retry=3, interval=5)
        
        # مکانیزم عبور از لایه امنیتی
        is_passed = False
        for i in range(12):
            time.sleep(5)
            
            # ۱. چک کردن لود شدن جدول
            if page.ele('.ds-dex-table', timeout=2):
                print("✅ پیروزی! جدول لود شد.")
                is_passed = True
                break
            
            # ۲. هندل کردن تیک کپچا
            if "verify" in page.title.lower() or "just a moment" in page.title.lower():
                print(f"⚠️ کپچا شناسایی شد (تلاش {i+1}). در حال کلیک...")
                btn = page.ele('@type=checkbox', timeout=2) or page.ele('text:Verify you are human', timeout=2)
                if btn:
                    btn.click(by_js=False)
                    time.sleep(5)
            
            # ۳. اگر صفحه در دسترس نبود (ERR_...)
            if "This site can't be reached" in page.html:
                print("❌ ارور: پروکسی هنوز متصل نیست یا پروتکل را قبول نمی‌کند.")
                break

        if is_passed:
            print("📊 شروع استخراج داده‌ها...")
            table = page.ele('.ds-dex-table')
            data_list = table.text.splitlines()

            # استخراج کنتراکت‌ها
            links = page.eles('tag:a')
            contracts = [l.attr('href').split('/')[-1] for l in links if l.attr('href') and len(l.attr('href').split('/')[-1]) > 30]

            # فیلتر و ساخت CSV
            titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
            dl_list = ['750', '3', '210', '880', '780', 'WP', 'V4', 'V3', 'V2', '/', 'CPMM', 'CLMM', 'V1', '100', '200']
            clean_data = [x for x in data_list if x not in dl_list and len(x) > 0]
            
            rows = [clean_data[x:x+15] for x in range(0, len(clean_data)-14, 15)]
            
            if rows:
                df = pd.DataFrame(rows, columns=titles)
                if contracts:
                    df['CONTRACT ADDRESS'] = (contracts * (len(df)//len(contracts)+1))[:len(df)]
                
                csv_file = 'dex_report.csv'
                df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                
                # ارسال ایمیل
                yag = yagmail.SMTP('dexscreeneramirzamani@gmail.com', 'urcs rehx ttyt hzbv')
                yag.send(to='amirhosseinzamanifarsi@gmail.com', subject='Report with Proxy', attachments=csv_file)
                print("📧 ایمیل ارسال شد.")
            else:
                print("⚠️ جدول پیدا شد اما خالی بود.")
        else:
            print("❌ شکست در عبور از امنیت.")
            page.get_screenshot('proxy_debug.png')

    except Exception as e:
        print(f"❌ خطا: {e}")
    finally:
        if page: page.quit()
        display.stop()

# اجرا
timing()
