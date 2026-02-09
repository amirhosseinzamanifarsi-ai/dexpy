from DrissionPage import ChromiumPage, ChromiumOptions
from pyvirtualdisplay import Display
import pandas as pd
import yagmail
import schedule
import time
import os

# --- تنظیمات اولیه ---
USE_TOR = True 
EMAIL_USER = 'dexscreeneramirzamani@gmail.com'
EMAIL_PASS = 'urcs rehx ttyt hzbv'
RECIPIENT = 'amirhosseinzamanifarsi@gmail.com'

def timing():
    print(f"\n--- شروع چرخه استخراج: {time.strftime('%H:%M:%S')} ---")
    
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    page = None
    try:
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        
        if USE_TOR:
            print("🛡️ اتصال از طریق شبکه Tor...")
            co.set_proxy("socks5://127.0.0.1:9050")
        
        co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
        
        page = ChromiumPage(co)
        page.get('https://dexscreener.com/', retry=3, interval=15)
        
        # ۱. تلاش برای عبور از سد امنیتی و لود جدول
        success = False
        for i in range(15):
            time.sleep(6) # صبر بیشتر برای شبکه تور
            
            # بررسی لود شدن المان اصلی جدول یا ردیف‌ها
            if page.ele('.ds-dex-table', timeout=2) or page.ele('.ds-dex-table-row', timeout=2):
                print("✅ جدول با موفقیت رویت شد.")
                success = True
                break
            
            # کلیک روی کپچا اگر وجود داشت
            if "verify" in page.title.lower() or "moment" in page.title.lower():
                print(f"⚠️ تشخیص کپچا (تلاش {i+1})...")
                btn = page.ele('@type=checkbox', timeout=2) or page.ele('text:Verify you are human', timeout=2)
                if btn:
                    btn.click(by_js=False)
                    print("👆 تیک زده شد.")
        
        # ۲. استخراج داده‌ها در صورت موفقیت
        if success:
            print("📊 در حال استخراج داده‌ها (لطفاً صبور باشید)...")
            time.sleep(15) # زمان طلایی برای لود کامل قیمت‌ها
            
            # گرفتن متن کل جدول
            table_raw = page.ele('.ds-dex-table')
            if not table_raw:
                table_raw = page.ele('tag:main') # لایه جایگزین
            
            data_text = table_raw.text
            data_list = data_text.splitlines()

            # استخراج لینک‌ها برای کنتراکت
            links = page.eles('tag:a')
            contracts = [l.attr('href').split('/')[-1] for l in links if l.attr('href') and len(l.attr('href').split('/')[-1]) > 30]

            # تمیزکاری داده‌ها
            titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
            dl_list = ['750', '3', '210', '880', '780', 'WP', 'V4', 'V3', 'V2', '/', 'CPMM', 'CLMM', 'V1', '100', '200']
            clean_data = [x for x in data_list if x not in dl_list and len(x) > 0]
            
            rows = []
            for i in range(0, len(clean_data) - 14, 15):
                rows.append(clean_data[i:i+15])

            if rows:
                df = pd.DataFrame(rows, columns=titles)
                if contracts:
                    unique_contracts = list(dict.fromkeys(contracts))
                    df['CONTRACT ADDRESS'] = (unique_contracts * (len(df)//len(unique_contracts)+1))[:len(df)]
                
                filename = f"report_{time.strftime('%H%M')}.csv"
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"💾 فایل {filename} با موفقیت ساخته شد.")

                # ۳. ارسال ایمیل با مدیریت خطا
                try:
                    yag = yagmail.SMTP(EMAIL_USER, EMAIL_PASS)
                    yag.send(to=RECIPIENT, subject=f"Dex Report {time.strftime('%H:%M')}", attachments=filename)
                    print("📧 ایمیل با موفقیت ارسال شد.")
                    # حذف فایل بعد از ارسال برای جلوگیری از پر شدن حافظه
                    os.remove(filename)
                except Exception as e:
                    print(f"❌ خطا در ارسال ایمیل (اما فایل در سرور موجود است): {e}")
            else:
                print("⚠️ داده‌ای در جدول یافت نشد. اسکرین‌شات چک شود.")
                page.get_screenshot('no_data.png')
        else:
            print("❌ صفحه لود شد اما جدول پیدا نشد. احتمالا کپچا رد نشده.")
            page.get_screenshot('failed_capture.png')

    except Exception as e:
        print(f"❌ خطای غیرمنتظره: {e}")
    finally:
        if page: page.quit()
        display.stop()
        print("--- پایان عملیات ---")

# زمان‌بندی ۱۰ دقیقه‌ای
schedule.every(10).minutes.do(timing)
timing() # اجرای اول

while True:
    schedule.run_pending()
    time.sleep(1)
