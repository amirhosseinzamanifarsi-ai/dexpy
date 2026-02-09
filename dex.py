from DrissionPage import ChromiumPage, ChromiumOptions
from pyvirtualdisplay import Display
import pandas as pd
import yagmail
import schedule
import time
import os

# --- تنظیمات ---
# اگر تور را نصب کردی، این را True بگذار. اگر می‌خواهی بدون پروکسی تست کنی False کن.
USE_TOR = True 
EMAIL_USER = 'dexscreeneramirzamani@gmail.com'
EMAIL_PASS = 'urcs rehx ttyt hzbv'
RECIPIENT = 'amirhosseinzamanifarsi@gmail.com'

def timing():
    print(f"\n--- شروع تسک جدید: {time.strftime('%H:%M:%S')} ---")
    
    # ۱. مدیریت نمایشگر مجازی
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    page = None
    try:
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        
        # ۲. تنظیم پروکسی (در صورت فعال بودن تور)
        if USE_TOR:
            print("🛡️ استفاده از پروکسی Tor (127.0.0.1:9050)")
            co.set_proxy("socks5://127.0.0.1:9050")
        
        # جعل هویت حرفه‌ای
        co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
        
        page = ChromiumPage(co)
        
        print("🌐 در حال فراخوانی DexScreener...")
        page.get('https://dexscreener.com/', retry=3, interval=10)
        
        # ۳. سیستم عبور از کپچا
        found_table = False
        for i in range(15):
            time.sleep(5)
            
            # الف: چک کردن وجود جدول
            if page.ele('.ds-dex-table', timeout=2):
                print("✅ جدول با موفقیت لود شد!")
                found_table = True
                break
            
            # ب: شناسایی و کلیک روی تیک کپچا
            title = page.title.lower()
            if "verify" in title or "just a moment" in title:
                print(f"⚠️ کپچا شناسایی شد (تلاش {i+1}). در حال کلیک...")
                # جستجوی عمیق برای دکمه تیک
                btn = page.ele('@type=checkbox', timeout=2) or \
                      page.ele('text:Verify you are human', timeout=2)
                
                if btn:
                    print("👆 کلیک فیزیکی روی دکمه انجام شد.")
                    btn.click(by_js=False)
                    time.sleep(8)
            
            if i == 7: # رفرش میانی برای باز شدن گره احتمالی
                print("🔄 رفرش صفحه...")
                page.refresh()

        # ۴. استخراج و پردازش داده‌ها
        if found_table:
            print("📊 در حال جمع‌آوری اطلاعات...")
            time.sleep(5) # صبر برای آپدیت نهایی قیمت‌ها
            
            # اسکرول برای لود شدن همه ردیف‌ها
            page.scroll.down(1000)
            
            table_element = page.ele('.ds-dex-table')
            data_list = table_element.text.splitlines()

            # استخراج آدرس‌های کنتراکت
            links = page.eles('tag:a')
            contracts = []
            for l in links:
                try:
                    href = l.attr('href')
                    if href and '/' in href:
                        part = href.split('/')[-1]
                        if len(part) > 30: contracts.append(part)
                except: pass

            # فیلتر و تمیزکاری
            titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
            dl_list = ['750', '3', '210', '880', '780', 'WP', 'V4', 'V3', 'V2', '/', 'CPMM', 'CLMM', 'V1', '100', '200']
            clean_data = [x for x in data_list if x not in dl_list and len(x) > 0]
            
            rows = []
            for i in range(0, len(clean_data) - 14, 15):
                rows.append(clean_data[i:i+15])

            if rows:
                df = pd.DataFrame(rows, columns=titles)
                # اضافه کردن کنتراکت‌ها
                if contracts:
                    # حذف تکراری‌ها و مچ کردن
                    unique_contracts = list(dict.fromkeys(contracts))
                    extended_contracts = (unique_contracts * (len(df)//len(unique_contracts)+1))[:len(df)]
                    df['CONTRACT ADDRESS'] = extended_contracts
                
                csv_name = 'dex_final_report.csv'
                df.to_csv(csv_name, index=False, encoding='utf-8-sig')
                print(f"💾 فایل با {len(df)} ردیف ذخیره شد.")

                # ۵. ارسال ایمیل
                try:
                    yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASS)
                    yag.send(
                        to=RECIPIENT,
                        subject=f'DexScreener Report - {time.strftime("%H:%M")}',
                        contents='گزارش استخراج شده پیوست شد.',
                        attachments=csv_name
                    )
                    print("📧 ایمیل با موفقیت ارسال شد.")
                except Exception as e:
                    print(f"❌ خطا در ارسال ایمیل: {e}")
            else:
                print("⚠️ جدول پیدا شد اما ردیفی استخراج نشد.")
        else:
            print("❌ شکست در عبور از لایه‌های امنیتی.")
            page.get_screenshot('final_failed.png')

    except Exception as e:
        print(f"❌ خطای سیستمی: {e}")
    finally:
        if page: page.quit()
        display.stop()
        print("--- پایان عملیات و آزادسازی رم ---")

# --- تنظیم زمان‌بندی ۱۰ دقیقه‌ای ---
schedule.every(10).minutes.do(timing)

# اجرای بار اول بلافاصله
timing()

while True:
    schedule.run_pending()
    time.sleep(1)
