from DrissionPage import ChromiumPage, ChromiumOptions
from pyvirtualdisplay import Display
import pandas as pd
import yagmail
import schedule
import time
import re
import os

def timing():
    print(f"\n--- شروع تسک: {time.strftime('%H:%M:%S')} ---")
    
    # ۱. راه‌اندازی نمایشگر مجازی
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    page = None
    try:
        # تنظیمات مرورگر
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-gpu')
        # نکته: حالت Headless را فعال نکنید، Display کار مخفی‌سازی را انجام می‌دهد
        
        page = ChromiumPage(co)
        
        print("🚀 در حال ورود به سایت...")
        page.get('https://dexscreener.com/')
        
        # ۲. تلاش برای عبور از کلودفلر (Cloudflare Bypass)
        # به جای ۳ بار، ۱۰ بار چک می‌کنیم چون گاهی طول می‌کشد
        for i in range(10):
            title = page.title.lower()
            if "just a moment" in title or "access denied" in title or "attention required" in title:
                print(f"⚠️ در حال تلاش برای عبور از امنیت (تلاش {i+1}/10)...")
                
                # تلاش برای پیدا کردن و کلیک روی دکمه کپچا
                # این دستور در تمام فریم‌ها و ShadowRootها می‌گردد
                if page.ele('@type=checkbox', timeout=2):
                    print("🔘 دکمه چک‌باکس پیدا شد! کلیک می‌کنیم...")
                    page.ele('@type=checkbox').click()
                elif page.ele('text:Verify you are human', timeout=2):
                    print("🔘 متن Verify پیدا شد! کلیک می‌کنیم...")
                    page.ele('text:Verify you are human').click()
                
                time.sleep(5)
            else:
                print("✅ به نظر می‌رسد از سد امنیتی عبور کردیم.")
                break
        
        # ۳. انتظار برای جدول (رفع ارور قبلی شما)
        print("⏳ منتظر لود شدن جدول (۶۰ ثانیه)...")
        
        # *** اصلاح شده: استفاده از متد صحیح wait.ele_displayed ***
        # اگر این متد در نسخه شما نبود، از page.ele استفاده می‌کنیم که خودش ویت دارد
        
        if page.ele('.ds-dex-table', timeout=60):
            print("✅ جدول پیدا شد! شروع استخراج...")
            
            # اسکرول
            page.scroll.down(600)
            time.sleep(3)

            # ۴. استخراج
            table_element = page.ele('.ds-dex-table')
            data_list = table_element.text.splitlines()

            # استخراج لینک‌ها
            links = page.eles('tag:a')
            contracts = []
            for link in links:
                try:
                    href = link.attr('href')
                    if href and '/' in href:
                        part = href.split('/')[-1]
                        if len(part) > 30: 
                            contracts.append(part)
                except:
                    pass

            # ۵. پردازش (فیلتر کردن)
            titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
            dl_list = ['750', '3', '210', '880', '780', 'WP', 'V4', 'V3', 'V2', '/', 'CPMM', 'CLMM', 'V1', '100', '200']
            
            clean_data = [x for x in data_list if x not in dl_list and len(x) > 0]
            
            rows = []
            for i in range(0, len(clean_data) - 14, 15):
                rows.append(clean_data[i:i+15])

            if rows:
                df = pd.DataFrame(rows, columns=titles)
                
                if contracts:
                    extended_contracts = (contracts * (len(df)//len(contracts)+1))[:len(df)]
                    df['CONTRACT ADDRESS'] = extended_contracts
                else:
                    df['CONTRACT ADDRESS'] = "Not Found"

                csv_name = 'dex_final.csv'
                df.to_csv(csv_name, index=False, encoding='utf-8-sig')
                print(f"📊 فایل CSV با {len(df)} ردیف ساخته شد.")

                # ارسال ایمیل
                try:
                    yag = yagmail.SMTP('dexscreeneramirzamani@gmail.com', 'urcs rehx ttyt hzbv')
                    yag.send(
                        to='amirhosseinzamanifarsi@gmail.com',
                        subject='DexScreener Live Report',
                        contents='گزارش جدید پیوست شد.',
                        attachments=csv_name
                    )
                    print("✉️ ایمیل ارسال شد.")
                except Exception as e:
                    print(f"خطا در ارسال ایمیل: {e}")
            else:
                print("⚠️ جدول دیتا نداشت.")
                page.get_screenshot('empty_data.png')

        else:
            print("❌ تایم‌اوت: جدول لود نشد (هنوز پشت کپچا هستیم).")
            page.get_screenshot('blocked_final.png')

    except Exception as e:
        print(f"❌ خطای کلی: {e}")
        
    finally:
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
