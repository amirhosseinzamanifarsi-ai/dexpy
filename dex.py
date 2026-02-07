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
    
    # ۱. راه‌اندازی نمایشگر مجازی برای مخفی کردن مرورگر در لینوکس
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    page = None
    try:
        # تنظیمات مرورگر برای عبور از آنتی‌بات
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-gpu')
        
        # اتصال به مرورگر
        page = ChromiumPage(co)
        
        print("🚀 در حال ورود به DexScreener...")
        page.get('https://dexscreener.com/')
        
        # ۲. سیستم هوشمند عبور از تیک "Verify you are human"
        found_table = False
        for i in range(12):  # ۱۲ تلاش (مجموعاً ۶۰ ثانیه)
            title = page.title.lower()
            
            # اگر هنوز در صفحه کپچا هستیم
            if "just a moment" in title or "attention required" in title or "verify" in title:
                print(f"⚠️ کپچا مشاهده شد (تلاش {i+1}). در حال تلاش برای کلیک...")
                
                # تلاش برای پیدا کردن دکمه در تمام لایه‌ها (Shadow DOM)
                # کلیک با پارامتر by_js=False برای شبیه‌سازی حرکت فیزیکی موس
                btn = page.ele('@type=checkbox', timeout=2) or page.ele('text:Verify you are human', timeout=2)
                
                if btn:
                    print("🔘 دکمه تیک پیدا شد! کلیک فیزیکی انجام می‌شود...")
                    btn.click(by_js=False)
                    time.sleep(5)
            
            # بررسی اینکه آیا جدول لود شده یا نه
            if page.ele('.ds-dex-table', timeout=2):
                print("✅ با موفقیت از سد کپچا عبور کردیم!")
                found_table = True
                break
            
            time.sleep(5)

        # ۳. استخراج داده‌ها در صورت موفقیت
        if found_table:
            print("📊 در حال استخراج اطلاعات جدول...")
            time.sleep(3) # فرصت برای لود کامل قیمت‌ها
            
            table_element = page.ele('.ds-dex-table')
            data_list = table_element.text.splitlines()

            # استخراج آدرس کنتراکت‌ها از لینک‌ها
            links = page.eles('tag:a')
            contracts = []
            for link in links:
                try:
                    href = link.attr('href')
                    if href and '/' in href:
                        part = href.split('/')[-1]
                        if len(part) > 30: # معمولاً آدرس‌های سولانا یا اتریوم بلند هستند
                            contracts.append(part)
                except:
                    continue

            # ۴. فیلتر و تمیزکاری داده‌ها
            titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
            dl_list = ['750', '3', '210', '880', '780', 'WP', 'V4', 'V3', 'V2', '/', 'CPMM', 'CLMM', 'V1', '100', '200']
            
            clean_data = [x for x in data_list if x not in dl_list and len(x) > 0]
            
            rows = []
            for i in range(0, len(clean_data) - 14, 15):
                rows.append(clean_data[i:i+15])

            if rows:
                df = pd.DataFrame(rows, columns=titles)
                
                # اضافه کردن ستون کنتراکت
                if contracts:
                    extended_contracts = (contracts * (len(df)//len(contracts)+1))[:len(df)]
                    df['CONTRACT ADDRESS'] = extended_contracts
                
                # ۵. ذخیره و ارسال
                csv_name = 'dex_report_final.csv'
                df.to_csv(csv_name, index=False, encoding='utf-8-sig')
                print(f"✅ فایل با {len(df)} ردیف آماده شد.")

                try:
                    yag = yagmail.SMTP('dexscreeneramirzamani@gmail.com', 'urcs rehx ttyt hzbv')
                    yag.send(
                        to='amirhosseinzamanifarsi@gmail.com',
                        subject=f'DexScreener Report {time.strftime("%H:%M")}',
                        contents='گزارش استخراج شده پیوست گردید.',
                        attachments=csv_name
                    )
                    print("✉️ ایمیل با موفقیت ارسال شد.")
                except Exception as e:
                    print(f"❌ خطا در ارسال ایمیل: {e}")
            else:
                print("⚠️ دیتایی برای پردازش یافت نشد.")
        else:
            print("❌ شکست در عبور از کپچا. اسکرین‌شات جدید گرفته شد.")
            page.get_screenshot('captcha_failed.png')

    except Exception as e:
        print(f"❌ خطای سیستم: {e}")
    
    finally:
        if page:
            page.quit()
        display.stop()
        print("--- پایان عملیات و آزادسازی منابع ---")

# زمان‌بندی اجرای خودکار هر ۱۰ دقیقه
schedule.every(10).minutes.do(timing)

# اجرای بار اول بلافاصله
timing()

while True:
    schedule.run_pending()
    time.sleep(1)
