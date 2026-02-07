from DrissionPage import ChromiumPage, ChromiumOptions
from pyvirtualdisplay import Display
import pandas as pd
import yagmail
import schedule
import time
import re
import os

def timing():
    print(f"\n--- شروع تسک هوشمند: {time.strftime('%H:%M:%S')} ---")
    
    # ۱. راه‌اندازی نمایشگر مجازی
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    page = None
    try:
        # تنظیمات پیشرفته برای عبور از شناسایی
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-gpu')
        # جعل هویت مرورگر برای اینکه سایت فکر کند شما ویندوز ۱۰ هستید
        co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        page = ChromiumPage(co)
        
        print("🌐 در حال فراخوانی DexScreener...")
        page.get('https://dexscreener.com/')
        
        # ۲. مکانیزم پیشرفته عبور از تیک Cloudflare
        is_passed = False
        for i in range(15):  # تلاش برای عبور (حدود ۷۵ ثانیه)
            time.sleep(5)
            title = page.title.lower()
            
            # اگر در صفحه کپچا هستیم
            if "just a moment" in title or "verify" in title or "attention required" in title:
                print(f"🔄 تلاش {i+1}: سد امنیتی شناسایی شد. در حال جستجوی تیک...")
                
                # جستجوی تیک در Shadow DOM و لایه‌های مخفی
                # استفاده از متد ele که در DrissionPage لایه‌های داخلی را هم می‌بیند
                btn = page.ele('@type=checkbox', timeout=2) or \
                      page.ele('text:Verify you are human', timeout=2) or \
                      page.ele('.ctp-checksum-container', timeout=2)
                
                if btn:
                    print("🔘 دکمه تیک پیدا شد! کلیک فیزیکی (Physical Click) انجام می‌شود...")
                    btn.click(by_js=False) 
                    time.sleep(10) # صبر برای تایید پس از کلیک
            
            # بررسی اینکه آیا به محتوای اصلی رسیدیم
            if page.ele('.ds-dex-table', timeout=3):
                print("✅ تیک زده شد و جدول لود گردید!")
                is_passed = True
                break
        
        # ۳. استخراج داده‌ها
        if is_passed:
            print("📊 در حال استخراج و پردازش داده‌های جدول...")
            time.sleep(5)
            
            table_element = page.ele('.ds-dex-table')
            data_text = table_element.text
            data_list = data_text.splitlines()

            # استخراج کنتراکت‌ها از لینک‌ها
            links = page.eles('tag:a')
            contracts = []
            for l in links:
                href = l.attr('href')
                if href and '/' in href:
                    part = href.split('/')[-1]
                    if len(part) > 30:
                        contracts.append(part)

            # ۴. تمیزکاری و فیلتر (منطق خودت)
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
                
                # ذخیره در فایل
                csv_file = 'dex_report_final.csv'
                df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                print(f"📝 فایل با {len(df)} ردیف ساخته شد.")

                # ۵. ارسال ایمیل
                try:
                    yag = yagmail.SMTP('dexscreeneramirzamani@gmail.com', 'urcs rehx ttyt hzbv')
                    yag.send(
                        to='amirhosseinzamanifarsi@gmail.com',
                        subject=f'Dex Report - {time.strftime("%H:%M")}',
                        contents='گزارش نهایی استخراج شد.',
                        attachments=csv_file
                    )
                    print("✉️ ایمیل با موفقیت ارسال شد.")
                except Exception as mail_err:
                    print(f"❌ خطا در ارسال ایمیل: {mail_err}")
            else:
                print("⚠️ جدول یافت شد اما خالی بود.")
        else:
            print("❌ شکست در عبور از تیک کپچا پس از ۱۵ تلاش.")
            page.get_screenshot('final_status.png')
            print("📸 اسکرین‌شات نهایی ذخیره شد: final_status.png")

    except Exception as e:
        print(f"❌ خطای بحرانی سیستم: {e}")
    
    finally:
        if page:
            page.quit()
        display.stop()
        print("--- پایان عملیات ---")

# زمان‌بندی ۱۰ دقیقه‌ای
schedule.every(10).minutes.do(timing)

# اجرای اول برای تست
timing()

while True:
    schedule.run_pending()
    time.sleep(1)
