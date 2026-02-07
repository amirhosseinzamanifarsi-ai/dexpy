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
    
    # ۱. راه‌اندازی نمایشگر مجازی (حیاتی برای لینوکس)
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    page = None
    try:
        # تنظیمات مرورگر
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-gpu')
        
        # حالت Headless را False می‌گذاریم چون Display داریم (این برای عبور از کلودفلر بهتر است)
        page = ChromiumPage(co)
        
        print("🚀 در حال ورود به سایت...")
        page.get('https://dexscreener.com/')
        
        # ۲. سیستم عبور از Cloudflare (اصلاح شده)
        # به جای صرفاً صبر کردن، چک می‌کنیم اگر دکمه‌ای هست کلیک کند
        for i in range(3):
            if "Just a moment" in page.title or "Access denied" in page.title:
                print(f"⚠️ در حال تلاش برای عبور از امنیت (تلاش {i+1})...")
                time.sleep(5)
                
                # تلاش برای پیدا کردن دکمه Cloudflare در Shadow DOM
                # این دستورات سعی می‌کنند چک‌باکس را پیدا و کلیک کنند
                if page.ele('@type=checkbox', timeout=2):
                    print("🔘 دکمه کپچا پیدا شد. کلیک می‌کنیم...")
                    page.ele('@type=checkbox').click()
                elif page.ele('text:Verify you are human', timeout=2):
                    page.ele('text:Verify you are human').click()
                
                time.sleep(5)
            else:
                break
        
        # ۳. انتظار برای جدول (دستور اصلاح شده برای رفع ارور شما)
        print("⏳ منتظر لود شدن جدول...")
        
        # *** تغییر مهم: استفاده از ele_display به جای ele_appearing ***
        if page.wait.ele_display('.ds-dex-table', timeout=40):
            print("✅ جدول پیدا شد! در حال استخراج...")
            
            # کمی اسکرول برای لود شدن کامل دیتا
            page.scroll.down(500)
            time.sleep(2)

            # ۴. استخراج داده‌ها
            table_text = page.ele('.ds-dex-table').text
            data_list = table_text.splitlines()

            # استخراج لینک‌ها برای کنتراکت
            links = page.eles('tag:a')
            contracts = []
            for link in links:
                try:
                    href = link.attr('href')
                    if href and '/' in href:
                        part = href.split('/')[-1]
                        if len(part) > 30: # تشخیص آدرس کنتراکت
                            contracts.append(part)
                except:
                    continue

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
                    # منطق تکرار کنتراکت‌ها برای پر کردن جدول
                    extended_contracts = (contracts * (len(df)//len(contracts)+1))[:len(df)]
                    df['CONTRACT ADDRESS'] = extended_contracts
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
                print("⚠️ جدول خالی بود. احتمالا ساختار سایت عوض شده.")
                page.get_screenshot('empty_table.png')

        else:
            print("❌ هنوز پشت کپچا هستیم یا سایت لود نشد.")
            # گرفتن عکس برای بررسی وضعیت
            page.get_screenshot('cloudflare_stuck.png')
            print("📸 اسکرین‌شات وضعیت ذخیره شد: cloudflare_stuck.png")

    except Exception as e:
        print(f"❌ خطا: {e}")
        
    finally:
        # بستن تمیز
        if page:
            page.quit()
        if display:
            display.stop()
        print("--- پایان عملیات ---")

# اجرا
timing()

# اسکژول
schedule.every(10).minutes.do(timing)
while True:
    schedule.run_pending()
    time.sleep(1)
