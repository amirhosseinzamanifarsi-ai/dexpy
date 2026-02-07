from DrissionPage import ChromiumPage, ChromiumOptions
from pyvirtualdisplay import Display
import pandas as pd
import yagmail
import schedule
import time
import re
import os

def timing():
    print(f"\n--- شروع تسک جدید: {time.strftime('%H:%M:%S')} ---")
    
    # ۱. راه‌اندازی نمایشگر مجازی (برای اینکه مرورگر فکر کند مانیتور دارد)
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    page = None
    try:
        # تنظیمات مرورگر برای مخفی ماندن کامل
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-gpu')
        
        # نکته کلیدی: در DrissionPage حالت Headless را از خود مرورگر فعال نکنید
        # ما آن را توسط Display (Xvfb) مخفی می‌کنیم. این باعث می‌شود کلودفلر شک نکند.
        
        page = ChromiumPage(co)
        
        print("🚀 در حال ورود به سایت...")
        page.get('https://dexscreener.com/')
        
        # ۲. استراتژی عبور از Cloudflare
        # بررسی می‌کنیم آیا عنوان صفحه "Just a moment" است یا خیر
        attempts = 0
        while attempts < 3:
            if "Just a moment" in page.title or "Attention Required" in page.title:
                print(f"⚠️ پشت دیوارهای امنیتی هستیم (تلاش {attempts+1})...")
                time.sleep(10)
                # اگر دکمه‌ای برای تایید انسان بودن هست، رویش کلیک کن (مخصوص DrissionPage)
                if page.ele('@type=checkbox', timeout=2):
                    page.ele('@type=checkbox').click()
                elif page.ele('text:Verify you are human', timeout=2):
                    page.ele('text:Verify you are human').click()
                attempts += 1
            else:
                break
        
        # ۳. انتظار برای جدول
        print("⏳ منتظر لود شدن جدول...")
        if page.wait.ele_appearing('.ds-dex-table', timeout=40):
            print("✅ جدول پیدا شد!")
            
            # اسکرول کوتاه برای اطمینان از لود دیتا
            page.scroll.down(500)
            time.sleep(2)

            # ۴. استخراج داده‌ها (بسیار سریع‌تر از سلنیوم)
            table_text = page.ele('.ds-dex-table').text
            data_list = table_text.splitlines()

            # استخراج لینک‌ها
            links = page.eles('tag:a')
            contracts = []
            for link in links:
                href = link.attr('href')
                if href and '/' in href:
                    part = href.split('/')[-1]
                    if len(part) > 30: # تشخیص آدرس کنتراکت
                        contracts.append(part)

            # ۵. پردازش داده‌ها (همان منطق کد خودت)
            titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
            dl_list = ['750', '3', '210', '880', '780', 'WP', 'V4', 'V3', 'V2', '/', 'CPMM', 'CLMM', 'V1', '100', '200']
            
            clean_data = [x for x in data_list if x not in dl_list and len(x) > 0]
            
            rows = []
            for i in range(0, len(clean_data) - 14, 15):
                rows.append(clean_data[i:i+15])

            if rows:
                df = pd.DataFrame(rows, columns=titles)
                
                # پر کردن ستون کنتراکت
                if contracts:
                    df['CONTRACT ADDRESS'] = (contracts * (len(df)//len(contracts)+1))[:len(df)]
                else:
                    df['CONTRACT ADDRESS'] = "Not Found"

                csv_name = 'dex_final.csv'
                df.to_csv(csv_name, index=False, encoding='utf-8-sig')
                print(f"📊 فایل CSV با {len(df)} ردیف ساخته شد.")

                # ارسال ایمیل
                yag = yagmail.SMTP('dexscreeneramirzamani@gmail.com', 'urcs rehx ttyt hzbv')
                yag.send(
                    to='amirhosseinzamanifarsi@gmail.com',
                    subject='DexScreener Live Report',
                    contents='گزارش جدید پیوست شد.',
                    attachments=csv_name
                )
                print("✉️ ایمیل ارسال شد.")
            else:
                print("⚠️ جدول خالی بود یا ساختار تغییر کرده است.")
                page.get_screenshot('empty_table.png')

        else:
            print("❌ هنوز پشت کپچا هستیم یا سایت لود نشد.")
            page.get_screenshot('cloudflare_stuck.png')

    except Exception as e:
        print(f"❌ خطا: {e}")
        
    finally:
        # بستن تمیز برای جلوگیری از هنگ کردن سرور
        if page:
            page.quit()
        if display:
            display.stop()
        print("--- پایان عملیات ---")

# اجرا
timing()
schedule.every(10).minutes.do(timing)

while True:
    schedule.run_pending()
    time.sleep(1)
