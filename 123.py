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
    """پاکسازی برای جلوگیری از قفل شدن رم سرور"""
    try:
        subprocess.run(["pkill", "-9", "chrome"], stderr=subprocess.DEVNULL)
        subprocess.run(["pkill", "-9", "Xvfb"], stderr=subprocess.DEVNULL)
    except:
        pass

def timing():
    print(f"\n--- شروع تلاش جدید: {time.strftime('%H:%M:%S')} ---")
    clean_env()
    
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    page = None
    try:
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_proxy(PROXY_ADDR)
        co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
        
        page = ChromiumPage(co)
        print("🌐 در حال فراخوانی سایت...")
        page.get('https://dexscreener.com/', retry=3)

        success = False
        # ۱۵ تلاش برای لود شدن کامل (مجموعاً حدود ۳ دقیقه)
        for i in range(20):
            time.sleep(8)
            
            # ۱. بررسی وجود متن‌های کلیدی جدول
            if "Price" in page.html and "Volume" in page.html:
                print("✅ محتوای واقعی جدول رویت شد!")
                # اسکرول به پایین برای لود شدن همه ردیف‌ها
                page.scroll.down(600)
                time.sleep(3)
                success = True
                break
            
            # ۲. هندل کردن کپچاهای احتمالی
            btn = page.ele('@type=checkbox', timeout=1) or \
                  page.ele('text:Verify you are human', timeout=1)
            
            if btn:
                print(f"⚠️ کلیک روی کپچا (تلاش {i+1})")
                btn.click()
                time.sleep(10)
            
            if i == 10:
                print("🔄 رفرش صفحه برای شانس مجدد...")
                page.refresh()

        if success:
            print("📊 در حال استخراج ردیف‌ها...")
            time.sleep(5)
            
            # پیدا کردن المان اصلی محتوا
            main_element = page.ele('.ds-dex-table') or page.ele('tag:main')
            data_list = main_element.text.splitlines()

            # استخراج آدرس کنتراکت‌ها
            links = page.eles('tag:a')
            contracts = [l.attr('href').split('/')[-1] for l in links if l.attr('href') and len(l.attr('href').split('/')[-1]) > 30]

            # ساختار ستون‌ها
            titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
            
            # تمیزکاری داده‌های اضافی
            dl_list = ['WP', 'V4', 'V3', 'V2', '/', 'CPMM', 'CLMM', 'V1']
            clean_data = [x for x in data_list if x not in dl_list and len(x) > 0]
            
            rows = []
            for j in range(0, len(clean_data) - 14, 15):
                rows.append(clean_data[j:j+15])

            if rows:
                df = pd.DataFrame(rows, columns=titles)
                if contracts:
                    unique_c = list(dict.fromkeys(contracts))
                    df['CONTRACT ADDRESS'] = (unique_c * (len(df)//len(unique_c)+1))[:len(df)]
                
                filename = f"report_{time.strftime('%H%M')}.csv"
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                
                # ارسال ایمیل
                try:
                    yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASS)
                    yag.send(to=RECIPIENT, subject=f"DexScreener Data {time.strftime('%H:%M')}", contents="Data Found!", attachments=filename)
                    print(f"📧 ایمیل با {len(rows)} ردیف ارسال شد.")
                    os.remove(filename)
                except Exception as e:
                    print(f"❌ خطا در ایمیل: {e}")
            else:
                print("⚠️ متن صفحه لود شده اما ردیف‌ها قابل تشخیص نیستند.")
                page.get_screenshot('parsing_error.png')
        else:
            print("❌ صفحه باز شد اما دیتای جدول هرگز لود نشد.")
            page.get_screenshot('no_data_rendered.png')

    except Exception as e:
        print(f"❌ خطای سیستم: {e}")
    finally:
        if page: page.quit()
        display.stop()
        print("--- پایان چرخه ---")

# شروع اجرا
timing()
schedule.every(10).minutes.do(timing)
while True:
    schedule.run_pending()
    time.sleep(1)
