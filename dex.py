from DrissionPage import ChromiumPage, ChromiumOptions
from pyvirtualdisplay import Display
import pandas as pd
import yagmail
import schedule
import time
import os

# ==============================================================================
# 🔐 تنظیمات پروکسی شما (اعمال شده)
# ==============================================================================
PROXY_AUTH = "http://yahfeawc:37tdqv7zdv4b@31.59.20.176:6754"
# ==============================================================================

def timing():
    print(f"\n--- شروع عملیات با پروکسی اختصاصی: {time.strftime('%H:%M:%S')} ---")
    
    # ۱. راه‌اندازی نمایشگر مجازی
    display = Display(visible=0, size=(1920, 1080))
    display.start()
    
    page = None
    try:
        co = ChromiumOptions()
        co.set_argument('--no-sandbox')
        co.set_argument('--disable-dev-shm-usage')
        co.set_argument('--disable-gpu')
        
        # اعمال پروکسی شما به مرورگر
        print(f"🛡️ در حال اتصال به پروکسی: 31.59.20.176")
        co.set_proxy(PROXY_AUTH)
        
        # جعل هویت مرورگر (Fingerprinting)
        co.set_user_agent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
        
        page = ChromiumPage(co)
        
        print("🌐 ورود به سایت DexScreener...")
        page.get('https://dexscreener.com/', retry=3, interval=5)
        
        # ۲. مکانیزم عبور از لایه‌های امنیتی Cloudflare
        is_success = False
        for i in range(12):  # تلاش برای عبور (حدود ۶۰ ثانیه)
            time.sleep(5)
            
            # بررسی لود شدن جدول (نشانه پیروزی)
            if page.ele('.ds-dex-table', timeout=2):
                print("✅ موفقیت! جدول لود شد.")
                is_success = True
                break
            
            # کلیک روی تیک "Verify you are human" در صورت وجود
            title = page.title.lower()
            if "verify" in title or "just a moment" in title or "attention" in title:
                print(f"⚠️ شناسایی کپچا (تلاش {i+1}). در حال کلیک خودکار...")
                
                # پیدا کردن دکمه در تمام لایه‌ها (Shadow DOM)
                btn = page.ele('@type=checkbox', timeout=1) or \
                      page.ele('text:Verify you are human', timeout=1)
                
                if btn:
                    print("👆 کلیک فیزیکی انجام شد...")
                    btn.click(by_js=False)
                    time.sleep(5)
            else:
                # اگر صفحه گیر کرده بود، یکبار رفرش کن
                if i == 5:
                    print("🔄 رفرش مجدد صفحه برای باز شدن گره...")
                    page.refresh()

        # ۳. استخراج و پردازش داده‌ها
        if is_success:
            print("📥 در حال استخراج داده‌های جدول...")
            time.sleep(5) # صبر برای آپدیت قیمت‌ها
            
            table = page.ele('.ds-dex-table')
            data_list = table.text.splitlines()

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

            # فیلتر کردن کلمات مزاحم
            titles = ['RANK', 'TOKEN', 'EXCHANGE', 'FULL NAME', 'PRICE', 'AGE', 'TXNS', 'VOLUME', 'MAKERS', '5M', '1H', '6H', '24H', 'LIQUIDITY', 'MCAP']
            dl_list = ['750', '3', '210', '880', '780', 'WP', 'V4', 'V3', 'V2', '/', 'CPMM', 'CLMM', 'V1', '100', '200']
            clean_data = [x for x in data_list if x not in dl_list and len(x) > 0]
            
            rows = []
            for i in range(0, len(clean_data) - 14, 15):
                rows.append(clean_data[i:i+15])

            if rows:
                df = pd.DataFrame(rows, columns=titles)
                # مچ کردن کنتراکت‌ها با سطرها
                if contracts:
                    extended_contracts = (contracts * (len(df)//len(contracts)+1))[:len(df)]
                    df['CONTRACT ADDRESS'] = extended_contracts
                
                csv_file = 'dex_proxy_report.csv'
                df.to_csv(csv_file, index=False, encoding='utf-8-sig')
                print(f"💾 فایل با موفقیت ساخته شد ({len(df)} ردیف).")

                # ۴. ارسال ایمیل
                try:
                    yag = yagmail.SMTP('dexscreeneramirzamani@gmail.com', 'urcs rehx ttyt hzbv')
                    yag.send(
                        to='amirhosseinzamanifarsi@gmail.com', 
                        subject=f'Dex Report [Proxy] - {time.strftime("%H:%M")}', 
                        attachments=csv_file
                    )
                    print("📧 گزارش به ایمیل شما ارسال شد.")
                except Exception as e:
                    print(f"❌ خطا در ارسال ایمیل: {e}")
            else:
                print("⚠️ جدول پیدا شد اما دیتایی داخل آن نبود.")
        else:
            print("❌ متأسفانه با این پروکسی هم از کپچا عبور نکردیم.")
            page.get_screenshot('proxy_error.png')
            print("📸 اسکرین‌شات نهایی ذخیره شد (proxy_error.png)")

    except Exception as e:
        print(f"❌ ارور بحرانی: {e}")
    finally:
        if page: page.quit()
        display.stop()
        print("--- پایان عملیات ---")

# تنظیم زمان‌بندی ۱۰ دقیقه‌ای
schedule.every(10).minutes.do(timing)

# اجرای اول
timing()

while True:
    schedule.run_pending()
    time.sleep(1)
